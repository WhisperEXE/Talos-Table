"""
Kinetic Sand Table - Pattern to Path Generator
----------------------------------------------
Python GUI program to generate a radial pattern using the formula:
    r = a * (cos(n * theta + d) + sin(n * theta + d))

Users can adjust 'a', 'n', and 'd' values via sliders and visually plot the resulting
pattern inside a Tkinter window. The program also generates a second simulated plot
based on the step resolution of the sand table system:
    - Rotation: 1.8° per step
    - In-out movement: 1/33 mm per step

Coordinates can be exported in both X-Y and R-Theta formats.

Author: [Your Name]
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

# --------- Machine Movement Parameters ---------
ROTATION_STEP_DEG = 1.8               # degrees per rotation step
INOUT_STEPS_PER_MM = 33              # steps per mm linear
COMPENSATION_RATIO = 0.3167          # in-out compensation per rotation step

# -------- Pattern Plotting Function --------
def plot_pattern():
    """
    Generate and display both the high-resolution and simulated pattern plots
    based on the current slider inputs for 'a', 'n', and 'd'.
    """
    try:
        a = a_slider.get()
        n = n_slider.get()
        d = d_slider.get()

        # High-Resolution Pattern
        theta_hr = np.linspace(0, 2 * np.pi, 2000)
        r_hr = a * (np.cos(n * theta_hr + d) + np.sin(n * theta_hr + d))
        x_hr = r_hr * np.cos(theta_hr)
        y_hr = r_hr * np.sin(theta_hr)

        # Simulated Machine Pattern
        theta_steps = np.deg2rad(np.arange(0, 360, ROTATION_STEP_DEG))
        r_sim = a * (np.cos(n * theta_steps + d) + np.sin(n * theta_steps + d))
        r_sim_steps = np.round(r_sim * INOUT_STEPS_PER_MM) / INOUT_STEPS_PER_MM  # round to nearest step
        x_sim = r_sim_steps * np.cos(theta_steps)
        y_sim = r_sim_steps * np.sin(theta_steps)

        # Clear axes
        ax_hr.clear()
        ax_sim.clear()

        # High-Res Plot
        ax_hr.plot(x_hr, y_hr, label="High-Resolution Pattern")
        _draw_boundary(ax_hr)
        ax_hr.set_title("High-Resolution Pattern")
        ax_hr.set_aspect('equal')
        ax_hr.set_xticks([-26, 0, 26])
        ax_hr.set_yticks([-26, 0, 26])
        ax_hr.grid(False)
        ax_hr.legend().remove()

        # Simulated Plot
        ax_sim.plot(x_sim, y_sim, 'r', label="Simulated Machine Pattern")
        _draw_boundary(ax_sim)
        ax_sim.set_title("Simulated Machine Pattern")
        ax_sim.set_aspect('equal')
        ax_sim.set_xticks([-26, 0, 26])
        ax_sim.set_yticks([-26, 0, 26])
        ax_sim.grid(False)
        ax_sim.legend().remove()

        canvas.draw()

    except Exception as e:
        messagebox.showerror("Plot Error", f"An error occurred while plotting:\n{e}")

# -------- Utility Function for Boundary --------
def _draw_boundary(ax):
    """
    Draw the fixed boundary circle representing the sand table's movement limit.
    """
    boundary_theta = np.linspace(0, 2 * np.pi, 500)
    boundary_x = 24 * np.cos(boundary_theta)
    boundary_y = 24 * np.sin(boundary_theta)
    ax.plot(boundary_x, boundary_y, 'k')

# -------- Main GUI Setup Function --------
def create_gui():
    """
    Create the main GUI window for adjusting pattern parameters, plotting the pattern,
    and exporting coordinates.
    """
    global root, a_slider, n_slider, d_slider, ax_hr, ax_sim, canvas
    root = tk.Tk()
    root.title("Pattern to Path Generator")

    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.LEFT, padx=10, pady=10)

    info_text = (
        "r = a * (cos(nθ + d) + sin(nθ + d))\n"
        "Adjust 'a', 'n' and 'd' via sliders.\n"
        "Simulated plot uses machine step limits.\n"
        "Boundary circle = physical movement limit."
    )
    tk.Label(control_frame, text=info_text, justify="left", font=("Verdana", 11)).pack(pady=(0, 10))

    tk.Label(control_frame, text="Adjust 'a' (Amplitude):", font=("Verdana", 12)).pack(pady=5)
    a_slider = tk.Scale(control_frame, from_=1, to=23, orient="horizontal", font=("Verdana", 11))
    a_slider.set(10)
    a_slider.pack()

    tk.Label(control_frame, text="Adjust 'n' (Frequency):", font=("Verdana", 12)).pack(pady=5)
    n_slider = tk.Scale(control_frame, from_=1, to=20, orient="horizontal", font=("Verdana", 11))
    n_slider.set(5)
    n_slider.pack()

    tk.Label(control_frame, text="Adjust 'd' (Phase Offset):", font=("Verdana", 12)).pack(pady=5)
    d_slider = tk.Scale(control_frame, from_=0, to=2 * np.pi, resolution=0.01 * np.pi, orient="horizontal", font=("Verdana", 11))
    d_slider.set(0)
    d_slider.pack()

    tk.Button(control_frame, text="Plot Pattern", command=plot_pattern, width=20, font=("Verdana", 12)).pack(pady=12)
  
    # Plotting area
    plot_frame = tk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    fig, (ax_hr, ax_sim) = plt.subplots(1, 2, figsize=(16, 8))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.get_tk_widget().pack()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def on_closing():
    """
    Handle clean shutdown when the GUI window is closed.
    """
    plt.close('all')
    root.destroy()
    root.quit()

# -------- Main Execution --------
if __name__ == "__main__":
    create_gui()
