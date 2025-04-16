import tkinter as tk
from tkinter import messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
import serial

# --------- Machine Parameters ---------
INOUT_STEPS_PER_MM = 33            # in-out steps per mm
ROTATION_DEG_PER_STEP = 0.0679     # rotation degrees/step
COMPENSATION_RATIO = 0.3167        # compensation: in-out steps per rotation step
MAX_INOUT_STEPS = 4280             # maximum allowed in-out step position

# --------- Global Variables ---------
start_point = None
end_point = None
last_move = (0, 0)
total_rotation_steps = 0
total_inout_steps = 0

# --------- Utility Functions ---------
def to_polar(x, y):
    """Convert Cartesian (x, y) to Polar (theta in degrees, r in mm)."""
    theta = math.degrees(math.atan2(y, x))
    r = math.hypot(x, y)
    return theta, r

def draw_line():
    """Draw a line between start and end points, update plot."""
    global start_point, end_point

    try:
        sx = float(start_x_entry.get()) * 10
        sy = float(start_y_entry.get()) * 10
        ex = float(end_x_entry.get()) * 10
        ey = float(end_y_entry.get()) * 10
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric coordinates.")
        return

    start_point = (sx, sy)
    end_point = (ex, ey)

    ax.clear()
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
    ax.set_aspect('equal')
    ax.grid(True)

    boundary_circle = plt.Circle((0, 0), 130, color='r', fill=False, linestyle='--')
    ax.add_artist(boundary_circle)

    limit_circle = plt.Circle((0, 0), 30, color='r', fill=False, linestyle='--')
    ax.add_artist(limit_circle)

    ax.plot(sx, sy, 'go')
    ax.plot(ex, ey, 'ro')
    ax.plot([sx, ex], [sy, ey], 'b--')

    canvas.draw()

def send_command(axis, steps):
    """Send formatted movement command to Arduino."""
    if arduino:
        command = f"{axis} {steps}\n"
        print(f"Sending command: {command.strip()}")
        arduino.write(command.encode())
    else:
        messagebox.showwarning("Not Connected", "Arduino connection not established.")

def execute_move():
    """Compute, compensate and send motor moves, then update cumulative totals."""
    global last_move, total_rotation_steps, total_inout_steps

    if not start_point or not end_point:
        messagebox.showwarning("Action Required", "Draw the line first.")
        return

    theta1, r1 = to_polar(*start_point)
    theta2, r2 = to_polar(*end_point)

    delta_theta = theta2 - theta1
    delta_r = r2 - r1

    rotation_steps = int(round(delta_theta / ROTATION_DEG_PER_STEP))
    inout_steps = int(round(delta_r * INOUT_STEPS_PER_MM))

    # Compensation: inout_steps -= compensation ratio * rotation_steps
    compensation_steps = int(round(COMPENSATION_RATIO * rotation_steps))
    compensated_inout_steps = inout_steps - compensation_steps

    # Predict new total in-out position
    predicted_total_inout = total_inout_steps + compensated_inout_steps

    if abs(predicted_total_inout) > MAX_INOUT_STEPS:
        messagebox.showerror("Movement Limit Exceeded", f"Move would exceed ±{MAX_INOUT_STEPS} in-out steps.\n"
                                                        f"Current: {total_inout_steps}, Move: {compensated_inout_steps}")
        return

    result_label.config(text=f"Δθ: {delta_theta:.2f}° ({rotation_steps} steps)\n"
                             f"Δr: {delta_r:.2f} mm ({inout_steps} steps)\n"
                             f"Compensation: -{compensation_steps} steps\n"
                             f"Final InOut: {compensated_inout_steps} steps")

    if rotation_steps:
        send_command('r', rotation_steps)
        total_rotation_steps += rotation_steps
    if compensated_inout_steps:
        send_command('i', compensated_inout_steps)
        total_inout_steps += compensated_inout_steps

    update_totals()
    last_move = (-rotation_steps, -compensated_inout_steps)

def undo_move():
    """Undo the last executed move."""
    global last_move, total_rotation_steps, total_inout_steps
    rot_steps, inout_steps = last_move

    if rot_steps == 0 and inout_steps == 0:
        messagebox.showinfo("Undo", "No move to undo.")
        return

    if rot_steps:
        send_command('r', rot_steps)
        total_rotation_steps += rot_steps
    if inout_steps:
        send_command('i', inout_steps)
        total_inout_steps += inout_steps

    update_totals()
    last_move = (0, 0)
    result_label.config(text="Last move undone.")

