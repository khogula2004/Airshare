from tkinter import Tk, filedialog

def select_file():
    root = Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename()
    return filepath
