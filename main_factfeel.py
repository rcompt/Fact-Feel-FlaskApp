# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 15:38:17 2019

@author: James
"""

import os

from flask import Flask, render_template
import logging


log = logging.getLogger("FactFeel_log.txt")

                        
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/predict")
def predict():
    pass

if __name__ == "__main__":
    app.run(debug=True)
    log.info("App is running")