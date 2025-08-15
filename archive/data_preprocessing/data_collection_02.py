#!/usr/bin/env python
"""
Real-time EEG Recording with Manual Labeling from Muse Headset

Features:
1. Streams EEG data from a Muse headset using pylsl.
2. Records each sample with a user-specified action label.
   - In a separate thread, you can type a new label (e.g., 'blink' or 'neutral') at any time.
   - Type 'q' to quit recording.
3. Outputs a CSV file where each row includes:
    - timestamp,
    - EEG channel values (columns ch1, ch2, ...),
    - and the current actionLabel.
4. (Optional) Post-processes the recorded data:
    - Filters the data (0.5–5 Hz) using MNE.
    - Applies a simple peak detection to detect blinks.
    - Optionally plots the filtered signal with detected blink peaks.
    
Usage:
    python realtime_labeling.py output_file.csv --duration 30 --postprocess --plot

If --duration is set to 0, the script will run indefinitely until you type 'q' to quit.
"""

import argparse
import threading
import time
import pandas as pd
import numpy as np
import mne
import matplotlib.pyplot as plt
from pylsl import StreamInlet, resolve_streams
from scipy.signal import find_peaks
import os

# Global variables for real-time labeling control
current_label = "neutral"
stop_recording = False
output_directory = "/blinking"

def label_listener():
    """
    Listen for user input to update the action label.
    Type a new label (e.g., 'blink', 'neutral') and press Enter to update.
    Type 'q' to quit recording.
    """
    global current_label, stop_recording
    print("Labeling Instructions:")
    print(" - Type a new label (e.g., 'blink', 'neutral') and press Enter to update the current label.")
    print(" - Type 'q' and press Enter to stop recording.")
    while not stop_recording:
        new_label = input()
        if new_label.lower() == 'q':
            stop_recording = True
            print("Stopping recording...")
        else:
            current_label = new_label
            print(f"Current label updated to: {current_label}")

def post_process_blink_detection(df, channel_name='ch1', l_freq=0.5, h_freq=5.0, min_distance=50):
    """
    Post-process the recorded data using MNE for filtering and blink detection.
    
    Args:
        df: DataFrame containing recorded data with 'timestamp' and EEG channel columns.
        channel_name: The column to use for blink detection (default 'ch1').
        l_freq: Low cutoff frequency for bandpass filtering.
        h_freq: High cutoff frequency for bandpass filtering.
        min_distance: Minimum samples between detected peaks.
    
    Returns:
        peaks: Indices of detected blinks.
        filtered_signal: The filtered EEG signal.
        times: Time vector corresponding to the signal.
    """
    # Estimate sampling frequency from the timestamp differences
    sfreq = 1.0 / np.mean(np.diff(df['timestamp']))
    data = df[channel_name].values[np.newaxis, :]  # shape: (1, n_samples)
    info = mne.create_info(ch_names=[channel_name], sfreq=sfreq, ch_types=['eeg'])
    raw = mne.io.RawArray(data, info, verbose=False)
    
    # Filter the data in the blink frequency range
    raw.filter(l_freq, h_freq, picks=[channel_name], verbose=False)
    filtered_signal = raw.get_data(picks=channel_name)[0]
    
    # Detect peaks: threshold is mean + 3*std
    threshold = np.mean(filtered_signal) + 3 * np.std(filtered_signal)
    peaks, _ = find_peaks(filtered_signal, height=threshold, distance=min_distance)
    return peaks, filtered_signal, raw.times

def main():
    parser = argparse.ArgumentParser(
        description="Real-time EEG recording with manual labeling from Muse headset."
    )
    parser.add_argument("output_file", help="Path to the output CSV file for labeled data.")
    parser.add_argument("--duration", type=float, default=30.0,
                        help="Recording duration in seconds (set to 0 for indefinite).")
    parser.add_argument("--postprocess", action="store_true",
                        help="After recording, run blink detection post-processing on channel 'ch1'.")
    parser.add_argument("--plot", action="store_true",
                        help="Plot the filtered signal with detected blink peaks (requires --postprocess).")
    args = parser.parse_args()
    
    global stop_recording, current_label
    stop_recording = False
    current_label = "neutral"
    
    # Start the labeling listener thread
    label_thread = threading.Thread(target=label_listener, daemon=True)
    label_thread.start()
    
    print("Resolving EEG stream... (Ensure your Muse headset is streaming)")
    streams = resolve_streams(10)
    if not streams:
        print("No EEG stream found. Exiting.")
        return
    inlet = StreamInlet(streams[0])
    print("EEG stream found. Starting real-time recording...")
    
    data_records = []
    start_time = time.time()
    
    # Main loop: continuously pull samples from the LSL stream
    while not stop_recording:
        sample, timestamp = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue  # No sample received in the allotted time
        record = {"timestamp": timestamp, "actionLabel": current_label}
        for i, value in enumerate(sample):
            record[f"ch{i+1}"] = value
        data_records.append(record)
        
        # Stop after the specified duration if duration > 0
        if args.duration > 0 and (time.time() - start_time) >= args.duration:
            stop_recording = True
    
    print("Recording stopped. Saving data...")
    df = pd.DataFrame(data_records)
    df.to_csv("output_file", index=False)
    print(f"Data saved to {args.output_file}.")
    
    # Optional post-processing: blink detection using channel 'ch1'
    if args.postprocess:
        peaks, filtered_signal, times = post_process_blink_detection(df, channel_name='ch1')
        print(f"Post-processing: Detected {len(peaks)} blink(s) on channel 'ch1'.")
        
        if args.plot:
            plt.figure(figsize=(10, 4))
            plt.plot(times, filtered_signal, label='Filtered EEG Signal')
            plt.plot(times[peaks], filtered_signal[peaks], "x", label="Detected Blinks", color="red")
            plt.xlabel("Time (s)")
            plt.ylabel("Amplitude")
            plt.title("Filtered EEG Signal with Detected Blink Peaks")
            plt.legend()
            plt.tight_layout()
            plt.show()

if __name__ == "__main__":
    main()