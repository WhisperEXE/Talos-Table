"""
Kinetic Sand Table - Pattern to Path Step Generator, Visualiser, & Motor Controller
-----------------------------------------------------------------------------------
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import os
import serial

# --------- Machine Parameters ---------
ROTATION_STEP_RAD = np.pi / 100    # rotation step in radians
INOUT_STEPS_PER_MM = 33            # steps per mm for in-out axis
BOUNDARY_RADIUS = 16               # max movement limit in mm
ROTATION_STEPS_PER_REV = 200       # for converting radians to steps (1 rev = 2pi rad)

# -------- Global Pattern Data --------
pattern_coords = []
step_movements = []
ser = None  # Serial connection

# -------- Pattern Plotting Function --------
def plot_pattern():
    """
    Generate and display a high-resolution pattern plot
    based on current slider inputs for 'a', 'n', and 'd'.
    Also prepares simulated path data for pathing.
    """
    try:
        a = a_slider.get()
        n = n_slider.get()
        d = d_slider.get()

        # High-Resolution Pattern
        theta_hr = np.linspace(0, 2*np.pi, 2000)
        r_hr = a * (np.cos(n * theta_hr + d) + np.sin(n * theta_hr + d))
        x_hr = r_hr * np.cos(theta_hr)
        y_hr = r_hr * np.sin(theta_hr)

        # Simulated Machine Pattern (data only)
        theta_sim = np.arange(0, 2*np.pi, ROTATION_STEP_RAD)
        r_sim = a * (np.cos(n * theta_sim + d) + np.sin(n * theta_sim + d))
        r_sim_steps = np.round(r_sim * INOUT_STEPS_PER_MM) / INOUT_STEPS_PER_MM
        x_sim = r_sim_steps * np.cos(theta_sim)
        y_sim = r_sim_steps * np.sin(theta_sim)

        global pattern_coords
        pattern_coords = list(zip(x_sim, y_sim))

        # Clear and redraw high-res plot
        ax_hr.clear()
        ax_hr.plot(x_hr, y_hr, label="High-Resolution Pattern")
        _draw_boundary(ax_hr)
        ax_hr.set_title("High-Resolution Preview")
        ax_hr.set_aspect('equal')
        ax_hr.grid(False)
        ax_hr.legend().remove()

        canvas.draw()

    except Exception as e:
        messagebox.showerror("Plot Error", f"An error occurred while plotting:\n{e}")

# -------- Utility: Draw Movement Boundary --------
def _draw_boundary(ax):
    """
    Draw the fixed boundary circle representing the sand table's movement limit.
    """
    boundary_theta = np.linspace(0, 2*np.pi, 500)
    boundary_x = BOUNDARY_RADIUS * np.cos(boundary_theta)
    boundary_y = BOUNDARY_RADIUS * np.sin(boundary_theta)
    ax.plot(boundary_x, boundary_y, 'k')

# -------- Convert Pattern to Step Movements --------
def convert_and_export_steps():
    """
    Converts the global pattern_coords list into per-section motor step movements.
    Exports to a text file 'exported_steps.txt'.
    """
    if not pattern_coords:
        messagebox.showerror("No Pattern", "Please generate a pattern before exporting steps.")
        return

    global step_movements
    step_movements = []

    with open("exported_steps.txt", "w") as f:
        for i in range(1, len(pattern_coords)):
            x1, y1 = pattern_coords[i-1]
            x2, y2 = pattern_coords[i]

            theta1, r1 = math.atan2(y1, x1), math.hypot(x1, y1)
            theta2, r2 = math.atan2(y2, x2), math.hypot(x2, y2)

            delta_theta = theta2 - theta1
            delta_r = r2 - r1

            # Wrap angle to [-pi, pi]
            if delta_theta > math.pi:
                delta_theta -= 2 * math.pi
            elif delta_theta < -math.pi:
                delta_theta += 2 * math.pi

            theta_steps = int(round(delta_theta / (2 * np.pi) * ROTATION_STEPS_PER_REV))
            r_steps = int(round(delta_r * INOUT_STEPS_PER_MM))

            step_movements.append((theta_steps, r_steps))
            f.write(f"{theta_steps} {r_steps}\n")

    messagebox.showinfo("Export Complete", "Step movements exported to 'exported_steps.txt'.")

# -------- Begin Path Simulation and Motor Control --------
def begin_pathing():
    """
    Opens a simulation window that visualises step movements by stepping through the exported file.
    Moves motors via serial as each step is performed.
    """
    if not os.path.exists("exported_steps.txt"):
        messagebox.showerror("No Steps", "Please export step movements first.")
        return

    connect_serial()

    global sim_root, sim_canvas, sim_ax, sim_steps, sim_index, sim_x, sim_y, point_marker

    sim_root = tk.Tk()
    sim_root.title("Step Movement Simulation")

    fig, sim_ax = plt.subplots(figsize=(7, 7))
    _draw_boundary(sim_ax)
    sim_ax.set_aspect('equal')
    sim_ax.set_xlim(-BOUNDARY_RADIUS-1, BOUNDARY_RADIUS+1)
    sim_ax.set_ylim(-BOUNDARY_RADIUS-1, BOUNDARY_RADIUS+1)
    sim_ax.grid(False)

    with open("exported_steps.txt", "r") as f:
        sim_steps = [tuple(map(int, line.strip().split())) for line in f.readlines()]

    sim_x, sim_y = 0, 0
    sim_ax.plot(sim_x, sim_y, 'go')
    point_marker, = sim_ax.plot(sim_x, sim_y, 'bo')

    sim_index = 0
    sim_canvas = FigureCanvasTkAgg(fig, master=sim_root)
    sim_canvas.get_tk_widget().pack()

    step_button = tk.Button(sim_root, text="Step Through Movement", command=simulate_step, font=("Verdana", 12))
    step_button.pack(pady=10)

    sim_canvas.draw()

    sim_root.protocol("WM_DELETE_WINDOW", on_closing_sim)
    sim_root.mainloop()

def simulate_step():
    """
    Applies one step movement from the sim_steps list to the current simulated position.
    Sends corresponding MOVE command to the Arduino via serial.
    """
    global sim_index, sim_x, sim_y

    if sim_index >= len(sim_steps):
        messagebox.showinfo("Complete", "All step movements traversed.")
        return

    theta_steps, r_steps = sim_steps[sim_index]

    delta_theta = theta_steps / ROTATION_STEPS_PER_REV * 2 * np.pi
    delta_r = r_steps / INOUT_STEPS_PER_MM

    # Update position based on deltas
    theta = math.atan2(sim_y, sim_x)
    r = math.hypot(sim_x, sim_y)

    theta += delta_theta
    r += delta_r

    # Update new coordinates
    sim_x = r * math.cos(theta)
    sim_y = r * math.sin(theta)

    # Ensure the coordinates are in a sequence format (lists)
    point_marker.set_data([sim_x], [sim_y])  # This ensures data is in sequence format

    sim_canvas.draw()

    send_move_command(theta_steps, r_steps)

    sim_index += 1

def send_move_command(theta_steps, r_steps):
    """
    Send MOVE command to Arduino in format 'MOVE <theta_steps> <r_steps>\n'
    """
    if ser:
        command = f"MOVE {theta_steps} {r_steps}\n"
        ser.write(command.encode())
    else:
        print("Serial not connected.")


# -------- Main GUI Setup Function --------
def create_gui():
    """
    Create the main GUI window for adjusting pattern parameters, plotting high-res patterns,
    and simulating the mechanical path.
    """
    global root, a_slider, n_slider, d_slider, ax_hr, canvas
    root = tk.Tk()
    root.title("Pattern to Step Generator & Motor Controller")

    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.LEFT, padx=10, pady=10)

    tk.Label(control_frame, text="Pattern Formula:\nr = a * (cos(nθ + d) + sin(nθ + d))", font=("Verdana", 11)).pack(pady=(0, 10))

    tk.Label(control_frame, text="Amplitude (a):", font=("Verdana", 12)).pack(pady=5)
    a_slider = tk.Scale(control_frame, from_=1, to=10, orient="horizontal", font=("Verdana", 11))
    a_slider.set(8)
    a_slider.pack()

    tk.Label(control_frame, text="Frequency (n):", font=("Verdana", 12)).pack(pady=5)
    n_slider = tk.Scale(control_frame, from_=1, to=20, orient="horizontal", font=("Verdana", 11))
    n_slider.set(5)
    n_slider.pack()

    tk.Label(control_frame, text="Phase Offset (d rad):", font=("Verdana", 12)).pack(pady=5)
    d_slider = tk.Scale(control_frame, from_=0, to=2*np.pi, resolution=0.01*np.pi, orient="horizontal", font=("Verdana", 11))
    d_slider.set(0)
    d_slider.pack()

    tk.Button(control_frame, text="Plot Pattern", command=plot_pattern, width=20, font=("Verdana", 12)).pack(pady=10)
    tk.Button(control_frame, text="Export Step Movements", command=convert_and_export_steps, width=20, font=("Verdana", 12)).pack(pady=5)
    tk.Button(control_frame, text="Simulate Step Movements", command=begin_pathing, width=20, font=("Verdana", 12)).pack(pady=5)

    plot_frame = tk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    fig, ax_hr = plt.subplots(figsize=(8, 8))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.get_tk_widget().pack()

    root.protocol("WM_DELETE_WINDOW", on_closing_root)
    root.mainloop()

def on_closing_root():
    if ser:
        ser.close()
    plt.close('all')
    root.destroy()
    root.quit()

def on_closing_sim():
    plt.close('all')
    sim_root.destroy()
    sim_root.quit()

# -------- Serial Connection Setup --------
def connect_serial():
    """
    Prompt user for COM port and establish serial connection.
    """
    global ser
    if ser is not None:
        return

    port = simpledialog.askstring("Connect Serial", "Enter COM port (e.g. COM4):")
    if port:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            messagebox.showinfo("Connected", f"Serial connection established on {port}.")
        except Exception as e:
            messagebox.showerror("Serial Error", f"Failed to connect: {e}")
    
# -------- COM Port Input Popup --------
def get_com_port():
    """
    Prompt user for the COM port of the Arduino via a pop-up dialog.
    
    Returns: COM port entered by the user
    """
    port = simpledialog.askstring("COM Port Selection", "Enter the COM port (e.g., COM3):")
    return port

# -------- Main Execution --------
if __name__ == "__main__":
    # Ask for COM port before proceeding
    arduino_port = get_com_port()  # Get COM port from user input

    if arduino_port:  # Proceed only if a valid COM port is entered
        baudrate = 115200
        create_gui()

    else:
        messagebox.showerror("COM Port Error", "No COM port entered. Exiting program.")
        exit()