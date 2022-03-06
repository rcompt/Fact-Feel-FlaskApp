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
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

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
    if request.data:
        #req_data = request.get_json()
        text = request.json.get('TEXT')
        feats = feat_extractor.run(text)
        prediction = ff_model.predict([feats])

        predictionData = {'prediction': list(prediction)}
        #encodedPrediction = json.dumps(predictionData, cls=NumpyArrayEncoder)
    #    return render_template("home.html",prediction=prediction)
        return jsonify(predictionData)
   
@app.route("/explain",methods=["POST"])
def explain():
    if request.data:
        #req_data = request.get_json()
        text = request.json.get('TEXT')
        feats, feat_categories = feat_extractor.run_explain(text)
        
        feat_coef = dict(zip(feat_extractor.feat_order, ff_model.model.coef_))
        word_weights = {}
        
        for word in feat_categories:
            word_weights[word] = sum([feat_coef[feat] for feat in feat_categories[word] if feat in feat_coef])
        
        prediction = ff_model.predict([feats])

        predictionData = {
            'prediction': list(prediction),
            'weights': word_weights
        }
        #encodedPrediction = json.dumps(predictionData, cls=NumpyArrayEncoder)
    #    return render_template("home.html",prediction=prediction)
        return jsonify(predictionData)

if __name__ == "__main__":
    app.run(debug=True)
    log.info("App is running")