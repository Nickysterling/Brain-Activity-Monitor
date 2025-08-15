import os
import time
import json
import argparse
import pandas as pd
import numpy as np

def moving_average(data, window_size=10):
    return np.convolve(data, np.ones(window_size) / window_size, mode="same")

def detect_action(signal, threshold, window_size):
    """
    Generic action detector.
    
    Applies a moving average filter to the signal and returns 1 if
    the maximum absolute value exceeds the threshold; otherwise 0.
    """
    smoothed = moving_average(signal, window_size)
    return int(np.max(np.abs(smoothed)) > threshold)

def detect_action_region(signal, threshold, window_size):
    """
    Find the start and end indices where the smoothed signal exceeds the threshold.
    Returns a tuple (start_idx, end_idx) or None if no region is found.
    """
    smoothed = moving_average(signal, window_size)
    indices = np.where(np.abs(smoothed) > threshold)[0]
    if len(indices) == 0:
        return None
    return indices[0], indices[-1]

def process_new_files(buffer_dir, processed_dir, detection_function, channel, threshold, window_size, action_code):
    # Process each CSV file in the buffer directory once.
    files = [f for f in os.listdir(buffer_dir) if f.endswith(".csv")]
    for file in files:
        file_path = os.path.join(buffer_dir, file)
        # Load EEG data.
        df = pd.read_csv(file_path)
        # Get binary detection result.
        detection = detection_function(df[channel].values, threshold, window_size)
        
        if detection == 1:
            # Use the provided action code if an event is detected.
            action_label = action_code
            region = detect_action_region(df[channel].values, threshold, window_size)
        else:
            # Set to -1 if no event is detected.
            action_label = -1
            region = None

        # Structure data for training, including the event region.
        processed_data = {
            "actionLabel": action_label,
            "actionRegion": region,
            "museHeadsetData": df.to_dict(orient="list")
        }

        # Save processed data to JSON using a custom encoder to handle NumPy types.
        annotation_file = os.path.join(processed_dir, file.replace(".csv", ".json"))
        with open(annotation_file, "w") as out_file:
            json.dump(processed_data, out_file, default=lambda o: int(o) if isinstance(o, np.integer) else o)
        print(f"Labeled file '{file}' with actionLabel {action_label} and region {region}")

    print("Finished processing all files in the buffer directory.")

def main():
    parser = argparse.ArgumentParser(description="EEG Action Detection")
    parser.add_argument("--action", choices=["blink", "jaw", "bite", "brow"], required=True,
                        help="Action to detect: 'blink' for blinking, 'jaw' for jaw clench, 'bite' for biting, 'brow' for eyebrow raises.")
    parser.add_argument("--threshold", type=float,
                        help="Detection threshold (overrides default for the chosen action)")
    parser.add_argument("--window_size", type=int,
                        help="Window size for moving average (overrides default for the chosen action)")
    args = parser.parse_args()

    # Define the mapping for action labels.
    # biting -> 0, blinking -> 1, brow -> 2, jaw -> 3.
    action_mapping = {"bite": 0, "blink": 1, "brow": 2, "jaw": 3}

    # Set directories, channel, and default parameters based on action.
    if args.action == "blink":
        buffer_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking/processed/data"
        processed_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking/processed/annotations"
        channel = "TP10"
        default_threshold = 30
        default_window_size = 10
    elif args.action == "jaw":
        buffer_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/jaw_clench/processed/data"
        processed_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/jaw_clench/processed/annotations"
        channel = "TP10"
        default_threshold = 2.5
        default_window_size = 11
    elif args.action == "bite":
        buffer_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/biting/processed/data"
        processed_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/biting/processed/annotations"
        channel = "TP10"
        default_threshold = 5.5
        default_window_size = 11
    elif args.action == "brow":
        buffer_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/eyebrow/processed/data"
        processed_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/eyebrow/processed/annotations"
        channel = "AF8"
        default_threshold = 3.75
        default_window_size = 11

    # Override defaults if parameters are provided.
    threshold = args.threshold if args.threshold is not None else default_threshold
    window_size = args.window_size if args.window_size is not None else default_window_size

    os.makedirs(processed_dir, exist_ok=True)
    # Pass the corresponding action code from the mapping.
    process_new_files(buffer_dir, processed_dir, detect_action, channel, threshold, window_size, action_mapping[args.action])

if __name__ == "__main__":
    main()
