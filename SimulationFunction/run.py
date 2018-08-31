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
import threading
import shutil

#get http body
class JSONObject:
    def __init__(self, d):
        self.__dict__ = d
def localTest():
    data = {
        'accelJSON': '{"b":["0.0e-3","0.0e-3","0.0e-3"],"b_drift":["5.0e-5","5.0e-5","5.0e-5"],"b_corr":["100.0","100.0","100.0"],"vrw":[0.03,0.03,0.03]}',
        'gpsJSON': '{"stdp":["5.0","5.0","7.0"],"stdv":[0.05,0.05,0.05]}',
        'initState': '[32,120,0,10,0,0,90,0,0]',
        'magJSON': '{"std":[0.01,0.01,0.01]}',
        #'motionCommand': '[[1,0,0,0,0,0,0,1,0],[1,-15,0,0,0,0,0,6,0],[1,0,0,0,0,0,0,3,0]]',
        'motionCommand': '[[1,0,0,0,0,0,0,200,0]]',
        'rateJSON': '{"b":["0.0","0.0","0.0"],"b_drift":[3.5,3.5,3.5],"b_corr":["100.0","100.0","100.0"],"arw":[0.25,0.25,0.25]}',
        'ref_frame': 1,
        'userId': 143,
        'algorithmName': 'Dmu380',
        #'algorithmName': 'FreeIntegration',
        'algorithmRunTimes': 1,
        'algorithmParams': '0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0',
        'algorithmStatistics': 'end-point',
        'userToken': 'giLbw9K01VBA9GAQsdSxpStrjTSPXRilNMdsPYFFaZDkQjkZYTdOQ5TB208pt5pU'
    }
    res = json.dumps(data)
    data1 = json.loads(res, object_hook=JSONObject)
    print data1
    fileName = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '-' + str(data1.userId)
    test_allan(data1,fileName,res)

def getHttpMsg():
    env = os.environ
    http_method = env['REQ_METHOD'] if 'REQ_METHOD' in env else 'GET'

    if http_method.lower() == 'post':
        request_body = open(env['req'], "r").read()
        if 'userId' in request_body:
            data = json.loads(request_body, object_hook=JSONObject)
            #fileName = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '-' + str(data.userId)
            fileName = data.fileName
            write_http_response(200,{'fileName': fileName})
            test_allan(data,fileName,request_body)
            #
            #t1 = threading.Thread(target=write_http_response, args=(200,{'statusCode': '200','fileName': fileName}))
            #t2 = threading.Thread(target=test_allan, args=(data,fileName,request_body))
            #t1.start()
            #t2.start()
            #t1.join()
            #t2.join()

        else :
            write_http_response(500,{'statusCode': '500','error': 'no user message'})        
    else :
        write_http_response(500,{'statusCode': '500','error': 'just support post'})        
#write response 
def write_http_response(status, body_dict):
    body_dict['statusCode'] = status
    return_dict = {
        "status": status,
        "body": body_dict,
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

def test_allan(data,fileName,request_body):
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
        if 'si' in data.magJSON:
            imu_err['mag_si'] = np.array([[float(magJSON.si[0]), float(magJSON.si[1]), float(magJSON.si[2])],
                [float(magJSON.si[3]), float(magJSON.si[4]), float(magJSON.si[5])],
                [float(magJSON.si[6]), float(magJSON.si[7]), float(magJSON.si[8])]])
        if 'hi' in data.magJSON:
            imu_err['mag_hi'] = np.array([float(magJSON.hi[0]), float(magJSON.hi[1]), float(magJSON.hi[2])])  
    if 'gpsJSON' in request_body:
        gpsFlag = True
        gpsJSON = json.loads(data.gpsJSON, object_hook=JSONObject)
        gpsObj['stdp'] = np.array([float(gpsJSON.stdp[0]), float(gpsJSON.stdp[1]), float(gpsJSON.stdp[2])])  
        gpsObj['stdv'] = np.array([float(gpsJSON.stdv[0]), float(gpsJSON.stdv[1]), float(gpsJSON.stdv[2])])  
        gpsObj['avail'] = 0.95
    # do not generate GPS and magnetometer data
    imu = imu_model.IMU(accuracy=imu_err, axis=axisNum, gps=False,gps_opt=gpsObj)

    
    if data.algorithmName == 'Allan':
        #### Allan analysis algorithm
        from demo_algorithms import allan_analysis
        algo = allan_analysis.Allan()
        #### start simulation
        sim = ins_sim.Sim([fs, 0.0, 0.0],
                          motion_def_path+"//motion_def-Allan.csv",
                          ref_frame=data.ref_frame,
                          imu=imu,
                          mode=None,
                          env=None,
                          algorithm=algo,
                          fileName = fileName
                          )
        sim.run(data.algorithmRunTimes,fileName,data)
        # generate simulation results, summary, and save data to files
        sim.results('demo',update_flag=True)  # save data files
        # plot data
        #sim.plot(['ad_accel', 'ad_gyro'])


    elif data.algorithmName == 'FreeIntegration':
        # Free integration in a virtual inertial frame
        ini_pos_vel_att = np.fromstring(data.algorithmParams, dtype=float, sep=',')
        #ini_pos_vel_att[0] = ini_pos_vel_att[0] * D2R
        #ini_pos_vel_att[1] = ini_pos_vel_att[1] * D2R
        #ini_pos_vel_att[6:9] = ini_pos_vel_att[6:9] * D2R
        # add initial states error if needed
        #ini_vel_err = np.array([0.0, 0.0, 0.0]) # initial velocity error in the body frame, m/s
        #ini_att_err = np.array([0.0, 0.0, 0.0]) # initial Euler angles error, deg
        #ini_pos_vel_att[3:6] += ini_vel_err
        #ini_pos_vel_att[6:9] += ini_att_err * D2R

        from demo_algorithms import free_integration
        algo = free_integration.FreeIntegration(ini_pos_vel_att)
        staticsFlag = data.algorithmStatistics == 'end-point' 
        sim = ins_sim.Sim([fs, 0.0, 0.0],
                      motion_def_path+"//motion_def-90deg_turn.csv",
                      ref_frame=data.ref_frame,
                      imu=imu,
                      mode=None,
                      env=None,
                      algorithm=algo,
                      fileName = fileName
                      )
        # run the simulation for 1000 times
        sim.run(data.algorithmRunTimes,fileName,data)
        # generate simulation results, summary
        # do not save data since the simulation runs for 1000 times and generates too many results
        sim.results('demo',end_point=staticsFlag,update_flag=True)
    
    elif data.algorithmName == 'VG':

        from demo_algorithms import dmu380_sim
        cfg_file = os.path.abspath('.//demo_algorithms//dmu380_sim_lib//ekfSim_tilt.cfg')
        algo = dmu380_sim.DMU380Sim(cfg_file)
        sim = ins_sim.Sim([fs, 0.0, fs],
                        "//mnt//share//jd_figure8.csv",
                        ref_frame=data.ref_frame,
                        imu=imu,
                        mode=None,
                        env=None,#'[0.1 0.01 0.11]g-random',
                        algorithm=algo,
                        fileName = fileName)
        sim.run(data.algorithmRunTimes,fileName,data)
        # generate simulation results, summary, and save data to files
        sim.results('aa',update_flag=True)  # do not save data

    #print int(( - times)*1000)

def deleteSaveDateFils():
    filePath = os.path.abspath(os.path.join(os.path.dirname( __file__ ),'.//demo_saved_data'))
    print filePath
    shutil.rmtree(filePath)

if __name__ == '__main__':
    getHttpMsg()
    #localTest()
