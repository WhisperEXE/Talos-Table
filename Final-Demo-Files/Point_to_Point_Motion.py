import tkinter as tk
from tkinter import messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np # Kept import as it's common in such projects, though not directly used in this specific logic.
import math
import serial
import time

# --------- Machine Parameters ---------
INOUT_STEPS_PER_MM = 33            # Steps for the in-out motor per millimeter of linear movement.
ROTATION_DEG_PER_STEP = 0.0675     # Degrees of platform rotation per step of the rotation motor.
COMPENSATION_RATIO = 0.3167        # Compensation factor: in-out steps to adjust per rotation step to counteract coupling.
# MAX_INOUT_STEPS = 4280           # Maximum allowed absolute in-out step position (requires absolute homing). Commented out as current logic is session-relative.
PLOT_LIMIT_MM = 200                # Plot area display limit in mm for x and y axes.
WORKSPACE_RADIUS_MM = 130          # Main operational boundary (outer circle) in mm for drawable area.
INNER_LIMIT_RADIUS_MM = 30         # Inner un-drawable circle radius in mm.

# --------- Global Variables ---------
start_point_mm = None              # Stores the start point as (x_mm, y_mm).
end_point_mm = None                # Stores the end point as (x_mm, y_mm).
point_selection_mode = "start"     # Tracks if the next click on the graph sets the "start" or "end" point.
last_move_steps = (0, 0)           # Stores (logical_rotation_steps, logical_inout_steps) of the last move for the undo function.
total_rotation_steps = 0           # Cumulative logical rotation steps during the current session.
total_inout_steps = 0              # Cumulative logical in-out steps (compensated) during the current session.
arduino = None                     # Holds the serial connection object for Arduino communication.

# GUI Elements (declared global for easier access in multiple functions)
root = None
input_frame = None
fig = None # Add fig to globals as it's part of the core plot setup
ax = None
canvas = None
result_label = None
total_label = None
click_mode_label = None
start_x_entry, start_y_entry, end_x_entry, end_y_entry = None, None, None, None

# --------- Utility Functions ---------
def to_polar(x_mm, y_mm):
    """
    Convert Cartesian coordinates (x, y) in millimeters to Polar coordinates.

    Args:
        x_mm (float): X-coordinate in millimeters.
        y_mm (float): Y-coordinate in millimeters.

    Returns:
        tuple: (theta_degrees, r_mm)
               theta_degrees (float): Angle in degrees (-180 to 180).
               r_mm (float): Radius in millimeters.
    """
    theta_degrees = math.degrees(math.atan2(y_mm, x_mm))
    r_mm = math.hypot(x_mm, y_mm)
    return theta_degrees, r_mm

def redraw_plot_with_points():
    """
    Clears and redraws the Matplotlib plot.
    This includes axes, grid, workspace boundaries, and currently defined start/end points and the line between them.
    """
    global fig, ax, canvas, start_point_mm, end_point_mm # Ensure globals are accessible

    if ax is None: # If axes aren't set up, can't draw.
        print("Error: Axes (ax) not initialized. Cannot redraw plot.")
        return

    ax.clear()
    ax.set_xlim(-PLOT_LIMIT_MM, PLOT_LIMIT_MM)
    ax.set_ylim(-PLOT_LIMIT_MM, PLOT_LIMIT_MM)
    ax.set_aspect('equal', adjustable='box') # Ensures circle looks like a circle
    ax.grid(True)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("Click to Set Points or Use Entries")

    # Draw workspace boundaries
    boundary_circle = plt.Circle((0, 0), WORKSPACE_RADIUS_MM, color='blue', fill=False, linestyle='--', label=f'Workspace ({WORKSPACE_RADIUS_MM}mm)')
    ax.add_artist(boundary_circle)
    inner_limit_circle = plt.Circle((0, 0), INNER_LIMIT_RADIUS_MM, color='red', fill=False, linestyle=':', label=f'Inner Limit ({INNER_LIMIT_RADIUS_MM}mm)')
    ax.add_artist(inner_limit_circle)

    legend_handles = [boundary_circle, inner_limit_circle]

    if start_point_mm:
        start_handle, = ax.plot(start_point_mm[0], start_point_mm[1], 'go', label='Start Point', markersize=7)
        legend_handles.append(start_handle)
    if end_point_mm:
        end_handle, = ax.plot(end_point_mm[0], end_point_mm[1], 'ro', label='End Point', markersize=7)
        legend_handles.append(end_handle)
    if start_point_mm and end_point_mm:
        ax.plot([start_point_mm[0], end_point_mm[0]], [start_point_mm[1], end_point_mm[1]], 'b--')

    ax.legend(handles=legend_handles, loc='upper right', fontsize='small')
    
    if canvas: # Check if canvas object exists and is not None
        canvas.draw()
    else:
        # This might occur if called before canvas is fully initialized, though the reorder should prevent it.
        print("Warning: Canvas not available during redraw. Plot may not display changes if called too early.")


