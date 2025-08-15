import os
import re
import threading
import time
from pylsl import resolve_byprop, StreamInlet

# Define the buffer directory (adjust this path as needed)
current_dir = os.path.dirname(os.path.abspath(__file__))
BUFFER_DIR = os.path.join(current_dir, "..", "classifier", "buffer")
BUFFER_DIR = os.path.normpath(BUFFER_DIR)

def get_next_filename(directory, prefix):
    """
    Returns a new filename in the given directory with an incremented index.
    Example: If files like "buffer_01.csv" exist, this returns "buffer_02.csv".
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

def record_sample(directory, prefix, target_samples=640, sample_rate=256, log_callback=None):
    """
    Resolves an EEG stream via pylsl, then records exactly target_samples of raw data.
    The data is saved as a CSV file in the given directory.
    Log messages (such as progress updates) are sent to log_callback if provided.
    
    By default, target_samples is set to 640 (i.e. 2.5 seconds at 256 Hz).
    """
    os.makedirs(directory, exist_ok=True)
    filename = get_next_filename(directory, prefix)
    file_path = os.path.join(directory, filename)
    
    streams = resolve_byprop('type', 'EEG', minimum=1, timeout=1.0)
    if not streams:
        if log_callback:
            log_callback("No EEG stream found!")
        else:
            print("No EEG stream found!")
        return
    inlet = StreamInlet(streams[0])
    
    data_samples = []
    timestamps = []
    start_ts = None
    log_interval = int(sample_rate * 0.5)  # log every 0.5 seconds (128 samples at 256 Hz)
    
    while len(data_samples) < target_samples:
        sample, ts = inlet.pull_sample(timeout=0.0)
        if sample is None:
            time.sleep(0.005)
            continue
        if start_ts is None:
            start_ts = ts

        data_samples.append(sample)
        timestamps.append(ts)
        
        # Log progress every 0.5 seconds (i.e. every 128 samples)
        if len(data_samples) % log_interval == 0:
            seconds = len(data_samples) / sample_rate
            if log_callback:
                log_callback(f"{seconds:.1f} seconds reached")
            else:
                print(f"{seconds:.1f} seconds reached")
    
    if log_callback:
        log_callback("Recording ended.")
    else:
        print("Recording ended.")
    
    if log_callback:
        log_callback(f"Collected {len(data_samples)} samples over {timestamps[-1] - start_ts:.3f} seconds.\n")
    else:
        print(f"Collected {len(data_samples)} samples over {timestamps[-1] - start_ts:.3f} seconds.")
        
    with open(file_path, 'w') as f:
        header = "timestamps,TP9,AF7,AF8,TP10,Right AUX"
        f.write(header + "\n")
        for ts, sample in zip(timestamps, data_samples):
            sample_str = ",".join(map(str, sample))
            f.write(f"{ts},{sample_str}\n")

def record_raw_snippet(log_callback=None):
    """
    Spawns a thread that records exactly 640 samples of raw EEG data.
    Data is saved to the BUFFER_DIR.
    The log_callback function is used for sending status messages.
    """
    threading.Thread(
        target=record_sample,
        args=(BUFFER_DIR, "buffer", 640, 256, log_callback),
        daemon=True
    ).start()
