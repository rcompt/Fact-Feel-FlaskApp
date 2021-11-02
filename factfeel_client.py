# imports
from phue import Bridge
from subprocess import call
import speech_recognition as sr
import serial
import requests
import json
  
# define the fact feel model api url  
FACTFEEL_API = "https://fact-feel-flaskapp.herokuapp.com/predict"

r = sr.Recognizer()
with sr.Microphone(device_index = 2) as source:
    r.adjust_for_ambient_noise(source,duration=10)

b = Bridge('192.168.0.186')
b.connect()

class LightOrchestrator:
    def __init__(self, bridge):
        
        self.bridge = bridge
        
        self.light_objs = self.bridge.get_light_objects('name')
        self.lamp_colors = {name : 50.0 for name in light_objs}
        
        self.left = "Desk Lamp 1"
        self.right = "Desk Lamp 2"
        self.center = "Desk Lightstrip 1"
        
        self.light_objs[self.left].xy = [0, self.lamp_colors[self.left] / 100]
        self.light_objs[self.right].xy = [self.lamp_colors[self.right] / 100, 0]
        self.light_objs[self.center].xy = [0,0]

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

    light_orchestrator = LightOrchestrator(b)
  
    
    while(1):
        audio1 = listen1()
        text = voice1(audio1)
                # data to be sent to api
        if text != 0:
            text_elem = {
                    'TEXT':text,
                    'SEQ':seq
                   }
            all_text[seq] = text_elem
            
            data = {
                    'TEXT':" ".join([all_text[idx]["TEXT"] for idx in all_text]),
                   }        
            print("Sending: %s"%data['TEXT'])
            # sending post request and saving response as response object 
            response = requests.post(url = FACTFEEL_API, json = data) 
              
            # extracting response text
            response_data = json.loads(response.text)
            prediction = response_data["prediction"][0]
            all_text[seq]["PRED"] = prediction
            print(f"Recieved prediction of {prediction}")
            
            if prediction < 0:
                lamp_1_color
                lamp_1_color = lamp_1_color + (abs(prediction)/10)*lamp_1_color
                if lamp_1_color > 99:
                    lamp_1_color = 99
                light_names["Desk Lamp 1"].xy = [0,lamp_1_color/100]
                print(f"Set Lamp 1 to {lamp_1_color}") 
                
                lamp_2_color = lamp_2_color - (abs(prediction)/1.25)*lamp_2_color
                if lamp_2_color < 1:
                    lamp_2_color = 1
                light_names["Desk Lamp 2"].xy = [lamp_2_color/100,0]
                print(f"Set Lamp 2 to {lamp_2_color}")
            elif prediction > 0:
                lamp_1_color = lamp_1_color - (abs(prediction)/10)*lamp_1_color
                if lamp_1_color < 1:
                    lamp_1_color = 1
                light_names["Desk Lamp 1"].xy = [0,lamp_1_color/100]
                print(f"Set Lamp 1 to {lamp_1_color}")
                
                lamp_2_color = lamp_2_color + (abs(prediction)/1.25)*lamp_2_color
                if lamp_2_color > 99:
                    lamp_2_color = 99
                light_names["Desk Lamp 2"].xy = [lamp_2_color/100,0]
                print(f"Set Lamp 2 to {lamp_2_color}")
        else:
            print("Skipping due to issues with response from Google")
        seq += 1