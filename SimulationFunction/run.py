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
import time,json

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
            fileName = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '-' + data.userToken
            write_http_response(200,{'fileName': fileName})
            test_allan(data,fileName)
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
motion_def_path = './/SimulationFunction//demo_motion_def_files//'
fs = 100.0          # IMU sample frequency

def test_allan(data,fileName):
    '''
    An Allan analysis demo for Sim.
    '''
    #### Customized IMU model parameters, typical for IMU381
    rateJSON = json.loads(data.rateJSON, object_hook=JSONObject)
    accelJSON = json.loads(data.accelJSON, object_hook=JSONObject)
    axisNum = 6
    gpsFlag = False
    gpsObj = {}
    imu_err = {'gyro_b': np.array([float(rateJSON.b[0]), float(rateJSON.b[1]), float(rateJSON.b[2])]),
               'gyro_arw': np.array([float(rateJSON.arw[0]), float(rateJSON.arw[1]), float(rateJSON.arw[2])]) * 1.0,
               'gyro_b_stability': np.array([float(rateJSON.b_drift[0]), float(rateJSON.b_drift[1]), float(rateJSON.b_drift[2])]) * 1.0,
               'gyro_b_corr': np.array([float(rateJSON.b_corr[0]), float(rateJSON.b_corr[1]), float(rateJSON.b_corr[2])]),
               'accel_b': np.array([float(accelJSON.b[0]), float(accelJSON.b[1]), float(accelJSON.b[2])]),
               'accel_vrw': np.array([float(accelJSON.vrw[0]), float(accelJSON.vrw[1]), float(accelJSON.vrw[2])]) * 1.0,
               'accel_b_stability': np.array([float(accelJSON.b_drift[0]), float(accelJSON.b_drift[1]), float(accelJSON.b_drift[2])]) * 1.0,
               'accel_b_corr': np.array([float(accelJSON.b_corr[0]), float(accelJSON.b_corr[1]), float(accelJSON.b_corr[2])])
              }

    if 'magJSON' in request_body:
        axisNum = 9
        magJSON = json.loads(data.magJSON, object_hook=JSONObject)
        imu_err['mag_std'] = np.array([float(magJSON.std[0]), float(magJSON.std[1]), float(magJSON.std[2])]) * 1.0
        if 'si' in magJSON:
            imu_err['mag_si'] = np.array([[float(magJSON.si[0]), float(magJSON.si[1]), float(magJSON.si[2])],
                        [float(magJSON.si[3]), float(magJSON.si[4]), float(magJSON.si[5])],
                        [float(magJSON.si[6]), float(magJSON.si[7]), float(magJSON.si[8])]])
        if 'hi' in magJSON:
            imu_err['mag_hi'] = np.array([float(magJSON.hi[0]), float(magJSON.hi[1]), float(magJSON.hi[2])])  
    if 'gpsJSON' in request_body:
        gpsFlag = True
        gpsJSON = json.loads(data.gpsJSON, object_hook=JSONObject)
        gpsObj['stdp'] = np.array([float(gpsJSON.stdp[0]), float(gpsJSON.stdp[1]), float(gpsJSON.stdp[2])])  
        gpsObj['stdv'] = np.array([float(gpsJSON.stdv[0]), float(gpsJSON.stdv[1]), float(gpsJSON.stdv[2])])  
        gpsObj['avail'] = 0.95
    # do not generate GPS and magnetometer data
    imu = imu_model.IMU(accuracy=imu_err, axis=axisNum, gps=False,gps_opt=gpsObj)

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
    sim.run('',fileName,data)
    # generate simulation results, summary, and save data to files
    sim.results('demo',update_flag=True)  # save data files
    # plot data
    #sim.plot(['ad_accel', 'ad_gyro'])

def testDefaultAllan():
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
    #sim.run()


if __name__ == '__main__':
    getHttpMsg()
