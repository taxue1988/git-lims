import websocket
import json
import threading
import time
import sys
import os
import shutil
from datetime import datetime

# 添加项目根目录到 Python 路径，以便导入 GCMS 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '模块开发运行代码', 'GCMS模块'))

try:
    from GCMS监测 import GCMS_module
except ImportError:
    print("警告: 无法导入 GCMS_module，将使用模拟模式")
    GCMS_module = None

# 导入序列管理器
try:
    from station_workers.GCMS液相.sequence_manager import get_sequence_file
    from station_workers.GCMS液相.sequence_manager import get_result_csv_path
    from station_workers.GCMS液相.sequence_manager import load_sequence_params_map
except Exception:
    # 兼容直接运行
    from sequence_manager import get_sequence_file
    from sequence_manager import get_result_csv_path
    from sequence_manager import load_sequence_params_map

# 导入质谱数据处理模块
try:
    from station_workers.GCMS液相.ms_converter import GCMSDataProcessor, MSPlotter
except Exception:
    try:
        from ms_converter import GCMSDataProcessor, MSPlotter
    except ImportError:
        print("警告: 无法导入 GCMSDataProcessor/MSPlotter，质谱功能将不可用")
        GCMSDataProcessor = None
        MSPlotter = None

import csv
import urllib.request
import urllib.error


