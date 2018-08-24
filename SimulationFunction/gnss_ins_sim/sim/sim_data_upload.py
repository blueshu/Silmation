# -*- coding: utf-8 -*-
# Fielname = sim_data.py

"""
update to azure bolb data class.
Created on 2018-7-25
@author: Kevin
"""
import os,sys
import shutil
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'myenv/Lib/site-packages')))
from azure.storage.blob import ContentSettings,AppendBlobService

class DataUpload(object):
    '''
    
    '''
    def __init__(self, dirName,dirPath):
        self.dirPath = dirPath
        self.dirName = dirName
        self.index = 0
        self.totalFiles = 0
        self.filse = []
        #self.readFils()

    def readFils1(self):
        n = 0
        filse = []
        filesName = self.dirPath
        filesName = os.path.abspath(os.path.join(os.path.dirname( __file__ ), filesName))
        for root, dirs, files in os.walk(filesName):
            for name in files:
                n += 1
                filse.append(name)
        self.totalFiles = n
        self.filse = filse

    def readFils(self):
        filesName = self.dirPath
        filesName = os.path.abspath(os.path.join(os.path.dirname( __file__ ), filesName))
        for root, dirs, files in os.walk(filesName):
            self.totalFiles = len(files)
            for name in files:
                self.update_files(name)

    def begin_update_files(self):
        self.readFils()
        #if self.totalFiles > 0:
            #self.update_files()

    def processCall(self,process,total):
        if process == total:
            if self.index < self.totalFiles-1:
                self.index += 1
            else: 
                self.clear_files()

    def update_files1(self):
        try:
            fileName = self.filse[self.index]
            filePath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), self.dirPath + '/' + fileName))
            f = open(filePath, 'r')
            text = f.read()
            f.close()
            name = self.dirName + '/' + fileName
            append_blob_service = AppendBlobService(account_name='navview', account_key='+roYuNmQbtLvq2Tn227ELmb6s1hzavh0qVQwhLORkUpM0DN7gxFc4j+DF/rEla1EsTN2goHEA1J92moOM/lfxg==', protocol='http')
            append_blob_service.create_blob(container_name='data', blob_name=name,content_settings=ContentSettings(content_type='text/plain'))
            append_blob_service.append_blob_from_bytes(container_name='data',blob_name=name,blob=text,progress_callback=self.processCall)
        except Exception as e:
            print(e)

    def update_files(self,fileName):
        try:
            filePath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), self.dirPath + '/' + fileName))
            f = open(filePath, 'r')
            text = f.read()
            f.close()
            name = self.dirName + '/' + fileName
            append_blob_service = AppendBlobService(account_name='navview', account_key='+roYuNmQbtLvq2Tn227ELmb6s1hzavh0qVQwhLORkUpM0DN7gxFc4j+DF/rEla1EsTN2goHEA1J92moOM/lfxg==', protocol='http')
            append_blob_service.create_blob(container_name='data', blob_name=name,content_settings=ContentSettings(content_type='text/plain'))
            append_blob_service.append_blob_from_bytes(container_name='data',blob_name=name,blob=text,progress_callback=self.processCall)
        except Exception as e:
            print(e)

    def clear_files(self):
        filePath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), self.dirPath))
        shutil.rmtree(filePath)
        print('end')

    def update_status(self,status = 0):
        text = str(status) + '&,&' + datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        name = self.dirName + '/status.cvs'
        append_blob_service = AppendBlobService(account_name='navview', account_key='+roYuNmQbtLvq2Tn227ELmb6s1hzavh0qVQwhLORkUpM0DN7gxFc4j+DF/rEla1EsTN2goHEA1J92moOM/lfxg==', protocol='http')
        append_blob_service.create_blob(container_name='data', blob_name=name,content_settings=ContentSettings(content_type='text/plain'))
        append_blob_service.append_blob_from_bytes(container_name='data',blob_name=name,blob=text)    


#if __name__ == '__main__':
    #DataUpload(dirPath='../../demo_saved_data/2018-07-25-13-01-51').begin_update_files()