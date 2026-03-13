from tkinter import Tk, Label, Button, Radiobutton, IntVar, simpledialog
import easygui


def ask_text_question(Title, prompt):

	# Create the main application window (it will be hidden)
#	ROOT = Tk()
#	ROOT.withdraw() # Hide the main window
	
	# Open the dialog window to ask for text input
	# Parameters: title of the dialog, prompt message
	return easygui.enterbox(prompt)
	
	
	
def ask_multiple_choice_question(prompt, options):
    root = Tk()
    if prompt:
        Label(root, text=prompt).pack()
    v = IntVar()
    for i, option in enumerate(options):
        Radiobutton(root, text=option, variable=v, value=i).pack(anchor="w")
    Button(text="OK", command=root.destroy).pack()
    root.mainloop()
#    if v.get() == 0: return None
    return v.get()