'''
Author       : your name
Date         : 2023-07-05 01:56:04
LastEditors  : your name
LastEditTime : 2023-08-17 02:50:37
FilePath     : /period_check_offline.py
Description  : 以天为单位，离线更新网元的周期性信息
Copyright 2023 OBKoro1, All Rights Reserved. 
2023-07-05 01:56:04
''' 

import multiprocessing
import os
from multiprocessing import Pool
from tqdm import tqdm
import pandas as pd
from utils import worker_periodicity_check
# from main_smf import read_file as read_file_smf
import pickle
from matplotlib.backends.backend_pdf import PdfPages


def read_file_smf(file_path, name_col="DNN_NAME",
              time_col="TIME_ID",
              encoding="gb18030"):
    df_5gc_smf = pd.read_csv(file_path, encoding=encoding)
    df_5gc_smf[name_col] = df_5gc_smf[name_col].str.lower()
    df_5gc_smf[time_col] = pd.to_datetime(df_5gc_smf[time_col])
    df_5gc_smf["time_stamp"] = df_5gc_smf[time_col].map(
        lambda x: x.timestamp())
    dnn_list = df_5gc_smf[name_col].dropna().drop_duplicates().values.tolist()
    return df_5gc_smf, dnn_list

# 将set对象写入文件
def write_set_to_file(file_path, my_set):
    with open(file_path, 'wb') as file:
        pickle.dump(my_set, file)

# # 从文件中读取set对象
# def read_set_from_file(file_path):
#     with open(file_path, 'rb') as file:
#         my_set = pickle.load(file)
#         return my_set

'''
func: period_check_entry
description: 网元分类入口
param {*} tempSliceMap
param {*} fieldName
param {*} dtw_threshold
return {*}figs_periodicity, figs_random, period_dnn, random_dnn, died_dnn
example: 
'''
def period_check_entry(dnn_set,tempSliceMap,fieldName,dtw_threshold,plot_indicator):
    # num_cpu_cores = multiprocessing.cpu_count()
    feature_df = pd.DataFrame(columns=["dnn","d1","d2","d3","d4","d5","d6","d7","d8","dist1","dist2","dist3","dist4","dist5","dist6","period"])
    num_cpu_cores=4
    pool = Pool(num_cpu_cores)

    result_list = []

    for dnn_name in tqdm(tempSliceMap.keys()):
        # result_list.append(worker_periodicity_check(tempSliceMap,dnn_name))
        # worker_periodicity_check(tempSliceMap, dnn_name, fieldName,dtw_threshold,plot_indicator)
        if dnn_name not in dnn_set:
            continue
        result_list.append(pool.apply_async(
            worker_periodicity_check, (tempSliceMap, dnn_name, fieldName,dtw_threshold,plot_indicator)))
        
    pool.close()
    pool.join()
    figs_periodicity = []
    figs_random = []
    period_dnn = set()
    random_dnn = set()
    died_dnn = set()
    

    for res in result_list:
        check_result, dist_list, dnn_name, fig = res.get()
        
        if check_result == "yes":
            if fig is not None:
                figs_periodicity.append(fig)
            period_dnn.add(dnn_name)
        elif check_result == "no":
            if fig is not None:
                figs_random.append(fig)
            random_dnn.add(dnn_name)
        else:
            died_dnn.add(dnn_name)
        if check_result != "None":
            try:
                feature_row = []
                feature_row.append(dnn_name)
                feature_row.extend(dist_list)
                feature_row.append(check_result)
                feature_df.loc[len(feature_df.index)] = feature_row
            except:
                print(feature_row)
    feature_df.to_csv("/root/zhouh/result/feature.csv")
    return figs_periodicity, figs_random, period_dnn, random_dnn, died_dnn


def periodicity_update():
    smf_base_path = "/root/zhouh/"
    if not os.path.exists(smf_base_path):
        os.makedirs(smf_base_path)
    
    df_dnn_list = pd.read_csv("/root/zhouh/dnn.csv")
    dnn_set = set()
    for dnn in df_dnn_list["APN名称"].unique():
        if pd.isnull(dnn):
            continue
        dnn_list =[item.lower() for item in dnn.split("、")]
        for dnn_item in dnn_list:
            dnn_set.add(dnn_item)
    
    df_5gc_smf, dnn_list = read_file_smf("/root/zhouh/data/smf/DM_5GC_SMF_ALARM_5M_0501_0531.csv")
    df_5gc_smf = df_5gc_smf[
            (df_5gc_smf["TIME_ID"]>=pd.to_datetime("2023-05-03")) & (df_5gc_smf["TIME_ID"]<pd.to_datetime("2023-05-17"))
        ]
    tempSliceMap = dict(map(lambda t2:
                            (t2[0], t2[1].sort_values(by="TIME_ID", ascending=True)), df_5gc_smf.groupby("DNN_NAME")))
    # worker_periodicity_check(tempSliceMap, "cmdtj", "AVG_PDU_SESSION_CNT",105,True)
    figs_periodicity_avg_pdu_cnt,figs_random_avg_pdu_cnt,period_dnn_avg_pdu_cnt,\
    random_dnn_avg_pdu_cnt, died_dnn_avg_pdu_cnt = period_check_entry(dnn_set,tempSliceMap,"AVG_PDU_SESSION_CNT",50,False)

    write_set_to_file(smf_base_path+"/period_dnn_avg_pdu_cnt.pickle",period_dnn_avg_pdu_cnt)
    write_set_to_file(smf_base_path+"/random_dnn_avg_pdu_cnt.pickle",random_dnn_avg_pdu_cnt)
    write_set_to_file(smf_base_path+"/died_dnn_avg_pdu_cnt.pickle",died_dnn_avg_pdu_cnt)
    
    # path_period = smf_base_path+"/period_dnn_avg_pdu_cnt.pdf"
    # path_random = smf_base_path+"/random_dnn_avg_pdu_cnt.pdf"
    # path_died = smf_base_path+"/died_dnn_avg_pdu_cnt.pdf"

    # with PdfPages(path_period) as pdf:
    #     for fig in figs_periodicity_avg_pdu_cnt:
    #         pdf.savefig(fig)
    # with PdfPages(path_random) as pdf:
    #     for fig in figs_random_avg_pdu_cnt:
    #         pdf.savefig(fig)

#     figs_periodicity_pdu_req_cnt,figs_random_avg_pdu_req_cnt,period_dnn_pdu_req_cnt,\
#     random_dnn_pdu_req_cnt, died_dnn_pdu_req_cnt = period_check_entry(tempSliceMap,"PDU_SESSION_REQ_CNT",40,False)

#     write_set_to_file(smf_base_path+"/period_dnn_pdu_req_cnt.pickle",period_dnn_pdu_req_cnt)
#     write_set_to_file(smf_base_path+"/random_dnn_pdu_req_cnt.pickle",random_dnn_pdu_req_cnt)
#     write_set_to_file(smf_base_path+"/died_dnn_pdu_req_cnt.pickle",died_dnn_pdu_req_cnt)

    


if __name__ == "__main__":
    periodicity_update() 
