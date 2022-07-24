import socket
import tkinter as tk
import factfeel_client as client
import json
import threading
import queue
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import pyplot as plt
import sys


class FactFeelUI(tk.Tk):
    # Constants
    window_size = '800x480'

    # Globals
    speech_to_text_widget = None
    prediction_tracker_canvas = None
    new_data_queue = []
    api_thread = None
    light_ipaddress = None
    gettrace = None

    # Config
    ip = None
    lights = None
    colors = None

    def __init__(self):
        super().__init__()
        self.parse_config()
        self.init_window()
        self.new_data_queue = queue.Queue()

    # Parse user-specific configuration needed for the API
    def parse_config(self):
        with open('config.json') as json_file:
            data = json.load(json_file)
            print(f"Config data {data}")

            ip = data["ip"]
            self.validate_ip(ip)
            self.ip = ip

            lights = data["lights"]
            self.validate_light_list(lights)
            self.lights = data["lights"]

            colors = data["colors"]
            self.validate_colors(colors)
            self.colors = data["colors"]

    # Validates the IP address by attempting to convert it to 32-bit packed binary format
    # Will raise exception if ip address is invalid
    @staticmethod
    def validate_ip(ip):
        socket.inet_aton(ip)

    # Validates that the light list is 1. a list and 2. contains only strings
    # Will raise exception if light list is invalid
    @staticmethod
    def validate_light_list(lights):
        if not all(isinstance(item, str) for item in lights):
            raise Exception("Light list is not in correct format. Must be list of string")

    # Validates that the color array is 1. 2-dimentional and 2. contains only floats
    # Will raise exception if color list is invalid
    @staticmethod
    def validate_colors(colors):
        if not len(colors) == 2:
            raise Exception("Colors array is not in correct format. Must be two-dimensional")
        if not all(all(isinstance(item, float) for item in items) for items in colors):
            raise Exception("Colors array must only contain floats")

    # Creation of init_window
    def init_window(self):
        self.title('Fact/Feel Engineering Tool')
        self.geometry(self.window_size)

        # Don't fullscreen app if running in debug
        self.gettrace = getattr(sys, 'gettrace', None)
        if self.gettrace is None:
            self.attributes("-fullscreen", True)
            self.resizable(width=True, height=True)
        elif self.gettrace():
            self.attributes("-fullscreen", False)
            self.resizable(width=False, height=False)

        # Menu bar
        menu_bar = tk.Menu(self)
        config_menu = tk.Menu(menu_bar, tearoff=0)
        config_menu.add_command(label="Config", command=self.config_app_cmd)
        menu_bar.add_cascade(label="Config", menu=config_menu)
        self.config(menu=menu_bar)

        # Set up grid
        self.columnconfigure(0, weight=15)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

        # Set up main speech-to-text textbox. This displays what the speech recognition converts to text
        self.speech_to_text_widget = tk.Text(self, wrap="word", borderwidth=3)
        self.speech_to_text_widget.grid(row=0, column=0, sticky='nsew')

        self.run_client_cmd()

        clear_text_button = tk.Button(self, text="Clear Text", command=self.clear_text_cmd)
        clear_text_button.grid(row=1, column=0, sticky='nsew')

        # Set up initial blank graph
        fig = self.plot(None)
        self.prediction_tracker_canvas = FigureCanvasTkAgg(fig, self)
        self.prediction_tracker_canvas.draw()
        self.prediction_tracker_canvas.get_tk_widget().grid(row=0, rowspan=2, column=1, sticky='ew')

    def update_clock(self):
        if not self.api_thread.is_alive() and not self.new_data_queue.empty():
            return

        while not self.new_data_queue.empty():
            new_data = self.new_data_queue.get()
            fig = self.plot(new_data)
            self.prediction_tracker_canvas = FigureCanvasTkAgg(fig, self)
            self.prediction_tracker_canvas.draw()
            self.prediction_tracker_canvas.get_tk_widget().grid(row=0, rowspan=2, column=1, sticky='ew')

        self.after(10000, self.update_clock)

    def update_text(self, text):
        if isinstance(text, str):
            self.speech_to_text_widget.insert(tk.END, text + '\n')

    def config_app_cmd(self):
        config_popup = tk.Toplevel(self)
        config_popup.geometry(self.window_size)
        config_popup.title("Configure Fact/Feel")

        # Don't fullscreen popup if running in debug
        if self.gettrace is None:
            config_popup.attributes("-fullscreen", True)
            config_popup.resizable(width=True, height=True)
        elif self.gettrace():
            config_popup.attributes("-fullscreen", False)
            config_popup.resizable(width=False, height=False)

        config_popup.resizable(width=False, height=False)
        config_popup.columnconfigure(0, weight=1)
        config_popup.columnconfigure(1, weight=10)
        config_popup.columnconfigure(2, weight=1)
        config_popup.columnconfigure(3, weight=10)
        config_popup.columnconfigure(4, weight=1)
        config_popup.columnconfigure(5, weight=10)
        config_popup.columnconfigure(6, weight=1)
        config_popup.columnconfigure(7, weight=1)
        config_popup.rowconfigure(0, weight=1, rowheight=100)
        config_popup.rowconfigure(1, weight=100)

        first_octet_text = tk.Text(config_popup).grid(row=0, column=0, sticky='news')
        tk.Label(config_popup, text=".").grid(row=0, column=1, sticky='news')
        second_octet_text = tk.Text(config_popup).grid(row=0, column=2, sticky='news')
        tk.Label(config_popup, text=".").grid(row=0, column=3, sticky='news')
        third_octet_text = tk.Text(config_popup).grid(row=0, column=4, sticky='news')
        tk.Label(config_popup, text=".").grid(row=0, column=5, sticky='news')
        fourth_octet_text = tk.Text(config_popup).grid(row=0, column=6, sticky='news')

        update_ip_button = tk.Button(config_popup, text="Update IP Address", command=self.update_ipaddress_cmd)
        update_ip_button.grid(row=0, column=7, sticky='news')

    def update_ipaddress_cmd(self, new_ipaddress):
        self.light_ipaddress = new_ipaddress

    def clear_text_cmd(self):
        self.speech_to_text_widget.delete("1.0", tk.END)

    def run_client_cmd(self):
        self.api_thread = threading.Thread(target=self.run_client)
        self.api_thread.daemon = True

        # start timer
        self.after(1000, self.update_clock)
        self.api_thread.start()

    @staticmethod
    def plot(fact_feel_text_data):
        plt.clf()
        fig, ax = plt.subplots()

        if fact_feel_text_data is not None:
            y = [fact_feel_text_data[seq]["PRED"] for seq in fact_feel_text_data]
            x = [seq for seq in fact_feel_text_data]
            ax.plot(x, y)

        ax.set_xlabel('Voice/Text Sample', fontsize=10)
        ax.set_ylabel('Fact-Feel Prediction', fontsize=10)
        ax.set_ylim(-5, 5)

        fig.tight_layout()

        return fig

    def run_client(self):
        light_orchestrator = client.LightOrchestrator(
            ip=self.ip,
            lights=self.lights,
            colors=self.colors
        )
        speech_to_text = client.SpeechToText(init=True)
        api = client.FactFeelApi(url="https://fact-feel-flaskapp.herokuapp.com/explain", plot_show=False)

        seq_num = 1

        while self.api_thread.is_alive():
            text = speech_to_text.listen_transcribe()

            self.update_text(text)

            # data to be sent to api
            if text != 0:
                prediction, weight_map = api.fact_feel_explain(text)

                print("Weight Map\n")
                for key_ in weight_map:
                    print(f"Key: {key_}, Value: {weight_map[key_]}\n")

                # grab new data from monitor thread
                new_data = api.get_fact_feel_text_data()

                # add to queue in order to pass to main GUI thread
                self.new_data_queue.put(new_data)

                # print(f"Received prediction of {prediction}")

                light_orchestrator.fact_feel_modify_lights(prediction)

            else:
                print("Skipping due to issues with response from Google")

            seq_num += 1


########################################################################################################################


if __name__ == "__main__":
    app = FactFeelUI()
    app.mainloop()
