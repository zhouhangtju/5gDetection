import requests
import pandas as pd
# base_path = "/root/zhouh/"
base_path = "./"
path_device_alarm = base_path+"data/alarm/device_alarm_test.csv"
path_smf = base_path + "data/smf/DM_5GC_SMF_ALARM_5M_test.csv"
path_upf = base_path + "data/upf/UPF_test.csv"

url = "http://127.0.0.1:9000/anormalyDetection/detect/zj"  # 根据你的服务器地址和路由进行修改




df_device_alarm = pd.read_csv(path_device_alarm)
df_5gc_smf = pd.read_csv(path_smf)
df_upf = pd.read_csv(path_upf)

json_device_alarm = df_device_alarm.to_json(orient="records",force_ascii=False)
json_5gc_smf = df_5gc_smf.to_json(orient="records",force_ascii=False)
json_upf = df_upf.to_json(orient="records",force_ascii=False)

data = {
    "json_device_alarm":1,
    "json_upf":"2323",
    "Sds":"sdsd"
}

response = requests.post(url, json=data)
print(response.json())
# if response.status_code == 200:
#     data = response.json()
#     df_res = pd.read_json(data)
#     print(df_res)
#     print(df_res.to_json(orient="records", force_ascii=False))
#
# else:
#     print("Request failed with status code:", response.status_code)