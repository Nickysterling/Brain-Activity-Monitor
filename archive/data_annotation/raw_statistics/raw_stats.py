import os
import random
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from glob import glob

# List of directories containing the raw CSV files
data_dirs = [
    "project_directory/data/jaw_clench/raw",
    "project_directory/data/biting/raw",
    "project_directory/data/blinking/raw",
    "project_directory/data/eyebrow/raw"
]

# Define snippet length (you can adjust as needed)
snippet_length = int(256 * 2.5)  # e.g., 640 timepoints

# Function to compute statistics from an EEG snippet (2D array: channels x timepoints)
def compute_stats(eeg_snippet):
    means = np.mean(eeg_snippet, axis=1)
    variances = np.var(eeg_snippet, axis=1)
    skews = skew(eeg_snippet, axis=1, nan_policy='omit')
    kurtoses = kurtosis(eeg_snippet, axis=1, nan_policy='omit')
    
    stats = {
        "avg_mean": np.mean(means),
        "avg_variance": np.mean(variances),
        "avg_skew": np.nanmean(skews),
        "avg_kurtosis": np.nanmean(kurtoses)
    }
    return stats

# List to collect statistics for all files
all_stats = []

# Loop through each data directory and each file within
for data_dir in data_dirs:
    # Use glob to pick up CSV files (adjust pattern if needed)
    file_pattern = os.path.join(data_dir, "*.csv")
    for file_path in glob(file_pattern):
        try:
            df = pd.read_csv(file_path)
            # Assume first column is timestamps; remaining columns are EEG channels.
            eeg_data = df.iloc[:, 1:].to_numpy().T  # Shape: (n_channels, n_timepoints)
            n_channels, n_timepoints = eeg_data.shape
            
            # Extract a snippet (if signal is long enough, else use full signal)
            if n_timepoints > snippet_length:
                start_idx = random.randint(0, n_timepoints - snippet_length)
                snippet = eeg_data[:, start_idx:start_idx + snippet_length]
            else:
                snippet = eeg_data
            
            # Compute statistical features from the snippet
            stats = compute_stats(snippet)
            
            # Optionally, add the file's directory info or action label
            # Here, we infer action from directory name by splitting the path.
            action = os.path.basename(os.path.normpath(data_dir))
            
            stats["file"] = os.path.basename(file_path)
            stats["action"] = action
            stats["n_channels"] = n_channels
            stats["n_timepoints"] = n_timepoints
            all_stats.append(stats)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# Convert the collected stats to a DataFrame for further analysis
stats_df = pd.DataFrame(all_stats)

# Print the summary statistics DataFrame
print(stats_df)

# Optionally, save to CSV for further exploration
stats_df.to_csv("raw_stats.csv", index=False)
