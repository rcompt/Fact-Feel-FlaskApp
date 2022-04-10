import tkinter as tk
import factfeel_client as client
import threading
import queue
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import pyplot as plt


class FactFeelUI(tk.Tk):
    # Globals
    speech_to_text_widget = None
    prediction_tracker_canvas = None
    new_data_queue = []
    api_thread = None

    def __init__(self):
        super().__init__()
        self.init_window()
        self.new_data_queue = queue.Queue()

    # Creation of init_window
    def init_window(self):
        self.title('Fact/Feel Engineering Tool')
        self.geometry('800x480')
        self.resizable(width=False, height=False)

        # Set up grid
        self.columnconfigure(0, weight=15)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

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
            ip='192.168.1.3',
            lights=[
                "Hue lightstrip 1",
            ],
            colors=[
                [0.3227, 0.3290],  # White
                [0.643, 0.3045]  # Dark Red
            ]
        )
        speech_to_text = client.SpeechToText()
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