# --------- Event Handlers ---------
def on_plot_click(event):
    """
    Handles mouse click events on the Matplotlib plot area.
    Sets the start or end point based on the current `point_selection_mode`.
    Updates corresponding Tkinter Entry widgets and redraws the plot.

    Args:
        event (matplotlib.backend_bases.MouseEvent): The mouse event object containing click data.
    """
    global start_point_mm, end_point_mm, point_selection_mode
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry, click_mode_label, ax # ax is needed for event.inaxes

    if event.inaxes != ax:  # Ignore clicks outside the defined plot axes
        return

    clicked_x_mm = event.xdata # xdata and ydata are in plot's data coordinates (mm)
    clicked_y_mm = event.ydata

    # Convert mm (from plot) to cm for display in Entry widgets
    clicked_x_cm = clicked_x_mm / 10.0
    clicked_y_cm = clicked_y_mm / 10.0

    if point_selection_mode == "start":
        start_point_mm = (clicked_x_mm, clicked_y_mm)
        if start_x_entry: start_x_entry.delete(0, tk.END); start_x_entry.insert(0, f"{clicked_x_cm:.2f}")
        if start_y_entry: start_y_entry.delete(0, tk.END); start_y_entry.insert(0, f"{clicked_y_cm:.2f}")

        if end_x_entry: end_x_entry.delete(0, tk.END)
        if end_y_entry: end_y_entry.delete(0, tk.END)
        end_point_mm = None
        point_selection_mode = "end"
        print(f"Start point set by click: ({clicked_x_mm:.2f} mm, {clicked_y_mm:.2f} mm)")
    elif point_selection_mode == "end":
        if start_point_mm is None:
            messagebox.showwarning("Selection Order", "Please set the start point first by clicking on the graph.")
            return
        end_point_mm = (clicked_x_mm, clicked_y_mm)
        if end_x_entry: end_x_entry.delete(0, tk.END); end_x_entry.insert(0, f"{clicked_x_cm:.2f}")
        if end_y_entry: end_y_entry.delete(0, tk.END); end_y_entry.insert(0, f"{clicked_y_cm:.2f}")
        point_selection_mode = "start"
        print(f"End point set by click: ({clicked_x_mm:.2f} mm, {clicked_y_mm:.2f} mm)")

    redraw_plot_with_points()
    if click_mode_label:
        click_mode_label.config(text=f"Click on graph to set: {point_selection_mode.capitalize()} point")

