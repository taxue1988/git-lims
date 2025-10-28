import os
from typing import Dict, Optional

# 读取 GCMS 序列清单，提供 序号->文件名 的映射
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SEQUENCE_LIST_PATH = os.path.join(_BASE_DIR, '..', '模块开发运行代码', 'GCMS模块', 'GCMS序列.txt')

_sequence_map: Dict[int, str] = {}


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
    global _sequence_map
    if _sequence_map:
        return _sequence_map
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
    mapping = load_sequence_map()
    return mapping.get(index)
