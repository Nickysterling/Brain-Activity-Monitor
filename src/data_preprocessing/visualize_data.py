import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

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
        # Default to 'blink' if no match is found.
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

def plot_eeg_comparison(raw_file_path, processed_file_path, channels, plot_title="EEG Channels Comparison"):
    # Load the CSV files.
    raw_df = pd.read_csv(raw_file_path)
    processed_df = pd.read_csv(processed_file_path)
    
    # Subtract the first timestamp so the time axis starts at 0.
    raw_df["timestamps"] = raw_df["timestamps"] - raw_df["timestamps"].iloc[0]
    processed_df["timestamps"] = processed_df["timestamps"] - processed_df["timestamps"].iloc[0]
    
    # Create side-by-side subplots.
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    
    # Plot raw data.
    for ch in channels:
        axs[0].plot(raw_df["timestamps"], raw_df[ch], label=ch)
    axs[0].set_title("Raw Data")
    axs[0].set_xlabel("Time")
    axs[0].set_ylabel("Amplitude")
    axs[0].legend()
    
    # Plot processed data.
    for ch in channels:
        axs[1].plot(processed_df["timestamps"], processed_df[ch], label=ch)
    axs[1].set_title("Processed Data")
    axs[1].set_xlabel("Time")
    axs[1].legend()
    
    fig.suptitle(plot_title)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def main():
    parser = argparse.ArgumentParser(
        description="Plot Raw and Processed EEG channels side by side, or batch save plots for an entire folder."
    )
    parser.add_argument("filename", nargs="?", default=None,
                        help="If provided (e.g., 'jaw_01'), the script will guess the folder (jaw, bite, blink, or brow) and plot that file interactively.")
    parser.add_argument("--save", choices=["blink", "jaw", "bite", "brow"],
                        help="Batch save plots for all files in the specified folder (e.g. '--save jaw' or '--save brow').")
    args = parser.parse_args()

    # Disallow combining single-file plotting with batch saving in the same command.
    if args.filename and args.save:
        parser.error("Cannot specify both a filename and --save in the same command. Choose one.")

    # If --save is provided, do batch saving for the specified folder.
    if args.save:
        action = args.save
        base_dir = get_base_dir(action)
        raw_dir = os.path.join(base_dir, "raw")
        processed_dir = os.path.join(base_dir, "processed", "data")
        plots_dir = os.path.join(base_dir, "plots", "processed_plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        channels = ["TP9", "AF7", "AF8", "TP10", "Right AUX"]
        
        csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
        if not csv_files:
            print(f"No CSV files found in {raw_dir}.")
            return
        
        for filename in csv_files:
            raw_path = os.path.join(raw_dir, filename)
            processed_path = os.path.join(processed_dir, filename)
            if os.path.exists(processed_path):
                base_name = os.path.splitext(filename)[0]
                title = f"EEG Channels Comparison: {base_name}"
                fig = plot_eeg_comparison(raw_path, processed_path, channels, plot_title=title)
                save_path = os.path.join(plots_dir, base_name + ".png")
                fig.savefig(save_path)
                plt.close(fig)
                print(f"Saved plot for {filename} to {save_path}")
            else:
                print(f"Processed file not found for {filename}. Skipping.")
    
    # If a filename is provided (and not using --save), plot that single file interactively.
    elif args.filename:
        # Ensure it has .csv extension
        filename = args.filename
        if not filename.endswith(".csv"):
            filename += ".csv"
        
        action = parse_action(filename)
        base_dir = get_base_dir(action)
        raw_dir = os.path.join(base_dir, "raw")
        processed_dir = os.path.join(base_dir, "processed", "data")
        
        raw_file_path = os.path.join(raw_dir, filename)
        processed_file_path = os.path.join(processed_dir, filename)
        
        if not os.path.exists(raw_file_path) or not os.path.exists(processed_file_path):
            print(f"File '{filename}' not found in:\n  {raw_dir}\n  or\n  {processed_dir}")
            return
        
        channels = ["TP9", "AF7", "AF8", "TP10", "Right AUX"]
        fig = plot_eeg_comparison(raw_file_path, processed_file_path, channels,
                                  plot_title=f"EEG Channels Comparison: {filename}")
        plt.show()
    
    else:
        # No filename and no --save => print usage.
        parser.print_help()

if __name__ == "__main__":
    main()
