# -*-coding:utf-8 -*-
"""
# Author     : Delight
# Time       : 2022/8/21 10:45
# Description:
"""
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.main.responser.enumer import Code
from src.main.responser.result import Result


def catch_exception(app: FastAPI):
    """
    捕获异常
    """
    # 参数有效性检查，重定义返回结构，必要，无需修改

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        请求参数验证异常
        :param request: 请求头信息
        :param exc: 异常对象
        :return:
        """
        message = ""
        for error in exc.errors():
            message += ".".join(map(str, error.get("loc"))) + ": " + error.get("msg") + ";"

        res = Result(Code.InvalidParameter, message, []).dict()
        return JSONResponse(status_code=status.HTTP_200_OK, content=res)

    # 其他异常
    # 参数有效性检查，重定义返回结构，必要，无需修改
    @app.exception_handler(Exception)
    async def validation_exception_handler(request: Request, exc: Exception):
        """
        请求参数验证异常
        :param request: 请求头信息
        :param exc: 异常对象
        :return:
        """
        res = Result(Code.InternalError, str(exc).replace("\n", " "), []).dict()
        return JSONResponse(status_code=status.HTTP_200_OK, content=res)
