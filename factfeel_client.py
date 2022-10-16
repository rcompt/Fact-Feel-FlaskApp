# imports
import phue
import speech_recognition as sr
import pyaudio
from rgbxy import Converter
from playsound import playsound

import numpy as np
from matplotlib import pyplot as plt

import threading
import queue
import requests
import json
import logging
import time

log_config = {
        "filename" : "FactFeelApi.log",
        "filemode" : "a",
        "level"    : logging.INFO
    }

logging.basicConfig(**log_config)

from datetime import datetime
import pytz
import os



class LightOrchestrator:
    
    def __init__(self, ip = None, lights = None, colors = None, spectrum_size = 11):
        
        self.spectrum_size = spectrum_size
        
        
        ######
        #
        # Converter has some drift if you convert back and forth between the 
        # xy_to_rgb and rgb_to_xy functions. This may be fixed if we find the
        # correct Gamut for each light. Or we recommed only a limited number
        # of calls to this function.
        #
        ######
        self.converter = Converter()
        
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
        self.bridge = phue.Bridge(self.ip)
        self.bridge.connect()
        
    def set_lights(self, lights):
        self.num_lights = len(lights)
        self.light_order = lights
        self.light_objs = self.bridge.get_light_objects('name')
        self.lamp_colors = {name : [0, 0] for name in self.light_objs}
        
        for light in self.light_order:
            if light not in self.lamp_colors:
                raise NameError(f'Light named {light} does not exist on the Hue Bridge!')
        
    def xy_to_rgb(self, colors):
        return [self.converter.xy_to_rgb(x, y) for x, y in colors]
    
    def rgb_to_xy(self, colors):
        return [self.converter.rgb_to_xy(r, g, b) for r, g, b in colors]    
    
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
    
    def check_spectrum_bounds(self):
        for idx, light in enumerate(self.light_order):
            self.lamp_spectrum_state[self.light_order[idx]] = min(
                self.lamp_spectrum_state[self.light_order[idx]], 
                len(self.spectrum) - 1
            )            
            
            self.lamp_spectrum_state[self.light_order[idx]] = max(
                self.lamp_spectrum_state[self.light_order[idx]], 
                0
            )
    
    def spectrum_to_color(self):
        
        self.check_spectrum_bounds()
        
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
    
    def __init__(self, device = 2, init = False, debug = False):
        
        self._debug = debug
        
        if debug:
            self._device_listings()
        self._device = device
        
        if init:
            self.initialize()

    
    @property
    def device(self):
        return self._device
    
    @device.setter
    def device(self, device):
        self._device = device
    
    def _device_listings(self):
        audio = pyaudio.PyAudio()
        
        num_devices = audio.get_host_api_info_by_index(0).get("deviceCount",0)
        device_count = 0
        self.devices = {}
        for i in range(0, num_devices):
            if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                if self._debug:
                    print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))
                    
                self.devices[i] = audio.get_device_info_by_host_api_device_index(0, i).get('name')
                device_count += 1
        if self._debug:
            print(f"{device_count} devices found through PyAudio.")
            
        return self.devices
        
    def _set_device(self, device_index):
        self.device
        
    def print_dict(self, dict_):
        new_str = "{"
        for elem in dict_:
            new_str += f"\n\t{elem}: '{dict_[elem]}',\n"
        new_str = new_str[:-2] +"\n}"
        return new_str
        
        
    def _check_device(self):
        audio = pyaudio.PyAudio()
        if hasattr(self, "device"):
            try:
                input_device = audio.get_device_info_by_index(self.device)
                if input_device.get("maxInputChannels",0) == 0:
                    raise RuntimeError(
                        (f"Device selected {input_device.get('name','Unknown')} "
                         "does not contain any input channels, please select "
                         "an input device with input channels!\n" + self.print_dict(self._device_listings())
                         )
                    )
            except:
                raise ValueError(
                    "Selected device index not present in the list of available "
                    "devices, please select one of the following:\n" + self.print_dict(self._device_listings())
                )
                                         
        else:
            raise ValueError("device has not been set for SpeechToText object, please set the 'device' property for this object!")
        
    
    def initialize(self):
        
        if self._debug:
            print(f"Using device index {self._device} : {self.devices[self._device]}")
        
        self._audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self._check_device()
        self.recognizer = sr.Recognizer()
        with sr.Microphone(device_index = self._device) as source:
            playsound(
                os.path.join(
                    "Fact-Feel-App",
                    "resources",
                    "Im_Listening.mp3"
                )
            )
            self.recognizer.adjust_for_ambient_noise(source,duration=10)  
    
    def _listen(self, duration):
        '''
        listen: Record audio for the given 'duration' in seconds
        Param
            duration: int
        return
            audio: <Unknown!!!>
        '''
        
        if hasattr(self, "recognizer"):

            with sr.Microphone(device_index = self._device) as source:
                #r.adjust_for_ambient_noise(source)
                ## print("Say Something")
                audio = self.recognizer.record(source, duration = duration)
                ## print("got it")
            return audio
        
        else:
            raise RuntimeError("_listen() was called before calling initializing the recognizer! Please call initialize() before calling _listen()!")
    
    
    def _stream_listen(self, duration):
        '''
        stream_listen: Streaming implementation of record audio for the given 'duration' in seconds
        Param
            duration: int
        return
            audio: <Unknown!!!>
        '''
        
        if hasattr(self, "recognizer"):

            while not self.audio_thread_stop_signal.is_set() and self.audio_thread.is_alive():
                with sr.Microphone(device_index = self._device) as source:
                    #r.adjust_for_ambient_noise(source)
                    #print("Stream_Listen: Say Something")
                    audio = self.recognizer.record(source, duration = duration)
                    #print("Stream_Listen: got it")
                    self._audio_queue.put(audio)
        
        else:
            raise RuntimeError("_listen() was called before calling initializing the recognizer! Please call initialize() before calling _listen()!")
    
    def _stream_transcribe(self, duration):
        '''
        stream_transcribe: check if new audio in queue, then send to transcribe that audio to text
        Param
            duration: int
        return
            audio: <Unknown!!!>
        '''        
        while not self.transcribe_thread_stop_signal.is_set() and self.transcribe_thread.is_alive():      
        
            while not self._audio_queue.empty():
                new_audio_data = self._audio_queue.get()
                text = self._voice(new_audio_data)
                self.text_queue.put(text)
                print(f"Stream_Listen: {text}")
            
            time.sleep(duration)
            
    
    def _voice(self, audio):
        '''
        voice: Given an audio <unknown type>, send to Google api for speech to text response
        Param
            audio: <Unknown!!!>
        return
            text: str if pass else int
        '''
        try:
            text = self.recognizer.recognize_google(audio)
            ## call('espeak ' + text, shell = True)
            ## print("you said: " + text)
            return text
        except sr.UnknownValueError:
            ## call(["espeak", "-s140 -ven+18 -z", "I don't know, it is hard to fucking hear."])
            print("Google Speech Recognition could not understand")
            return 0
        except sr.RequestError as e:
            print(f"Could not request results from Google: {e}")
            return 0
    
    def stream_main_loop(self, duration = 15):
        try:      
            if not self.audio_thread.is_alive() and not self.audio_thread_stop_signal.is_set():
                return
        
            while not self._audio_queue.empty():
                new_audio_data = self._audio_queue.get()
                text = self._voice(new_audio_data)
                self.text_queue.put(text)
                print(f"Stream_Listen: {text}")
            
            time.sleep(duration)
            self.stream_main_loop()
            
        except KeyboardInterrupt:
            print("Keyboard Interrupt, stopping stream")
            self.stream_stop()

    
    def stream_stop(self):
        """
        Stops the API thread in order to update initial configuration
        :return:
        """
        # Set the event that will cause the thread to stop
        self.audio_thread_stop_signal.set()
        self.audio_thread.join()
    
    def stream_listen_transcribe(self, duration = 15):
        try:
            self.audio_thread_stop_signal = threading.Event()
            self.audio_thread = threading.Thread(target=self._stream_listen, args=[duration])
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            self.transcribe_thread_stop_signal = threading.Event()
            self.transcribe_thread = threading.Thread(target=self._stream_transcribe, args=[duration])
            self.transcribe_thread.daemon = True
            self.transcribe_thread.start()        
            
            #time.sleep(duration)
            #self.stream_main_loop(duration = duration)
                              
        except KeyboardInterrupt:
            print("Keyboard Interrupt, stopping stream")
            self.stream_stop()
            
    def listen_transcribe(self, duration = 15):
        return self._voice(self._listen(duration))
    