class GcmsWorker:
    def __init__(self, server_url=None):
        # 优先级：入参 > 环境变量 GCMS_SERVER_URL > 默认公网地址（非TLS）
        self.server_url = (
            server_url
            or os.environ.get("GCMS_SERVER_URL")
            or "ws://192.168.58.8:8000/ws/gcms/"
        )
        self.ws = None
        self.gcms_module = None
        self.is_connected = False
        self.arm_is_connected = False
        self.instrument_is_connected = False
        self.current_status = "离线"
        
        # 质谱数据处理器
        self.ms_processor = None
        self.current_sequence_index = None
        self.current_data_folder = None
        self.current_data_mtime = None

        # 峰提取（MassHunter Qual 服务）
        self.qual_base_url = os.environ.get("GCMS_QUAL_BASE_URL", "http://192.168.58.125:8082")

        # 初始化 GCMS 模块
        self.init_gcms_module()
        
        # 初始化质谱处理器
        self.init_ms_processor()

    def init_gcms_module(self):
        """初始化 GCMS 模块并独立检查其组件"""
        try:
            if GCMS_module:
                self.gcms_module = GCMS_module()

                # 独立检查机械臂连接
                if self.gcms_module.check_arm_connection():
                    self.arm_is_connected = True
                    print("机械臂连接成功")
                else:
                    self.arm_is_connected = False
                    print("错误：机械臂连接失败")

                # 独立检查GCMS仪器连接
                if self.gcms_module.check_instrument_connection():
                    self.instrument_is_connected = True
                    print("GCMS仪器连接成功")
                else:
                    self.instrument_is_connected = False
                    print("错误：GCMS仪器连接失败")

                self.current_status = "就绪"  # Worker本身是就绪的
                print("GCMS 模块初始化完成")

            else:
                print("GCMS 模块未找到，无法进行操作")
                self.current_status = "模块未找到"
        except Exception as e:
            print(f"GCMS 模块初始化失败: {e}")
            self.gcms_module = None
            self.current_status = "初始化失败"
    
    def init_ms_processor(self):
        """初始化质谱数据处理器"""
        try:
            if GCMSDataProcessor:
                self.ms_processor = GCMSDataProcessor()
                print("质谱数据处理器初始化完成")
            else:
                print("警告: GCMSDataProcessor 未可用，质谱功能将不可用")
        except Exception as e:
            print(f"质谱处理器初始化失败: {e}")
            self.ms_processor = None
    
    def on_message(self, ws, message):
        """处理从服务器接收到的消息"""
        try:
            data = json.loads(message)
            
            # 如果消息是 worker 自己发送的，则忽略
            if data.get('sender') == 'worker':
                return
                
            command = data.get('message', '')
            print(f"收到指令: {command}")
            
            # 根据不同的指令执行不同的操作
            if command == "get_status":
                self.handle_get_status()
            elif command == "get_arm_status":
                self.handle_get_arm_status()
            elif command.startswith("start_analysis_"):
                parts = command.split("_")
                # 兼容旧格式: start_analysis_{bottle}
                if len(parts) == 3:
                    bottle_num = int(parts[-1])
                    sequence_index = None
                elif len(parts) >= 4:
                    bottle_num = int(parts[-2])
                    sequence_index = int(parts[-1])
                else:
                    self.send_response({'type': 'error', 'message': f"指令格式错误: {command}"})
                    return
                self.handle_start_analysis(bottle_num, sequence_index)
            elif command == "move_tower":
                self.handle_move_tower()
            elif command == "get_instrument_info":
                self.handle_get_instrument_info()
            elif command == "get_sequence_list":
                self.handle_get_sequence_list()
            elif command.startswith("get_result_"):
                # 兼容 archive_id 中包含下划线：格式 get_result_{bottle}_{sequence}_{archiveId...}
                payload = command[len("get_result_"):]
                bottle_num = None
                sequence_index = None
                archive_id = None
                try:
                    parts = payload.split("_")
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        bottle_num = int(parts[0])
                        sequence_index = int(parts[1])
                        archive_id = "_".join(parts[2:]) if len(parts) > 2 else None
                    elif len(parts) >= 1 and parts[0].isdigit():
                        # 仅提供了 sequence（兼容旧格式 get_result_{sequence}）
                        sequence_index = int(parts[0])
                        archive_id = "_".join(parts[1:]) if len(parts) > 1 else None
                    else:
                        raise ValueError("格式不匹配")
                except Exception:
                    self.send_response({'type': 'error', 'message': f"指令格式错误: {command}"})
                    return
                self.handle_get_result(bottle_num, sequence_index, archive_id)
            elif command.startswith("get_mass_spectrum_"):
                # 支持两种格式:
                # 1) get_mass_spectrum_{sequence_index}_{retention_time}
                # 2) get_mass_spectrum_{sequence_index}_{retention_time}_{archiveId...}
                try:
                    payload = command[len("get_mass_spectrum_"):]
                    parts = payload.split("_")
                    if len(parts) < 2:
                        raise ValueError("参数数量不正确")
                    sequence_index = int(parts[0])
                    retention_time = float(parts[1])
                    archive_id = "_".join(parts[2:]) if len(parts) > 2 else None
                except Exception:
                    self.send_response({'type': 'error', 'message': f"质谱请求指令格式错误: {command}"})
                    return
                self.handle_get_mass_spectrum(sequence_index, retention_time, archive_id)
            elif command.startswith("get_peaks_"):
                # 支持格式:
                # 1) get_peaks_{sequence_index}_{archiveId...}  -> 默认 1%
                # 2) get_peaks_{sequence_index}_{percent}_{archiveId...}（percent 必须在 0~100 之间）
                try:
                    payload = command[len("get_peaks_"):]
                    parts = payload.split("_")
                    if len(parts) < 1:
                        raise ValueError("参数数量不正确")
                    sequence_index = int(parts[0])
                    relative_percent = 1.0
                    archive_id = None
                    if len(parts) >= 2:
                        token = parts[1]
                        # 仅当 token 可解析为 [0,100] 的数字时才视为百分比，否则视为 archiveId 的开始
                        try:
                            v = float(token)
                            if 0.0 <= v <= 100.0:
                                relative_percent = v
                                archive_id = "_".join(parts[2:]) if len(parts) > 2 else None
                            else:
                                archive_id = "_".join(parts[1:]) if len(parts) > 1 else None
                        except Exception:
                            archive_id = "_".join(parts[1:]) if len(parts) > 1 else None
                except Exception:
                    self.send_response({'type': 'error', 'message': f"峰信息请求指令格式错误: {command}"})
                    return
                self.handle_get_peaks(sequence_index, archive_id, relative_percent)
            else:
                self.send_response({'type': 'error', 'message': f"未知指令: {command}"})
                
        except json.JSONDecodeError:
            print(f"无法解析消息: {message}")
        except Exception as e:
            print(f"处理消息时出错: {e}")
            self.send_response({'type': 'error', 'message': f"处理指令时出错: {str(e)}"})
    
    def handle_get_status(self):
        """获取 GCMS 整体状态"""
        try:
            # 检查模块是否加载，以及仪器在初始化时是否连接成功
            if self.gcms_module and self.instrument_is_connected:
                # 实时检查仪器连接
                if self.gcms_module.check_instrument_connection():
                    try:
                        run_status = self.gcms_module.instrument_control.get_run_status()
                        run_mode = self.gcms_module.instrument_control.get_run_mode()
                        status_info = {
                            "type": "status_update",
                            "status": "运行中" if run_mode != '"NotRun"' else "就绪",
                            "run_status": run_status,
                            "run_mode": run_mode,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    except Exception as e:
                        status_info = {
                            "type": "status_update",
                            "status": "连接失败",
                            "error": f"获取仪器状态时出错: {str(e)}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                else:
                    self.instrument_is_connected = False # 更新状态标志
                    status_info = {
                        "type": "status_update",
                        "status": "连接失败",
                        "error": "GCMS仪器通信中断",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                status_info = {
                    "type": "status_update",
                    "status": "连接失败",
                    "error": "GCMS仪器未连接或模块初始化失败",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            self.send_response(status_info)
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取GCMS状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)

    def handle_get_mass_spectrum(self, sequence_index, retention_time, archive_id=None):
        """处理获取质谱图的请求"""
        try:
            if not self.ms_processor:
                self.send_response({
                    'type': 'mass_spectrum_result',
                    'sequence_index': sequence_index,
                    'retention_time': retention_time,
                    'available': False,
                    'message': '质谱处理器未初始化'
                })
                return

            # 1) 若提供了归档ID，优先使用归档同名 meta.json 指定的 .D 数据目录
            data_folder_from_meta = None
            archive_dir = None
            if archive_id:
                try:
                    archive_dir = self._ensure_archive_dir()
                    meta_path = os.path.join(archive_dir, f"{archive_id}.meta.json")
                    if os.path.isfile(meta_path):
                        with open(meta_path, 'r', encoding='utf-8') as mf:
                            meta = json.load(mf)
                            if isinstance(meta, dict) and meta.get('data_folder'):
                                data_folder_from_meta = os.path.normpath(meta['data_folder'])
                except Exception as e:
                    print(f"读取归档元数据失败: {e}")

            # 2) 决定本次要用的数据文件夹
            data_folder = data_folder_from_meta
            if not data_folder:
                # 回退到参数表
                params = load_sequence_params_map()
                triple = params.get(sequence_index)
                if not triple:
                    raise RuntimeError(f"未找到序列 {sequence_index} 的参数")
                _seq_file, data_name, data_path = triple
                folder_name = data_name if data_name.lower().endswith('.d') else f"{data_name}.D"
                data_folder = os.path.normpath(os.path.join(data_path, folder_name))

                if not os.path.isdir(data_folder):
                    try:
                        candidates = []
                        for entry in os.listdir(data_path):
                            if entry.lower().startswith(data_name.lower()) and entry.lower().endswith('.d'):
                                p = os.path.join(data_path, entry)
                                try:
                                    mtime = os.path.getmtime(p)
                                    candidates.append((mtime, os.path.normpath(p)))
                                except Exception:
                                    pass
                        if candidates:
                            candidates.sort(reverse=True)
                            data_folder = candidates[0][1]
                    except Exception:
                        pass

                if not os.path.isdir(data_folder):
                    raise RuntimeError(f"未找到序列 {sequence_index} 对应的数据文件夹: {data_folder}")

                print(f"为序列 {sequence_index} 加载新的数据文件夹: {data_folder}")
                # 记录当前数据文件夹的修改时间，用于判断是否需要重新转换
                try:
                    data_mtime = int(os.path.getmtime(data_folder))
                except Exception:
                    data_mtime = None
                # 按需强制重转（相同序列但数据更新时也会重转）
                # 为避免覆盖历史文件，使用唯一文件名（优先 archive_id）
                folder_base = os.path.basename(data_folder).replace('.D','').replace('.d','')
                out_name = f"{folder_base}_{archive_id}.mzML" if archive_id else f"{folder_base}_{int(time.time()*1000)}.mzML"
                target_path = os.path.join(self.ms_processor.temp_dir, out_name)
                force_flag = not os.path.exists(target_path)
                success, mzml_path, error = self.ms_processor.process_data_folder(
                    data_folder,
                    force_reconvert=force_flag,
                    output_dir=self.ms_processor.temp_dir,
                    output_filename=out_name
                )
                if not success:
                    raise RuntimeError(f"处理数据文件夹失败: {error}")
                print(f"mzML 转换完成: {mzml_path}")
                # 通知前端缓存位置
                self.send_response({
                    'type': 'msconvert_info',
                    'sequence_index': sequence_index,
                    'data_folder': data_folder,
                    'mzml_path': mzml_path
                })
                
                self.current_sequence_index = sequence_index
                self.current_data_folder = data_folder
                self.current_data_mtime = data_mtime
            else:
                # 使用归档指定的目录
                self.current_sequence_index = sequence_index
                self.current_data_folder = data_folder
                try:
                    current_mtime = int(os.path.getmtime(self.current_data_folder)) if self.current_data_folder else None
                except Exception:
                    current_mtime = None
                need_reconvert = (self.current_data_mtime is None) or (current_mtime is None) or (current_mtime != self.current_data_mtime)
                if need_reconvert:
                    print(f"使用归档目录进行转换: {self.current_data_folder}")
                    folder_base = os.path.basename(self.current_data_folder).replace('.D','').replace('.d','')
                    out_name = f"{folder_base}_{archive_id}.mzML" if archive_id else f"{folder_base}_{int(time.time()*1000)}.mzML"
                    target_path = os.path.join(self.ms_processor.temp_dir, out_name)
                    force_flag = not os.path.exists(target_path)
                    success, mzml_path, error = self.ms_processor.process_data_folder(
                        self.current_data_folder,
                        force_reconvert=force_flag,
                        output_dir=self.ms_processor.temp_dir,
                        output_filename=out_name
                    )
                    if not success:
                        raise RuntimeError(f"处理数据文件夹失败: {error}")
                    print(f"mzML 转换完成: {mzml_path}")
                    self.send_response({
                        'type': 'msconvert_info',
                        'sequence_index': sequence_index,
                        'data_folder': self.current_data_folder,
                        'mzml_path': mzml_path
                    })
                    self.current_data_mtime = current_mtime

            # 获取质谱数据（单位自适应 + 扩大容差提升命中率）
            rt_query = retention_time
            try:
                # 若 mzML 的 RT（分钟）最大值明显小于请求值，说明前端传的是秒，先换算为分钟
                if self.ms_processor and self.ms_processor.extractor:
                    rts_all = list(self.ms_processor.extractor.retention_time_map.keys())
                    if rts_all:
                        rt_max = max(rts_all)
                        if rt_max and retention_time > (rt_max * 2):
                            rt_query = retention_time / 60.0
            except Exception:
                rt_query = retention_time

            spectrum_data = self.ms_processor.get_mass_spectrum_at_retention_time(rt_query, tolerance=0.1)
            # 若仍未命中，尝试备用换算（双向尝试）
            if not spectrum_data:
                spectrum_data = self.ms_processor.get_mass_spectrum_at_retention_time(retention_time/60.0, tolerance=0.1)
            if not spectrum_data:
                spectrum_data = self.ms_processor.get_mass_spectrum_at_retention_time(retention_time, tolerance=0.5)
            if not spectrum_data:
                # 兜底：不设容差限制，取最近的一个光谱
                try:
                    if self.ms_processor and self.ms_processor.extractor:
                        matched_rt, spec_raw = self.ms_processor.extractor.get_nearest_spectrum_any(rt_query)
                        if spec_raw:
                            spectrum_data = MSPlotter.prepare_mass_spectrum_data(spec_raw.get('mz', []), spec_raw.get('intensity', []))
                            rt_query = matched_rt if matched_rt is not None else rt_query
                except Exception:
                    pass

            if not spectrum_data:
                self.send_response({
                    'type': 'mass_spectrum_result',
                    'sequence_index': sequence_index,
                    'retention_time': retention_time,
                    'available': False,
                    'message': f'在保留时间 {retention_time:.2f} 附近未找到质谱数据（已尝试单位换算、扩大容差与就近匹配）'
                })
                return

            # 计算最接近的实际 RT（分钟）用于显示
            nearest_rt = None
            try:
                if self.ms_processor and self.ms_processor.extractor:
                    rts = list(self.ms_processor.extractor.retention_time_map.keys())
                    if rts:
                        nearest_rt = min(rts, key=lambda v: abs(v - rt_query))
            except Exception:
                nearest_rt = None

            self.send_response({
                'type': 'mass_spectrum_result',
                'sequence_index': sequence_index,
                'retention_time': nearest_rt if nearest_rt is not None else rt_query,
                'requested_rt': retention_time,
                'available': True,
                'series': spectrum_data,
                'archive_id': archive_id
            })

        except Exception as e:
            self.send_response({
                'type': 'error',
                'message': f'获取质谱图失败: {str(e)}'
            })
    
    def _resolve_data_folder_for_sequence(self, sequence_index, archive_id=None):
        """根据 archive_id 或 CSV 参数解析 .D 数据目录路径。"""
        # 优先：归档 meta
        if archive_id:
            try:
                archive_dir = self._ensure_archive_dir()
                meta_path = os.path.join(archive_dir, f"{archive_id}.meta.json")
                if os.path.isfile(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                        d = meta.get('data_folder')
                        if d and os.path.isdir(d):
                            return os.path.normpath(d)
            except Exception:
                pass
        # 回退：CSV 参数表
        params = load_sequence_params_map()
        triple = params.get(sequence_index)
        if not triple:
            raise RuntimeError(f"未找到序列 {sequence_index} 的参数")
        _seq_file, data_name, data_path = triple
        folder_name = data_name if data_name.lower().endswith('.d') else f"{data_name}.D"
        data_folder = os.path.normpath(os.path.join(data_path, folder_name))
        if os.path.isdir(data_folder):
            return data_folder
        # 回退：在 data_path 下模糊匹配最新 .D 目录
        candidates = []
        try:
            for entry in os.listdir(data_path):
                if entry.lower().startswith(data_name.lower()) and entry.lower().endswith('.d'):
                    p = os.path.join(data_path, entry)
                    try:
                        mtime = os.path.getmtime(p)
                    except Exception:
                        mtime = 0
                    candidates.append((mtime, os.path.normpath(p)))
        except Exception:
            pass
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]
        raise RuntimeError(f"未找到序列 {sequence_index} 对应的数据目录")

    def _call_qual_find_peaks(self, data_dir, relative_area_percent=1.0):
        """调用 MassHunter Qual 的 /qual/findPeaks 服务，返回列表。"""
        url = f"{self.qual_base_url}/qual/findPeaks"
        payload = {
            "dataDir": data_dir,
            "filter": {
                "msLevel": "All",
                "scanType": "All",
                "chromatogramType": "TotalIon",
                "smoothFunction": "Gaussian",
                "smoothGaussianWidth": 5,
                "smoothFunctionWidth": 15,
                "relativeAreaPercent": float(relative_area_percent) / 100.0
            }
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            return json.loads(text)

    def handle_get_peaks(self, sequence_index, archive_id=None, relative_area_percent=1.0):
        """实时获取峰信息（centerX/area 等），每次查看都从当前路径重新拉取。"""
        try:
            data_folder = self._resolve_data_folder_for_sequence(sequence_index, archive_id)
            peaks = self._call_qual_find_peaks(data_folder, relative_area_percent=relative_area_percent)
            if not isinstance(peaks, list):
                raise RuntimeError("峰信息返回格式异常")
            # 仅回传关心字段，避免过大
            simplified = []
            for p in peaks:
                try:
                    simplified.append({
                        'centerX': float(p.get('centerX', 0) or 0),
                        'area': float(p.get('area', 0) or 0),
                        'startX': float(p.get('startX', 0) or 0),
                        'endX': float(p.get('endX', 0) or 0),
                        'width': float(p.get('width', 0) or 0),
                        'baselineIsLinear': p.get('baselineIsLinear', None)
                    })
                except Exception:
                    continue
            self.send_response({
                'type': 'peaks_result',
                'sequence_index': sequence_index,
                'archive_id': archive_id,
                'available': True,
                'relative_area_percent': float(relative_area_percent),
                'data_folder': data_folder,
                'peaks': simplified
            })
        except urllib.error.HTTPError as e:
            self.send_response({
                'type': 'peaks_result',
                'sequence_index': sequence_index,
                'archive_id': archive_id,
                'available': False,
                'message': f'Qual服务错误: {e.code} {e.reason}'
            })
        except Exception as e:
            self.send_response({
                'type': 'peaks_result',
                'sequence_index': sequence_index,
                'archive_id': archive_id,
                'available': False,
                'message': f'获取峰失败: {str(e)}'
            })

    def handle_get_arm_status(self):
        """获取机械臂状态"""
        try:
            # 检查模块是否加载，以及机械臂在初始化时是否连接成功
            if self.gcms_module and self.arm_is_connected:
                # 实时检查机械臂连接
                if self.gcms_module.check_arm_connection():
                    try:
                        b_value = self.gcms_module.get_b_status()
                        arm_info = {
                            "type": "arm_status",
                            "b_value": b_value,
                            "status": "正常",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    except Exception as e:
                        arm_info = {
                            "type": "arm_status",
                            "status": "连接失败",
                            "error": f"获取机械臂状态时出错: {str(e)}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                else:
                    self.arm_is_connected = False # 更新状态标志
                    arm_info = {
                        "type": "arm_status",
                        "status": "连接失败",
                        "error": "机械臂通信中断",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                arm_info = {
                    "type": "arm_status",
                    "status": "连接失败",
                    "error": "机械臂未连接或模块初始化失败",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            self.send_response(arm_info)
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取机械臂状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取机械臂状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_start_analysis(self, bottle_num, sequence_index=None):
        """开始分析指定瓶号的样品，可选指定序列号"""
        try:
            if self.gcms_module:
                # 在新线程中执行分析，避免阻塞 WebSocket 连接
                analysis_thread = threading.Thread(
                    target=self.run_analysis,
                    args=(bottle_num, sequence_index)
                )
                analysis_thread.daemon = True
                analysis_thread.start()
                
                start_info = {
                    "type": "analysis_started",
                    "bottle_num": bottle_num,
                    "sequence_index": sequence_index,
                    "message": f"开始分析瓶号 {bottle_num} 的样品",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.send_response(start_info)
            else:
                error_info = {
                    "type": "analysis_error",
                    "bottle_num": bottle_num,
                    "sequence_index": sequence_index,
                    "message": "GCMS模块未就绪，无法开始分析。",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.send_response(error_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"启动分析失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def run_analysis(self, bottle_num, sequence_index=None):
        """在后台线程中运行分析，并发送详细进度。若提供序列号则按映射运行对应序列文件。"""
        def send_progress(stage, message):
            progress_info = {
                "type": "analysis_progress",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
                "stage": stage,
                "message": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(progress_info)
 
        try:
            self.current_status = "分析中"
            send_progress("任务开始", f"开始分析瓶号 {bottle_num}")
 
            # 实际的分析流程，分解自 self.gcms_module.start(bottle_num)
            send_progress("设备准备", "移动GCMS塔...")
            self.gcms_module.gc_move_to_tower()
            time.sleep(1) # 模拟操作耗时
 
            send_progress("机械臂操作", f"机械臂夹取 {bottle_num} 号瓶至GCMS")
            self.gcms_module.kb_to_gcms(bottle_num)
            time.sleep(1)
 
            send_progress("仪器分析", "GCMS开始执行分析序列...")
            if sequence_index is not None:
                seq_file = get_sequence_file(int(sequence_index))
                if not seq_file:
                    raise RuntimeError(f"未找到序列号 {sequence_index} 对应的序列文件")
                # 调用底层仪器方法直接按文件启动
                self.gcms_module.instrument_control.start_data_acquisition(seq_file, 0, True)
            else:
                # 兼容旧逻辑：调用预设序列
                self.gcms_module.gc_action_conb()
            time.sleep(5)
 
            send_progress("等待分析完成", "GCMS运行中，请稍候...")
            while self.gcms_module.instrument_control.get_run_mode() != '"NotRun"':
                time.sleep(10)
             
            send_progress("设备复位", "分析完成，准备复位设备")
            time.sleep(5)
            self.gcms_module.gc_move_to_tower()
            time.sleep(2)
 
            send_progress("机械臂操作", f"机械臂取回 {bottle_num} 号瓶")
            self.gcms_module.gc_drop(bottle_num)
             
            # 等待结果文件生成并归档（最多等待 ~60s）
            archive_id = None
            try:
                from .sequence_manager import get_result_csv_path as _find_result
            except Exception:
                from sequence_manager import get_result_csv_path as _find_result

            last_result_path = None
            max_waits = 30
            for _ in range(max_waits):
                path_try = _find_result(int(sequence_index)) if sequence_index is not None else None
                if path_try and os.path.isfile(path_try):
                    last_result_path = path_try
                    try:
                        archive_id = self.archive_result(sequence_index)
                        # 写入本次运行的元数据（记录本次使用的 .D 路径）
                        if archive_id and last_result_path:
                            try:
                                archive_dir = self._ensure_archive_dir()
                                meta_path = os.path.join(archive_dir, f"{archive_id}.meta.json")
                                meta = {"data_folder": os.path.dirname(last_result_path)}
                                with open(meta_path, 'w', encoding='utf-8') as mf:
                                    json.dump(meta, mf, ensure_ascii=False)
                            except Exception as _e:
                                print(f"写入归档元数据失败: {_e}")
                    except Exception:
                        archive_id = None
                    break
                time.sleep(2)

            # 发送分析完成通知
            complete_info = {
                "type": "analysis_complete",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
                "archive_id": archive_id,
                "message": f"瓶号 {bottle_num} 分析完成",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(complete_info)
            self.current_status = "就绪"
 
        except Exception as e:
            error_info = {
                "type": "analysis_error",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
                "message": f"分析过程中出错: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
            self.current_status = "错误"
    
    def handle_move_tower(self):
        """移动塔位置"""
        try:
            if self.gcms_module:
                try:
                    self.gcms_module.gc_move_to_tower()
                    tower_info = {
                        "type": "tower_moved",
                        "message": "塔位置移动完成",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    tower_info = {
                        "type": "error",
                        "message": f"塔位置移动失败: {str(e)}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

            
            self.send_response(tower_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"移动塔位置失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_get_instrument_info(self):
        """获取仪器信息"""
        try:
            if self.gcms_module:
                try:
                    model = self.gcms_module.instrument_control.get_model()
                    laboratory = self.gcms_module.instrument_control.get_laboratory()
                    
                    instrument_info = {
                        "type": "instrument_info",
                        "model": model,
                        "laboratory": laboratory,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    instrument_info = {
                        "type": "error",
                        "message": f"获取仪器信息失败: {str(e)}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

            
            self.send_response(instrument_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取仪器信息失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)

    def handle_get_sequence_list(self):
        """获取序列清单"""
        try:
            # 构造 items 数组 [{index, name}, ...]
            items = []
            # 读取映射
            mapping = {}
            try:
                # 内部加载，若失败则为空
                from .sequence_manager import load_sequence_map  # 再次局部导入以避免循环
            except Exception:
                from sequence_manager import load_sequence_map
            mapping = load_sequence_map() or {}
            for k in sorted(mapping.keys()):
                items.append({"index": k, "name": mapping[k]})

            payload = {
                "type": "sequence_list",
                "items": items,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(payload)
        except Exception as e:
            self.send_response({
                "type": "error",
                "message": f"获取序列清单失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

    def handle_get_result(self, bottle_num, sequence_index, archive_id=None):
        """读取归档结果（必须提供 archive_id），返回裁剪后的 x/y 数据。
        为避免在任务未运行/未完成时误读旧文件，这里强制要求提供 archive_id。
        """
        try:
            # 必须提供归档ID
            if not archive_id:
                self.send_response({
                    'type': 'analysis_result',
                    'bottle_num': bottle_num,
                    'sequence_index': sequence_index,
                    'available': False,
                    'message': '任务未完成或未归档，无法查看结果（缺少归档ID）'
                })
                return

            path = self.get_archive_file_path(archive_id)
            if not path:
                self.send_response({
                    'type': 'analysis_result',
                    'bottle_num': bottle_num,
                    'sequence_index': sequence_index,
                    'available': False,
                    'message': '归档结果不存在或已被清理',
                    'debug': { 'archive_id': archive_id }
                })
                return

            x_vals = []
            y_vals = []
            try:
                with open(path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    # 跳过表头（若有）
                    first = next(reader, None)
                    # 如果首行两列均为数字，则视为数据行，否则跳过
                    if first is not None:
                        try:
                            _x0 = float(first[0])
                            _y0 = float(first[1])
                            x_vals.append(_x0)
                            y_vals.append(_y0)
                        except Exception:
                            pass
                    for row in reader:
                        if len(row) < 2:
                            continue
                        try:
                            x = float(row[0])
                            y = float(row[1])
                            x_vals.append(x)
                            y_vals.append(y)
                        except Exception:
                            continue
            except Exception as e:
                self.send_response({
                    'type': 'analysis_result',
                    'bottle_num': bottle_num,
                    'sequence_index': sequence_index,
                    'available': False,
                    'message': f'读取CSV失败: {str(e)}'
                })
                return

            # 不再在后端做抽样，完整返回数据点（由前端按需降采样显示）
            # 如需保护带宽，可在此处加更高阈值再做抽样，例如 > 200000 点再抽样。
            n = len(x_vals)
            # 保留原顺序与完整形状

            self.send_response({
                'type': 'analysis_result',
                'bottle_num': bottle_num,
                'sequence_index': sequence_index,
                'available': True,
                'series': {'x': x_vals, 'y': y_vals},
                'archive_id': archive_id,
                'path': path
            })
        except Exception as e:
            self.send_response({
                'type': 'error',
                'message': f'获取结果失败: {str(e)}'
            })

    def _ensure_archive_dir(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        archive_dir = os.path.join(base_dir, 'results_archive')
        os.makedirs(archive_dir, exist_ok=True)
        return archive_dir

    def archive_result(self, sequence_index):
        """复制当前结果文件到归档目录，返回 archive_id（时间戳+序列）。"""
        src = get_result_csv_path(int(sequence_index))
        if not src or not os.path.isfile(src):
            return None
        archive_dir = self._ensure_archive_dir()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_id = f"{ts}_seq{sequence_index}"
        dst = os.path.join(archive_dir, f"{archive_id}.csv")
        shutil.copy2(src, dst)
        return archive_id

    def get_archive_file_path(self, archive_id):
        if not archive_id:
            return None
        archive_dir = self._ensure_archive_dir()
        candidate = os.path.join(archive_dir, f"{archive_id}.csv")
        return candidate if os.path.isfile(candidate) else None
    
    def send_response(self, message):
        """发送响应消息到服务器"""
        if self.ws and self.is_connected:
            try:
                # 直接发送消息，不再进行二次打包
                response_data = {
                    "message": message,
                    "sender": "worker"  # 添加发送者标识
                }
                self.ws.send(json.dumps(response_data))
            except Exception as e:
                print(f"发送消息失败: {e}")
    
    def on_error(self, ws, error):
        """处理 WebSocket 错误"""
        print(f"WebSocket 错误: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """处理 WebSocket 连接关闭"""
        print("WebSocket 连接已关闭")
        self.is_connected = False
    
    def on_open(self, ws):
        """处理 WebSocket 连接建立"""
        print("GCMS Worker 已连接到服务器")
        self.is_connected = True
        
        # 发送初始状态
        initial_status = {
            "type": "worker_connected",
            "message": "GCMS Worker 已连接",
            "status": self.current_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.send_response(initial_status)
    
    def start(self):
        """启动 Worker"""
        print(f"正在连接到 {self.server_url}")
        

        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        
        # 启动 WebSocket 连接（这会阻塞当前线程）
        self.ws.run_forever()

if __name__ == "__main__":
    # 允许通过命令行参数指定服务器地址：--server-url 或 -s
    # 例如：python gcms_worker.py -s ws://62.234.51.178/ws/gcms/
    server_arg = None
    try:
        if "-s" in sys.argv:
            idx = sys.argv.index("-s")
            if idx + 1 < len(sys.argv):
                server_arg = sys.argv[idx + 1]
        elif "--server-url" in sys.argv:
            idx = sys.argv.index("--server-url")
            if idx + 1 < len(sys.argv):
                server_arg = sys.argv[idx + 1]
    except Exception:
        server_arg = None

    # 创建并启动 GCMS Worker（可被环境变量 GCMS_SERVER_URL 或命令行参数覆盖）
    worker = GcmsWorker(server_url=server_arg)
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n正在关闭 GCMS Worker...")
    except Exception as e:
        print(f"Worker 运行出错: {e}")
