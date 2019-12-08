# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 00:38:07 2019

@author: James
"""

# test_hello_add.py
from main_factfeel import app
from flask import json

def test_add():        
    response = app.test_client().post(
        '/predict',
        data=json.dumps({'TEXT': "Hello there! How is your day going? I hope you are having an amazing happy time!"}),
        content_type='application/json',
    )

    data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    print(data['prediction'])
    
if __name__ == "__main__":
    test_add()