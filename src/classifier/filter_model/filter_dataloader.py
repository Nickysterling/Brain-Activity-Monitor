import os
import numpy as np
import pandas as pd
import mne
from mne.io import RawArray
from mne import create_info


def dataloader():

    # Directory where CSV data files are stored
    JAW_DATA_DIR = "project_directory/data/jaw_clench/raw"
    BITING_DATA_DIR = "project_directory/data/biting/raw"
    BLINKING_DATA_DIR = "project_directory/data/blinking/raw"
    EYEBROW_DATA_DIR = "project_directory/data/eyebrow/raw"

    # Define actions (directories)
    actions = [JAW_DATA_DIR, BITING_DATA_DIR, BLINKING_DATA_DIR, EYEBROW_DATA_DIR]

    # Storage for dataset
    all_data = []
    all_labels = []

    # Loop through all CSV files
    for actionSet in actions:
        for file in os.listdir(actionSet):
            action_label = file.split("_")[0]  # Extract label from filename

            # Read CSV file
            df = pd.read_csv(os.path.join(actionSet, file))

            # Extract timestamps and EEG channel data
            timestamps = df.iloc[:, 0].values
            eeg_data = df.iloc[:, 1:].to_numpy().T  # Transpose for MNE format

            # Estimate Sampling Frequency (sfreq)
            time_diffs = np.diff(timestamps)
            sfreq = 1 / np.mean(time_diffs)

            # Define channel names and types
            ch_names = df.columns[1:].tolist()
            ch_types = ["eeg"] * len(ch_names)

            # Create MNE Info and RawArray
            info = create_info(ch_names, sfreq, ch_types)
            raw = RawArray(eeg_data, info)

            # Store data and labels
            all_data.append(raw.get_data())
            all_labels.append(action_label)

    # Find the minimum number of timepoints across all samples
    min_timepoints = min(sample.shape[1] for sample in all_data)
    print(f"Using {min_timepoints} timepoints for all samples.")

    # Standardize data lengths
    X = standardize_length(all_data, min_timepoints)
    y = np.array(all_labels)

    print(f"Dataset Loaded: {X.shape[0]} samples, {X.shape[1]} channels, {X.shape[2]} timepoints per sample.")
    print(f"Actions: {set(y)}")

    return X, y, info

def standardize_length(data_list, target_length):
    """Trim or pad EEG data to ensure all samples have the same number of timepoints."""
    standardized_data = []
    for sample in data_list:
        n_channels, n_timepoints = sample.shape
        if n_timepoints > target_length:
            standardized_sample = sample[:, :target_length]
        else:
            pad_width = target_length - n_timepoints
            standardized_sample = np.pad(sample, ((0, 0), (0, pad_width)), mode="constant")
        standardized_data.append(standardized_sample)
    return np.array(standardized_data)