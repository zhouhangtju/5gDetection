import pandas as pd
import numpy as np

class AnormalyDetectionService:


    def __init__(self,path_dnn2Gnode2upf,path_gnodeAlarm,path_dnnHistoryModel,df_device_alarm):
        df_gnodeAlarmSet = pd.read_csv(path_gnodeAlarm)
        gnodeAlarmSet = set(df_gnodeAlarmSet["alarm_name"].values)
        self.gnodeAlarmSet = gnodeAlarmSet
        self.deviceAlarmSet = {"DRA不可达","UPF设备发生阻断","5GC网络中AMF/SMF/UDM/UPF/PCF等网元出现媒体面网络故障","5GC网络中AMF/SMF/UDM/UPF/PCF等网元出现信令面网络故障"}
        
        df_dnn2Gnode2upf = pd.read_csv(path_dnn2Gnode2upf)
        df_dnn2Gnode2upf["APN名称"] = df_dnn2Gnode2upf["APN名称"].str.lower()
        df_dnn2Gnode2upf.set_index("APN名称",inplace=True)
        df_device_alarm["告警最后发生时间"] = pd.to_datetime(df_device_alarm["告警最后发生时间"])
        self.df_device_alarm = df_device_alarm
        self.df_dnn2Gnode2upf = df_dnn2Gnode2upf

        df_model = pd.read_csv(path_dnnHistoryModel)
        self.df_model = df_model
        self.df_model.set_index("DNN",inplace=True)


    def alarmReduction(self,df_performance_alarm):
        # df_performance_alarm = pd.read_csv(path_performance_alarm)
        df_performance_alarm["告警最后发生时间"] = pd.to_datetime(df_performance_alarm["告警最后发生时间"])
        df_device_alarm = self.df_device_alarm
        df_dnn2Gnode2upf = self.df_dnn2Gnode2upf
        df_performance_alarm = self.link_alarm(df_performance_alarm,df_device_alarm,df_dnn2Gnode2upf)
        return df_performance_alarm
        

    
    def prediction_model(self,dnn,alarm_time,ind,df_performance_alarm):
        if dnn in self.df_model.index:
            sat = self.df_model.loc[dnn,"Sat"]
            sun = self.df_model.loc[dnn,"Sun"]
            night = self.df_model.loc[dnn,"night"]
            if int(night) == 1:
                time1 = pd.to_datetime(self.df_model.loc[dnn,"START_TIME"],format="%H:%M:%S").time()
                time2 = pd.to_datetime(self.df_model.loc[dnn,"END_TIME"], format="%H:%M:%S").time()
                if time1 <= time2:
                    if time1 <= alarm_time.time() <= time2:
                        df_performance_alarm = df_performance_alarm.drop(ind)
                        
                else:
                    if time1 <= alarm_time.time() or alarm_time.time() <= time2:
                        df_performance_alarm = df_performance_alarm.drop(ind)
            
            elif alarm_time.dayofweek >= 5:
                if sat==1 or sun==1:
                    df_performance_alarm = df_performance_alarm.drop(ind)
        return df_performance_alarm
    
    def link_alarm(self, df_performance_alarm, df_device_alarm, df_dnn2Gnode2upf):
        for index, row in df_performance_alarm.iterrows():
            dnn = row["网元名称"].lower()
            alarm_time = row["告警最后发生时间"]
            if dnn not in df_dnn2Gnode2upf.index:
                continue
            #upf列表upf_list
            if pd.isnull(df_dnn2Gnode2upf.loc[dnn,"关联UPF"]):
                upf_list = []
            else:
                upf_list = df_dnn2Gnode2upf.loc[dnn,"关联UPF"].split("|")
            #基站列表gnode_list
            if pd.isnull(df_dnn2Gnode2upf.loc[dnn,"关联基站"]):
                gnode_list = []
            else:
                gnode_list = df_dnn2Gnode2upf.loc[dnn,"关联基站"].split("|")
                
            #关联设备/基站告警
            # for upf in upf_list:
            start_time = alarm_time-pd.Timedelta("10min")
            end_time = alarm_time+pd.Timedelta("10min")
       
            df_alarm = df_device_alarm[((df_device_alarm["网元名称"].isin(upf_list)) |
                                    (df_device_alarm["网元名称"].isin(gnode_list))) & 
                                    (df_device_alarm["告警最后发生时间"]>start_time) & 
                                    (df_device_alarm["告警最后发生时间"]<=end_time)].copy()
            #cond1 重要告警
            cond1 = (df_alarm[(df_alarm["告警标题"].isin(self.deviceAlarmSet)) | (df_alarm["告警标题"].isin(self.gnodeAlarmSet))].shape[0]>0)
            if cond1:
                continue
            #cond2 告警量很大
            cond2 = (df_alarm[df_alarm["设备类型"]=="UPF"]["告警标题"].unique().shape[0]>10 | df_alarm[df_alarm["设备类型"]=="GNodeB"]["告警标题"].unique().shape[0]>3 )
            if cond2:
                continue
            
            ### 预测模型
            df_performance_alarm = self.prediction_model(dnn,alarm_time,index,df_performance_alarm)
        return df_performance_alarm



    
    def process_file_smf(self,df_5gc_smf, name_col="DNN_NAME",
              time_col="TIME_ID"):
        df_5gc_smf[name_col] = df_5gc_smf[name_col].str.lower()
        df_5gc_smf[time_col] = pd.to_datetime(df_5gc_smf[time_col])
        dnn_list = df_5gc_smf[name_col].dropna().drop_duplicates().values.tolist()
        return df_5gc_smf, dnn_list


    def process_file_upf(self,df_upf):
        df_upf_count_temp = df_upf[["ManagedElement名称", "DNN", "时间"]].groupby(["DNN"]).agg(
            {"ManagedElement名称": lambda x: len(set(x))}
        ).rename(columns={"DNN": "DNN",
                        "ManagedElement名称": "ManagedElemenCount"}).sort_values("ManagedElemenCount", ascending=False).reset_index()
        df_upf_count_temp = df_upf_count_temp[df_upf_count_temp["ManagedElemenCount"] <= 2]
        df_upf_count_temp_slice = df_upf_count_temp.merge(
            df_upf, on=["DNN"], how='inner')

        # dnn4upf = df_upf_count_temp_slice.groupby("DNN").agg({"ManagedElement名称":lambda x: '/'.join(set([str(item) for item in x.tolist()]))}).reset_index().rename(columns={"DNN": NAME_COL})

        df_upf_input = df_upf_count_temp_slice.groupby(["DNN", "时间"]).agg(
            {
                "分DNN的N6接口出错丢弃的IP包数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的N6接口发送IP包数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的N6接口发送字节数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的N6接口接收IP包数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的N6接口接收字节数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的平均QOS流数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的最大QOS流数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话建立请求次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话建立成功次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话建立失败次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话修改请求次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话修改成功次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "分DNN的PFCP会话修改失败次数": lambda x: 0+sum([float(value) for value in x.tolist() if value != " " and not pd.isnull(value)]),
                "ManagedElement名称": lambda x: '/'.join(set(x.tolist())),

            }
        ).reset_index()
        df_upf_input["分DNN的PFCP会话建立成功率"] = df_upf_input.apply(lambda x: 1 if x["分DNN的PFCP会话建立请求次数"]==0 else x["分DNN的PFCP会话建立成功次数"]/x["分DNN的PFCP会话建立请求次数"],axis=1)
        df_upf_input["分DNN的PFCP会话修改成功率"] = df_upf_input.apply(lambda x: 1 if x["分DNN的PFCP会话修改请求次数"]==0 else x["分DNN的PFCP会话修改成功次数"]/x["分DNN的PFCP会话修改请求次数"],axis=1)
        df_upf_input = df_upf_input.rename(columns={"DNN": "DNN_NAME"})
        df_upf_input["分DNN的N6口丢包率"] = df_upf_input[["分DNN的N6接口出错丢弃的IP包数", "分DNN的N6接口接收IP包数"]].apply(
            lambda x: 0 if x[1] == 0 or x[0] == 0 or pd.isnull(x[0]) or pd.isnull(x[1]) else x[0]/x[1], axis=1)
        df_upf_input["TIME_ID"] = df_upf_input[["时间"]].apply(
            lambda x: pd.to_datetime(x))

        tempSliceMap = dict(map(lambda t2:
                        (t2[0], t2[1].sort_values(by="TIME_ID", ascending=True)), df_upf_input.groupby("DNN_NAME")))

        return tempSliceMap,df_upf_input,df_upf_count_temp_slice

    def anormalyDetection(self,df_5gc_smf,df_upf):
        df_5gc_smf, dnn_list = self.process_file_smf(df_5gc_smf)
        smfSliceMap = dict(map(lambda t2:
                                (t2[0], t2[1].sort_values(by="TIME_ID", ascending=True)), df_5gc_smf.groupby("DNN_NAME")))
        
        upfByDnnSliceMap,df_upf_input, _ = self.process_file_upf(df_upf)

        time_diff = pd.Timedelta("20min")
        df_res = pd.DataFrame(columns=["TIME_id", "DNN_NAME", "FAULT_REASON"])
        for dnn in self.df_dnn2Gnode2upf.index:
            #分DNN的pdu会话建立成功率异常
            if dnn in smfSliceMap.keys() and dnn in upfByDnnSliceMap.keys():
                smf_dnn_slice = smfSliceMap[dnn] 
                if dnn in upfByDnnSliceMap.keys():
                    upf_by_dnn_slice = upfByDnnSliceMap[dnn]
                    df_res = self.anormlyDetectionPduSuccRate(smf_dnn_slice, upf_by_dnn_slice, time_diff, df_res, 10,-0.1, "分DNN的pdu会话建立成功率异常", target_name = "PDU_SESSION_SUCC_RATE",support_name = "PDU_SESSION_SUCC_CNT")
                    # anormlyDetectionPduSuccRate(self, dnn_slice, upf_by_dnn_slice, timediff, df_res, threshold_support_cnt,threshold_target_gradient, msg, target_name = "PDU_SESSION_SUCC_RATE",support_name = "PDU_SESSION_SUCC_CNT")
            #分DNN的分DNN的pdu会话数异常
            if dnn in smfSliceMap.keys():
                smf_dnn_slice = smfSliceMap[dnn]
                df_res = self.anormlyDetectionPduSessCnt(smf_dnn_slice, time_diff, df_res, 100,-0.1,"分DNN的pdu会话数异常", target_name="AVG_PDU_SESSION_CNT",support_name="AVG_PDU_SESSION_CNT")
            
            #分DNN的PFCP会话建立成功率异常
            if dnn in upfByDnnSliceMap.keys():
                upf_by_dnn_slice = upfByDnnSliceMap[dnn]
                df_res = self.anormlyDetectionPFCP(upf_by_dnn_slice, time_diff, df_res, 10,-0.1,"分DNN的PFCP会话建立成功率异常", target_name = "分DNN的PFCP会话建立成功率",support_name = "分DNN的PFCP会话建立请求次数")

            #分DNN的流量异常
                upf_by_dnn_slice = upfByDnnSliceMap[dnn]
                df_res = self.anormlyDetectionN6Flow(upf_by_dnn_slice, time_diff, df_res, 100,-0.15,"分DNN的流量异常", target_name = "分DNN的N6接口发送IP包数",support_name = "分DNN的N6接口发送IP包数")

            
        return df_res



    def anormlyDetectionPduSessCnt(self, dnn_slice, time_diff, df_res, threshold_support_cnt,threshold_target_gradient, msg, target_name ="AVG_PDU_SESSION_CNT", support_name="AVG_PDU_SESSION_CNT"):
        dnn_slice_label = self.rule(dnn_slice, time_diff, df_res, threshold_support_cnt,threshold_target_gradient, msg, target_name,support_name)
        for index, row in dnn_slice_label.iterrows():
            start_time = row["TIME_ID"]-pd.Timedelta("30min")
            end_time = row["TIME_ID"]+pd.Timedelta("30min")

            dnn = row["DNN_NAME"]
            ### 预测模型
            df_model = self.df_model
            
            if dnn in df_model.index:
                sat = df_model.loc[dnn,"Sat"]
                sun = df_model.loc[dnn,"Sun"]
                night = df_model.loc[dnn,"night"]
                # if int(night) == 1:
                #     time1 = pd.to_datetime(df_model.loc[dnn,"START_TIME"],format="%H:%M:%S").time()
                #     time2 = pd.to_datetime(df_model.loc[dnn,"END_TIME"], format="%H:%M:%S").time()
                #     alarm_time = row["TIME_ID"]
                #     if time1 <= alarm_time.time() or alarm_time.time() <= time2:
                #         df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
                # elif alarm_time.dayofweek >= 5:
                #     if sat==0 and sun==0:
                #         df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]

                alarm_time = row["TIME_ID"]
                if int(night) == 1:
                    time1 = pd.to_datetime(df_model.loc[dnn,"START_TIME"],format="%H:%M:%S").time()
                    time2 = pd.to_datetime(df_model.loc[dnn,"END_TIME"], format="%H:%M:%S").time()
                    if time1 <= time2:
                        if time1 <= alarm_time.time() <= time2:
                            continue

                    else:
                        if time1 <= alarm_time.time() or alarm_time.time() <= time2:
                            continue

                elif alarm_time.dayofweek >= 5:
                    if sat==1 or sun==1:
                        continue
            
            
            
            #upf列表upf_list
            if pd.isnull(self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"]):
                upf_list = []
            else:
                upf_list = self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"].split("|")
            #基站列表gnode_list
            if pd.isnull(self.df_dnn2Gnode2upf.loc[dnn,"关联基站"]):
                gnode_list = []
            else:
                gnode_list = self.df_dnn2Gnode2upf.loc[dnn,"关联基站"].split("|")
            
            df_device_alarm = self.df_device_alarm
            df_alarm = df_device_alarm[((df_device_alarm["网元名称"].isin(upf_list)) |
                                        (df_device_alarm["网元名称"].isin(gnode_list))) & 
                                        (df_device_alarm["告警最后发生时间"]>start_time) & 
                                        (df_device_alarm["告警最后发生时间"]<=end_time)].copy()
            #cond1 重要告警
            cond1 = (df_alarm[(df_alarm["告警标题"].isin(self.deviceAlarmSet)) | (df_alarm["告警标题"].isin(self.gnodeAlarmSet))].shape[0]>0)
            #cond2 告警数量
            cond2 = (df_alarm[df_alarm["设备类型"]=="UPF"]["告警标题"].unique().shape[0]>10 | df_alarm[df_alarm["设备类型"]=="GNodeB"]["告警标题"].unique().shape[0]>3 )
            if cond1 or cond2:
                df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
                continue
                
                
            # ### 预测模型
            # df_model = self.df_model
            
            # if dnn in df_model.index:
            #     sat = df_model.loc[dnn,"Sat"]
            #     sun = df_model.loc[dnn,"Sun"]
            #     night = df_model.loc[dnn,"night"]
            #     if int(night) == 1:
            #         time1 = pd.to_datetime(df_model.loc[dnn,"START_TIME"],format="%H:%M:%S").time()
            #         time2 = pd.to_datetime(df_model.loc[dnn,"END_TIME"], format="%H:%M:%S").time()
            #         alarm_time = row["TIME_ID"]
            #         if time1 <= alarm_time.time() or alarm_time.time() <= time2:
            #             df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
            #     elif alarm_time.dayofweek >= 5:
            #         if sat==0 and sun==0:
            #             df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
        return df_res


    def cal_label_rule(self,x,target_name,support_name,threshold_support_cnt,threshold_target_gradient):
        if pd.isnull(x[target_name]) or pd.isnull(x[target_name+"_mean"]) or pd.isnull(x[support_name+"_mean"]):
            return 0
        if x[target_name+"_mean"]==0:
            return 0
        gradient = (x[target_name]-x[target_name+"_mean"])/x[target_name+"_mean"]
        support_cnt = x[support_name+"_mean"]
        if support_cnt>=threshold_support_cnt and gradient<threshold_target_gradient:
            return 1
        else:
            return 0 

    def anormlyDetectionPduSuccRate(self, dnn_slice, upf_by_dnn_slice, timediff, df_res, threshold_support_cnt,threshold_target_gradient, msg, target_name = "PDU_SESSION_SUCC_RATE",support_name = "PDU_SESSION_SUCC_CNT"):
        smf_dnn_slice_label = self.rule(dnn_slice, timediff, df_res, threshold_support_cnt,threshold_target_gradient,msg, target_name,support_name)
        for index, row in smf_dnn_slice_label.iterrows():
            start_time = row["TIME_ID"]-pd.Timedelta("30min")
            end_time = row["TIME_ID"]+pd.Timedelta("30min")
            pfcp_succ_rate = upf_by_dnn_slice[(upf_by_dnn_slice["TIME_ID"]<=end_time) & (upf_by_dnn_slice["TIME_ID"]>=start_time)]["分DNN的PFCP会话建立成功率"].values
            if pfcp_succ_rate.shape[0]>0:
                if pfcp_succ_rate.min()<0.7:
                    df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
        return df_res

    def rule(self, dnn_slice, timediff, df_res, threshold_support_cnt,threshold_target_gradient,msg, target_name = "PDU_SESSION_SUCC_RATE",support_name = "PDU_SESSION_SUCC_CNT"):
        dnn_slice = dnn_slice.reset_index(drop=True)
        dnn_slice[target_name+"_mean"] = dnn_slice.copy().set_index("TIME_ID").rolling(timediff).agg({
            target_name:lambda target_list:np.mean([x for x in target_list[0:-1] if pd.isnull(x) == False])
            }).reset_index()[target_name]
        dnn_slice[support_name+"_mean"] = dnn_slice.copy().set_index("TIME_ID").rolling(timediff).agg({
            support_name:lambda target_list:np.mean([x for x in target_list if pd.isnull(x) == False])
            }).reset_index()[support_name]

        dnn_slice["label"] = dnn_slice.apply(lambda x:self.cal_label_rule(x,target_name,support_name,threshold_support_cnt,threshold_target_gradient),axis=1)
        smf_dnn_slice_label = dnn_slice[dnn_slice["label"] == 1].copy()
        return smf_dnn_slice_label


    def anormlyDetectionPFCP(self, dnn_slice, time_diff, df_res, threshold_support_cnt,threshold_target_gradient, msg="分DNN的pdu会话建立成功率异常", target_name ="PDU_SESSION_SUCC_RATE", support_name="PDU_SESSION_SUCC_CNT"):
        dnn_slice_label = self.rule(dnn_slice.copy(), time_diff, df_res, threshold_support_cnt,threshold_target_gradient, msg, target_name,support_name)
        for index, row in dnn_slice_label.iterrows():
            start_time = row["TIME_ID"]-pd.Timedelta("30min")
            end_time = row["TIME_ID"]+pd.Timedelta("30min")
            dnn = row["DNN_NAME"]

            #upf列表upf_list
            if pd.isnull(self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"]):
                upf_list = []
            else:
                upf_list = self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"].split("|")
    
            df_device_alarm = self.df_device_alarm
            df_alarm =  df_device_alarm[(df_device_alarm["网元名称"].isin(upf_list)) & 
                                        (df_device_alarm["告警最后发生时间"]>start_time) & 
                                        (df_device_alarm["告警最后发生时间"]<=end_time)].copy()
        
            cond1 = (df_alarm[(df_alarm["告警标题"].isin(self.deviceAlarmSet))].shape[0]>0)
            cond2 = (df_alarm[df_alarm["设备类型"]=="UPF"]["告警标题"].unique().shape[0]>10)
            if cond1 or cond2:
                df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
    
        return df_res
                
    def anormlyDetectionN6Flow(self,dnn_slice, time_diff, df_res, threshold_support_cnt,threshold_target_gradient,msg="分DNN的pdu会话建立成功率异常", target_name ="PDU_SESSION_SUCC_RATE", support_name="PDU_SESSION_SUCC_CNT"):
        dnn_slice_label = self.rule(dnn_slice.copy(), time_diff, df_res, threshold_support_cnt,threshold_target_gradient,msg, target_name,support_name)
        for index, row in dnn_slice_label.iterrows():
            start_time = row["TIME_ID"]-pd.Timedelta("15min")
            end_time = row["TIME_ID"]+pd.Timedelta("15min")
            dnn = row["DNN_NAME"]

            #upf列表upf_list
            if pd.isnull(self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"]):
                upf_list = []
            else:
                upf_list = self.df_dnn2Gnode2upf.loc[dnn,"关联UPF"].split("|")
            #基站列表gnode_list
            if pd.isnull(self.df_dnn2Gnode2upf.loc[dnn,"关联基站"]):
                gnode_list = []
            else:
                gnode_list = self.df_dnn2Gnode2upf.loc[dnn,"关联基站"].split("|")
            df_device_alarm = self.df_device_alarm

            df_alarm = df_device_alarm[((df_device_alarm["网元名称"].isin(upf_list)) |
                                    (df_device_alarm["网元名称"].isin(gnode_list))) & 
                                    (df_device_alarm["告警最后发生时间"]>start_time) & 
                                    (df_device_alarm["告警最后发生时间"]<=end_time)].copy()
            #cond1 重要告警
            cond1 = (df_alarm[(df_alarm["告警标题"].isin(self.deviceAlarmSet)) | (df_alarm["告警标题"].isin(self.gnodeAlarmSet))].shape[0]>0)
            cond2 = (df_alarm[df_alarm["设备类型"]=="UPF"]["告警标题"].unique().shape[0]>10 | df_alarm[df_alarm["设备类型"]=="GNodeB"]["告警标题"].unique().shape[0]>3 )
            if cond1 or cond2:
                df_res.loc[len(df_res.index)]=[row["TIME_ID"],row["DNN_NAME"],msg]
                continue
                
                
            # ### 预测模型
            # df_model = self.df_model
            # alarm_time = row["TIME_ID"]
            # if dnn in df_model.index:
            #     sat = df_model.loc[dnn,"Sat"]
            #     sun = df_model.loc[dnn,"Sun"]
            #     night = df_model.loc[dnn,"night"]
            #     if int(night) == 1:
            #         time1 = pd.to_datetime(df_model.loc[dnn,"START_TIME"],format="%H:%M").time()
            #         time2 = pd.to_datetime(df_model.loc[dnn,"END_TIME"], format="%H:%M").time()
            #         if time1 <= alarm_time.time() or alarm_time.time() <= time2:
            #             df_res.append([row["TIME_ID"],row["DNN_NAME"],msg])
            #     elif alarm_time.dayofweek >= 5:
            #         if sat==0 and sun==0:
            #             df_res.append([row["TIME_ID"],row["DNN_NAME"],msg])
            #     else: 
            #         continue
        return df_res

if __name__ == '__main__':
    base_path = "/root/zhouh/"
    path_performance_alarm = base_path+"data/alarm/performance_alarm.csv"
    path_device_alarm = base_path+"data/alarm/device_alarm_0501_0501.csv"
    path_dnn2Gnode2upf = base_path+"data/dnnInformation/dnn2Gnode2upf.csv"
    path_gnodeAlarm = base_path+"data/GnodeInfo/GnodeInfo.csv"
    path_dnnHistoryModel = base_path+"model/dnn_info.csv"

    df_device_alarm = pd.read_csv(path_device_alarm)
    ads = AnormalyDetectionService(path_dnn2Gnode2upf,path_gnodeAlarm,path_dnnHistoryModel,df_device_alarm)
    df_5gc_smf = pd.read_csv("/root/zhouh/data/smf/DM_5GC_SMF_ALARM_5M_0501_0501.csv")
    df_upf = pd.read_csv("/root/zhouh/data/upf/UPF_0501_0501.csv")
    df_performance_alarm = pd.read_csv(path_performance_alarm)
    df_performance_alarm = ads.alarmReduction(df_performance_alarm)
    # df_res = ads.anormalyDetection(df_5gc_smf,df_upf)
    # print(df_res)
    pass