import tkinter as tk
import threading
import subprocess
import os
import re
import time

# Base directory is the folder containing annotation.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the target subdirectories (siblings of annotation.py)
BLINK_DIR = os.path.join(BASE_DIR, "blinking")
JAW_DIR   = os.path.join(BASE_DIR, "jaw_clench")
BITE_DIR  = os.path.join(BASE_DIR, "biting")

# Create the subdirectories if they do not exist
for directory in [BLINK_DIR, JAW_DIR, BITE_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_next_filename(directory, prefix):
    """
    Look in the directory for files matching the pattern prefix_XX.csv,
    then return a new filename with the number incremented.
    """
    pattern = re.compile(rf"{re.escape(prefix)}_(\d+)\.csv$")
    max_num = 0
    for file in os.listdir(directory):
        match = pattern.match(file)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    new_num = max_num + 1
    new_filename = f"{prefix}_{new_num:02d}.csv"
    return new_filename

def call_muselsl_stream():
    # Start the Muse stream
    subprocess.call(["muselsl", "stream"])

def call_muselsl_view():
    # View the Muse data
    subprocess.call(["muselsl", "view"])

def record_with_duration(directory, prefix, cmd_duration=10, effective_duration=5):
    """
    Generates the next filename using the given prefix, then calls muselsl to record.
    The command is given a duration (cmd_duration) so that muselsl has enough time to connect.
    Meanwhile, this function polls the CSV file until data appears, and then starts a countdown
    for the effective_duration (the actual time of valid data recording).
    """
    filename = get_next_filename(directory, prefix)
    # Prepare the command. Using a relative filename so that it saves in 'directory'
    cmd = [
        "muselsl", "record",
        "--filename", f".\\{filename}",
        "--duration", str(cmd_duration)
    ]
    print(f"\nStarting muselsl recording (requested duration {cmd_duration} s) to: {os.path.join(directory, filename)}")

    # Start the muselsl record process in the specified directory
    proc = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait until the file exists and reaches a minimum size (indicating that data has started)
    file_path = os.path.join(directory, filename)
    poll_timeout = 10  # seconds
    poll_interval = 0.1  # seconds
    start_record_time = None
    elapsed_poll = 0
    min_file_size = 200  # bytes; adjust as needed
    while elapsed_poll < poll_timeout:
        if os.path.exists(file_path) and os.path.getsize(file_path) > min_file_size:
            start_record_time = time.time()
            print("Data started being recorded.")
            break
        time.sleep(poll_interval)
        elapsed_poll += poll_interval

    if start_record_time is None:
        print("Warning: Data did not start recording within the timeout.")
        start_record_time = time.time()  # fallback
    
    # Now, perform a countdown for the effective duration (actual data capture time)
    print(f"Counting down {effective_duration} seconds of valid data capture:")
    for sec in range(1, effective_duration + 1):
        print(f"{sec} second(s) elapsed")
        time.sleep(1)
    
    # Optionally, wait until the muselsl process ends (it should terminate after cmd_duration seconds)
    stdout, stderr = proc.communicate()
    print("\nmuselsl stdout:")
    print(stdout)
    print("muselsl stderr:")
    print(stderr)
    
    print(f"Recording finished. The file should be saved at: {file_path}\n")

def record_blink():
    threading.Thread(target=record_with_duration, args=(BLINK_DIR, "blink", 10, 5), daemon=True).start()

def record_jaw():
    threading.Thread(target=record_with_duration, args=(JAW_DIR, "jaw", 10, 5), daemon=True).start()

def record_bite():
    threading.Thread(target=record_with_duration, args=(BITE_DIR, "bite", 10, 5), daemon=True).start()

def start_stream():
    threading.Thread(target=call_muselsl_stream, daemon=True).start()

def start_view():
    threading.Thread(target=call_muselsl_view, daemon=True).start()

# Set up the Tkinter window
root = tk.Tk()
root.title("Muse Command Launcher with Accurate Countdown")

# Button to start the Muse stream
stream_button = tk.Button(root, text="Start Muse Stream", command=start_stream, padx=20, pady=10)
stream_button.pack(padx=20, pady=10)

# Button to view Muse data
view_button = tk.Button(root, text="View Muse Data", command=start_view, padx=20, pady=10)
view_button.pack(padx=20, pady=10)

# Button to record Blink data
blink_record_button = tk.Button(root, text="Record Blink", command=record_blink, padx=20, pady=10)
blink_record_button.pack(padx=20, pady=10)

# Button to record Jaw Clench data
jaw_record_button = tk.Button(root, text="Record Jaw Clench", command=record_jaw, padx=20, pady=10)
jaw_record_button.pack(padx=20, pady=10)

# Button to record Bite Down data
bite_record_button = tk.Button(root, text="Record Bite Down", command=record_bite, padx=20, pady=10)
bite_record_button.pack(padx=20, pady=10)

# Start the Tkinter event loop
root.mainloop()
