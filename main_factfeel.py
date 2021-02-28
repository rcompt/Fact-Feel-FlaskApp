# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 15:38:17 2019

@author: James
"""

import os
import json

from flask import Flask, render_template, request, jsonify
import logging

from .model.Fact_Feel_Regression import FactFeelRegressor
from .feature_extraction.feature_extractor import FeatureExtractor

log = logging.getLogger("FactFeel_log.txt")

ff_model = FactFeelRegressor()
feat_extractor = FeatureExtractor()      
                  
app = Flask(__name__)

#class NumpyArrayEncoder(JSONEncoder):
#    def default(self, obj):
#        if isinstance(obj, numpy.ndarray):
#            return obj.tolist()
#        return JSONEncoder.default(self, obj)

@app.route("/")
def home():
    return render_template("home.html",prediction="2.56")

@app.route("/predict",methods=["POST"])
def predict():
    req_data = request.get_json()
    text = req_data["TEXT"]
    feats = feat_extractor.run(text)
    prediction = ff_model.predict([feats])
    
    predictionData = {'prediction': list(prediction)}
    #encodedPrediction = json.dumps(predictionData, cls=NumpyArrayEncoder)
#    return render_template("home.html",prediction=prediction)
    return jsonify(predictionData)
    

if __name__ == "__main__":
    app.run(debug=True)
    log.info("App is running")