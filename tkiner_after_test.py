import tkinter as tk

count = 0

def update_function():
    global count
    print(f'{count} Hello')
    count = count + 1

    root.after(100, update_function)

root = tk()
root.geometry('800x500')
root.mainloop()