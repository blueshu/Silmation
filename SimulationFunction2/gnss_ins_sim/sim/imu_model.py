# -*- coding: utf-8 -*-
# Fielname = imu_model.py

"""
IMU class.
Created on 2017-12-19
@author: dongxiaoguang
"""

import math
import numpy as np

D2R = math.pi/180

## default IMU, magnetometer and GPS error profiles.
# low accuracy, from AHRS380
#http://www.memsic.cn/userfiles/files/Datasheets/Inertial-System-Datasheets/AHRS380SA_Datasheet.pdf
gyro_low_accuracy = {'b': np.array([0.0, 0.0, 0.0]) * D2R,
                     'b_drift': np.array([10.0, 10.0, 10.0]) * D2R/3600.0,
                     'b_corr':np.array([100.0, 100.0, 100.0]),
                     'arw': np.array([0.75, 0.75, 0.75]) * D2R/60.0}
accel_low_accuracy = {'b': np.array([0.0e-3, 0.0e-3, 0.0e-3]),
                      'b_drift': np.array([2.0e-4, 2.0e-4, 2.0e-4]),
                      'b_corr': np.array([100.0, 100.0, 100.0]),
                      'vrw': np.array([0.05, 0.05, 0.05]) / 60.0}
mag_low_accuracy = {'si': np.eye(3) + np.random.randn(3, 3)*0.0,
                    'hi': np.array([10.0, 10.0, 10.0])*0.0,
                    'std': np.array([0.1, 0.1, 0.1])}
# mid accuracy, partly from IMU381
gyro_mid_accuracy = {'b': np.array([0.0, 0.0, 0.0]) * D2R,
                     'b_drift': np.array([3.5, 3.5, 3.5]) * D2R/3600.0,
                     'b_corr':np.array([100.0, 100.0, 100.0]),
                     'arw': np.array([0.25, 0.25, 0.25]) * D2R/60}
accel_mid_accuracy = {'b': np.array([0.0e-3, 0.0e-3, 0.0e-3]),
                      'b_drift': np.array([5.0e-5, 5.0e-5, 5.0e-5]),
                      'b_corr': np.array([100.0, 100.0, 100.0]),
                      'vrw': np.array([0.03, 0.03, 0.03]) / 60}
mag_mid_accuracy = {'si': np.eye(3) + np.random.randn(3, 3)*0.0,
                    'hi': np.array([10.0, 10.0, 10.0])*0.0,
                    'std': np.array([0.01, 0.01, 0.01])}
# high accuracy, partly from HG9900, partly from
# http://www.dtic.mil/get-tr-doc/pdf?AD=ADA581016
gyro_high_accuracy = {'b': np.array([0.0, 0.0, 0.0]) * D2R,
                      'b_drift': np.array([0.1, 0.1, 0.1]) * D2R/3600.0,
                      'b_corr':np.array([100.0, 100.0, 100.0]),
                      'arw': np.array([2.0e-3, 2.0e-3, 2.0e-3]) * D2R/60}
accel_high_accuracy = {'b': np.array([0.0e-3, 0.0e-3, 0.0e-3]),
                       'b_drift': np.array([3.6e-6, 3.6e-6, 3.6e-6]),
                       'b_corr': np.array([100.0, 100.0, 100.0]),
                       'vrw': np.array([2.5e-5, 2.5e-5, 2.5e-5]) / 60}
mag_high_accuracy = {'si': np.eye(3) + np.random.randn(3, 3)*0.0,
                     'hi': np.array([10.0, 10.0, 10.0])*0.0,
                     'std': np.array([0.001, 0.001, 0.001])}

## built-in GPS error profiles
gps_low_accuracy = {'stdp': np.array([5.0, 5.0, 7.0]),
                    'stdv': np.array([0.05, 0.05, 0.05]),
                    'avail': 0.95}
