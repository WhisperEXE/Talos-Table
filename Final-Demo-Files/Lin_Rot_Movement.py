"""
Kinetic Sand Table Stepper Motor Controller with Position Tracking
-------------------------------------------------------------------
"""

# --------- Imports ---------
import serial
import tkinter as tk
from tkinter import messagebox, simpledialog
import win32gui
import win32con
import sqlite3

# --------- Machine Parameters ---------
INOUT_STEPS_PER_MM = 33            # in-out steps per mm
ROTATION_DEG_PER_STEP = 0.0679     # rotation degrees/step
COMPENSATION_RATIO = 0.3167        # compensation: in-out steps per rotation step
MAX_INOUT_STEPS = 4280             # maximum allowed in-out step position

# --------- Serial Communication Setup ---------
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

# --------- SQLite Database Setup ---------
def initialize_database():
    """
    Create or connect to local SQLite database for position tracking.
    """
    conn = sqlite3.connect("motor_positions.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY,
                        theta REAL,
                        in_out REAL
                    )""")
    # Initialize record if none exists
    cursor.execute("SELECT COUNT(*) FROM positions")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO positions (theta, in_out) VALUES (0, 185)")
    conn.commit()
    return conn

def get_current_position(conn):
    """
    Retrieve the current theta and in_out positions from the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT theta, in_out FROM positions WHERE id = 1")
    return cursor.fetchone()

def update_position(conn, new_theta, new_in_out):
    """
    Update the current theta and in_out positions in the database.
    """
    cursor = conn.cursor()
    cursor.execute("UPDATE positions SET theta = ?, in_out = ? WHERE id = 1", (new_theta, new_in_out))
    conn.commit()

# --------- Command Sending Function ---------
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

# --------- Motor Movement Handler ---------
def move_motors():
    """
    Calculate required step movements based on target slider positions
    and current database-stored positions. Send move commands to Arduino.
    """
    target_theta = theta_slider.get()
    target_in_out = inout_slider.get()

    current_theta, current_in_out = get_current_position(db_conn)

    delta_theta = target_theta - current_theta
    delta_in_out = target_in_out - current_in_out

    """
    Calculate motor steps for rotation (theta) and in-out (radius). 
    Rotation steps are based on angle change, and in-out steps are adjusted for rotation compensation.
    """
    steps_theta = int(delta_theta / ROTATION_DEG_PER_STEP)
    steps_in_out = int((delta_in_out * INOUT_STEPS_PER_MM) - (COMPENSATION_RATIO * steps_theta))

    if steps_theta != 0:
        send_command('r', steps_theta)
    if steps_in_out != 0:
        send_command('i', steps_in_out)

    # Update position record
    update_position(db_conn, target_theta, target_in_out)

    # Update step counters
    theta_count_label.config(text=f"Theta = {target_theta:.2f}°")
    inout_count_label.config(text=f"In-Out = {target_in_out/10:.2f} cm")

# --------- Position Reset Function ---------
def reset_positions():
    """
    Reset position database and update GUI counters.
    """
    update_position(db_conn, 0, 185)
    theta_count_label.config(text="Theta = 0.00°")
    inout_count_label.config(text="In-Out = 18.50 cm")
    theta_slider.set(0)
    inout_slider.set(185)

# --------- COM Port Input Popup ---------
def get_com_port():
    """
    Prompt user for the COM port of the Arduino via a pop-up dialog.

    Returns: COM port entered by the user
    """
    port = simpledialog.askstring("COM Port Selection", "Enter the COM port (e.g., COM3):")
    return port

# --------- Main GUI Setup ---------
def create_gui():
    global theta_slider, inout_slider
    global theta_count_label, inout_count_label

    root = tk.Tk()
    root.title("Kinetic Sand Table Motor Control")

    # Rotation (Theta) Slider
    tk.Label(root, text="Rotation (Theta) [°]:").grid(row=0, column=0, padx=10, pady=5)
    theta_slider = tk.Scale(root, from_=0, to=360, orient="horizontal", resolution=0.1, length=300)
    theta_slider.grid(row=0, column=1, padx=10, pady=5)

    # In-Out (Radius) Slider
    tk.Label(root, text="In-Out (Radius) [mm]:").grid(row=1, column=0, padx=10, pady=5)
    inout_slider = tk.Scale(root, from_=75, to=185, orient="horizontal", resolution=0.01, length=300)
    inout_slider.grid(row=1, column=1, padx=10, pady=5)

    # Control Buttons
    tk.Button(root, text="Move Motors", command=move_motors, width=20).grid(row=2, column=0, padx=10, pady=10)
    tk.Button(root, text="Reset Positions", command=reset_positions, width=20).grid(row=2, column=1, padx=10, pady=10)

    # Position Display Labels
    theta_count_label = tk.Label(root, text="Theta = 0.00°")
    theta_count_label.grid(row=3, column=0, padx=10, pady=5)

    inout_count_label = tk.Label(root, text="In-Out = 18.50 cm")
    inout_count_label.grid(row=3, column=1, padx=10, pady=5)

    root.mainloop()

# --------- Main Execution ---------
if __name__ == "__main__":
    arduino_port = get_com_port()

    if arduino_port:
        baudrate = 115200
        arduino = connect_to_arduino(arduino_port, baudrate)

        if arduino:
            # Setup position tracking
            db_conn = initialize_database()

            # Start GUI
            create_gui()

            # Close serial and database connections on exit
            arduino.close()
            db_conn.close()
            print("Connections closed.")
    else:
        messagebox.showerror("COM Port Error", "No COM port entered. Exiting program.")
        exit()
