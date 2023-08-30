import requests
import pandas as pd
# base_path = "/root/zhouh/"
base_path = "./"
path_device_alarm = base_path+"data/alarm/device_alarm_test2.csv"
path_performance_alarm = base_path+"data/alarm/performance_alarm_test.csv"




df_device_alarm = pd.read_csv(path_device_alarm)
df_performance_alarm = pd.read_csv(path_performance_alarm)

json_device_alarm = df_device_alarm.to_json(orient="records",force_ascii=False)
json_performance_alarm = df_performance_alarm.to_json(orient="records",force_ascii=False)


url = "http://127.0.0.1:9000/anormalyDetection/alarmReduction/zj"  # 根据你的服务器地址和路由进行修改
data_alarm_reduction ={
    "json_device_alarm":json_device_alarm,
    "json_performance_alarm":json_performance_alarm}
response = requests.post(url, json=data_alarm_reduction)
print(response.json())
# if response.status_code == 200:
#     data = response.json()
#     df_res = pd.read_json(data)
#     print(df_res.to_json(orient="records", force_ascii=False))
#     # print(df_res)
# else:
#     print("Request failed with status code:", response.status_code)