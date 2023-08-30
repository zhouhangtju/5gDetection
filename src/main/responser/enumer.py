# -*-coding:utf-8 -*-
"""
# Author     : Delight
# Time       : 2023/1/15 17:46
# Description:
"""
from enum import unique, IntEnum


@unique
class Code(IntEnum):
    """返回的服务状态码"""
    OK = 200
    InternalError = 201  # 内部错误
    InvalidParameter = 202  # 无效参数，请检查参数是否正确

