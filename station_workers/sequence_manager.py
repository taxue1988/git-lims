import os
from typing import Dict, Optional, Tuple

# 读取 GCMS 序列清单，提供 序号->文件名 的映射
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SEQUENCE_LIST_PATH = os.path.join(_BASE_DIR, '..', '模块开发运行代码', 'GCMS模块', 'GCMS序列.txt')
_SEQUENCE_PARAMS_CSV = os.path.join(_BASE_DIR, '..', '模块开发运行代码', 'GCMS模块', 'GCMS序列及参数表.csv')

_sequence_map: Dict[int, str] = {}
_sequence_params_map: Dict[int, Tuple[str, str, str]] = {}


def _parse_line_to_kv(line: str) -> Optional[tuple]:
    line = line.strip()
    if not line:
        return None
    # 支持中文冒号与英文冒号
    if '：' in line:
        idx, name = line.split('：', 1)
    elif ':' in line:
        idx, name = line.split(':', 1)
    else:
        return None
    idx = idx.strip()
    name = name.strip()
    if not idx.isdigit():
        return None
    return int(idx), name


def load_sequence_map() -> Dict[int, str]:
    """返回 {序号: 序列文件名} 的映射。
    优先从 CSV 参数表生成（唯一来源）；若 CSV 不可用或为空，回退到旧的 TXT。
    """
    global _sequence_map
    if _sequence_map:
        return _sequence_map

    # 1) 优先从 CSV 参数表加载
    params = load_sequence_params_map()
    if params:
        mapping: Dict[int, str] = {}
        for idx, triple in params.items():
            seq_file = triple[0]
            mapping[idx] = seq_file
        _sequence_map = mapping
        return _sequence_map

    # 2) 回退：从旧 TXT 解析（兼容保留）
    path = os.path.normpath(_SEQUENCE_LIST_PATH)
    if not os.path.isfile(path):
        return {}
    mapping: Dict[int, str] = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            kv = _parse_line_to_kv(line)
            if kv is None:
                continue
            k, v = kv
            mapping[k] = v
    _sequence_map = mapping
    return _sequence_map


def get_sequence_file(index: int) -> Optional[str]:
    """返回序列号对应的序列文件名（来自 CSV 参数表）。
    若 CSV 缺失则回退至 TXT 结果。
    """
    mapping = load_sequence_map()
    return mapping.get(index)


def load_sequence_params_map() -> Dict[int, Tuple[str, str, str]]:
    """读取参数表：返回 {序号: (序列文件名, 数据名称, 数据存储路径)}。
    CSV 结构应为：序号, 序列文件名, 数据名称, 数据存储路径
    兼容带 BOM 或中文表头，首行若非数字将被跳过。
    """
    global _sequence_params_map
    if _sequence_params_map:
        return _sequence_params_map

    path = os.path.normpath(_SEQUENCE_PARAMS_CSV)
    if not os.path.isfile(path):
        return {}

    mapping: Dict[int, Tuple[str, str, str]] = {}
    # 尝试多种常见编码
    encodings = ['utf-8-sig', 'utf-8', 'gbk']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                lines = [line.strip() for line in f if line.strip()]
            break
        except Exception:
            lines = None
    if not lines:
        return {}

    for i, line in enumerate(lines):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 4:
            continue
        # 跳过表头行（首列非数字）
        if i == 0 and not parts[0].isdigit():
            continue
        if not parts[0].isdigit():
            continue
        idx = int(parts[0])
        seq_file = parts[1].strip().strip('"')
        data_name = parts[2].strip().strip('"')
        data_path = parts[3].strip().strip('"')
        # 规范化路径分隔符
        data_path = os.path.normpath(data_path)
        mapping[idx] = (seq_file, data_name, data_path)

    _sequence_params_map = mapping
    return _sequence_params_map


def get_result_csv_path(sequence_index: int) -> Optional[str]:
    """根据序列号返回本地 tic_front.csv 的绝对路径。
    构造规则：data_path / (data_name + '.D') / 'tic_front.csv'
    """
    params = load_sequence_params_map()
    triple = params.get(sequence_index)
    if not triple:
        return None
    _seq_file, data_name, data_path = triple
    # 数据名可能已经包含 .D，避免重复
    folder = data_name if data_name.lower().endswith('.d') else f"{data_name}.D"
    # 优先尝试常见大小写的文件名
    filename_candidates = ['tic_front.csv', 'tic_front.CSV', 'TIC_front.csv', 'TIC_front.CSV']
    for fname in filename_candidates:
        candidate = os.path.normpath(os.path.join(data_path, folder, fname))
        if os.path.isfile(candidate):
            return candidate

    # 回退：在 data_path 下寻找形如 data_name*.D 的最新目录中的 tic_front.csv
    try:
        if not os.path.isdir(data_path):
            return None
        candidates = []
        for entry in os.listdir(data_path):
            if not entry.lower().endswith('.d'):
                continue
            # 前缀匹配（忽略大小写）
            if not entry.lower().startswith(data_name.lower()):
                continue
            for fname in filename_candidates:
                p = os.path.join(data_path, entry, fname)
                if not os.path.isfile(p):
                    continue
                try:
                    mtime = os.path.getmtime(p)
                except Exception:
                    mtime = 0
                candidates.append((mtime, os.path.normpath(p)))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return os.path.normpath(candidates[0][1])
    except Exception:
        return None
