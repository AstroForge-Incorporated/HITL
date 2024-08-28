import subprocess
import sys
import os
import webbrowser
import time

def run_script(script_name):
    """Run a Python script using subprocess."""
    try:
        # Construct the command to execute the script
        command = [sys.executable, script_name]
        print(f"Running {script_name} with command: {' '.join(command)}")
        
        # Execute the script
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    
    except Exception as e:
        print(f"An error occurred while running {script_name}: {e}")

def main():
    scripts_folder = '/root/HITL/scripts'  # Adjust the path to your folder
    
    # List all Python scripts in the scripts folder
    scripts = [os.path.join(scripts_folder, f) for f in os.listdir(scripts_folder) if f.endswith('.py')]

    # List to keep track of processes
    processes = []

    # Start each script in its own process
    for script in scripts:
        process = run_script(script)
        if process:
            processes.append(process)

    # Open the URLs in the default web browser
    url1 = 'http://192.168.80.85:3000/dashboards'
    url2 = 'http://192.168.80.85:8080'
    
    print(f"Opening URL: {url1}")
    webbrowser.open(url1)
    
    # Optional: delay between opening URLs
    time.sleep(2)  # Adjust the delay as needed
    
    print(f"Opening URL: {url2}")
    webbrowser.open(url2)

    # Wait for all processes to complete
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            print(f"Process completed successfully.")
            print(stdout.decode())
        else:
            print(f"Error occurred:")
            print(stderr.decode())

if __name__ == '__main__':
    main()






