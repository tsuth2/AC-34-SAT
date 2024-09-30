#GUI imports
from tkinter import *
import threading

#TRANSCRIPTION imports
import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

my_list = ['1', '2', '3', '4']
your_list = ['5', '6', '7', '8']
i = 0
z = 0

class App(Tk):
    def __init__(self, title):
        super().__init__()
        self.geometry("600x400")
        self.title(title)
        self.configure(bg='white')
        self.resizable(False, False)

        #CALLING CHILD CLASSES FOR USE IN METHODS
        self.t_display = Text_Display(self)
        self.run = Run_Label(self, self)

        #INPUT BOX WIDGETS FOR CHANGE_INPUT() METHOD
        self.input_box = self.t_display.input_box
        self.change_input_id = None
        self.i = 0

        #OUTPUT BOX WIDGETS FOR CHANGE_OUTPUT() METHOD
        self.output_box = self.t_display.output_box
        self.change_output_id = None
        self.z = 0

        #TRANSCRIPTION THREAD VARIABLE
        self.transcripting_thread = None

        self.mainloop()
    '''
    def change_input(self):
        global i
        self.input_box.configure(text=(my_list[self.i]))
        if len(my_list) - 1 == self.i:
            self.i = 0
        else:
            self.i += 1

        if self.run.is_on:
            self.change_input_id = self.after(1500, self.change_input)
        else:
            if self.change_input_id is not None:
                self.after_cancel(self.change_input_id)
                self.change_input_id = None
    '''


    def change_output(self):
        global z
        self.output_box.configure(text=(your_list[self.z]))
        if len(your_list) - 1 == self.z:
            self.z = 0
        else:
            self.z += 1
        
        if self.run.is_on:
            self.change_output_id = self.after(1500, self.change_output)
        else:
            if self.change_output_id is not None:
                self.after_cancel(self.change_output_id)
                self.change_output_id = None

    def start_transcription(self):
        def run_transcription():
            def main():
                parser = argparse.ArgumentParser()
                parser.add_argument("--model", default="tiny", help="Model to use",
                                    choices=["tiny", "base", "small", "medium", ""])
                parser.add_argument("--non_english", action='store_true',
                                    help="Don't use the english model.")
                parser.add_argument("--energy_threshold", default=1000,
                                    help="Energy level for mic to detect.", type=int)
                parser.add_argument("--record_timeout", default=2,
                                    help="How real time the recording is in seconds.", type=float)
                parser.add_argument("--phrase_timeout", default=3,
                                    help="How much empty space between recordings before we "
                                        "consider it a new line in the transcription.", type=float)
                if 'linux' in platform:
                    parser.add_argument("--default_microphone", default='pulse',
                                        help="Default microphone name for SpeechRecognition. "
                                            "Run this with 'list' to view available Microphones.", type=str)
                args = parser.parse_args()

                # The last time a recording was retrieved from the queue.
                phrase_time = None
                # Thread safe Queue for passing data from the threaded recording callback.
                data_queue = Queue()
                # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
                recorder = sr.Recognizer()
                recorder.energy_threshold = args.energy_threshold
                # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
                recorder.dynamic_energy_threshold = False

                # Important for linux users.
                # Prevents permanent application hang and crash by using the wrong Microphone
                if 'linux' in platform:
                    mic_name = args.default_microphone
                    if not mic_name or mic_name == 'list':
                        print("Available microphone devices are: ")
                        for index, name in enumerate(sr.Microphone.list_microphone_names()):
                            print(f"Microphone with name \"{name}\" found")
                        return
                    else:
                        for index, name in enumerate(sr.Microphone.list_microphone_names()):
                            if mic_name in name:
                                source = sr.Microphone(sample_rate=16000, device_index=index)
                                break
                else:
                    source = sr.Microphone(sample_rate=16000)

                # Load / Download model
                model = args.model
                if args.model != "large" and not args.non_english:
                    model = model + ".en"
                audio_model = whisper.load_model("tiny")

                record_timeout = args.record_timeout
                phrase_timeout = args.phrase_timeout

                transcription = ['']

                with source:
                    recorder.adjust_for_ambient_noise(source)

                def record_callback(_, audio:sr.AudioData) -> None:
                    """
                    Threaded callback function to receive audio data when recordings finish.
                    audio: An AudioData containing the recorded bytes.
                    """
                    # Grab the raw bytes and push it into the thread safe queue.
                    data = audio.get_raw_data()
                    data_queue.put(data)

                # Create a background thread that will pass us raw audio bytes.
                # We could do this manually but SpeechRecognizer provides a nice helper.
                recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

                self.input_box.configure(text="Model loading...")
                # Cue the user that we're ready to go.
                self.input_box.configure(text="Transcription model loaded")
                print("Model loaded.\n")

                while True:
                    try:
                        now = datetime.utcnow()
                        # Pull raw recorded audio from the queue.
                        if not data_queue.empty():
                            phrase_complete = False
                            # If enough time has passed between recordings, consider the phrase complete.
                            # Clear the current working audio buffer to start over with the new data.
                            if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                                phrase_complete = True
                            # This is the last time we received new audio data from the queue.
                            phrase_time = now
                            
                            # Combine audio data from queue
                            audio_data = b''.join(data_queue.queue)
                            data_queue.queue.clear()
                            
                            # Convert in-ram buffer to something the model can use directly without needing a temp file.
                            # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                            # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                            # Read the transcription.
                            result = audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                            text = result['text'].strip()

                            # If we detected a pause between recordings, add a new item to our transcription.
                            # Otherwise edit the existing one.
                            if phrase_complete:
                                transcription.append(text)
                            else:
                                transcription[-1] = text

                            # Clear the console to reprint the updated transcription.
                            os.system('cls' if os.name=='nt' else 'clear')
                            for line in transcription:
                                print(line)
                                if self.run.is_on:
                                    self.change_input_id = self.after(1500, self.input_box.configure(text=transcription))
                                else:
                                    if self.change_input_id is not None:
                                        self.after_cancel(self.change_input_id)
                                        self.change_input_id = None
                            # Flush stdout.
                            print('', end='', flush=True)
                        else:
                            # Infinite loops are bad for processors, must sleep.
                            sleep(0.25)
                    except KeyboardInterrupt:
                        break

                print("\n\nTranscription:")
                for line in transcription:
                    print(line)
                    if self.run.is_on:
                        self.change_input_id = self.after(1500, self.input_box.configure(text=transcription))
                    else:
                        if self.change_input_id is not None:
                            self.after_cancel(self.change_input_id)
                            self.change_input_id = None
                    
                return transcription
            main()
        
        self.transcripting_thread = threading.Thread(target=run_transcription)
        self.transcripting_thread.start()


    def stop_transcription(self):
        if self.transcripting_thread is not None:
            KeyboardInterrupt
            pass


