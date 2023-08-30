import pandas as pd
from src.main.service.pn_zj_service import AnormalyDetectionService
from src.main.responser.parameter import anormalyDetectionItem, alarmReductionItem
from src.main.responser.enumer import Code
from src.main.responser.result import Result
import uvicorn
from fastapi import FastAPI, APIRouter


router = APIRouter(prefix="/anormalyDetection")


# class Item(BaseModel):
#     json_device_alarm:str
#     json_5gc_smf:str
#     json_upf:str

# class alarmReductionItem(BaseModel):
#     json_device_alarm:str
#     json_performance_alarm:str

@router.post("/detect/zj",summary="异常检测")
async def get_train(data: anormalyDetectionItem):
    df_device_alarm = pd.read_json(data.json_device_alarm)
    df_5gc_smf = pd.read_json(data.json_5gc_smf)
    df_upf = pd.read_json(data.json_upf)

    base_path = "./"

    path_performance_alarm = base_path+"data/alarm/performance_alarm.csv"
    path_dnn2Gnode2upf = base_path+"data/dnnInformation/dnn2Gnode2upf.csv"
    path_gnodeAlarm = base_path+"data/GnodeInfo/GnodeInfo.csv"
    path_dnnHistoryModel = base_path+"model/dnn_info.csv"
    ads = AnormalyDetectionService(path_dnn2Gnode2upf,path_gnodeAlarm,path_dnnHistoryModel,df_device_alarm)
    res = ads.anormalyDetection(df_5gc_smf,df_upf)
    res["TIME_id"] = res["TIME_id"].apply(lambda x :str(x))
    # return res.to_json(orient="records",force_ascii=False)
    return Result(Code.OK, "success", res.to_json(orient="records",force_ascii=False)).dict()

@router.post("/alarmReduction/zj",summary="故障压降")
async def alarmReduction(data: alarmReductionItem):
    df_performance_alarm = pd.read_json(data.json_performance_alarm)
    df_device_alarm = pd.read_json(data.json_device_alarm)

    base_path = "./"

    path_performance_alarm = base_path+"data/alarm/performance_alarm.csv"
    path_dnn2Gnode2upf = base_path+"data/dnnInformation/dnn2Gnode2upf.csv"
    path_gnodeAlarm = base_path+"data/GnodeInfo/GnodeInfo.csv"
    path_dnnHistoryModel = base_path+"model/dnn_info.csv"

    ads = AnormalyDetectionService(path_dnn2Gnode2upf,path_gnodeAlarm,path_dnnHistoryModel,df_device_alarm)
    res = ads.alarmReduction(df_performance_alarm)
    res["告警最后发生时间"] = res["告警最后发生时间"].apply(lambda x :str(x))
    res = res[["地市","告警最后发生时间","网元名称","告警标题","网络专业","告警对象设备类型","设备类型","告警工程状态"]]
    # return res.to_json(orient="records",force_ascii=False)
    return Result(Code.OK, "success", res.to_json(orient="records",force_ascii=False)).dict()


# @router.post("/detect/zj",summary="异常检测")
# async def get_train(files: List[UploadFile]):
#     # print("######")
#     # print(files)
#     uploaded_dataframes = []
#     for file in files:
#         contents = file.file.read()
#         buffer = BytesIO(contents)
#         df = pd.read_csv(buffer)
#         buffer.close()
#         file.file.close()
#         uploaded_dataframes.append(df)
#     # except Exception as e:
#     #     return {"message": "An error occurred", "error": str(e)}
#     df_device_alarm = uploaded_dataframes[0]
#     df_5gc_smf = uploaded_dataframes[1]
#     df_upf = uploaded_dataframes[2]

#     base_path = "/root/zhouh/"
#     path_performance_alarm = base_path+"data/alarm/performance_alarm.csv"
#     path_dnn2Gnode2upf = base_path+"data/dnnInformation/dnn2Gnode2upf.csv"
#     path_gnodeAlarm = base_path+"data/GnodeInfo/GnodeInfo.csv"
#     path_dnnHistoryModel = base_path+"model/dnn_info.csv"
#     print(path_dnnHistoryModel)
#     ads = AnormalyDetectionService(path_dnn2Gnode2upf,path_gnodeAlarm,path_dnnHistoryModel,df_device_alarm)
#     res = ads.anormalyDetection(df_5gc_smf,df_upf)
#     print(res)
#     return res

if __name__ == '__main__':
    app = FastAPI()
    # 添加路由
    app.include_router(router)
    uvicorn.run(app=app)