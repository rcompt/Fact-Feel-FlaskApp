# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 15:38:17 2019

@author: James
"""

import os
import json

from flask import Flask, render_template, request, jsonify
import logging

from model.Fact_Feel_Regression import FactFeelRegressor
from feature_extraction.feature_extractor import FeatureExtractor

log = logging.getLogger("FactFeel_log.txt")

ff_model = FactFeelRegressor()
feat_extractor = FeatureExtractor()      
                  
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html",prediction="NULL")

@app.route("/predict",methods=["POST"])
def predict():
    req_data = request.get_json()
    text = req_data["TEXT"]
    feats = feat_extractor.get_feats(text)
    prediction = ff_model.predict(feats)
    
#    return render_template("home.html",prediction=prediction)
    return jsonify({'prediction': prediction})
    

if __name__ == "__main__":
    app.run(debug=True)
    log.info("App is running")