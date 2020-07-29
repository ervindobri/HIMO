import tkinter as tk
from tkinter import filedialog, Text
import os
import HIMO

# global filename
# Color palette
BLUE = "#00b8e6"


def RecordTrainingData():
    pass


def OpenTrainingData():
    filename = filedialog.askopenfilename(initialdir="\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\results",
                                          title="Open EMG data",
                                          filetypes=(("text files", "*.txt"), ("all files", "*.*"))
                                          )
    # print(filename)
    fileLabel = tk.Label(box2, text=filename)
    fileLabel.grid_propagate(False)
    fileLabel.pack()
    pass


root = tk.Tk()
root.title("HIMO - Health In Motion")
root.configure(background="black")
root.geometry("1000x700")

# canvas = tk.Canvas(root, height=700, width=1000, bg="white")
# canvas.pack()
left = tk.Frame(root, borderwidth=1, bg=BLUE)
left.place(relwidth=0.5, relheight=1)
right = tk.Frame(root, borderwidth=1, bg=BLUE)
right.place(relwidth=0.5, relheight=1)

container = tk.Frame(left, borderwidth=1, relief="solid", bg=BLUE)
box1 = tk.Frame(right, borderwidth=2, relief="solid")
box2 = tk.Frame(right, borderwidth=2, relief="solid", height=50)
buttonContainer = tk.Frame(left, relief="solid", bg=BLUE)

label1 = tk.Label(container, text="Training Gestures", fg="white", bg=BLUE)
label2 = tk.Label(left, text="I could be a button")
label3 = tk.Label(left, text="So could I")
label4 = tk.Label(box1, text="I could be your image")
label5 = tk.Label(box2, text="I could be your setup window")

left.pack(side="left", expand=True, fill="both", padx=10, pady=10)
right.pack(side="right", expand=True, fill="both", padx=10, pady=10)
container.pack(expand=True, fill="both", padx=5, pady=5)
box1.pack(expand=True, fill="both", padx=10, pady=10)
box2.pack(expand=False, fill="both", side=tk.BOTTOM, padx=10, pady=10)
box2.pack_propagate(False)
box2.grid_propagate(False)

buttonContainer.pack(side=tk.BOTTOM, padx=10, pady=10)

label1.pack()
# label2.pack()
# label3.pack()
# label4.pack()
# label5.pack()

# left.place(relwidth=.7, relheight=.7, relx=0.1, rely=0.1)
# region BUTTONS

buttonImage = tk.PhotoImage(
    file="X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/resources/button.png")  # make sure to add "/" not "\"
openFileButton = tk.Button(buttonContainer, text="Open training Data", padx=10, pady=5, bg="white", fg=BLUE,
                           command=OpenTrainingData)
# openFileButton.config(image=buttonImage)
openFileButton.configure(borderwidth=0)
recordDataButton = tk.Button(buttonContainer, text="New training Data", padx=10, pady=5, bg="white",
                             fg=BLUE,
                             command=RecordTrainingData)
# recordDataButton.config(image=buttonImage)
recordDataButton.configure(borderwidth=0)

openFileButton.pack(side=tk.LEFT, padx=10)
recordDataButton.pack(side=tk.LEFT, padx=10)
# endregion

subjectName = tk.Label(buttonContainer, text="Subject Name")
subjectName.pack(padx=10)
entry = tk.Entry(subjectName)
entry.pack(side=tk.RIGHT, padx=10)
# entry.place()
# entry.focus_set()

root.mainloop()
