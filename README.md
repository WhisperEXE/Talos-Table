# Psamathe-Table
Kinetic Sand Art Table - Individual Project for Robotics, Mechatronics &amp; Control Engineering at Loughborough University 

Guide: Setting Up Your Python Environment to Run the Psamathe Controller
This guide will help you install the Python libraries required to run the "Psamathe - Point-to-Point Motion Controller" script.
Prerequisites:
	1. Python Installed: You need Python installed on your computer. If you don't have it, download the latest version from python.org and install it. During installation, make sure to check the box that says "Add Python to PATH" (or similar).
	2. pip (Python Package Installer): pip usually comes with Python if you've installed a recent version. You can check if pip is installed by opening a terminal or command prompt and typing: 
Bash

pip --version

If it's not found, you might need to reinstall Python or look up instructions for installing pip separately for your Python version and operating system.
Step 1: Open Your Terminal or Command Prompt
	• Windows: Search for "Command Prompt" or "PowerShell".
	• macOS: Search for "Terminal" (usually in Applications > Utilities).
	• Linux: You likely know how to open your terminal (e.g., Ctrl+Alt+T).
Step 2: (Recommended) Create and Activate a Virtual Environment
Using a virtual environment is good practice because it keeps the dependencies for different projects separate.
	1. Navigate to your project directory (optional but good practice): Open your terminal and use the cd command to go to the folder where you've saved the Python script (e.g., psamathe_controller.py).
Bash

cd path/to/your/script_directory
	2. Create the virtual environment: Replace myenv with any name you like for your environment (e.g., psamathe_env).
Bash

python -m venv myenv
	3. Activate the virtual environment:
		○ Windows (Command Prompt): 
Bash

myenv\Scripts\activate
		○ Windows (PowerShell): 
Bash

.\myenv\Scripts\Activate.ps1

(If you get an error about execution policies, you might need to run Set-ExecutionPolicy Unrestricted -Scope Process first, then try activating again.)
		○ macOS/Linux: 
Bash

source myenv/bin/activate

Your terminal prompt should now change to indicate that the virtual environment is active (e.g., (myenv) C:\path\to\project>).
Step 3: Install the Required Libraries
The Python script uses the following external libraries that you need to install:
	• Matplotlib: For plotting the graph.
	• NumPy: For numerical operations (though not heavily used in the visible logic, it's a common dependency for Matplotlib and good to have if future extensions might use it).
	• Pyserial: For communicating with the Arduino via the serial port.
You can install these libraries using pip. Type the following commands into your terminal (while the virtual environment is active, if you created one) and press Enter after each one:
Bash

pip install matplotlib
Bash

pip install numpy
Bash

pip install pyserial
Alternatively, you can install them all in one line:
Bash

pip install matplotlib numpy pyserial
Pip will download and install the packages and their dependencies. Wait for each command to complete.
Step 4: Verify Installation (Optional)
You can quickly check if the libraries are installed by trying to import them in Python:
	1. Type python in your terminal and press Enter. This will open the Python interpreter.
	2. Try importing each library: 
Python

import tkinter
import matplotlib
import numpy
import serial
exit()
	3. If no errors appear after each import statement, the libraries are installed correctly. Type exit() to leave the Python interpreter.
Step 5: Run the Script
Once all the libraries are installed, you can run your Python script:
	1. Make sure you are in the directory where the script is saved (use the cd command if necessary).
	2. If you are using a virtual environment, ensure it is activated.
	3. Run the script using: 
Bash

python your_script_name.py

(Replace your_script_name.py with the actual name of your Python file).
Troubleshooting:
	• pip or python command not found: This usually means Python or pip is not correctly installed or not added to your system's PATH. Revisit the Python installation steps.
	• ModuleNotFoundError: If you get an error like ModuleNotFoundError: No module named 'matplotlib', it means that specific library wasn't installed correctly or you are not running the script in the environment where you installed it (e.g., virtual environment is not active). Double-check the installation steps.
	• Permissions Issues (Linux/macOS): If you get permission errors, you might need to use sudo pip install ... (though it's generally better to use virtual environments to avoid needing sudo for pip). On Windows, you might need to run the Command Prompt as an Administrator if you encounter permission issues, but this is less common for pip installs into user space or virtual environments.
![image](https://github.com/user-attachments/assets/267e889e-52b6-486b-a054-12cb5f0fd98c)
