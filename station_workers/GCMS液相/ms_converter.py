"""
mzML 转换和质谱图数据处理模块

功能：
1. 将 .D 文件夹转换为 mzML 格式
2. 从 mzML 文件中提取质谱数据
3. 生成质谱图所需的 m/z 和强度数据
"""

import os
import subprocess
import json
import tempfile
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

try:
    import pymzml
except ImportError:
    pymzml = None

# 可选的 numpy 支持（用于更健壮地处理 peaks 的返回类型）
try:
    import numpy as np
except Exception:
    np = None

logger = logging.getLogger(__name__)


class MSConverter:
    """mzML 格式转换器"""
    
    # 常见的 msconvert.exe 路径
    MSCONVERT_PATHS = [
        r'C:\Program Files\ProteoWizard\ProteoWizard 3.0.25323.6de0b61\msconvert.exe',
        r'C:\Program Files\ProteoWizard\msconvert.exe',
        r'C:\Program Files (x86)\ProteoWizard\msconvert.exe',
    ]
    
    def __init__(self, msconvert_path: Optional[str] = None):
        """
        初始化转换器
        
        Args:
            msconvert_path: msconvert.exe 的路径，若不提供则自动查找
        """
        self.msconvert_path = msconvert_path or self._find_msconvert()
        
    def _find_msconvert(self) -> Optional[str]:
        """查找 msconvert.exe 的路径，优先使用环境变量 MSCONVERT_EXE"""
        env_path = os.environ.get('MSCONVERT_EXE')
        if env_path and os.path.exists(env_path):
            logger.info(f"使用环境变量指定的 msconvert: {env_path}")
            return env_path
        for path in self.MSCONVERT_PATHS:
            if os.path.exists(path):
                logger.info(f"找到 msconvert: {path}")
                return path
        logger.warning("未找到 msconvert.exe，请安装 ProteoWizard 或设置环境变量 MSCONVERT_EXE 指向 msconvert.exe")
        return None
    
    def convert_to_mzml(self, input_folder: str, output_file: str) -> bool:
        """
        将 .D 文件夹转换为 mzML 格式
        
        Args:
            input_folder: 输入的 .D 文件夹路径
            output_file: 输出的 mzML 文件路径
            
        Returns:
            转换是否成功
        """
        if not self.msconvert_path:
            logger.error("msconvert.exe 未找到，无法进行转换")
            return False
        
        if not os.path.exists(input_folder):
            logger.error(f"输入文件夹不存在: {input_folder}")
            return False
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 调用 msconvert 进行转换
            base_name = os.path.splitext(os.path.basename(input_folder))[0]
            target_name = os.path.basename(output_file)
            # 调用 msconvert 并指定输出文件名
            cmd = [
                self.msconvert_path,
                '--mzML',
                input_folder,
                '-o', output_dir or '.',
                '--outfile', target_name
            ]
            
            logger.info(f"执行转换命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=False, timeout=1200)
            
            if result.returncode != 0:
                err = (result.stderr or b'').decode(errors='ignore')
                out = (result.stdout or b'').decode(errors='ignore')
                logger.error(f"转换失败: {err}\nSTDOUT: {out}")
                return False
            
            # 验证输出文件是否存在；若不存在，尝试按目录中查找
            if not os.path.exists(output_file):
                # 兼容某些版本忽略 --outfile 的情况
                candidate = os.path.join(output_dir or '.', f"{base_name}.mzML")
                if os.path.exists(candidate):
                    try:
                        # 将文件重命名为期望的输出路径
                        shutil.move(candidate, output_file)
                    except Exception:
                        pass
            
            exists = os.path.exists(output_file)
            logger.info(f"转换完成，目标文件{ '已找到' if exists else '未找到' }: {output_file}")
            return exists
            
        except subprocess.TimeoutExpired:
            logger.error("转换超时（600秒）")
            return False
        except Exception as e:
            logger.error(f"转换过程出错: {e}")
            return False


class MSDataExtractor:
    """质谱数据提取器"""
    
    def __init__(self, mzml_file_path: str):
        """
        初始化提取器
        
        Args:
            mzml_file_path: mzML 文件路径
        """
        if not pymzml:
            raise ImportError("pymzml 未安装，请运行: pip install pymzml")
        
        self.mzml_file_path = mzml_file_path
        self.spectra_cache = {}
        self.retention_time_map = {}  # 保留时间到 spectrum ID 的映射
        self._load_spectra()
    
    def _load_spectra(self):
        """加载 mzML 文件中的所有光谱，并规范化保留时间单位为分钟"""
        try:
            run = pymzml.run.Reader(self.mzml_file_path)
            rts = []
            tmp_map = {}
            for spectrum in run:
                spectrum_id = None
                try:
                    spectrum_id = spectrum.get('id', None)
                except Exception:
                    pass
                if not spectrum_id:
                    try:
                        spectrum_id = getattr(spectrum, 'ID', None) or spectrum.ID
                    except Exception:
                        spectrum_id = None
                if spectrum_id:
                    self.spectra_cache[spectrum_id] = spectrum
                    rt = self._extract_retention_time(spectrum)
                    if rt is not None:
                        tmp_map[spectrum_id] = rt
                        rts.append(rt)
            # 规范化单位：若绝大多数 RT > 100，视为秒，将其转换为分钟
            factor = 1.0
            if rts:
                count_over_100 = sum(1 for v in rts if v > 100)
                if count_over_100 / len(rts) > 0.5:
                    factor = 1.0 / 60.0
                for sid, rt in tmp_map.items():
                    norm_rt = rt * factor
                    self.retention_time_map[norm_rt] = sid
                    logger.debug(f"Spectrum {sid}: RT(raw)={rt}, RT(norm_min)={norm_rt}")
            # 统计信息
            try:
                rts_norm = sorted(self.retention_time_map.keys())
                if rts_norm:
                    rt_min = rts_norm[0]
                    rt_max = rts_norm[-1]
                    sample = rts_norm[:5]
                    logger.info(f"mzML加载完成: 光谱数={len(self.spectra_cache)}, RT条目={len(self.retention_time_map)}, RT范围(分钟)=[{rt_min:.4f}, {rt_max:.4f}], 示例={sample}")
                    # 同时打印到控制台，便于在 Worker 控制台可见
                    print(f"[MSDataExtractor] 加载 {os.path.basename(self.mzml_file_path)}: 光谱数={len(self.spectra_cache)}, RT范围(分)=[{rt_min:.4f}, {rt_max:.4f}]，示例={sample}")
                else:
                    logger.warning("mzML加载完成，但未解析到任何RT条目")
                    print("[MSDataExtractor] 警告：未解析到任何RT条目")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"加载 mzML 文件失败: {e}")
            raise
    
    def _extract_retention_time(self, spectrum) -> Optional[float]:
        """从光谱中提取保留时间，统一以分钟返回"""
        try:
            # 1) 首选 pymzml 提供的方法
            if hasattr(spectrum, 'scan_time_in_minutes'):
                rt = spectrum.scan_time_in_minutes()
                if rt is not None:
                    return float(rt)
            # 2) 常见键名（单位不确定，优先假设分钟）
            for key in ['scan time', 'retention time', 'retentionTime', 'scan start time']:
                if key in spectrum:
                    val = spectrum[key]
                    try:
                        return float(val)
                    except Exception:
                        pass
            # 3) mzML CV term（MS:1000016 为 scan start time，单位通常为分钟或秒）
            try:
                if 'MS:1000016' in spectrum:
                    val = spectrum['MS:1000016']
                    return float(val)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"提取保留时间失败: {e}")
        return None
    
    def get_spectrum_by_retention_time(self, rt: float, tolerance: float = 0.1) -> Optional[Dict]:
        """
        根据保留时间获取光谱（优先容差内，失败则返回 None）
        """
        closest_rt = None
        min_diff = float('inf')
        for stored_rt in self.retention_time_map.keys():
            diff = abs(stored_rt - rt)
            if diff < min_diff and diff <= tolerance:
                min_diff = diff
                closest_rt = stored_rt
        if closest_rt is None:
            logger.warning(f"未找到保留时间 {rt} 附近的光谱（容差: {tolerance}）")
            return None
        spectrum_id = self.retention_time_map[closest_rt]
        spectrum = self.spectra_cache.get(spectrum_id)
        if spectrum is None:
            return None
        return self._extract_spectrum_data(spectrum)

    def get_nearest_spectrum_any(self, rt: float) -> Tuple[Optional[float], Optional[Dict]]:
        """
        返回距离 rt 最近的光谱（不限制容差）。
        Returns: (matched_rt, spectrum_dict)；若无光谱则 (None, None)
        """
        if not self.retention_time_map:
            return None, None
        closest_rt = None
        min_diff = float('inf')
        for stored_rt in self.retention_time_map.keys():
            diff = abs(stored_rt - rt)
            if diff < min_diff:
                min_diff = diff
                closest_rt = stored_rt
        if closest_rt is None:
            return None, None
        spectrum_id = self.retention_time_map[closest_rt]
        spectrum = self.spectra_cache.get(spectrum_id)
        if spectrum is None:
            return None, None
        return closest_rt, self._extract_spectrum_data(spectrum)
    
    def _extract_spectrum_data(self, spectrum) -> Dict:
        """
        从光谱对象中提取 m/z 和强度数据（兼容多种 peaks 返回结构：二维数组、(mzs,ints) 二元组、列表/迭代器等）
        """
        mz_values: List[float] = []
        intensity_values: List[float] = []

        try:
            peaks = None
            # 优先 centroided
            try:
                peaks = spectrum.peaks('centroided')
            except Exception:
                peaks = None
            # 为空或长度为 0 则回退 raw
            need_fallback = (peaks is None)
            try:
                if not need_fallback and hasattr(peaks, '__len__'):
                    need_fallback = (len(peaks) == 0)
            except Exception:
                pass
            if need_fallback:
                try:
                    peaks = spectrum.peaks('raw')
                except Exception:
                    peaks = None
            # 无可用 peaks
            if peaks is None:
                return {'mz': [], 'intensity': [], 'peak_count': 0}

            # 情形1：(mzs, intensities) 二元组/列表
            try:
                if isinstance(peaks, (tuple, list)) and len(peaks) == 2:
                    mzs, ints = peaks[0], peaks[1]
                    if hasattr(mzs, '__len__') and hasattr(ints, '__len__') and len(mzs) == len(ints):
                        for idx in range(len(mzs)):
                            mz_values.append(float(mzs[idx]))
                            intensity_values.append(float(ints[idx]))
                        return {
                            'mz': mz_values,
                            'intensity': intensity_values,
                            'peak_count': len(mz_values)
                        }
            except Exception:
                pass

            # 情形2：二维数组/可索引序列，形如 [[mz,int], [mz,int], ...]
            try:
                first = peaks[0]
                if hasattr(first, '__len__') and len(first) >= 2:
                    for pair in peaks:
                        try:
                            mz_values.append(float(pair[0]))
                            intensity_values.append(float(pair[1]))
                        except Exception:
                            continue
                    return {
                        'mz': mz_values,
                        'intensity': intensity_values,
                        'peak_count': len(mz_values)
                    }
            except Exception:
                pass

            # 情形3：迭代器（逐个元素为二元）
            try:
                for peak in peaks:
                    try:
                        m = float(peak[0])
                        i = float(peak[1])
                        mz_values.append(m)
                        intensity_values.append(i)
                    except Exception:
                        continue
            except Exception:
                # peaks 不可迭代，直接返回空
                return {'mz': [], 'intensity': [], 'peak_count': 0}

        except Exception as e:
            logger.warning(f"提取光谱峰失败: {e}")

        return {
            'mz': mz_values,
            'intensity': intensity_values,
            'peak_count': len(mz_values)
        }
    
    def get_all_retention_times(self) -> List[float]:
        """获取所有保留时间"""
        return sorted(self.retention_time_map.keys())
    
    def get_spectrum_data_at_index(self, index: int) -> Optional[Dict]:
        """
        根据索引获取光谱数据
        
        Args:
            index: 光谱索引
            
        Returns:
            光谱数据字典
        """
        if index < 0 or index >= len(self.spectra_cache):
            return None
        
        spectrum_id = list(self.spectra_cache.keys())[index]
        spectrum = self.spectra_cache[spectrum_id]
        return self._extract_spectrum_data(spectrum)


