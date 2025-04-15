"""
Kinetic Sand Table - Simple Radial Pattern Generator
-----------------------------------------------------------------
r = a * cos(n * theta + d)
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------- Simple Pattern Plotting Function --------
def plot_simple_pattern():
    """
    Generate and display a simple radial pattern plot based on slider inputs for 'a', 'n', and 'd'.
    Formula:
        r = a * (cos(n * theta + d) + sin(n * theta + d))
    """
    try:
        a = a_slider.get()
        n = n_slider.get()
        d = d_slider.get()

        theta = np.linspace(0, 2 * np.pi, 1000)
        r = a * (np.cos(n * theta + d) + np.sin(n * theta + d))
        # Limit r values within [-23, 23]
        r = np.clip(r, -23, 23) 

        ax.clear()
        ax.plot(r * np.cos(theta), r * np.sin(theta))

        # Boundary circle at radius 24
        boundary_theta = np.linspace(0, 2 * np.pi, 500)
        ax.plot(24 * np.cos(boundary_theta), 24 * np.sin(boundary_theta), 'k')

        ax.set_aspect('equal')
        ax.set_title("Radial Pattern Plot")
        ax.set_xticks([-26, 0, 26])
        ax.set_yticks([-26, 0, 26])
        ax.grid(False)
        ax.legend().remove()

        canvas.draw()

    except Exception as e:
        messagebox.showerror("Plot Error", f"An error occurred while plotting:\n{e}")

# -------- Simple Generator GUI --------
def simple_gen_gui():
    """
    Launch the Simple Pattern Generator GUI window with 'a', 'n', and 'd' sliders.
    """
    global root, a_slider, n_slider, d_slider, ax, canvas
    root = tk.Tk()
    root.title("Simple Pattern Generator")

    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.LEFT, padx=10, pady=10)

    info = (
        "r = a * (cos(n * θ + d) + sin(n * θ + d))\n"
        "Adjust 'a', 'n', and 'd' via sliders.\n"
        "The boundary circle marks the limit."
    )
    tk.Label(control_frame, text=info, justify="left", padx=10, pady=10, font=("Verdana", 12)).pack()

    tk.Label(control_frame, text="Adjust 'a' (Amplitude):", font=("Verdana", 12)).pack(pady=5)
    a_slider = tk.Scale(control_frame, from_=1, to=40, orient="horizontal", resolution=1, font=("Verdana", 12))
    a_slider.set(10)
    a_slider.pack(pady=5)

    tk.Label(control_frame, text="Adjust 'n' (Frequency):", font=("Verdana", 12)).pack(pady=5)
    n_slider = tk.Scale(control_frame, from_=1, to=20, orient="horizontal", resolution=1, font=("Verdana", 12))
    n_slider.set(5)
    n_slider.pack(pady=5)

    tk.Label(control_frame, text="Adjust 'd' (Phase Offset):", font=("Verdana", 12)).pack(pady=5)
    d_slider = tk.Scale(control_frame, from_=0, to=2*np.pi, orient="horizontal", resolution=0.01*np.pi, font=("Verdana", 12), length=300)
    d_slider.set(0)
    d_slider.pack(pady=5)

    tk.Button(control_frame, text="Plot Pattern", command=plot_simple_pattern, width=20, font=("Verdana", 12)).pack(pady=15)

    plot_frame = tk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    fig, ax = plt.subplots(figsize=(8, 8))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.get_tk_widget().pack()

    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()

def on_closing(window):
    """
    Handle proper shutdown when closing any of the GUI windows.
    Added because matplotlib continues generating plots even when GUI is closed.
    """
    plt.close('all')
    window.destroy()
    window.quit()

# -------- Main Execution --------
if __name__ == "__main__":
    simple_gen_gui()
