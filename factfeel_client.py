# imports
from phue import Bridge
from subprocess import call
import numpy as np
import speech_recognition as sr
import serial
import requests
import json


class LightOrchestrator:
    
    def __init__(self, ip = None, lights = None, colors = None, spectrum_size = 11):
        
        self.spectrum_size = spectrum_size
        
        if ip:
            self.set_ip(ip)
            self.connect_to_bridge()
        
            if lights:
                self.set_lights(lights)
                
            if colors:
                self.set_base_colors(colors[0], colors[1])
                self.set_colors()
                self.set_color_spectrum()
                self.set_colors()
        
    def set_ip(self, ip):
        self.ip = ip
        
    def connect_to_bridge(self):
        self.bridge = Bridge(self.ip)
        self.bridge.connect()
        
    def set_lights(self, lights):
        self.num_lights = len(lights)
        self.light_order = lights
        self.light_objs = self.bridge.get_light_objects('name')
        self.lamp_colors = {name : [0, 0] for name in self.light_objs}
        
        for light in self.light_order:
            if light not in self.lamp_colors:
                raise NameError(f'Light named {light} does not exist on the Hue Bridge!')
        
    def set_base_colors(self, fact_base, feel_base):
        self.fact_base_color = fact_base
        self.feel_base_color = feel_base
    
        
    def set_colors(self):
        for idx, light in enumerate(self.light_order):
            self.light_objs[light].xy = self.lamp_colors[light]
            print(f"Setting {light} to {self.lamp_colors[light]}")
        
    def set_color_spectrum(self):
        
        x_step_size = -1 * (self.fact_base_color[0] - self.feel_base_color[0]) / (self.spectrum_size - 2)
        y_step_size = -1 * (self.fact_base_color[1] - self.feel_base_color[1]) / (self.spectrum_size - 2)
        print(f"X Step Size: {x_step_size}")
        print(f"Y Step Size: {y_step_size}")
        
        x_range = np.arange(self.fact_base_color[0], self.feel_base_color[0] + x_step_size, x_step_size)
        y_range = np.arange(self.fact_base_color[1], self.feel_base_color[1] + y_step_size, y_step_size)
        
        self.spectrum = list(zip(x_range, y_range))
        self.lamp_spectrum_state = {}
        
        if len(self.light_order) == 1:
            self.lamp_spectrum_state[self.light_order[0]] = int(len(self.spectrum) / 2)
        else:
            for idx, light in enumerate(self.light_order):
                self.lamp_spectrum_state[light] = int(len(self.spectrum) / self.num_lights) * idx
        
        self.spectrum_to_color()
    
    def spectrum_to_color(self):
        if len(self.light_order) == 1:
            self.lamp_colors[self.light_order[0]] = self.spectrum[self.lamp_spectrum_state[self.light_order[0]]]
        else:
            for idx, light in enumerate(self.light_order):
                self.lamp_colors[light] = self.spectrum[self.lamp_spectrum_state[light]]
            
    
    def fact_feel_modify_lights(self, prediction):
        
        if prediction < 0:
            step_size = -1 + int(prediction)
        else:
            step_size = 1 + int(prediction)
            
        if self.num_lights == 1:
            self.lamp_spectrum_state[self.light_order[0]] = self.lamp_spectrum_state[self.light_order[0]] + step_size
        else:
            for idx, light in enumerate(self.light_order):
                self.lamp_spectrum_state[self.light_order[idx]] = self.lamp_spectrum_state[self.light_order[idx]] + step_size
                
        self.spectrum_to_color()
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

    light_orchestrator = LightOrchestrator(
        ip = '192.168.0.186',
        lights = [
            "Desk Lamp 1",
            "Desk Lightstrip 1",
            "Desk Lamp 2"
            ],
        colors = [
            [0.3227, 0.3290], # White
            [0.643, 0.3045]   # Dark Red
            ]
        )
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