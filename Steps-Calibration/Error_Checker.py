"""
Kinetic Sand Table - Error Compensation Calibration Tool
--------------------------------------------------------
Python GUI program to assist users in calculating the compensation ratio needed to
counteract positional error caused by rotational movement in a kinetic sand art table system.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import serial.tools.list_ports

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

# -------- COM Port Input Popup --------
def get_com_port():
    """
    Prompt user for the COM port of the Arduino via a pop-up dialog.
    
    Returns: COM port entered by the user
    """
    port = simpledialog.askstring("COM Port Selection", "Enter the COM port (e.g., COM3):")
    return port

# -------- Command Sending Function --------
def send_command(axis, steps):
    """
    Send a formatted command string to the Arduino.

    Args:
        axis (str): 'r' for rotation, 'i' for in-out
        steps (str): Number of steps as string
    """
    if arduino:
        command = f"{axis} {steps}\n"
        print(f"Sending command: {command.strip()}")
        arduino.write(command.encode())
    else:
        messagebox.showwarning("Not Connected", "Arduino connection not established.")

# Compensation Calculation Function
def calculate_compensation():
    """
    Calculate and display the compensation ratio based on user inputs.

    Formula:
        compensation_ratio = 0.5 * (mm_moved_by_rotation / mm_moved_by_inout)

    Error handled for invalid or missing numerical entries.
    """
    try:
        mm_inout = float(inout_mm_entry.get())
        mm_rotation = float(rotation_mm_entry.get())

        if mm_inout == 0:
            messagebox.showerror("Input Error", "In-Out movement cannot be zero.")
            return

        mm_per_step_inout = 100/mm_inout
        compensation_ratio = 0.5 * (mm_rotation / mm_inout)
        linear_label.config(text=f"Linear Ratio (step/mm) = {linear_label:.4f}")
        compensation_label.config(text=f"Compensation Ratio (steps/rotation) = {compensation_ratio:.4f}")

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numerical values for both movement fields.")

# -------- GUI Button Callbacks --------
def move_inout_positive():
    """Move in-out motor by +1000 steps."""
    send_command('i', '1000')

def move_inout_negative():
    """Move in-out motor by -1000 steps."""
    send_command('i', '-1000')

def rotate_positive():
    """Rotate system by +2000 steps."""
    send_command('r', '2000')

def rotate_negative():
    """Rotate system by -2000 steps."""
    send_command('r', '-2000')

# -------- Main GUI Setup --------
def create_gui():
    root = tk.Tk()
    root.title("Kinetic Sand Table Error Calibration")

    # Step-by-step Instruction Text
    instructions = (
        "Step-by-Step Instructions:\n\n"
        "1. Move the In-Out motor by +1000 or -1000 steps using your controller.\n"
        "2. Measure how many mm the rack moved, and enter it in the first box.\n"
        "3. Rotate the system by +2000 or -2000 steps.\n"
        "4. Measure how many mm the rack shifted due to rotation, and enter it in the second box.\n"
        "5. Press 'Calculate Compensation' to get the compensation ratio.\n"
    )

    instruction_label = tk.Label(root, text=instructions, justify="left", padx=10, pady=10)
    instruction_label.grid(row=0, column=2, rowspan=6, sticky="n")

    # In-Out Movement Input Field
    tk.Label(root, text="mm Moved by ±1000 In-Out Steps:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    global inout_mm_entry
    inout_mm_entry = tk.Entry(root)
    inout_mm_entry.grid(row=0, column=1, padx=10, pady=5)

    # Rotation Movement Input Field
    tk.Label(root, text="mm Moved by ±2000 Rotation Steps:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    global rotation_mm_entry
    rotation_mm_entry = tk.Entry(root)
    rotation_mm_entry.grid(row=1, column=1, padx=10, pady=5)

    # Control Buttons
    tk.Button(root, text="Move In-Out +1000 Steps", command=move_inout_positive).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(root, text="Move In-Out -1000 Steps", command=move_inout_negative).grid(row=2, column=1, padx=5, pady=5)

    tk.Button(root, text="Rotate System +2000 Steps", command=rotate_positive).grid(row=3, column=0, padx=5, pady=5)
    tk.Button(root, text="Rotate System -2000 Steps", command=rotate_negative).grid(row=3, column=1, padx=5, pady=5)

    # Calculate Button
    calc_button = tk.Button(root, text="Calculate", command=calculate_compensation, width=25)
    calc_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Result Display Label
    global linear_label
    linear_label = tk.Label(root, text="Linear Ratio (step/mm) = ")
    linear_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    # Result Display Label
    global compensation_label
    compensation_label = tk.Label(root, text="Compensation Ratio (steps/rotation) = ")
    compensation_label.grid(row=5, column=1, columnspan=2, padx=10, pady=10)

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

