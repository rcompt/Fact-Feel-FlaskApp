# imports
from phue import Bridge
from subprocess import call
import speech_recognition as sr
import serial
import requests
import json


class LightOrchestrator:
    
    def __init__(self):
        
        self.bridge = Bridge('192.168.0.186')
        self.bridge.connect()
        
        self.light_objs = self.bridge.get_light_objects('name')
        self.lamp_colors = {name : 50.0 for name in self.light_objs}
        
        self.left = "Desk Lamp 1"
        self.right = "Desk Lamp 2"
        self.center = "Desk Lightstrip 1"
        
        self.set_colors()
        
    def set_colors(self):
        
        self.light_objs[self.left].xy = [0, self.lamp_colors[self.left] / 100]
        self.light_objs[self.right].xy = [self.lamp_colors[self.right] / 100, 0]
        self.light_objs[self.center].xy = [0,0]
        print(f"Set Lamp 1 to {self.lamp_colors[self.left]}")
        print(f"Set Lamp 2 to {self.lamp_colors[self.right]}")
        
    def fact_feel_modify_lights(self, prediction):
        
        if prediction < 0:
            self.lamp_colors[self.left] = self.lamp_colors[self.left] + (abs(prediction)/10)*self.lamp_colors[self.left]
            if self.lamp_colors[self.left] > 99:
                self.lamp_colors[self.left] = 99
             
            self.lamp_colors[self.right] = self.lamp_colors[self.right] - (abs(prediction)/1.25)*self.lamp_colors[self.right]
            if self.lamp_colors[self.right] < 1:
                self.lamp_colors[self.right] = 1
            
        elif prediction > 0:
            self.lamp_colors[self.left] = self.lamp_colors[self.left] - (abs(prediction)/10)*self.lamp_colors[self.left]
            if self.lamp_colors[self.left] < 1:
                self.lamp_colors[self.left] = 1
            
            self.lamp_colors[self.right] = self.lamp_colors[self.right] + (abs(prediction)/1.25)*self.lamp_colors[self.right]
            if self.lamp_colors[self.right] > 99:
                self.lamp_colors[self.right] = 99
        
        self.set_colors()


class SpeechToText:
    
    def __init__(self):
        
        self.r = sr.Recognizer()
        with sr.Microphone(device_index = 2) as source:
            self.r.adjust_for_ambient_noise(source,duration=10)
    
    def _listen(self, duration):
        '''
        listen: Record audio for the given 'duration' in seconds
        Param
            duration: int
        return
            audio: <Unknown!!!>
        '''
        with sr.Microphone(device_index = 2) as source:
            #r.adjust_for_ambient_noise(source)
            print("Say Something")
            audio = self.r.record(source, duration = duration)
            print("got it")
        return audio
    
    def _voice(self, audio):
        '''
        voice: Given an audio <unknown type>, send to Google api for speech to text response
        Param
            audio: <Unknown!!!>
        return
            text: str if pass else int
        '''
        try:
            text = self.r.recognize_google(audio)
            ## call('espeak ' + text, shell = True)
            print("you said: " + text)
            return text
        except sr.UnknownValueError:
            call(["espeak", "-s140 -ven+18 -z", "I don't know, it is hard to fucking hear."])
            print("Google Speech Recognition could not understand")
            return 0
        except sr.RequestError as e:
            print("Could not request results from Google")
            return 0
    
    def listen_transcribe(self, duration = 15):
        
        return self._voice(self._listen(duration))
    
class FactFeelApi:
    
    def __init__(self, url = "https://fact-feel-flaskapp.herokuapp.com/predict"):
        # define the fact feel model api url  
        self.fact_feel_url = url
        self.seq = 1
        self.all_text = {}
        
    def fact_feel_prediction(self, text):
        
        text_elem = {
            'TEXT': text,
            'SEQ' : self.seq
           }
        
        self.all_text[seq] = text_elem
        
        data = {
            'TEXT' : text
        }
        
        print("Sending: %s"%data['TEXT'])
        
        # sending post request and saving response as response object 
        response = requests.post(url = self.fact_feel_url, json = data) 
          
        # extracting response text
        response_data = json.loads(response.text)
        
        prediction = response_data["prediction"][0]
        
        self.all_text[seq]["PRED"] = prediction
        
        return prediction

def listen(duration):
    '''
    listen: Record audio for the given 'duration' in seconds
    Param
        duration: int
    return
        audio: <Unknown!!!>
    '''
    with sr.Microphone(device_index = 2) as source:
        #r.adjust_for_ambient_noise(source)
        print("Say Something")
        audio = r.record(source,duration=duration)
        print("got it")
        
    return audio

def voice(audio):
    '''
    voice: Given an audio <unknown type>, send to Google api for speech to text response
    Param
        audio: <Unknown!!!>
    return
        text: str if pass else int
    '''
    try:
        text = r.recognize_google(audio)
        ## call('espeak ' + text, shell = True)
        print("you said: " + text)
        return text
    except sr.UnknownValueError:
        call(["espeak", "-s140 -ven+18 -z", "I don't know, it is hard to fucking hear."])
        print("Google Speech Recognition could not understand")
        return 0
    except sr.RequestError as e:
        print("Could not request results from Google")
        return 0
    



if __name__ == "__main__":
    
    all_text = {}
    seq = 1

    light_orchestrator = LightOrchestrator()
    listener = SpeechToText()
    fact_feel = FactFeelApi(url = "https://fact-feel-flaskapp.herokuapp.com/predict")
    
    while(1):
        
        text = listener.listen_transcribe()
                # data to be sent to api
        if text != 0:
            
            prediction = fact_feel.fact_feel_prediction(text)
            print(f"Recieved prediction of {prediction}")
            
            light_orchestrator.fact_feel_modify_lights(prediction)
            
        else:
            
            print("Skipping due to issues with response from Google")
            
        seq += 1