# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 23:12:05 2019

@author: James
"""

import pickle

from sklearn.preprocessing import Normalizer
import pandas as pd

normalizer = Normalizer()

data = pd.read_csv("qr_emo_liwc_pos_subj_features_MLready.csv")

X = data[[x for x in data.columns if "response" in x.lower()]]

normalizer.fit(X)

with open("Fact_Feel_noramlizer.pkl","wb") as f_p:
    pickle.dump(normalizer,f_p)
