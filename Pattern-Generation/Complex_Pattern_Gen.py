"""
Kinetic Sand Table - Complex Radial Pattern Generator
-----------------------------------------------------------------
r = a * ((cos(2*arcsin(k)+pi*m)/2*n) / (cos(2*arcsin(k*cos(n*theta))+pi*m)/2*n))
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------- Complex Pattern Plotting Function --------
def plot_complex_pattern():
    """
    Generate and display a complex radial pattern plot based on 'a', 'k', 'm', and 'n'.
    Formula:
        r = a * ((cos(2*arcsin(k)+pi*m)/2*n) / (cos(2*arcsin(k*cos(n*theta))+pi*m)/2*n))
    """
    try:
        a = a_slider.get()
        k = k_slider.get()
        m = m_slider.get()
        n = n_slider.get()

        theta = np.linspace(0, 2 * np.pi, 1000)
        numerator = np.cos(2 * np.arcsin(k) + np.pi * m) / (2 * n)
        denominator = np.cos(2 * np.arcsin(k * np.cos(n * theta)) + np.pi * m) / (2 * n)
        r = a * (numerator / denominator)
        # Limit r values within [-23, 23]
        r = np.clip(r, -23, 23) 

        ax.clear()
        ax.plot(r * np.cos(theta), r * np.sin(theta))

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

# -------- Complex Generator GUI --------
def complex_gen_gui():
    """
    Launch the Complex Pattern Generator GUI window with 'a', 'k', 'm', and 'n' sliders.
    """
    global root, a_slider, k_slider, m_slider, n_slider, ax, canvas
    root = tk.Tk()
    root.title("Complex Pattern Generator")

    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.LEFT, padx=10, pady=10)

    info = (
        "r = a * ((cos(2*arcsin(k)+pi*m)/2n) / (cos(2*arcsin(k*cos(nθ))+pi*m)/2n))\n"
        "Adjust 'a', 'k', 'm' and 'n' via sliders.\n"
        "A boundary circle marks the limit."
    )
    tk.Label(control_frame, text=info, justify="left", padx=10, pady=10, font=("Verdana", 12)).pack()

    tk.Label(control_frame, text="Adjust 'a' (Amplitude):", font=("Verdana", 12)).pack(pady=5)
    a_slider = tk.Scale(control_frame, from_=1, to=40, orient="horizontal", resolution=1, font=("Verdana", 12))
    a_slider.set(10)
    a_slider.pack(pady=5)

    tk.Label(control_frame, text="Adjust 'k':", font=("Verdana", 12)).pack(pady=5)
    k_slider = tk.Scale(control_frame, from_=0.01, to=0.99, orient="horizontal", resolution=0.01, font=("Verdana", 12))
    k_slider.set(0.5)
    k_slider.pack(pady=5)

    tk.Label(control_frame, text="Adjust 'm':", font=("Verdana", 12)).pack(pady=5)
    m_slider = tk.Scale(control_frame, from_=0, to=2, orient="horizontal", resolution=0.1, font=("Verdana", 12))
    m_slider.set(1)
    m_slider.pack(pady=5)

    tk.Label(control_frame, text="Adjust 'n' (Frequency):", font=("Verdana", 12)).pack(pady=5)
    n_slider = tk.Scale(control_frame, from_=1, to=20, orient="horizontal", resolution=1, font=("Verdana", 12))
    n_slider.set(5)
    n_slider.pack(pady=5)

    tk.Button(control_frame, text="Plot Pattern", command=plot_complex_pattern, width=20, font=("Verdana", 12)).pack(pady=15)

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
    complex_gen_gui()