class FactFeelApi:
    
    def __init__(self, url = "https://fact-feel-flaskapp.herokuapp.com/predict", plot_show = True):
        # define the fact feel model api url  
        self.fact_feel_url = url
        self.seq = 1
        self.fact_feel_text_data = {}
        self.plot_show = plot_show
        
        plt.style.use("fivethirtyeight")
        
        self.logger = logging.getLogger('api_logger')
        self.logger.setLevel(logging.INFO)
        
        
        self.timezone = pytz.timezone("America/Los_Angeles")
        self.logger.info(datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S"))
        
    def fact_feel_prediction(self, text):
        
        self.logger.info(datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info(f"Sending Text to Prediction: {text} \n")
        
        text_elem = {
            'TEXT': text,
            'SEQ' : self.seq
           }
        
        self.fact_feel_text_data[self.seq] = text_elem
        
        data = {
            'TEXT' : text
        }
        
        print("Sending: %s"%data['TEXT'])
        
        # sending post request and saving response as response object 
        response = requests.post(url = self.fact_feel_url, json = data) 
          
        # extracting response text
        response_data = json.loads(response.text)
        
        prediction = response_data["prediction"][0]
        
        self.fact_feel_text_data[self.seq]["PRED"] = prediction
        
        if self.plot_show:
            self.plot()
        
        self.seq += 1
        
        
        self.logger.info(f"Recieved Prediction: {prediction} \n")
        return prediction
    
    def fact_feel_explain(self, text):
        
        self.logger.info(datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info(f"Sending Text to Explain: {text} \n")
        
        text_elem = {
            'TEXT': text,
            'SEQ' : self.seq
           }
        
        self.fact_feel_text_data[self.seq] = text_elem
        
        data = {
            'TEXT' : text
        }
        
        print("Sending: %s"%data['TEXT'])
        
        # sending post request and saving response as response object 
        response = requests.post(url = self.fact_feel_url, json = data) 
          
        # extracting response text
        response_data = json.loads(response.text)
        
        prediction = response_data["prediction"][0]
        weights = response_data["weights"]
        
        self.fact_feel_text_data[self.seq]["PRED"] = prediction
        self.fact_feel_text_data[self.seq]["WEIGHTS"] = weights
        
        if self.plot_show:
            self.plot()
        
        self.seq += 1
        
        self.logger.info(f"Recieved Prediction: {prediction} \n")
        self.logger.info(f"Recieved Weights: {weights} \n")
        
        return prediction, weights
    
    def plot(self):
        y = [self.fact_feel_text_data[seq]["PRED"] for seq in self.fact_feel_text_data]
        x = [seq for seq in self.fact_feel_text_data]
        fig = plt.plot(x, y)
        plt.xlabel('Voice/Text Sample', fontsize=18)
        plt.ylabel('Fact-Feel Prediction', fontsize=18)
        plt.ylim(-5, 5)
        if self.plot_show:
           plt.show()
        else:
            return fig

    def get_fact_feel_text_data(self):
        return self.fact_feel_text_data

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
    listener = SpeechToText(device = 4,init = True, debug = True)
    fact_feel = FactFeelApi(url = "https://fact-feel-flaskapp.herokuapp.com/explain")
    
    listener.stream_listen_transcribe()
    
    while(1):
        
         #text = listener.listen_transcribe()
        
         #time.sleep(5)
        
         if not listener.text_queue.empty():
        
             text = listener.text_queue.get()
            
             # data to be sent to api
             if text != 0:
            
                 prediction, _ = fact_feel.fact_feel_explain(text)
                 print(f"Recieved prediction of {prediction}")
            
                 light_orchestrator.fact_feel_modify_lights(prediction)
            
             else:
            
                 print("Skipping due to issues with response from Google")
            
             seq += 1