import matplotlib.pyplot as plt
import numpy as np
import mne
import os

# Get the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Move up to the project root (../project_directory)
project_root = os.path.abspath(os.path.join(script_dir, ".."))

# Construct absolute paths
input_file = os.path.join(project_root, "data", "processed", "cleaned_data.csv")
output_folder = os.path.join(project_root, "output")

print(f"Looking for cleaned data at: {input_file}")  # Debugging
print(f"Saving output to: {output_folder}")

# Check if cleaned_data.csv exists
if not os.path.exists(input_file):
    raise FileNotFoundError(f"File not found: {input_file}")

# Load cleaned data
data = np.genfromtxt(input_file, delimiter=',', skip_header=1).T  # Transpose for MNE

# Define EEG channels
channels = ['TP9', 'AF7', 'AF8', 'TP10']
sfreq = 256  # Sampling frequency (default for Muse EEG)

# Create MNE RawArray
info = mne.create_info(ch_names=channels, sfreq=sfreq, ch_types='eeg')
raw = mne.io.RawArray(data, info)

# Set Montage (standardized electrode locations)
montage = mne.channels.make_standard_montage('standard_1020')
raw.set_montage(montage)

# Filter data (optional, to clean noise)
raw.filter(l_freq=1., h_freq=40.)  # Bandpass filter between 1-40 Hz

# Create Evoked data for plotting (average over all data points)
events = np.array([[i, 0, 1] for i in range(0, len(raw.times), int(sfreq))])
event_id = {'event': 1}
epochs = mne.EpochsArray(raw.get_data().reshape(1, len(channels), -1), info, events, event_id=event_id)
evoked = epochs.average()

# Plot topographic maps
times = np.linspace(0, 1, 5)  # Example: First 1 second, 5 time points
fig = evoked.plot_topomap(times=times, ch_type='eeg', show=True)

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Save the plot
fig.savefig(os.path.join(output_folder, "topomap.png"))

print(f"Topographic map saved to {output_folder}/topomap.png")