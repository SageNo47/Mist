# coding=utf-8
# 2025.9.19
"""
数据模型模块共有的工具
"""

import ulid

def generate_ulid() -> str:
    """生成ULID"""
    return str(ulid.ulid())