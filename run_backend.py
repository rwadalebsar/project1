import subprocess
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')

# Change to the backend directory
os.chdir(backend_dir)

# Activate virtual environment and run the backend server
activate_cmd = f"cd {backend_dir} && bash -c 'source venv/bin/activate && python main.py'"
subprocess.call(activate_cmd, shell=True)
