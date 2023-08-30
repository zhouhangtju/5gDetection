# -*-coding:utf-8 -*-
"""
# Author     ：Delight
# Time       ：2022/7/12 14:29
# Description：
"""
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.main.responser.enumer import Code


class Meta(BaseModel):
    code: int = Field(..., description="服务返回代码，2000正常, 2001服务异常, 2002参数错误")
    message: str = Field(..., description="异常信息/参数验证失败：location:reason")


class Response(BaseModel):
    meta: Meta = Field(..., description="返回状态")
    data: Any = Field([], description="返回数据")


class Result(Dict):
    """服务返回结构，不用Response的原因是不用写变量名"""
    def __init__(self, code=Code.OK, message="success", data=None):
        """
        :param code:
        :param message:
        :param data:
        """
        super().__init__()
        if data is None:
            data = []
        self.meta = {"code": code, "message": message}
        self.data = data

    def dict(self):
        return self.__dict__


if __name__ == "__main__":
    print(Result(Code.OK, "333").dict())
