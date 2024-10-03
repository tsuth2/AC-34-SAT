# GUI imports
from tkinter import *
import threading
import queue  # Import queue for thread-safe communication

# TRANSCRIPTION imports
import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch
from datetime import datetime, timedelta
from time import sleep
from sys import platform

# API imports
from openai import OpenAI
import os

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
        # Queue for communication between the API response thread and the main thread
        self.output_queue = queue.Queue()

        # Transcription thread variables
        self.transcribing_thread = None
        self.transcription_running = False  # Flag to control transcription

        # Output response thread variables
        self.output_thread = None
        self.output_running = False  # Flag to control outputted response

        # Polling queue for both transcription and response updates
        self.input_poll_transcription_queue()
        self.output_poll_response_queue()

        self.upd_text = Text_Display(self)
        # Calling the function for updating input text
        self.update_input_text = self.upd_text.update_input_text

        # Calling the function for updating output text
        self.update_output_text = self.upd_text.update_output_text

        # Accumulated transcription for resetting every 30 seconds
        self.transcription_accumulated = None

        self.mainloop()

    def input_poll_transcription_queue(self):
        """
        Poll the transcription queue to check for updates from the transcription thread.
        If new transcription data is available, update the input box.
        """        
        try:
            transcription = self.transcription_queue.get_nowait()
            if transcription.strip():  # Only proceed if transcription contains actual text
                self.update_input_text(transcription)
        except queue.Empty: 
            pass  # No transcription data available yet

        self.after(1500, self.input_poll_transcription_queue)

    def output_poll_response_queue(self):      
        """
        Same as the input poll function but checking the output queue
        for any changes and then applying them if so.
        """
        try:
            response = self.output_queue.get_nowait()
            if response.strip():  # Only proceed if response contains actual text
                self.update_output_text(response)
        except queue.Empty:
            pass  # No transcription data available yet

        self.after(3000, self.output_poll_response_queue)

    def start_transcription(self):
        self.transcription_running = True
        self.transcription_accumulated = ''  # Variable to store accumulated transcription
        
        # Start the transcription thread
        self.transcribing_thread = threading.Thread(target=self.run_transcription, daemon=True)
        self.transcribing_thread.start()

    def run_transcription(self):
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

            # Clear transcription every 30 seconds
            def clear_and_send_transcription():
                while self.transcription_running:
                    print("30-second interval reached, sending transcription segment...")

                    if self.transcription_accumulated.strip():
                        print("Sending transcription segment to API")
                        self.respond(self.transcription_accumulated)  # Send to OpenAI API

                        # Clear accumulated transcription and input box (UI)
                        self.transcription_accumulated = ''
                        self.input_box.config(state=NORMAL)
                        self.input_box.delete(1.0, END)
                        self.input_box.config(state=DISABLED)

                    # Wait for the next 30-second interval
                    sleep(30)

            # Start a thread for sending accumulated transcription every 30 seconds
            threading.Thread(target=clear_and_send_transcription, daemon=True).start()

            # Continuously transcribe and accumulate text
            while self.transcription_running:
                try:
                    now = datetime.utcnow()
                    if not data_queue.empty():
                        print("Processing audio data...")
                        audio_data = b''.join(data_queue.queue)
                        data_queue.queue.clear()

                        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        result = model.transcribe(audio_np, fp16=torch.cuda.is_available())
                        text = result['text'].strip()

                        if text:
                            print(f"Transcribed text: {text}")
                            transcription[-1] = text
                            self.transcription_accumulated += text + " "  # Accumulate transcription

                            # Update UI with the latest transcription
                            self.transcription_queue.put("\n".join(transcription))

                        sleep(0.25)  # Allow other threads to run
                except KeyboardInterrupt:
                    break

        # Start the main transcription logic in a thread
        threading.Thread(target=main, daemon=True).start()

    def respond(self, transcription_segment):
        def api_response(transcription_segment):
            try:
                print(f"Sending transcription to API: {transcription_segment}")
                client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are speaking to somebody on the phone that is discussing computer issues, and are purposely being unhelpful to them because they are a scammer."},
                        {"role": "user", "content": transcription_segment}
                    ]
                )

                response = completion.choices[0].message.content  # Use .content instead of subscripting
                print(f"Received API response: {response}")
                self.output_queue.put(response)  # Put the response in the queue to update the output box

            except Exception as e:
                print(f"Error with API request: {e}")

        # Start the API response thread for each transcription segment
        self.output_thread = threading.Thread(target=api_response, args=(transcription_segment,), daemon=True)
        self.output_thread.start()


    def stop_transcription(self):
        if self.transcription_running:
            print("Stopping transcription...")
            self.transcription_running = False  # Stop the transcription loop

            # Wait for the transcription thread to finish if it's still running
            if self.transcribing_thread and self.transcribing_thread.is_alive():
                self.transcribing_thread.join()
                print("Transcription thread stopped.")


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

            # Make sure to call respond only if there's accumulated transcription
            if self.app_instance.transcription_accumulated.strip():
                self.app_instance.respond(self.app_instance.transcription_accumulated)



class Text_Display(Label, LabelFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.input_label = Label(parent, text='INPUT', font=('Arial Bold', 11))
        # Changed from Label to Text widget
        self.input_box = Text(parent, font=('Arial Bold', 9), width=36, height=17, wrap=WORD, borderwidth=2, state=DISABLED)
        self.output_label = Label(parent, text='OUTPUT', font=('Arial Bold', 11))
        self.output_box = Text(parent, font=('Arial Bold', 9), width=36, height=17, wrap=WORD, borderwidth=2, state=DISABLED)

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

    def update_output_text(self, response):
        if response.strip():
            print("State NORMAL-ified!")
            self.output_box.config(state=NORMAL)
            print("Inserting jargon")
            self.output_box.insert(END, response + "\n")
            print("State DISABLED-ified!")
            self.output_box.config(state=DISABLED)

            # Scroll to bottom automatically
            print("Scrolling!")
            self.output_box.see(END)

# Initialize and run the app
app1 = App('Scam-Bait')
