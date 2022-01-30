import tkinter as tk
import factfeel_client as client
import threading


class FactFeelUI(tk.Frame):
    speech_to_text_widget = None

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
        self.speech_to_text_widget = tk.Text(self, width=800, height=240)
        self.speech_to_text_widget.config(state=tk.NORMAL)
        self.speech_to_text_widget.insert(tk.END, "Speech-to-text goes here")
        self.speech_to_text_widget.place(x=0, y=0)

        # create run button
        run_client_button = tk.Button(self, text="Run", command=self.run_client_cmd, width=120)
        run_client_button.place(x=0, y=240)

    def update_text(self, text):
        self.speech_to_text_widget.delete(1.0, tk.END)
        self.speech_to_text_widget.insert(tk.END, text)

    def run_client_cmd(self):
        threading.Thread(target=self.run_client).start()

    def run_client(self):
        light_orchestrator = client.LightOrchestrator(
            ip='192.168.1.9',
            lights=[
                "Hue lightstrip 1",
            ],
            colors=[
                [0.3227, 0.3290],  # White
                [0.643, 0.3045]  # Dark Red
            ]
        )
        speech_to_text = client.SpeechToText()
        server = client.FactFeelApi(url="https://fact-feel-flaskapp.herokuapp.com/predict")

        seq_num = 1

        while 1:

            text = speech_to_text.listen_transcribe()

            self.update_text(text)

            # data to be sent to api
            if text != 0:

                prediction = server.fact_feel_prediction(text)
                print(f"Received prediction of {prediction}")

                light_orchestrator.fact_feel_modify_lights(prediction)

            else:

                print("Skipping due to issues with response from Google")

            seq_num += 1


########################################################################################################################

if __name__ == "__main__":
    root = tk.Tk()
    FactFeelUI(root)
    root.mainloop()
