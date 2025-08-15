import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os

def parse_action(filename):
    """
    Return 'blink', 'jaw', 'bite', or 'brow' by checking substrings in the filename.
    Defaults to 'blink' if no match is found.
    """
    filename_lower = filename.lower()
    if "jaw" in filename_lower:
        return "jaw"
    elif "bite" in filename_lower:
        return "bite"
    elif "brow" in filename_lower or "eyebrow" in filename_lower:
        return "brow"
    elif "blink" in filename_lower:
        return "blink"
    else:
        return "blink"

def get_base_dir(action):
    """
    Return the base directory for the given action.
    """
    if action == "blink":
        return r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking"
    elif action == "jaw":
        return r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/jaw_clench"
    elif action == "bite":
        return r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/biting"
    elif action == "brow":
        return r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/eyebrow"
    else:
        raise ValueError(f"Unsupported action: {action}")

def get_detection_params(action):
    """
    Return a human-readable action label for the given action.
    """
    if action == "blink":
        return "Blink"
    elif action == "jaw":
        return "Jaw Clench"
    elif action == "bite":
        return "Biting"
    elif action == "brow":
        return "Eyebrow Raise"
    else:
        raise ValueError(f"Unsupported action: {action}")

def plot_eeg_with_action(csv_file_path, json_file_path, action_label_name):
    # Load the CSV file.
    df = pd.read_csv(csv_file_path)
    
    # Use the 'timestamp' or 'timestamps' column as the x-axis if available;
    # otherwise, use the row index.
    if "timestamp" in df.columns:
        time_axis = df["timestamp"].values - df["timestamp"].iloc[0]
    elif "timestamps" in df.columns:
        time_axis = df["timestamps"].values - df["timestamps"].iloc[0]
    else:
        time_axis = np.arange(len(df))
    
    # Load the annotation file.
    with open(json_file_path, "r") as f:
        annotation = json.load(f)
    
    # Get the numeric label and precomputed event region from the annotation.
    # Here, -1 indicates no event detected.
    label = annotation.get("actionLabel", -1)
    region = annotation.get("actionRegion", None)
    
    if label == -1:
        print(f"No {action_label_name} event detected in the annotation.")
    elif region is None:
        print(f"{action_label_name} event detected but no region was found in the annotation.")
    
    # Define channels to plot.
    channels = ["TP9", "AF7", "AF8", "TP10"]
    
    # Create subplots.
    fig, axs = plt.subplots(len(channels), 1, sharex=True, figsize=(12, 10))
    
    for ax, channel in zip(axs, channels):
        sig = df[channel].values
        ax.plot(time_axis, sig, label=channel, color="blue")
        # If an event is detected and a region exists, highlight the region.
        if label != -1 and region is not None:
            start_idx, end_idx = region
            ax.axvspan(time_axis[start_idx], time_axis[end_idx], color="red", alpha=0.3,
                       label=f"{action_label_name} Region")
        ax.set_ylabel("Amplitude")
        ax.legend(loc="upper right")
    
    axs[-1].set_xlabel("Time (s)")
    xticks = np.arange(0, 3, 0.5)
    for ax in axs:
        ax.set_xticks(xticks)
        ax.set_xlim(0, 2.5)
    
    fig.suptitle(f"EEG Signals with Annotated {action_label_name} Region")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def main():
    parser = argparse.ArgumentParser(
        description="Visualize EEG data with annotated event regions based solely on the JSON label."
    )
    parser.add_argument("basename", nargs="?", default=None,
                        help="Base name of the file (e.g., jaw_01) for interactive plotting.")
    parser.add_argument("--save", choices=["blink", "jaw", "bite", "brow"],
                        help="Batch save plots for all files in the corresponding folder (e.g., --save jaw or --save brow)")
    args = parser.parse_args()
    
    if args.save:
        # Batch saving mode: action is provided via --save.
        action = args.save
        base_dir = get_base_dir(action)
        processed_dir = os.path.join(base_dir, "processed")
        data_dir = os.path.join(processed_dir, "data")
        annotations_dir = os.path.join(processed_dir, "annotations")
        # For plots, use the plots folder under the base directory.
        plots_dir = os.path.join(base_dir, "plots", "labelled_plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        action_label_name = get_detection_params(action)
        
        for file in os.listdir(data_dir):
            if file.endswith(".csv"):
                base_name = os.path.splitext(file)[0]
                csv_file_path = os.path.join(data_dir, file)
                json_file_path = os.path.join(annotations_dir, f"{base_name}.json")
                if os.path.exists(json_file_path):
                    fig = plot_eeg_with_action(csv_file_path, json_file_path, action_label_name)
                    save_path = os.path.join(plots_dir, f"{base_name}.png")
                    fig.savefig(save_path)
                    plt.close(fig)
                    print(f"Saved plot for {base_name} to {save_path}")
                else:
                    print(f"No annotation found for {base_name}. Skipping.")
    
    elif args.basename:
        # Interactive mode: infer action from the basename.
        basename = args.basename
        if basename.endswith(".csv"):
            basename = basename[:-4]
        action = parse_action(basename)
        base_dir = get_base_dir(action)
        processed_dir = os.path.join(base_dir, "processed")
        data_dir = os.path.join(processed_dir, "data")
        annotations_dir = os.path.join(processed_dir, "annotations")
        csv_file_path = os.path.join(data_dir, f"{basename}.csv")
        json_file_path = os.path.join(annotations_dir, f"{basename}.json")
        if not os.path.exists(csv_file_path) or not os.path.exists(json_file_path):
            print(f"File '{basename}' not found in:\nData: {data_dir}\nAnnotations: {annotations_dir}")
        else:
            action_label_name = get_detection_params(action)
            fig = plot_eeg_with_action(csv_file_path, json_file_path, action_label_name)
            plt.show()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
