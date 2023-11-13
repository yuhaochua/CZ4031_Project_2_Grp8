# GUIimport tkinter as tk
import tkinter as tk

def executeQuery(query):
    output_text.config(state=tk.NORMAL)  # Set the text widget to editable
    output_text.delete("1.0", tk.END) # Clear previous content
    output_text.insert(tk.END, query)  # Insert input text
    output_text.config(state=tk.DISABLED)  # Set the text widget to read-only
    label.config(text="Executed!")

def processQuery():
    # label.config(text="Button 2 Clicked!")
    qry = text.get("1.0", tk.END).strip()
    executeQuery(qry)

def clearText():
    text.delete("1.0", tk.END)
    label.config(text="Cleared!")


# Create the main window
root = tk.Tk()
root.title("Simple Tkinter GUI")

# Create a Text widget for multiline input
text = tk.Text(root, height=13, width=60)  # Set height and width as needed

# Create an output Text widget
output_text = tk.Text(root, height=13, width=60, state=tk.DISABLED)  # Set height and width as needed, initially read-only

# Create a label
label = tk.Label(root, text="Input:\n")
labelOut = tk.Label(root, text="Output:\n")
# Create two buttons
ExecuteBtn = tk.Button(root, text="Execute", command=processQuery)
clearBtn = tk.Button(root, text="Clear Input", command=clearText)



##########################################################################################
# Pack the label and buttons into the window
label.pack(side=tk.TOP,pady=10)
text.pack(pady=10)
ExecuteBtn.pack(pady=5)
# clearBtn.pack(pady=5)
labelOut.pack(side=tk.TOP,pady=10)
output_text.pack(pady=5)
# button2.pack(pady=5)

# Start the Tkinter event loop
root.mainloop()
