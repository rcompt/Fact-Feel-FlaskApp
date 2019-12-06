# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 15:10:10 2019

@author: Ryan
"""

import pickle
import os

from sklearn import linear_model

class FactFeelRegressor():
    
    def __init__(self):
        self.model = self.load_model()
        
    def load_model(self):
        with open(os.path.join("model","Linear_Model_qr_py3.pkl"),"rb") as f_p:
            return pickle.load(f_p,encoding="latin-1")
        
    def predict(self,data):
        return self.model.predict(data)