# --------- GUI Button Callbacks ---------
def draw_line_from_entries():
    """
    Reads coordinates from the Tkinter Entry widgets (in cm), converts them to mm,
    updates the global start_point_mm and end_point_mm, and redraws the plot.
    """
    global start_point_mm, end_point_mm
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry

    try:
        sx_cm = float(start_x_entry.get())
        sy_cm = float(start_y_entry.get())
        ex_cm = float(end_x_entry.get())
        ey_cm = float(end_y_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric coordinates in all X and Y fields.")
        return

    start_point_mm = (sx_cm * 10.0, sy_cm * 10.0)
    end_point_mm = (ex_cm * 10.0, ey_cm * 10.0)

    print(f"Line defined from entries: Start {start_point_mm} mm, End {end_point_mm} mm")
    redraw_plot_with_points()

def send_arduino_command(axis_char, steps_to_send):
    """
    Sends a formatted movement command string to the connected Arduino.

    Args:
        axis_char (str): Character representing the axis ('r' for rotation, 'i' for in-out).
        steps_to_send (int): The number of steps to command the motor.
    """
    global arduino
    if arduino and arduino.is_open:
        command = f"{axis_char} {steps_to_send}\n"
        print(f"Sending to Arduino: {command.strip()}")
        try:
            arduino.write(command.encode('utf-8'))
        except serial.SerialTimeoutException:
            messagebox.showerror("Serial Timeout", "Timeout occurred while writing to Arduino. Please check the connection.")
        except Exception as e:
            messagebox.showerror("Serial Error", f"An error occurred while writing to Arduino: {e}")
    else:
        messagebox.showwarning("Not Connected", "Arduino connection is not established or has been closed.")

def execute_move():
    """
    Calculates and executes motor movements based on defined start and end points.
    Applies compensation and inverts steps for reversed motor wiring.
    Updates session totals and prepares for the next move.
    """
    global start_point_mm, end_point_mm, last_move_steps, total_rotation_steps, total_inout_steps
    global result_label, point_selection_mode, click_mode_label
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry

    if not start_point_mm or not end_point_mm:
        messagebox.showwarning("Action Required", "Please define both start and end points first.")
        return

    theta1_deg, r1_mm = to_polar(start_point_mm[0], start_point_mm[1])
    theta2_deg, r2_mm = to_polar(end_point_mm[0], end_point_mm[1])

    if not (INNER_LIMIT_RADIUS_MM <= r1_mm <= WORKSPACE_RADIUS_MM and \
            INNER_LIMIT_RADIUS_MM <= r2_mm <= WORKSPACE_RADIUS_MM):
        messagebox.showwarning("Workspace Violation", "Start or end point is outside the defined drawable workspace limits.")
        return

    delta_theta_deg = theta2_deg - theta1_deg
    if delta_theta_deg > 180.0: delta_theta_deg -= 360.0
    elif delta_theta_deg < -180.0: delta_theta_deg += 360.0
    delta_r_mm = r2_mm - r1_mm

    logical_rotation_steps = int(round(delta_theta_deg / ROTATION_DEG_PER_STEP))
    logical_inout_steps_raw = int(round(delta_r_mm * INOUT_STEPS_PER_MM))
    compensation_adjustment_steps = int(round(COMPENSATION_RATIO * logical_rotation_steps))
    logical_inout_steps_compensated = logical_inout_steps_raw - compensation_adjustment_steps

    final_steps_to_send_rotation = -logical_rotation_steps
    final_steps_to_send_inout = -logical_inout_steps_compensated

    if result_label:
        result_label.config(text=f"Logic: Δθ={delta_theta_deg:.2f}° ({logical_rotation_steps} steps), Δr={delta_r_mm:.2f} mm ({logical_inout_steps_raw} steps)\n"
                                 f"Comp: -{compensation_adjustment_steps} for InOut. Final InOut Logic: {logical_inout_steps_compensated} steps\n"
                                 f"Sent: Rot={final_steps_to_send_rotation} steps, InOut={final_steps_to_send_inout} steps")

    time.sleep(1)

    if final_steps_to_send_rotation != 0:
        send_arduino_command('r', final_steps_to_send_rotation)
        total_rotation_steps += logical_rotation_steps
    if final_steps_to_send_inout != 0:
        send_arduino_command('i', final_steps_to_send_inout)
        total_inout_steps += logical_inout_steps_compensated

    time.sleep(2)
    update_totals_display()
    last_move_steps = (-logical_rotation_steps, -logical_inout_steps_compensated)

    start_point_mm = end_point_mm
    if start_x_entry: start_x_entry.delete(0, tk.END); start_x_entry.insert(0, f"{start_point_mm[0]/10.0:.2f}")
    if start_y_entry: start_y_entry.delete(0, tk.END); start_y_entry.insert(0, f"{start_point_mm[1]/10.0:.2f}")
    if end_x_entry: end_x_entry.delete(0, tk.END)
    if end_y_entry: end_y_entry.delete(0, tk.END)
    end_point_mm = None
    point_selection_mode = "end"
    if click_mode_label: click_mode_label.config(text=f"Click on graph to set: {point_selection_mode.capitalize()} point")
    redraw_plot_with_points()

def undo_last_move():
    """
    Reverses the last executed move by sending inverted logical steps to the Arduino.
    Updates session totals and resets relevant state variables.
    """
    global last_move_steps, total_rotation_steps, total_inout_steps, result_label
    global start_point_mm, end_point_mm, point_selection_mode, click_mode_label
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry

    logical_rot_steps_to_reverse, logical_inout_steps_to_reverse = last_move_steps

    if logical_rot_steps_to_reverse == 0 and logical_inout_steps_to_reverse == 0:
        messagebox.showinfo("Undo", "No move to undo, or the last move was already undone.")
        return

    actual_rot_steps_to_send_for_undo = -logical_rot_steps_to_reverse
    actual_inout_steps_to_send_for_undo = -logical_inout_steps_to_reverse

    time.sleep(1) #1 second delay to allow me to hold the motors in place becasue their housing didnt print properly

    if actual_rot_steps_to_send_for_undo != 0:
        send_arduino_command('r', actual_rot_steps_to_send_for_undo)
        total_rotation_steps += logical_rot_steps_to_reverse
    if actual_inout_steps_to_send_for_undo != 0:
        send_arduino_command('i', actual_inout_steps_to_send_for_undo)
        total_inout_steps += logical_inout_steps_to_reverse

    time.sleep(2) #update display after 2 seconds so the motors finish moving

    update_totals_display()
    last_move_steps = (0, 0)
    if result_label: result_label.config(text="Last move successfully undone.")

    start_point_mm = None; end_point_mm = None
    if start_x_entry: start_x_entry.delete(0, tk.END)
    if start_y_entry: start_y_entry.delete(0, tk.END)
    if end_x_entry: end_x_entry.delete(0, tk.END)
    if end_y_entry: end_y_entry.delete(0, tk.END)
    point_selection_mode = "start"
    if click_mode_label: click_mode_label.config(text=f"Click on graph to set: {point_selection_mode.capitalize()} point")
    redraw_plot_with_points()

def update_totals_display():
    """
    Updates the GUI Label showing cumulative logical rotation and in-out steps for the current session.
    """
    global total_label, total_rotation_steps, total_inout_steps
    if total_label:
        total_label.config(text=f"Session Totals (Logical): Rotation Steps: {total_rotation_steps}, In-Out Steps: {total_inout_steps}")

def reset_graph_visuals_and_state():
    """
    Resets the application to its initial state: clears points, totals, entry fields, and redraws an empty plot.
    """
    global start_point_mm, end_point_mm, last_move_steps, total_rotation_steps, total_inout_steps, point_selection_mode
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry, result_label, click_mode_label

    start_point_mm = None; end_point_mm = None
    last_move_steps = (0, 0)
    total_rotation_steps = 0; total_inout_steps = 0
    point_selection_mode = "start"

    if start_x_entry: start_x_entry.delete(0, tk.END)
    if start_y_entry: start_y_entry.delete(0, tk.END)
    if end_x_entry: end_x_entry.delete(0, tk.END)
    if end_y_entry: end_y_entry.delete(0, tk.END)

    redraw_plot_with_points()
    if result_label: result_label.config(text="Graph and totals reset. Define new points.")
    update_totals_display()
    if click_mode_label: click_mode_label.config(text=f"Click on graph to set: {point_selection_mode.capitalize()} point")
    print("Graph, points, and session totals have been reset.")

# --------- Serial Connection Functions ---------
def attempt_arduino_connection(port_str, baud_rate):
    """
    Attempts to establish a serial connection to the Arduino.

    Args:
        port_str (str): The COM port string (e.g., "COM3").
        baud_rate (int): The baud rate for the serial connection.

    Returns:
        serial.Serial or None: The serial object if successful, else None.
    """
    global arduino
    try:
        arduino = serial.Serial(port_str, baud_rate, timeout=1)
        print(f"Successfully connected to Arduino on {port_str} at {baud_rate} baud.")
        return arduino
    except serial.SerialException as e:
        messagebox.showerror("Arduino Connection Error", f"Failed to connect on {port_str}.\nError: {e}\nCheck port and connection.")
        return None

def prompt_for_com_port(parent_window):
    """
    Prompts the user for the Arduino COM port via a simple dialog.

    Args:
        parent_window (tk.Tk or tk.Toplevel): The parent window for the dialog.

    Returns:
        str or None: The COM port string if entered, else None.
    """
    port = simpledialog.askstring("Arduino COM Port", "Enter Arduino COM port (e.g., COM3):", parent=parent_window)
    return port

# --------- GUI Setup ---------
def create_main_gui():
    """
    Initializes and runs the main Tkinter GUI, including Matplotlib canvas and event bindings.
    """
    global root, input_frame, fig, ax, canvas, result_label, total_label, click_mode_label
    global start_x_entry, start_y_entry, end_x_entry, end_y_entry, point_selection_mode

    root = tk.Tk()
    root.title("Psamathe - Point-to-Point Motion Controller v1.2")

    input_frame = tk.Frame(root, padx=10, pady=5)
    input_frame.pack(pady=(5,0))

    tk.Label(input_frame, text="Start X (cm):").grid(row=0, column=0, sticky="w", padx=(0,2))
    start_x_entry = tk.Entry(input_frame, width=8)
    start_x_entry.grid(row=0, column=1, padx=(0,5))
    tk.Label(input_frame, text="Start Y (cm):").grid(row=0, column=2, sticky="w", padx=(5,2))
    start_y_entry = tk.Entry(input_frame, width=8)
    start_y_entry.grid(row=0, column=3, padx=(0,0))
    tk.Label(input_frame, text="End X (cm):").grid(row=1, column=0, sticky="w", padx=(0,2), pady=(5,0))
    end_x_entry = tk.Entry(input_frame, width=8)
    end_x_entry.grid(row=1, column=1, padx=(0,5), pady=(5,0))
    tk.Label(input_frame, text="End Y (cm):").grid(row=1, column=2, sticky="w", padx=(5,2), pady=(5,0))
    end_y_entry = tk.Entry(input_frame, width=8)
    end_y_entry.grid(row=1, column=3, padx=(0,0), pady=(5,0))

    click_mode_label = tk.Label(root, text=f"Click on graph to set: {point_selection_mode.capitalize()} point", font=("Arial", 10, "italic"))
    click_mode_label.pack(pady=(2,2))

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)
    tk.Button(button_frame, text="Draw Line (from Entries)", command=draw_line_from_entries, font=("Arial", 10), width=22).grid(row=0, column=0, padx=5, pady=2)
    tk.Button(button_frame, text="Execute Move", command=execute_move, font=("Arial", 10, "bold"), width=15, bg="#90EE90").grid(row=0, column=1, padx=5, pady=2)
    tk.Button(button_frame, text="Undo Last Move", command=undo_last_move, font=("Arial", 10), width=15).grid(row=0, column=2, padx=5, pady=2)
    tk.Button(button_frame, text="Reset All", command=reset_graph_visuals_and_state, font=("Arial", 10), width=12, bg="#FFCCCB").grid(row=0, column=3, padx=5, pady=2)

    result_label = tk.Label(root, text="Define points and press 'Execute Move'", justify="left", font=("Courier New", 9), relief=tk.SUNKEN, bd=1, width=65, height=4, anchor="nw")
    result_label.pack(pady=5, padx=10, fill="x")
    total_label = tk.Label(root, text="Session Totals: Awaiting first move", font=("Arial", 9), relief=tk.SUNKEN, bd=1)
    total_label.pack(pady=(0,5), padx=10, fill="x")
    update_totals_display()

    # --- Matplotlib Figure and Canvas ---
    fig, ax = plt.subplots(figsize=(5, 5))
    canvas = FigureCanvasTkAgg(fig, master=root) # Create canvas before first redraw call

    redraw_plot_with_points() # Now this call is safe as ax and canvas exist

    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(pady=(0,5), padx=10, fill=tk.BOTH, expand=True)
    fig.canvas.mpl_connect('button_press_event', on_plot_click)

    root.protocol("WM_DELETE_WINDOW", on_closing_application)
    root.mainloop()

def on_closing_application():
    """
    Handles clean shutdown: confirms quit, closes serial port, and destroys GUI window.
    """
    global root, arduino
    if messagebox.askokcancel("Quit", "Do you want to quit the Psamathe Controller?"):
        if arduino and arduino.is_open:
            arduino.close()
            print("Arduino serial connection closed.")
        if plt: plt.close('all')
        if root: root.destroy()
        print("Application closed by user.")

# --------- Program Execution ---------
if __name__ == "__main__":
    temp_root_for_dialog = tk.Tk()
    temp_root_for_dialog.withdraw()
    arduino_com_port_str = prompt_for_com_port(parent_window=temp_root_for_dialog)
    temp_root_for_dialog.destroy()

    if arduino_com_port_str:
        BAUDRATE = 115200
        arduino = attempt_arduino_connection(arduino_com_port_str, BAUDRATE)
        if arduino:
            create_main_gui()
        else:
            print("Could not connect to Arduino. Application will exit.")
    else:
        print("No COM port selected. Application will exit.")