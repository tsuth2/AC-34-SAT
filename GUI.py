from tkinter import *
from tkinter import ttk
import time
import transcribe_demo

input_status = 0#"| Waiting for activation |"
output_status = 0#"| Waiting for activation |"
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

        #CALLING CHILD CLASSES FOR USE IN METHODS
        self.t_display = Text_Display(self)
        self.run = Run_Label(self, self)

        #INPUT BOX WIDGETS FOR CHANGE_INPUT() METHOD
        self.input_box = self.t_display.input_box
        self.change_input_id = None

        #OUTPUT BOX WIDGETS FOR CHANGE_OUTPUT() METHOD
        self.output_box = self.t_display.output_box
        self.change_output_id = None


        self.mainloop()

    def change_input(self):
        global i
        self.input_box.configure(text=(my_list[i]))
        if len(my_list) - 1 == i:
            i = 0
        else:
            i += 1

        if self.run.is_on:
            self.change_input_id = self.after(1500, self.change_input)
        else:
            if self.change_input_id is not None:
                self.after_cancel(self.change_input_id)
                self.change_input_id = None
        
    def change_output(self):
        transcribe_demo.main.transcription
        global z
        self.output_box.configure(text=(your_list[z]))
        if len(your_list) - 1 == z:
            z = 0
        else:
            z += 1
        
        if self.run.is_on:
            self.change_output_id = self.after(1500, self.change_output)
        else:
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