#GUI imports
from tkinter import *
import threading
import queue  # Import queue for thread-safe communication

#TRANSCRIPTION imports
import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from time import sleep
from sys import platform

class App(Tk):
    def __init__(self, title):
        super().__init__()
        self.geometry("600x400")
        self.title(title)
        self.configure(bg='white')
        self.resizable(False, False)

        # CALLING CHILD CLASSES FOR USE IN METHODS
        self.t_display = Text_Display(self)
        self.run = Run_Label(self, self)

        # INPUT BOX WIDGETS
        self.input_box = self.t_display.input_box
        self.change_input_id = None

        # Queue for communication between the transcription thread and the main thread
        self.transcription_queue = queue.Queue()

        # Transcription thread variable
        self.transcripting_thread = None
        self.transcription_running = False # Flag to control transcription

        # Polling queue for transcription updates
        self.input_poll_transcription_queue()

        #Calling the function for updating input text
        self.upd_inp_text = Text_Display(self)
        self.update_input_text = self.upd_inp_text.update_input_text

        self.mainloop()
        
    def input_poll_transcription_queue(self):
        """
        Poll the transcription queue to check for updates from the transcription thread.
        If new transcription data is available, update the input box.
        """        
        try:
            transcription = self.transcription_queue.get_nowait()
            if transcription:
                print(f"Received transcription: {transcription}")
            # Call the update method to update the Text widget
            self.update_input_text(transcription)
        except queue.Empty:  # Use queue.Empty instead of Queue.Empty
            pass  # No transcription data available yet

        

        self.after(1500, self.input_poll_transcription_queue)

        


    def start_transcription(self):
        self.transcription_running = True
        def run_transcription():
            def main():
                print("Running transcription")
                parser = argparse.ArgumentParser()
                parser.add_argument("--model", default="tiny", help="Model to use", choices=["tiny"])
                parser.add_argument("--energy_threshold", default=1000, type=int)
                parser.add_argument("--record_timeout", default=2, type=float)
                parser.add_argument("--phrase_timeout", default=3, type=float)
                args = parser.parse_args()

                phrase_time = None
                data_queue = queue.Queue()
                recorder = sr.Recognizer()
                recorder.energy_threshold = args.energy_threshold
                recorder.dynamic_energy_threshold = False

                source = sr.Microphone(sample_rate=16000)

                try:
                    model = whisper.load_model("tiny")
                except Exception as e:
                    print(f"Error loading model: {e}")
                    return

                record_timeout = args.record_timeout
                phrase_timeout = args.phrase_timeout
                transcription = ['']

                with source:
                    recorder.adjust_for_ambient_noise(source)

                def record_callback(_, audio: sr.AudioData) -> None:
                    data = audio.get_raw_data()
                    data_queue.put(data)

                recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

                while self.transcription_running:
                    try:
                        now = datetime.utcnow()
                        if not data_queue.empty():
                            phrase_complete = False
                            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                                phrase_complete = True
                            phrase_time = now

                            audio_data = b''.join(data_queue.queue)
                            data_queue.queue.clear()

                            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                            result = model.transcribe(audio_np, fp16=torch.cuda.is_available())
                            text = result['text'].strip()

                            if phrase_complete:
                                transcription.append(text)
                            else:
                                transcription[-1] = text

                            # Send the transcription to the main thread via the queue
                            self.transcription_queue.put("\n".join(transcription))

                        sleep(0.25)
                    except KeyboardInterrupt:
                        break

            main()

        # Start the transcription thread
        self.transcripting_thread = threading.Thread(target=run_transcription)
        self.transcripting_thread.start()

    def stop_transcription(self):
        self.transcription_running = False
        print("Transcription stopping.")
        if self.transcripting_thread is not None:
            self.transcripting_thread.join(timeout=1)


class Run_Label(Label):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app_instance = app_instance
        self.is_on = False
        self.starter = PhotoImage(file="GUI elements/button/starter.png")
        self.on = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/green.png")
        self.off = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/red.png")

        self.running_label = Label(parent, text='CLICK TO RUN.', borderwidth=2, relief=SUNKEN, width=29, height=2, font=('Arial', 19))
        self.running_label.place(relx=0.95, rely=0.1, anchor=E)
        self.on_button = Button(parent, image=self.starter, bd=0, command=self.Switch, borderwidth=0)
        self.on_button.place(relx=0.05, rely=0.03)

    def Switch(self):
        print("Button clicked.")
        if self.is_on:
            self.on_button.config(image=self.off)
            self.running_label.config(text="STOPPED. CLICK AGAIN TO RUN.")
            self.is_on = False
            self.app_instance.stop_transcription()
        else:
            self.on_button.config(image=self.on)
            self.running_label.config(text="RUNNING. CLICK AGAIN TO STOP.")
            self.is_on = True
            self.app_instance.start_transcription()


class Text_Display(Label, LabelFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.input_label = Label(parent, text='INPUT', font=('Arial Bold', 11))
        # Changed from Label to Text widget
        self.input_box = Text(parent, font=('Arial Bold', 9), width=36, height=17, wrap=WORD, borderwidth=2, state=DISABLED)
        self.output_label = Label(parent, text='OUTPUT', font=('Arial Bold', 11))
        self.output_box = Label(parent, text="Waiting for activation...", font=('Arial Bold', 9), anchor=NW, width=36, height=17, bd=2)

        self.input_label.place(relx=0.225, rely=0.21)
        self.output_label.place(relx=0.685, rely=0.21)
        self.input_box.place(relx=0.05, rely=0.29)
        self.output_box.place(relx=0.5225, rely=0.29)

    def update_input_text(self, transcription_text):
        if transcription_text.strip():  # Check if the text is not just whitespace
            self.input_box.config(state=NORMAL)  # Enable editing to insert text
            self.input_box.insert(END, transcription_text + "\n")  # Add a new line for each new entry
            self.input_box.config(state=DISABLED)  # Disable editing again

            # Scroll to the end of the text widget
            self.input_box.see(END)  # Automatically scroll to the latest entry

# Initialize and run the app
app1 = App('Scam-Bait')
