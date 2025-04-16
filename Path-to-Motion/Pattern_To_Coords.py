"""
Kinetic Sand Table - Pattern to Path Exporter
---------------------------------------------
Extends the simple radial pattern generator by adding export options to save the
pattern as coordinate lists in both Cartesian (X, Y) and polar (R, Theta) formats.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------- Pattern Plotting Function --------
def plot_pattern():
    """
    Generate and display a radial pattern plot based on slider inputs for 'a', 'n', and 'd'.

    Formula:
        r = a * (cos(n*theta + d) + sin(n*theta + d))
    """
    try:
        global x, y, r_vals, theta_vals  # Store for export

        a = a_slider.get()
        n = n_slider.get()
        d = d_slider.get()

        theta = np.linspace(0, 2 * np.pi, 1000)
        r = a * (np.cos(n * theta + d) + np.sin(n * theta + d))

        # Convert polar to Cartesian
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        # Store polar values
        r_vals = r
        theta_vals = theta

        # Clear previous figure content
        ax.clear()

        # Plot pattern
        ax.plot(x, y)

        # Plot boundary circle at radius 24
        boundary_theta = np.linspace(0, 2 * np.pi, 500)
        boundary_x = 24 * np.cos(boundary_theta)
        boundary_y = 24 * np.sin(boundary_theta)
        ax.plot(boundary_x, boundary_y, 'k')

        # Plot settings
        ax.set_aspect('equal')
        ax.set_title("Radial Pattern Plot")
        ax.set_xticks([-26, 0, 26])
        ax.set_yticks([-26, 0, 26])
        ax.grid(False)

        canvas.draw()

    except Exception as e:
        messagebox.showerror("Plot Error", f"An error occurred while plotting:\n{e}")

# -------- Export X-Y Coordinates --------
def export_xy():
    """
    Export the current pattern as a list of (x, y) coordinates to a text file.
    """
    try:
        if x is None or y is None:
            messagebox.showwarning("No Data", "Please plot a pattern first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

        if file_path:
            with open(file_path, "w") as file:
                for xi, yi in zip(x, y):
                    file.write(f"({xi:.3f}, {yi:.3f})\n")
            messagebox.showinfo("Export Complete", f"Coordinates exported to:\n{file_path}")

    except Exception as e:
        messagebox.showerror("Export Error", f"An error occurred during export:\n{e}")

# -------- Export R-Theta Coordinates --------
def export_rtheta():
    """
    Export the current pattern as a list of (r, theta) coordinates to a text file.
    """
    try:
        if r_vals is None or theta_vals is None:
            messagebox.showwarning("No Data", "Please plot a pattern first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

        if file_path:
            with open(file_path, "w") as file:
                for ri, ti in zip(r_vals, theta_vals):
                    file.write(f"({ri:.3f}, {ti:.3f})\n")
            messagebox.showinfo("Export Complete", f"Coordinates exported to:\n{file_path}")

    except Exception as e:
        messagebox.showerror("Export Error", f"An error occurred during export:\n{e}")

# -------- Main GUI Setup Function --------
def create_gui():
    """
    Create the main GUI window for adjusting pattern parameters and plotting.
    The Matplotlib figure is embedded directly inside the Tkinter window.
    """

    global root, a_slider, n_slider, d_slider, ax, canvas, x, y, r_vals, theta_vals
    x = y = r_vals = theta_vals = None

    root = tk.Tk()
    root.title("Kinetic Sand Table Pattern to Path Exporter")

    # Left frame for sliders and controls
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.LEFT, padx=10, pady=10)

    # Info Text
    info = (
        "r = a * (cos(n*theta + d) + sin(n*theta + d))\n"
        "Adjust 'a', 'n', 'd' values via sliders, plot, and export pattern coordinates."
    )
    tk.Label(control_frame, text=info, justify="left", padx=10, pady=10, font=("Verdana", 12)).pack(side="top", fill="x", pady=(0, 10))

    # 'a' Slider
    tk.Label(control_frame, text="Adjust 'a' (Amplitude):", font=("Verdana", 12)).pack(pady=5)
    a_slider = tk.Scale(control_frame, from_=1, to=23, orient="horizontal", resolution=1, font=("Verdana", 12))
    a_slider.set(10)
    a_slider.pack(pady=5)

    # 'n' Slider
    tk.Label(control_frame, text="Adjust 'n' (Frequency):", font=("Verdana", 12)).pack(pady=5)
    n_slider = tk.Scale(control_frame, from_=1, to=20, orient="horizontal", resolution=1, font=("Verdana", 12))
    n_slider.set(5)
    n_slider.pack(pady=5)

    # 'd' Slider
    tk.Label(control_frame, text="Adjust 'd' (Phase Offset):", font=("Verdana", 12)).pack(pady=5)
    d_slider = tk.Scale(control_frame, from_=0, to=2*np.pi, orient="horizontal", resolution=0.01*np.pi, font=("Verdana", 12))
    d_slider.set(0)
    d_slider.pack(pady=5)

    # Plot Button
    tk.Button(control_frame, text="Plot Pattern", command=plot_pattern, width=20, font=("Verdana", 12)).pack(pady=15)

    # Export Buttons
    tk.Button(control_frame, text="Export Coordinates X-Y", command=export_xy, width=25, font=("Verdana", 12)).pack(pady=5)
    tk.Button(control_frame, text="Export Coordinates R-Theta", command=export_rtheta, width=25, font=("Verdana", 12)).pack(pady=5)

    # Right frame for Matplotlib figure
    plot_frame = tk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    # Matplotlib figure setup
    fig, ax = plt.subplots(figsize=(8, 8))
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def on_closing():
    """
    Handle proper application shutdown when the window is closed.
    """
    plt.close('all')
    root.destroy()
    root.quit()

# -------- Main Execution --------
if __name__ == "__main__":
    create_gui()