class MSPlotter:
    """质谱图绘制器（数据处理）"""
    
    @staticmethod
    def prepare_mass_spectrum_data(mz_values: List[float], 
                                   intensity_values: List[float],
                                   max_points: int = 1000) -> Dict:
        """
        准备质谱图数据
        
        Args:
            mz_values: m/z 值列表
            intensity_values: 强度值列表
            max_points: 最大数据点数（用于降采样）
            
        Returns:
            包含处理后数据的字典
        """
        if not mz_values or not intensity_values:
            return {'mz': [], 'intensity': [], 'peak_count': 0}
        
        # 如果数据点过多，进行降采样
        n = len(mz_values)
        if n > max_points:
            step = max(1, n // max_points)
            mz_values = mz_values[::step]
            intensity_values = intensity_values[::step]
        
        return {
            'mz': mz_values,
            'intensity': intensity_values,
            'peak_count': len(mz_values),
            'max_mz': max(mz_values) if mz_values else 0,
            'min_mz': min(mz_values) if mz_values else 0,
            'max_intensity': max(intensity_values) if intensity_values else 0,
        }


class GCMSDataProcessor:
    """GCMS 数据处理器（整合转换和提取）"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化处理器
        
        Args:
            temp_dir: 临时目录，用于存放转换后的 mzML 文件（默认使用项目内持久缓存目录）
        """
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.temp_dir = os.path.join(base_dir, 'mzml_cache')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.converter = MSConverter()
        self.extractor = None
    
    def process_data_folder(self, data_folder: str, force_reconvert: bool = False, output_dir: Optional[str] = None, output_filename: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        处理数据文件夹，转换为 mzML 并返回路径
        
        Args:
            data_folder: .D 数据文件夹路径
            force_reconvert: 是否强制重新转换（忽略已有缓存）
            
        Returns:
            (成功标志, mzML文件路径, 错误信息)
        """
        if not os.path.exists(data_folder):
            return False, None, f"数据文件夹不存在: {data_folder}"
        
        try:
            folder_name = os.path.basename(data_folder).replace('.D', '').replace('.d', '')
            # 确定输出目标路径：优先使用传入的 output_dir/output_filename，否则回退至缓存目录+mtime 指纹
            if output_dir or output_filename:
                out_dir = output_dir or self.temp_dir
                os.makedirs(out_dir, exist_ok=True)
                target_name = output_filename or f"{folder_name}.mzML"
                output_file = os.path.join(out_dir, target_name)
                # 当明确指定输出文件名时，不清理旧文件；若文件已存在且不强制，则直接复用
                if (not force_reconvert) and os.path.exists(output_file):
                    logger.info(f"使用已存在的 mzML 文件: {output_file}")
                    self.extractor = MSDataExtractor(output_file)
                    return True, output_file, None
            else:
                # 使用目录的最后修改时间作为指纹，避免复用旧数据
                try:
                    mtime = int(os.path.getmtime(data_folder))
                except Exception:
                    mtime = int(time.time())  # 兜底
                output_file = os.path.join(self.temp_dir, f"{folder_name}_{mtime}.mzML")
                # 若非强制，且目标文件已存在，则直接复用
                if (not force_reconvert) and os.path.exists(output_file):
                    logger.info(f"使用已存在的 mzML 文件: {output_file}")
                    self.extractor = MSDataExtractor(output_file)
                    return True, output_file, None
                # 仅在未指定固定输出名时，为避免缓存堆积，清理同前缀的旧缓存
                try:
                    for p in os.listdir(self.temp_dir):
                        if p.startswith(f"{folder_name}_") and p.endswith('.mzML'):
                            fullp = os.path.join(self.temp_dir, p)
                            try:
                                os.remove(fullp)
                            except Exception:
                                pass
                except Exception:
                    pass

            # 执行转换
            logger.info(f"开始转换: {data_folder} -> {output_file}")
            success = self.converter.convert_to_mzml(data_folder, output_file)
            if not success:
                return False, None, "mzML 转换失败"
            # 加载提取器
            self.extractor = MSDataExtractor(output_file)
            return True, output_file, None
            
        except Exception as e:
            logger.error(f"处理数据文件夹时出错: {e}")
            return False, None, str(e)
    
    def get_mass_spectrum_at_retention_time(self, rt: float, tolerance: float = 0.1) -> Optional[Dict]:
        """
        获取指定保留时间的质谱数据
        
        Args:
            rt: 保留时间（分钟）
            tolerance: 容差（分钟）
            
        Returns:
            质谱数据字典
        """
        if not self.extractor:
            logger.warning("提取器未初始化")
            return None
        
        # 先用给定容差尝试，不行则退而求其次扩大容差
        spectrum_data = self.extractor.get_spectrum_by_retention_time(rt, tolerance=tolerance)
        if spectrum_data is None and tolerance < 0.3:
            spectrum_data = self.extractor.get_spectrum_by_retention_time(rt, tolerance=0.3)
        if spectrum_data is None:
            return None
        
        return MSPlotter.prepare_mass_spectrum_data(
            spectrum_data['mz'],
            spectrum_data['intensity']
        )
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理临时目录: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")

