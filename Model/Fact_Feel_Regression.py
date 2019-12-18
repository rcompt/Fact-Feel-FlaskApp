# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 15:10:10 2019

@author: Ryan
"""

import pickle
import os

#Temporary fix, need to provide main project path
#TODO: Fix need for absolute paths on importing other scripts
os.chdir("C:\\Users\\Ryan\\Documents\\Projects\\Fact-Feel-FlaskApp")

from sklearn import linear_model

from feature_extraction.feature_extractor import FeatureExtractor

class FactFeelRegressor():
    
    def __init__(self):
        
        
        with open(os.path.join("model","Fact_Feel_noramlizer.pkl"),"rb") as f_p:
            self.normalizer = pickle.load(f_p)
        
        self.model = self.load_model()
        
    def load_model(self):
        with open(os.path.join("model","Linear_Model_qr_py3.pkl"),"rb") as f_p:
            return pickle.load(f_p,encoding="latin-1")
        
    def predict(self,data):
        t_data = self.normalizer.transform(data)
        return self.model.predict(t_data)*-1


if __name__ == "__main__":
    print(os.getcwd())
    MODEL_ = FactFeelRegressor()
    FE_ = FeatureExtractor()
