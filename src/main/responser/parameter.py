from pydantic import BaseModel

class anormalyDetectionItem(BaseModel):
    json_device_alarm:str
    json_5gc_smf:str
    json_upf:str

class alarmReductionItem(BaseModel):
    json_device_alarm:str
    json_performance_alarm:str