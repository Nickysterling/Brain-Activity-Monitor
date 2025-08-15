import pandas as pd
import numpy as np
import mne
import matplotlib.pyplot as plt

# --- Step 1. Load CSV Data ---
csv_file = "project_directory/data/test/filtered_output.csv"
df = pd.read_csv(csv_file)
df["timestamps"] = df["timestamps"] - df["timestamps"].iloc[0]

# Define the EEG channels (adjust these names to match your CSV)
channels = ["TP9", "AF7", "AF8", "TP10", "Right AUX"]

# --- Step 2. Create MNE Raw Object ---
# Convert EEG data (exclude timestamps) to a NumPy array with shape (n_channels, n_samples)
data = df[channels].to_numpy().T

# Set your sampling frequency (adjust if necessary)
sfreq = 256.0

# Create the MNE info object. Here we assume all channels are EEG.
info = mne.create_info(ch_names=channels, sfreq=sfreq, ch_types=["eeg"] * len(channels))

# Create the Raw object
raw = mne.io.RawArray(data, info)

# --- Define the Five Brainwave Bands ---
bands = {
    "Delta": (0.5, 4),
    "Theta": (4, 8),
    "Alpha": (8, 13),
    "Beta":  (13, 30),
    "Gamma": (30, 50)
}

# --- Process and Plot for Each EEG Channel ---
for channel in channels:
    # Pick the current channel data from the raw object
    raw_channel = raw.copy().pick_channels([channel])
    
    # Create a new figure for the channel with one subplot per band
    fig, axes = plt.subplots(len(bands), 1, figsize=(10, 10), sharex=True)
    
    for ax, (band_name, (l_freq, h_freq)) in zip(axes, bands.items()):
        # Copy the channel and apply the bandpass filter for the current band
        raw_band = raw_channel.copy().filter(l_freq=l_freq, h_freq=h_freq, fir_design="firwin", verbose=False)
        
        # Retrieve the filtered data and corresponding time points
        data_band, times = raw_band[:]
        
        # Plot the first (and only) channel's data for this band
        ax.plot(times, data_band[0], color="C0")
        ax.set_ylabel(band_name)
        ax.set_title(f"{band_name} ({l_freq}-{h_freq} Hz)")
        ax.grid(True)
    
    # Label the x-axis on the bottom subplot
    axes[-1].set_xlabel("Time (s)")
    
    # Set a super title for the figure indicating which channel is displayed
    plt.suptitle(f"EEG Channel {channel} Filtered into 5 Brainwave Bands", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
