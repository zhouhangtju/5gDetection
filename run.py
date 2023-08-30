import platform
import warnings
from fastapi import FastAPI
from src.main.router import pn_router
from src.main.responser.exception import catch_exception
import uvicorn

warnings.filterwarnings("ignore")

app = FastAPI()
catch_exception(app)

# 添加路由
app.include_router(pn_router.router)

# if __name__ == '__main__':
if __name__ == '__main__':
    app = FastAPI()
    # 添加路由
    app.include_router(pn_router.router)
    # uvicorn.run(app=app,port=9000)
    host = "127.0.0.1"
    reload = True

    if platform.system().lower() == 'linux':
        host = "0.0.0.0"
        reload = False

    uvicorn.run(app="run:app", host=host, port=9000, log_config=None, access_log=False, reload=reload, workers=1)
    # uvicorn.run(app="run:app",port=9000)
    # uvicorn.run(app=app,port=9000)

