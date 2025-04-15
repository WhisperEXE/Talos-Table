"""
Kinetic Sand Table - Pattern to Path Simulator
------------------------------------------------
Generates a radial pattern using sliders, visually previews it,
and simulates the mechanical path considering the machine's step resolution.

Author: [Your Name]
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

# --------- Machine Parameters ---------
ROTATION_STEP_RAD = np.pi / 100    # rotation step in radians
INOUT_STEPS_PER_MM = 33            # steps per mm for in-out axis
BOUNDARY_RADIUS = 16               # max movement limit in mm

# -------- Global Pattern Data --------
pattern_coords = []

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

        # Simulated Machine Pattern (data only — no root GUI plot)
        theta_sim = np.arange(0, 2*np.pi, ROTATION_STEP_RAD)
        r_sim = a * (np.cos(n * theta_sim + d) + np.sin(n * theta_sim + d))
        r_sim_steps = np.round(r_sim * INOUT_STEPS_PER_MM) / INOUT_STEPS_PER_MM
        x_sim = r_sim_steps * np.cos(theta_sim)
        y_sim = r_sim_steps * np.sin(theta_sim)

        # Update global pattern coords for path sim
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

# -------- Begin Path Simulation --------
def begin_pathing():
    """
    Open path simulation window using simulated pattern data.
    """
    if not pattern_coords:
        messagebox.showerror("No Pattern", "Please generate a pattern before simulating.")
        return

    global sim_root
    sim_root = tk.Tk()
    sim_root.title("Path Simulation")

    fig, ax = plt.subplots(figsize=(7, 7))

    # Draw boundary
    _draw_boundary(ax)
    ax.set_aspect('equal')
    ax.set_xlim(-BOUNDARY_RADIUS-1, BOUNDARY_RADIUS+1)
    ax.set_ylim(-BOUNDARY_RADIUS-1, BOUNDARY_RADIUS+1)
    ax.grid(False)

    # Start point at top of boundary (0, 16)
    start_point = (0, BOUNDARY_RADIUS)

    # Find nearest pattern point to start point
    distances = [np.hypot(px - start_point[0], py - start_point[1]) for px, py in pattern_coords]
    nearest_idx = np.argmin(distances)
    nearest_point = pattern_coords[nearest_idx]

    # Build path: start -> nearest -> pattern points -> start
    path_x = [start_point[0], nearest_point[0]] + [x for x, y in pattern_coords] + [start_point[0]]
    path_y = [start_point[1], nearest_point[1]] + [y for x, y in pattern_coords] + [start_point[1]]

    ax.plot(path_x, path_y, 'b')

    canvas_sim = FigureCanvasTkAgg(fig, master=sim_root)
    canvas_sim.get_tk_widget().pack()
    canvas_sim.draw()

    sim_root.protocol("WM_DELETE_WINDOW", on_closing_sim)
    sim_root.mainloop()

# -------- Main GUI Setup Function --------
def create_gui():
    """
    Create the main GUI window for adjusting pattern parameters, plotting high-res patterns,
    and simulating the mechanical path.
    """
    global root, a_slider, n_slider, d_slider, ax_hr, canvas
    root = tk.Tk()
    root.title("Pattern to Path Simulator")

    # Control panel
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
    tk.Button(control_frame, text="Begin Pathing", command=begin_pathing, width=20, font=("Verdana", 12)).pack(pady=5)

    # Plot area
    plot_frame = tk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    fig, ax_hr = plt.subplots(figsize=(8, 8))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.get_tk_widget().pack()

    root.protocol("WM_DELETE_WINDOW", on_closing_root)
    root.mainloop()

def on_closing_root():
    """
    Handle clean shutdown when the GUI window is closed.
    """
    plt.close('all')
    root.destroy()
    root.quit()

def on_closing_sim():
    """
    Handle clean shutdown when the GUI window is closed.
    """
    plt.close('all')
    sim_root.destroy()
    sim_root.quit()

# -------- Main Execution --------
if __name__ == "__main__":
    create_gui()
