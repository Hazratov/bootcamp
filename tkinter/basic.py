import tkinter as tk


def main():
    print('Hello:', get_name(), "About him:", get_description())

def get_name():
    name = entry.get()
    return name

def get_description():
    description = text.get("1.0", tk.END)
    return description

root = tk.Tk()
root.title('My program')
root.geometry('500x300')


label = tk.Label(root, text="Enter your name")
label.pack()
entry = tk.Entry(root, width=40)
entry.pack()

label = tk.Label(root, text="Enter your about yourself")
label.pack()
text = tk.Text(root, width=40, height=5)
text.pack()

button = tk.Button(root, text="Button 1", command=main)
button.pack()

root.mainloop()