class Run_Label(Label):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app_instance = app_instance  # Reference to the App instance

        self.is_on = False
        self.starter = PhotoImage(file="GUI elements/button/starter.png")
        self.on = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/green.png")
        self.off = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/red.png")

        self.running_label = Label(parent, text='CLICK TO RUN.', borderwidth=2, relief=SUNKEN, width=29, height=2, font=('Arial', 19))
        self.running_label.place(relx=0.95, rely=0.1, anchor=E)
        self.on_button = Button(parent, image=self.starter, bd=0, command=self.Switch, borderwidth=0)
        self.on_button.place(relx=0.05, rely=0.03)

    def Switch(self):
        if self.is_on:  # If it was running, stop everything
            self.on_button.config(image=self.off)
            self.running_label.config(text="STOPPED. CLICK AGAIN TO RUN.")
            self.is_on = False
            #self.app_instance.change_input()  # Start the input loop
            self.app_instance.change_output()
            self.app_instance.stop_transcription()
        else:  # If it was stopped, start both loops
            self.on_button.config(image=self.on)
            self.running_label.config(text="RUNNING. CLICK AGAIN TO STOP.")
            self.is_on = True
            #self.app_instance.change_input()  # Start the input loop
            self.app_instance.change_output()  # Start the output loop
            self.app_instance.start_transcription() #Start the transcription

