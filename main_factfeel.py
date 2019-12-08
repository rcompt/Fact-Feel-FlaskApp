# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 15:38:17 2019

@author: James
"""

import os

from flask import Flask, render_template, request
import logging

from model.Fact_Feel_Regression import FactFeelRegressor
from feature_extraction.feature_extractor import FeatureExtractor

log = logging.getLogger("FactFeel_log.txt")

ff_model = FactFeelRegressor()
feat_extractor = FeatureExtractor()      
                  
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/predict",methods=["POST"])
def predict():
    req_data = request.get_json()
    data = req_data["DATA"]
    ff_model.predict(data)
    

if __name__ == "__main__":
    app.run(debug=True)
    log.info("App is running")