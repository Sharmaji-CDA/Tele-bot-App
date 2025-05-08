import os
import subprocess
import sys

# Define virtual environment directory name
VENV_DIR = "venv"

def create_virtualenv():
    """Creates a virtual environment."""
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR])
        print("Virtual environment created successfully!")
    else:
        print("Virtual environment already exists.")

def install_requirements():
    """Installs dependencies from requirements.txt."""
    print("Installing dependencies from requirements.txt...")
    pip_path = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "pip")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully!")

def run_python_script():
    """Runs a basic test script inside the virtual environment."""
    python_path = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
    script_content = """import openai\nprint("OpenAI package installed successfully!")"""
    with open("test_script.py", "w") as f:
        f.write(script_content)
    print("Running test script...")
    subprocess.run([python_path, "test_script.py"])
    print("Script executed successfully!")

def run_app():
    """Runs app.py inside the virtual environment."""
    python_path = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python")
    print("Starting app.py...")
    subprocess.call([python_path, "app.py"])    

if __name__ == "__main__":
    create_virtualenv()
    install_requirements()
    run_python_script()
    run_app()