class IMU(object):
    '''
    IMU class
    '''

    def __init__(self, accuracy='low-accuracy', axis=6, gps=True, gps_opt=None):
        '''
        Args:
            accuracy: IMU grade.
                This can be a string to use the built-in IMU models:
                    'low-accuracy':
                    'mid-accuracy':
                    'high-accuracy':
                or a dictionary to custom the IMU model:
                    'gyro_b': gyro bias, deg/hr
                    'gyro_arw': gyro angle random walk, deg/rt-hr
                    'gyro_b_stability': gyro bias instability, deg/hr
                    'gyro_b_corr': gyro bias isntability correlation time, sec
                    'accel_b': accel bias, m/s2
                    'accel_vrw' : accel velocity random walk, m/s/rt-hr
                    'accel_b_stability': accel bias instability, m/s2
                    'accel_b_corr': accel bias isntability correlation time, sec
            axis: 6 for IMU, 9 for IMU+magnetometer
            gps: True if GPS exists, False if not.
            gps_op: a dictionary to specify the GPS error model.
                'stdp': position RMS error, meters
                'stdv': vertical RMS error, meters
                'avail': availability percentage, (0.0, 1.0]
        '''
        # check axis
        self.magnetometer = False
        if axis == 9:
            self.magnetometer = True
        elif axis != 6:
            raise ValueError('axis should be either 6 or 9.')

        # build imu error model
        self.gyro_err = gyro_low_accuracy                   #   default is low accuracy
        self.accel_err = accel_low_accuracy
        self.mag_err = mag_low_accuracy

        # accuracy is a string, use built-in models
        if isinstance(accuracy, str):
            if accuracy == 'low-accuracy':                  # 'low-accuracy'
                pass
            elif accuracy == 'mid-accuracy':                # 'mid-accuracy'
                self.gyro_err = gyro_mid_accuracy
                self.accel_err = accel_mid_accuracy
                self.mag_err = mag_mid_accuracy
            elif accuracy == 'high-accuracy':               # 'high-accuracy'
                self.gyro_err = gyro_high_accuracy
                self.accel_err = accel_high_accuracy
                self.mag_err = mag_high_accuracy
            else:                                           # not a valid string
                raise ValueError('accuracy is not a valid string.')
        # accuracy is a dict, user defined models
        elif isinstance(accuracy, dict):
            # set IMU and mag error params
            if 'gyro_b' in accuracy and\
               'gyro_b_stability' in accuracy and\
               'gyro_arw' in accuracy and\
               'accel_b' in accuracy and\
               'accel_b_stability' in accuracy and\
               'accel_vrw' in accuracy:                 # check keys in accuracy
                # required parameters
                self.gyro_err['b'] = accuracy['gyro_b'] * D2R / 3600.0
                self.gyro_err['b_drift'] = accuracy['gyro_b_stability'] * D2R / 3600.0
                self.gyro_err['arw'] = accuracy['gyro_arw'] * D2R / 60.0
                self.accel_err['b'] = accuracy['accel_b']
                self.accel_err['b_drift'] = accuracy['accel_b_stability']
                self.accel_err['vrw'] = accuracy['accel_vrw'] /60.0
                if self.magnetometer:   # at least noise std should be specified
                    if 'mag_std' in accuracy:
                        self.mag_err['std'] = accuracy['mag_std']
                    else:
                        raise ValueError('Magnetometer is enabled, ' +\
                                         'but its noise std is not specified.')
                # optional parameters
                if 'gyro_b_corr' in accuracy:
                    self.gyro_err['b_corr'] = accuracy['gyro_b_corr']
                else:
                    self.gyro_err['b_corr'] = np.array([float("inf"), float("inf"), float("inf")])
                if 'accel_b_corr' in accuracy:
                    self.accel_err['b_corr'] = accuracy['accel_b_corr']
                else:
                    self.accel_err['b_corr'] = np.array([float("inf"), float("inf"), float("inf")])
                if 'mag_si' in accuracy:
                    self.mag_err['si'] = accuracy['mag_si']
                else:
                    self.mag_err['si'] = np.eye(3)
                if 'mag_hi' in accuracy:
                    self.mag_err['hi'] = accuracy['mag_hi']
                else:
                    self.mag_err['hi'] = np.array([0.0, 0.0, 0.0])
            # raise error when required keys are missing
            else:
                raise ValueError('accuracy should at least have keys: \n' +\
                                 'gyro_b, gyro_b_stability, gyro_arw, ' +\
                                 'accel_b, accel_b_stability and accel_vrw')
        else:
            raise TypeError('accuracy is not valid.')

        # build GPS model
        if gps:
            self.gps = True
            if gps_opt is None:
                self.gps_err = gps_low_accuracy
            elif isinstance(gps_opt, dict):
                if 'stdp' in gps_opt and\
                   'stdv' in gps_opt and\
                   'avail' in gps_opt:
                    self.gps_err = gps_opt
                else:
                    raise ValueError('gps_opt should have key: stdp, stdv and avail')
            else:
                raise TypeError('gps_opt should be None or a dict')
        else:
            self.gps = False
            self.gps_err = None

    def set_gyro_error(self, gyro_error='low-accuracy'):
        '''
        set gyro error model
        Args:
            gyro_error
        '''
        pass

    def set_accel_error(self, accel_error='low-accuracy'):
        '''
        set accel error model
        Args:
            accel_error
        '''
        pass

    def set_gps(self, gps=True, gps_opt=None):
        '''
        set GPS options
        '''
        pass