class Text_Display(Label, LabelFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.input_label = Label(parent, text='INPUT', font=('Arial Bold', 11))
        self.input_box = Label(parent, text="Waiting for activation...", font=('Arial Bold', 9), anchor=NW, width=36, height=17, borderwidth=2)
        self.output_label = Label(parent, text='OUTPUT', font=('Arial Bold', 11))
        self.output_box = Label(parent, text="Waiting for activation...", font=('Arial Bold', 9), anchor=NW, width=36, height=17, bd=2)
        
        self.input_label.place(relx=0.225, rely=0.21)
        self.output_label.place(relx=0.685, rely=0.21)
        self.input_box.place(relx=0.05, rely=0.29)
        self.output_box.place(relx=0.5225, rely=0.29)

#print(transcription)
app1 = App('Scam-Bait')
'''

input_status = 0  # "| Waiting for activation |"
output_status = 0  # "| Waiting for activation |"
counter = 0
my_list = ['1', '2', '3', '4']
your_list = ['5', '6', '7', '8']
i = 0
z = 0


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

        # INPUT BOX WIDGETS FOR CHANGE_INPUT() METHOD
        self.input_box = self.t_display.input_box
        self.change_input_id = None

        # OUTPUT BOX WIDGETS FOR CHANGE_OUTPUT() METHOD
        self.output_box = self.t_display.output_box
        self.change_output_id = None

        self.mainloop()

    def change_input(self):
        
        self.input_box.configure(text=(my_list[i]))

        if self.run.is_on:  # Only continue looping if is_on is True
            self.change_input_id = self.after(1500, self.change_input)
        else:  # Cancel loop when is_on is False
            if self.change_input_id is not None:
                self.after_cancel(self.change_input_id)
                self.change_input_id = None

    def change_output(self):
        global z
        self.output_box.configure(text=(your_list[z]))
        if len(your_list) - 1 == z:
            z = 0
        else:
            z += 1

        if self.run.is_on:  # Only continue looping if is_on is True
            self.change_output_id = self.after(1500, self.change_output)
        else:  # Cancel loop when is_on is False
            if self.change_output_id is not None:
                self.after_cancel(self.change_output_id)
                self.change_output_id = None


class Run_Label(Label):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app_instance = app_instance  # Reference to the App instance

        self.is_on = False
        self.starter = PhotoImage(file="GUI elements/button/starter.png")
        self.on = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/green.png")
        self.off = PhotoImage(file="c:/Users/SUT0001/Desktop/AC 34 SAT/GUI elements/button/red.png")

        self.running_label = Label(parent, text='CLICK TO RUN.', borderwidth=2, relief=SUNKEN, width=29, height=2, font=('Arial', 19))
        self.running_label.place(relx=0.95, rely=0.1, anchor=E)
        self.on_button = Button(parent, image=self.starter, bd=0, command=self.Switch, borderwidth=0)
        self.on_button.place(relx=0.05, rely=0.03)

    def Switch(self):
        if self.is_on:  # If it was running, stop everything
            self.on_button.config(image=self.off)
            self.running_label.config(text="STOPPED. CLICK AGAIN TO RUN.")
            self.is_on = False
            self.app_instance.change_input()  # Start the input loop
            self.app_instance.change_output()
        else:  # If it was stopped, start both loops
            self.on_button.config(image=self.on)
            self.running_label.config(text="RUNNING. CLICK AGAIN TO STOP.")
            self.is_on = True
            self.app_instance.change_input()  # Start the input loop
            self.app_instance.change_output()  # Start the output loop


class Text_Display(Label, LabelFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.input_label = Label(parent, text='INPUT', font=('Arial Bold', 11))
        self.input_box = Label(parent, text=input_status, font=('Arial Bold', 9), anchor=NW, width=36, height=17, borderwidth=2)
        self.output_label = Label(parent, text='OUTPUT', font=('Arial Bold', 11))
        self.output_box = Label(parent, text=output_status, font=('Arial Bold', 9), anchor=NW, width=36, height=17, bd=2)

        self.input_label.place(relx=0.225, rely=0.21)
        self.output_label.place(relx=0.685, rely=0.21)
        self.input_box.place(relx=0.05, rely=0.29)
        self.output_box.place(relx=0.5225, rely=0.29)


app1 = App('Scam-Bait')
'''