def update_totals():
    """Update cumulative step totals displayed in the GUI."""
    total_label.config(text=f"Total Rotation Steps: {total_rotation_steps}\n"
                            f"Total In-Out Steps: {total_inout_steps}")

def reset_graph():
    """Reset graph plot, points and cumulative totals."""
    global start_point, end_point, last_move, total_rotation_steps, total_inout_steps
    start_point = None
    end_point = None
    last_move = (0, 0)
    total_rotation_steps = 0
    total_inout_steps = 0

    start_x_entry.delete(0, tk.END)
    start_y_entry.delete(0, tk.END)
    end_x_entry.delete(0, tk.END)
    end_y_entry.delete(0, tk.END)

    ax.clear()
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
    ax.set_aspect('equal')
    ax.grid(True)

    boundary_circle = plt.Circle((0, 0), 130, color='r', fill=False, linestyle='--')
    ax.add_artist(boundary_circle)

    limit_circle = plt.Circle((0, 0), 30, color='r', fill=False, linestyle='--')
    ax.add_artist(limit_circle)

    canvas.draw()
    result_label.config(text="")
    update_totals()

def connect_to_arduino(port, baudrate):
    """Attempt to establish serial connection to Arduino."""
    try:
        arduino = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to Arduino on {port} at {baudrate} baud.")
        return arduino
    except serial.SerialException:
        messagebox.showerror("Connection Error", f"Failed to connect to {port}. Check connection.")
        return None

def get_com_port():
    """Prompt for user COM port input."""
    port = simpledialog.askstring("COM Port Selection", "Enter the COM port (e.g., COM3):")
    return port

def create_gui():
    """Initialize and run the tkinter-based GUI."""
    global root, input_frame, ax, canvas, result_label, total_label
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry
    root = tk.Tk()
    root.title("Kinetic Sand Table - Point Move Test (w/ Compensation)")

    input_frame = tk.Frame(root)
    input_frame.pack(pady=5)

    tk.Label(input_frame, text="Start X (cm):").grid(row=0, column=0)
    start_x_entry = tk.Entry(input_frame, width=5)
    start_x_entry.grid(row=0, column=1)

    tk.Label(input_frame, text="Start Y (cm):").grid(row=0, column=2)
    start_y_entry = tk.Entry(input_frame, width=5)
    start_y_entry.grid(row=0, column=3)

    tk.Label(input_frame, text="End X (cm):").grid(row=0, column=4)
    end_x_entry = tk.Entry(input_frame, width=5)
    end_x_entry.grid(row=0, column=5)

    tk.Label(input_frame, text="End Y (cm):").grid(row=0, column=6)
    end_y_entry = tk.Entry(input_frame, width=5)
    end_y_entry.grid(row=0, column=7)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    tk.Button(button_frame, text="Draw Line", command=draw_line, font=("Verdana", 11)).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Execute Move", command=execute_move, font=("Verdana", 11)).grid(row=0, column=1, padx=10)
    tk.Button(button_frame, text="Undo Move", command=undo_move, font=("Verdana", 11)).grid(row=0, column=2, padx=10)
    tk.Button(button_frame, text="Reset", command=reset_graph, font=("Verdana", 11)).grid(row=0, column=3, padx=10)

    result_label = tk.Label(root, text="", font=("Verdana", 12))
    result_label.pack(pady=5)

    total_label = tk.Label(root, text="", font=("Verdana", 11))
    total_label.pack(pady=3)
    update_totals()

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
    ax.set_aspect('equal')
    ax.grid(True)

    boundary_circle = plt.Circle((0, 0), 130, color='r', fill=False, linestyle='--')
    ax.add_artist(boundary_circle)

    limit_circle = plt.Circle((0, 0), 30, color='r', fill=False, linestyle='--')
    ax.add_artist(limit_circle)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()

    root.protocol("WM_DELETE_WINDOW", on_closing_root)
    root.mainloop()

def on_closing_root():
    """Close the application cleanly."""
    plt.close('all')
    root.destroy()
    root.quit()

# --------- Program Execution ---------
if __name__ == "__main__":
    arduino_port = get_com_port()

    if arduino_port:
        baudrate = 115200
        arduino = connect_to_arduino(arduino_port, baudrate)

        if arduino:
            create_gui()
            arduino.close()
            print("Arduino connection closed.")
    else:
        messagebox.showerror("COM Port Error", "No COM port entered. Exiting program.")
        exit()