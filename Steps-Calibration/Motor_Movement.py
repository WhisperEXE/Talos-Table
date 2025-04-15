"""
Kinetic Sand Table Stepper Motor Controller
-------------------------------------------
"""

import serial
import tkinter as tk
from tkinter import messagebox, simpledialog
import win32gui
import win32con

# -------- Serial Communication Setup --------
def connect_to_arduino(port, baudrate):
    """
    Establish serial connection to Arduino.

    Serial object if successful, None otherwise
    """
    try:
        arduino = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to Arduino on {port} at {baudrate} baud.")
        return arduino
    except serial.SerialException:
        messagebox.showerror("Connection Error", f"Failed to connect to {port}. Check connection.")
        return None

# -------- Command Sending Functions --------
def send_command(axis, steps):
    """
    Send formatted command string to Arduino via serial.
    """
    if arduino:
        command = f"{axis} {steps}\n"
        print(f"Sending command: {command.strip()}")
        arduino.write(command.encode())
    else:
        messagebox.showwarning("Not Connected", "Arduino connection not established.")

# -------- GUI Button Callbacks --------
# -------- GUI Button Callbacks --------
def move_both():
    theta_steps = theta_entry.get()
    radius_steps = radius_entry.get()
    moved = False

    if theta_steps:
        try:
            send_command('r', theta_steps)
            theta_cumulative[0] += int(theta_steps)
            theta_count_label.config(text=f"Theta_Steps = {theta_cumulative[0]}")
            moved = True
        except ValueError:
            messagebox.showerror("Input Error", "Invalid step value for Rotation.")

    if radius_steps:
        try:
            send_command('i', radius_steps)
            radius_cumulative[0] += int(radius_steps)
            radius_count_label.config(text=f"Radius_Steps = {radius_cumulative[0]}")
            moved = True
        except ValueError:
            messagebox.showerror("Input Error", "Invalid step value for Radius.")

    if not moved:
        messagebox.showinfo("Input Error", "Please enter a value in either Rotation or Radius.")

    # Clear both textboxes
    theta_entry.delete(0, tk.END)
    radius_entry.delete(0, tk.END)

def reset_counters():
    theta_cumulative[0] = 0
    radius_cumulative[0] = 0
    theta_count_label.config(text=f"Theta_Steps = 0")
    radius_count_label.config(text=f"Radius_Steps = 0")

# -------- COM Port Input Popup --------
def get_com_port():
    """
    Prompt user for the COM port of the Arduino via a pop-up dialog.
    
    Returns: COM port entered by the user
    """
    port = simpledialog.askstring("COM Port Selection", "Enter the COM port (e.g., COM3):")
    return port

# -------- Focus on the GUI Window --------
def bring_window_to_front(window_title):
    """
    Bring the window with the specified title to the front.
    """
    def enum_windows_callback(hwnd, lparam):
        # Get the title of each window
        if win32gui.IsWindowVisible(hwnd):
            if win32gui.GetWindowText(hwnd) == window_title:
                # Bring the window to the front
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)

    win32gui.EnumWindows(enum_windows_callback, None)

# -------- Main GUI Setup --------
def create_gui():
    root = tk.Tk()
    root.title("Kinetic Sand Table Motor Control")

    # Input Labels and Entry Boxes
    tk.Label(root, text="Rotation (Theta) Steps:").grid(row=0, column=0, padx=10, pady=5)
    global theta_entry
    theta_entry = tk.Entry(root)
    theta_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="In-Out (Radius) Steps:").grid(row=1, column=0, padx=10, pady=5)
    global radius_entry
    radius_entry = tk.Entry(root)
    radius_entry.grid(row=1, column=1, padx=10, pady=5)

    # Step Counters
    global theta_cumulative
    global radius_cumulative
    theta_cumulative = [0]
    radius_cumulative = [0]

    # Control Buttons
    tk.Button(root, text="Move Both Motors", command=move_both, width=20).grid(row=2, column=0, padx=10, pady=10)
    tk.Button(root, text="Reset All Steps", command=reset_counters, width=20).grid(row=2, column=1, padx=10, pady=10)

    global theta_count_label
    theta_count_label = tk.Label(root, text=f"Theta_Steps = 0")
    theta_count_label.grid(row=3, column=0, padx=10, pady=5)

    global radius_count_label
    radius_count_label = tk.Label(root, text=f"Radius_Steps = 0")
    radius_count_label.grid(row=3, column=1, padx=10, pady=5)

    root.mainloop()

# -------- Main Execution --------
if __name__ == "__main__":
    # Ask for COM port before proceeding
    arduino_port = get_com_port()  # Get COM port from user input

    if arduino_port:  # Proceed only if a valid COM port is entered
        baudrate = 115200

        # Connect to Arduino
        arduino = connect_to_arduino(arduino_port, baudrate)

        if arduino:
             # Start GUI event loop
            create_gui()

            # Close serial connection when window is closed
            arduino.close()
            print("Arduino connection closed.")
    else:
        messagebox.showerror("COM Port Error", "No COM port entered. Exiting program.")
        exit()
