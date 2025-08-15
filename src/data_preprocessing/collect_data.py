import os
import re
import threading
import time
import tkinter as tk
from pylsl import resolve_byprop, StreamInlet

# Define your project's data directory explicitly (change as needed)
PROJECT_DATA_DIR = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data"

# Define the target subdirectories as specified:
BLINK_DIR = os.path.join(PROJECT_DATA_DIR, "blinking", "raw")
JAW_DIR   = os.path.join(PROJECT_DATA_DIR, "jaw_clench", "raw")
BITE_DIR  = os.path.join(PROJECT_DATA_DIR, "biting", "raw")
EYEBROW_DIR = os.path.join(PROJECT_DATA_DIR, "eyebrow", "raw")

# Create the subdirectories if they do not exist
for directory in [BLINK_DIR, JAW_DIR, BITE_DIR, EYEBROW_DIR]:
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
    return f"{prefix}_{new_num:02d}.csv"

def record_sample(directory, prefix, sample_duration=2.5):
    """
    Uses pylsl to resolve an EEG stream via resolve_byprop.
    It creates an inlet from the first available EEG stream and then
    records data until the difference between the first sample's timestamp
    and the current sample's timestamp is at least sample_duration seconds.
    A countdown is printed at every 0.5-second interval.
    The samples (returned as floats) and their timestamps are saved to a CSV file.
    """
    filename = get_next_filename(directory, prefix)
    file_path = os.path.join(directory, filename)
    
    print("Resolving EEG stream...")
    streams = resolve_byprop('type', 'EEG', minimum=1, timeout=1.0)
    if not streams:
        print("No EEG stream found!")
        return
    inlet = StreamInlet(streams[0])
    
    print(f"Recording data until exactly {sample_duration} seconds of EEG data are captured...")
    data_samples = []
    timestamps = []
    start_ts = None
    next_threshold = 0.5  # next countdown marker in seconds
    
    # Pull samples until the timestamp difference reaches sample_duration
    while True:
        sample, ts = inlet.pull_sample(timeout=0.0)
        if sample is None:
            time.sleep(0.005)
            continue
        if start_ts is None:
            start_ts = ts
            print("Recording started.")
        data_samples.append(sample)
        timestamps.append(ts)
        
        elapsed = ts - start_ts
        # Print countdown messages at every 0.5-second milestone.
        if elapsed >= next_threshold:
            print(f"{next_threshold:.1f} seconds reached")
            next_threshold += 0.5
        
        if elapsed >= sample_duration:
            print("Recording ended.")
            break

    print(f"Collected {len(data_samples)} samples over {timestamps[-1] - start_ts:.3f} seconds.")
    
    # Save the recorded data to a CSV file.
    with open(file_path, 'w') as f:
        # Write the custom header.
        header = "timestamps,TP9,AF7,AF8,TP10,Right AUX"
        f.write(header + "\n")
        for ts, sample in zip(timestamps, data_samples):
            sample_str = ",".join(map(str, sample))
            f.write(f"{ts},{sample_str}\n")
    
    print(f"Data saved to: {file_path}")

def record_blink():
    threading.Thread(target=record_sample, args=(BLINK_DIR, "blink", 2.5), daemon=True).start()

def record_jaw():
    threading.Thread(target=record_sample, args=(JAW_DIR, "jaw", 2.5), daemon=True).start()

def record_bite():
    threading.Thread(target=record_sample, args=(BITE_DIR, "bite", 2.5), daemon=True).start()

def record_eyebrow():
    threading.Thread(target=record_sample, args=(EYEBROW_DIR, "eyebrow", 2.5), daemon=True).start()

# Set up the Tkinter window
root = tk.Tk()
root.title("Muse Data Recorder")

blink_button = tk.Button(root, text="Record Blink", command=record_blink, padx=20, pady=10)
blink_button.pack(padx=20, pady=10)

jaw_button = tk.Button(root, text="Record Jaw Clench", command=record_jaw, padx=20, pady=10)
jaw_button.pack(padx=20, pady=10)

bite_button = tk.Button(root, text="Record Bite Down", command=record_bite, padx=20, pady=10)
bite_button.pack(padx=20, pady=10)

eyebrow_button = tk.Button(root, text="Record Eyebrow Raise", command=record_eyebrow, padx=20, pady=10)
eyebrow_button.pack(padx=20, pady=10)

root.mainloop()