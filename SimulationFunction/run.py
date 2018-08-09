# -*- coding: utf-8 -*-
# Filename: demo_allan.py

"""
Test Sim with Allan analysis.
Created on 2018-01-23
@author: dongxiaoguang
"""

import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'myenv/Lib/site-packages')))
import math
import numpy as np
from gnss_ins_sim.sim import imu_model
from gnss_ins_sim.sim import ins_sim
from azure.storage.blob import ContentSettings,AppendBlobService
import time

#get http body
class JSONObject:
    def __init__(self, d):
        self.__dict__ = d
        
def getHttpMsg():
    env = os.environ
    http_method = env['REQ_METHOD'] if 'REQ_METHOD' in env else 'GET'

    if http_method.lower() == 'post':
        request_body = open(env['req'], "r").read()
        if 'userId' in request_body:
            data = json.loads(request_body, object_hook=JSONObject)

            print(data)
            fileName = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '' + data.userToken
            data['name'] = fileName
            write_http_response(200,{'fileName': fileName})
            #test_allan(data)
        else :
            write_http_response(500,{'error': 'no user message'})        
    else :
        write_http_response(500,{'error': 'just support post'})        
#write response 
def write_http_response(status, body_dict):
    return_dict = {
        "status": status,
        "body": json.dumps(body_dict),
        "headers": {
            "Content-Type": "application/json"
        }
    }
    output = open(os.environ['res'], 'w')
    output.write(json.dumps(return_dict))
# globals
D2R = math.pi/180

motion_def_path = os.path.abspath('.//demo_motion_def_files//')
fs = 100.0          # IMU sample frequency

def test_allan():
    '''
    An Allan analysis demo for Sim.
    '''
    #### Customized IMU model parameters, typical for IMU381
    imu_err = {'gyro_b': np.array([0.0, 0.0, 0.0]),
               'gyro_arw': np.array([0.25, 0.25, 0.25]) * 1.0,
               'gyro_b_stability': np.array([3.5, 3.5, 3.5]) * 1.0,
               'gyro_b_corr': np.array([100.0, 100.0, 100.0]),
               'accel_b': np.array([0.0e-3, 0.0e-3, 0.0e-3]),
               'accel_vrw': np.array([0.03119, 0.03009, 0.04779]) * 1.0,
               'accel_b_stability': np.array([4.29e-5, 5.72e-5, 8.02e-5]) * 1.0,
               'accel_b_corr': np.array([200.0, 200.0, 200.0]),
               'mag_std': np.array([0.2, 0.2, 0.2]) * 1.0
              }
    # do not generate GPS and magnetometer data
    imu = imu_model.IMU(accuracy=imu_err, axis=6, gps=False)

    #### Allan analysis algorithm
    from demo_algorithms import allan_analysis
    algo = allan_analysis.Allan()

    #### start simulation
    sim = ins_sim.Sim([fs, 0.0, 0.0],
                      motion_def_path+"//motion_def-Allan.csv",
                      ref_frame=1,
                      imu=imu,
                      mode=None,
                      env=None,
                      algorithm=algo)
    sim.run()
    # generate simulation results, summary, and save data to files
    sim.results('demo',update_flag=True)  # save data files
    # plot data
    #sim.plot(['ad_accel', 'ad_gyro'])
def test1():
    text = 'status:0,userId:143'
    name = 'test/statue.cvs'
    append_blob_service = AppendBlobService(account_name='navview', account_key='+roYuNmQbtLvq2Tn227ELmb6s1hzavh0qVQwhLORkUpM0DN7gxFc4j+DF/rEla1EsTN2goHEA1J92moOM/lfxg==', protocol='http')
    append_blob_service.create_blob(container_name='data', blob_name=name,content_settings=ContentSettings(content_type='text/plain'))
    append_blob_service.append_blob_from_bytes(container_name='data',blob_name=name,blob=text)

if __name__ == '__main__':
    getHttpMsg()
