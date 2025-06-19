import tkinter as tk

print("Starting simple test...")

root = tk.Tk()
root.title("Desktop Test")
root.geometry("400x300")

label = tk.Label(root, text="Desktop Test Working!", font=("Arial", 16))
label.pack(pady=50)

print("Window created, starting mainloop...")
root.mainloop()
print("Window closed.") 