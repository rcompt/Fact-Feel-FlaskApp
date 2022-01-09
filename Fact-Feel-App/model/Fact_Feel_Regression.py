# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 15:10:10 2019

@author: Ryan
"""

import pickle
import os

from feature_extraction.feature_extractor import FeatureExtractor

feature_extract_path = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(
    feature_extract_path.split("Fact-Feel-App")[0],
    "Fact-Feel-App",
    "model"
    )

class FactFeelRegressor():
    
    def __init__(self):
        
        with open(os.path.join(model_path,"Fact_Feel_noramlizer.pkl"),"rb") as f_p:
            self.normalizer = pickle.load(f_p)
        
        self.model = self.load_model()
        
    def load_model(self):
        with open(os.path.join(model_path,"Linear_Model_qr_py3.pkl"),"rb") as f_p:
            return pickle.load(f_p)
        
    def predict(self,data):
        t_data = self.normalizer.transform(data)
        return self.model.predict(t_data)*-1


if __name__ == "__main__":
    print(os.getcwd())
    MODEL_ = FactFeelRegressor()
    FE_ = FeatureExtractor()
