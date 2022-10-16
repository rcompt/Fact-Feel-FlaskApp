import socket
import tkinter as tk
import factfeel_client as client
import json
import threading
import queue
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib import pyplot as plt
import sys


class FactFeelUI(tk.Tk):
    # Constants
    window_size = '800x480'

    # Globals
    config_popup = None
    speech_to_text_textbox = None
    ip_address_textbox = None
    light_list_textbox = None
    color_list_textbox = None

    prediction_tracker_canvas = None
    new_data_queue = []
    api_thread = None
    api_thread_stop_signal = None
    gettrace = None

    # Config
    ip = None
    lights = None
    colors = None

    def __init__(self):
        super().__init__()
        self.read_config_file()
        self.init_main_window()
        self.new_data_queue = queue.Queue()
        self.api_thread_stop_signal = threading.Event()
        self.start_factfeel_thread()

    def read_config_file(self):
        """
        Parse user-specific configuration needed for the API
        :return:
        """
        with open('config.json') as json_file:
            data = json.load(json_file)
            print(f"Config data {data}")

            ip = data["ip"]
            self.validate_config_ip_address(ip)
            self.ip = ip

            lights = data["lights"]
            self.validate_config_light_list(lights)
            self.lights = data["lights"]

            colors = data["colors"]
            self.validate_config_colors(colors)
            self.colors = data["colors"]

    def write_config_file(self):
        """
        Writes configuration data to file
        :return:
        """
        with open('config.json') as json_file:
            data = json.load(json_file)

        data['ip'] = self.ip
        data['lights'] = self.lights
        data['colors'] = self.colors

        with open('config.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

    @staticmethod
    def validate_config_ip_address(ip):
        """
        Validates the IP address by attempting to convert it to 32-bit packed binary format
        Will raise exception if ip address is invalid
        :param ip:
        :return:
        """
        socket.inet_aton(ip)

    @staticmethod
    def validate_config_light_list(lights):
        """
        Validates that the light list is 1. a list and 2. contains only strings
        Will raise exception if light list is invalid
        :param lights:
        :return:
        """
        if not all(isinstance(item, str) for item in lights):
            raise Exception("Light list is not in correct format. Must be list of string")

    @staticmethod
    def validate_config_colors(colors):
        """
        Validates that the color array is 1. 2-dimentional and 2. contains only floats
        Will raise exception if color list is invalid
        :param colors:
        :return:
        """
        if not len(colors) == 2:
            raise Exception("Colors array is not in correct format. Must be two-dimensional")
        if not all(all(isinstance(item, float) for item in items) for items in colors):
            raise Exception("Colors array must only contain floats")

    def init_main_window(self):
        """
        Creation of main UI View
        :return:
        """
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
        config_menu.add_command(label="Config", command=self.runtime_update_app_config_cmd)
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
        self.speech_to_text_textbox = tk.Text(self, wrap="word", borderwidth=3)
        self.speech_to_text_textbox.grid(row=0, column=0, sticky='nsew')

        clear_text_button = tk.Button(self, text="Clear Text", command=self.clear_text_cmd)
        clear_text_button.grid(row=1, column=0, sticky='nsew')

        # Set up initial blank graph
        fig = self.plot(None)
        self.prediction_tracker_canvas = FigureCanvasTkAgg(fig, self)
        self.prediction_tracker_canvas.draw()
        self.prediction_tracker_canvas.get_tk_widget().grid(row=0, rowspan=2, column=1, sticky='ew')

    def poll_api_thread(self):
        """
        Updates the GUI thread when the fact/feel thread updates
        :return:
        """
        if not self.api_thread.is_alive() and not self.new_data_queue.empty():
            return

        while not self.new_data_queue.empty():
            new_data = self.new_data_queue.get()
            fig = self.plot(new_data)

            for item in self.prediction_tracker_canvas.get_tk_widget().find_all():
                self.prediction_tracker_canvas.get_tk_widget().delete(item)

            self.prediction_tracker_canvas = FigureCanvasTkAgg(fig, self)
            self.prediction_tracker_canvas.draw()
            self.prediction_tracker_canvas.get_tk_widget().grid(row=0, rowspan=2, column=1, sticky='ew')

        self.after(10000, self.poll_api_thread)

    def append_textbox(self, text):
        """
        Appends the text box contents in the GUI with incoming data
        :param text: the new text
        :return:
        """
        if isinstance(text, str):
            self.speech_to_text_widget.insert(tk.END, text + '\n')

    def runtime_update_app_config_cmd(self):
        """
        Stops the API thread in order to update initial configuration
        :return:
        """
        # Set the event that will cause the thread to stop
        self.api_thread_stop_signal.set()
        self.api_thread.join()
        self.setup_runtime_config_popup()

    def setup_runtime_config_popup(self):
        """
        Builds the config popup that allows for changing the initial configuration at runtime.
        Displays over the main view until the changes have been confirmed
        :return:
        """
        self.config_popup = tk.Toplevel(self)
        self.config_popup.geometry(self.window_size)
        self.config_popup.title("Configure Fact/Feel")

        # Don't fullscreen popup if running in debug
        if self.gettrace is None:
            self.config_popup.attributes("-fullscreen", True)
            self.config_popup.resizable(width=True, height=True)
        elif self.gettrace():
            self.config_popup.attributes("-fullscreen", False)
            self.config_popup.resizable(width=False, height=False)

        self.config_popup.columnconfigure(0, weight=1)
        self.config_popup.columnconfigure(1, weight=1)
        self.config_popup.columnconfigure(2, weight=1)
        self.config_popup.columnconfigure(3, weight=1)
        self.config_popup.rowconfigure(0, weight=1)
        self.config_popup.rowconfigure(1, weight=1)
        self.config_popup.rowconfigure(2, weight=1)

        # Setup IP capture
        tk.Label(self.config_popup, text='IP Address:').grid(row=0, column=0, sticky='news')
        self.ip_address_textbox = tk.Text(self.config_popup)
        self.ip_address_textbox.grid(row=0, column=1, sticky='ew')
        self.ip_address_textbox.insert(tk.END, self.ip)

        # Setup Light list capture
        tk.Label(self.config_popup, text='Lights:').grid(row=1, column=0, sticky='news')
        self.light_list_textbox = tk.Text(self.config_popup)
        self.light_list_textbox.grid(row=1, column=1, sticky='ew')
        self.light_list_textbox.insert(tk.END, ', '.join(self.lights))

        # Setup Color list capture
        tk.Label(self.config_popup, text='Colors:').grid(row=2, column=0, sticky='news')
        self.color_list_textbox = tk.Text(self.config_popup)
        self.color_list_textbox.grid(row=2, column=1, sticky='ew')
        for i in range(len(self.colors)):
            for n in range(len(self.colors[i])):
                self.color_list_textbox.insert(tk.END, str(self.colors[i][n]))
                if n < len(self.colors[i]) - 1:
                    self.color_list_textbox.insert(tk.END, ', ')
            self.color_list_textbox.insert(tk.END, '\n')

        tk.Button(self.config_popup, text='Save', command=self.save_new_config_cmd).grid(row=3, column=0, sticky='news')
        tk.Button(self.config_popup, text='Cancel', command=self.new_config_complete_cmd).grid(row=3, column=1, sticky='news')

    def save_new_config_cmd(self):
        """
        Captures data entry from the config popup and writes the config file with it
        :return:
        """
        new_ip_address = self.ip_address_textbox.get("1.0", tk.END).strip()
        self.validate_config_ip_address(new_ip_address)
        self.ip = new_ip_address

        new_light_list = self.light_list_textbox.get("1.0", tk.END).strip().split(',')
        self.validate_config_light_list(new_light_list)
        self.lights = new_light_list

        new_color_list = []
        split1 = self.color_list_textbox.get("1.0", tk.END).strip().split('\n')
        for i in range(len(split1)):
            split2 = split1[i].strip().split(',')
            temp_array = []
            for n in range(len(split2)):
                temp_array.append(float(split2[n]))
            new_color_list.append(temp_array)
        self.validate_config_colors(new_color_list)
        self.colors = new_color_list

        self.write_config_file()
        self.new_config_complete_cmd()

    def new_config_complete_cmd(self):
        self.config_popup.destroy()
        self.start_factfeel_thread()

    def clear_text_cmd(self):
        """
        Clears all text from the GUI textbox
        :return:
        """
        self.speech_to_text_widget.delete("1.0", tk.END)

    def start_factfeel_thread(self):
        """
        This function kicks off the API thread from the main GUI thread
        :return:
        """
        self.api_thread_stop_signal.clear()
        self.api_thread = threading.Thread(target=self.run_factfeel)
        self.api_thread.daemon = True

        # start timer
        self.after(1000, self.poll_api_thread)
        self.api_thread.start()

    @staticmethod
    def plot(fact_feel_text_data):
        """
        Adds a new data point to the current chart
        :param fact_feel_text_data:
        :return:
        """
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

    def run_factfeel(self):
        """
        The fact/feel thread. Spun up from the main GUI thread
        :return:
        """
        try:
            light_orchestrator = client.LightOrchestrator(
                ip=self.ip,
                lights=self.lights,
                colors=self.colors
            )
        except client.phue.PhueRequestTimeout as prt:
            print(prt.message)
            return

        speech_to_text = client.SpeechToText(init=True)
        api = client.FactFeelApi(url="https://fact-feel-flaskapp.herokuapp.com/explain", plot_show=False)

        seq_num = 1

        while not self.api_thread_stop_signal.is_set():
            print(f"Thread is_alive() is: ", self.api_thread.is_alive())
            text = speech_to_text.listen_transcribe()

            self.append_textbox(text)

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
