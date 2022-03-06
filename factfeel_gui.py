import queue
import tkinter as tk
import factfeel_client as client
import threading
from matplotlib.backends.backend_tkagg import ( FigureCanvasTkAgg, NavigationToolbar2Tk )
from matplotlib import pyplot as plt

class FactFeelUI(tk.Frame):

    speech_to_text_widget = None
    prediction_tracker_canvas = None
    new_data_queue = []
    api_thread = None

    # Define settings upon initialization. Here you can specify
    def __init__(self, master=None):

        # parameters that you want to send through the Frame class.
        tk.Frame.__init__(self, master)

        # reference to the master widget, which is the tk window
        self.master = master
        self.master.geometry("800x480")

        # with that, we want to then run init_window, which doesn't yet exist
        self.init_window()

    # Creation of init_window
    def init_window(self):
        # changing the title of our master widget
        self.master.title("Fact/Feel UI")

        # allowing the widget to take the full space of the root window
        self.pack(fill=tk.BOTH, expand=1)

        # create speech to text field
        self.speech_to_text_widget = tk.Text(self)
        self.speech_to_text_widget.grid(row=0, sticky='ew')
        self.speech_to_text_widget.config(state=tk.NORMAL)
        self.speech_to_text_widget.insert(tk.END, "Speech-to-text goes here")
        self.speech_to_text_widget.place()

        # create run button
        run_client_button = tk.Button(self, text="Run", command=self.run_client_cmd)
        run_client_button.grid(row=1, sticky='ew')
        run_client_button.place()

        # queue
        self.new_data_queue = queue.Queue()

    def update_clock(self):
        if not self.api_thread.is_alive() and self.new_data_queue.empty():
            return

        while not self.new_data_queue.empty():
            new_data = self.new_data_queue.get()
            fig = self.plot(new_data)
            self.prediction_tracker_canvas = FigureCanvasTkAgg(fig, self)
            self.prediction_tracker_canvas.draw()
            self.prediction_tracker_canvas.get_tk_widget().grid(row=2, sticky='ew')

        self.master.after(10000, self.update_clock)

    def update_text(self, text):
        self.speech_to_text_widget.delete(1.0, tk.END)
        self.speech_to_text_widget.insert(tk.END, text)

    def run_client_cmd(self):
        # self.data_update_event = threading.Event()
        self.api_thread = threading.Thread(target=self.run_client)

        # start timer
        self.master.after(1000, self.update_clock)

        self.api_thread.start()

    def plot(self, fact_feel_text_data):
        y = [fact_feel_text_data[seq]["PRED"] for seq in fact_feel_text_data]
        x = [seq for seq in fact_feel_text_data]
        # fig = plt.plot(x, y)
        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_xlabel('Voice/Text Sample', fontsize=18)
        ax.set_ylabel('Fact-Feel Prediction', fontsize=18)
        ax.set_ylim(-5, 5)
        return fig

    def run_client(self):
        light_orchestrator = client.LightOrchestrator(
            ip='192.168.1.5',
            lights=[
                "Hue lightstrip 1",
            ],
            colors=[
                [0.3227, 0.3290],  # White
                [0.643, 0.3045]  # Dark Red
            ]
        )
        speech_to_text = client.SpeechToText()
        server = client.FactFeelApi(url="https://fact-feel-flaskapp.herokuapp.com/explain", plot_show=False)

        seq_num = 1

        while 1:

            text = speech_to_text.listen_transcribe()

            self.update_text(text)

            # data to be sent to api
            if text != 0:

                prediction = server.fact_feel_prediction(text)

                # grab new data from monitor thread
                new_data = server.get_fact_feel_text_data()

                # add to queue in order to pass to main GUI thread
                self.new_data_queue.put(new_data)

                # print(f"Received prediction of {prediction}")

                light_orchestrator.fact_feel_modify_lights(prediction)

            else:

                print("Skipping due to issues with response from Google")

            seq_num += 1


########################################################################################################################

if __name__ == "__main__":
    root = tk.Tk()
    FactFeelUI(root)
    root.mainloop()
