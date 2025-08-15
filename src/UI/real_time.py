import joblib
import numpy as np
import random
import os, pandas as pd
import time
from scipy.signal import welch, butter, filtfilt
from scipy.stats import skew, kurtosis
import time

# ---------------- Filtering & Normalization Functions ----------------

def bandpass_filter(signal, fs, lowcut, highcut, order=4):
    nyq = 0.5 * fs  # Nyquist frequency
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

def filter_biting(signal, fs):
    return bandpass_filter(signal, fs, lowcut=20, highcut=50)

def filter_blink(signal, fs):
    return bandpass_filter(signal, fs, lowcut=0.1, highcut=4)

def filter_eyebrow(signal, fs):
    return bandpass_filter(signal, fs, lowcut=25, highcut=40)

def filter_jaw(signal, fs):
    return bandpass_filter(signal, fs, lowcut=20, highcut=50)

def compute_band_power(signal, fs, lowcut, highcut):
    freqs, psd = welch(signal, fs=fs, nperseg=min(256, len(signal)))
    band_idx = (freqs >= lowcut) & (freqs <= highcut)
    band_power = np.trapezoid(psd[band_idx], freqs[band_idx])
    return band_power

# ---------------- Filter Selector Model Integration ----------------

# Load the trained filter selector model.
current_dir = os.path.dirname(os.path.abspath(__file__))
filter_model_path = os.path.join(current_dir, "..", "classifier", "models", "filter_selector.pkl")
filter_model_path = os.path.normpath(filter_model_path)
filter_clf, filter_label_encoder = joblib.load(filter_model_path)

def extract_filter_features(snippet, fs):
    """
    Extracts 6 summary features from an EEG snippet for filter selection.
      - Average variance across channels
      - Average skewness across channels
      - Average kurtosis across channels
      - Average power in high-frequency band (20-50 Hz)
      - Average power in low-frequency band (0.1-4 Hz)
      - Ratio of high-frequency to low-frequency power
    """
    avg_variance = np.mean(np.var(snippet, axis=1))
    avg_skew = np.nanmean(skew(snippet, axis=1, nan_policy='omit'))
    avg_kurtosis = np.nanmean(kurtosis(snippet, axis=1, nan_policy='omit'))
    avg_high_freq_power = np.mean([compute_band_power(channel, fs, 20, 50) for channel in snippet])
    avg_low_freq_power = np.mean([compute_band_power(channel, fs, 0.1, 4) for channel in snippet])
    power_ratio = avg_high_freq_power / avg_low_freq_power if avg_low_freq_power != 0 else np.inf
    return np.array([avg_variance, avg_skew, avg_kurtosis, avg_high_freq_power, avg_low_freq_power, power_ratio])

def choose_filter(snippet, fs):
    """
    Uses the trained filter selector model to choose the appropriate filter.
    """
    features = extract_filter_features(snippet, fs).reshape(1, -1)
    pred_class = filter_clf.predict(features)[0]
    filter_name = filter_label_encoder.inverse_transform([pred_class])[0]
    
    mapping = {
        "Biting": filter_biting,
        "Blink": filter_blink,
        "Eyebrow": filter_eyebrow,
        "Jaw Clench": filter_jaw
    }
    filter_func = mapping.get(filter_name, filter_jaw)
    return filter_func, filter_name

def apply_filter_to_snippet(snippet, fs):
    filter_func, filter_name = choose_filter(snippet, fs)
    filtered = [filter_func(channel, fs) for channel in snippet]
    return np.array(filtered), filter_name

# ---------------- End Filtering Functions ----------------

# Build the model file's absolute path relative to this script.
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "..", "classifier", "models", "eeg_model.pkl")
model_path = os.path.normpath(model_path)

clf = joblib.load(model_path)

# Build the buffer directory path relative to this script.
buffer_dir = os.path.join(current_dir, "..", "classifier", "buffer")
buffer_dir = os.path.normpath(buffer_dir)

# Ensure the buffer directory exists before using it.
os.makedirs(buffer_dir, exist_ok=True)

# Record files already in the buffer when the program starts
processed_files = set(os.listdir(buffer_dir))

# Initialize predicted_action to a default value
predicted_action = "None"

def extract_features_from_sample(eeg_sample, sfreq):
    feature_vector = []
    for channel in eeg_sample:
        freqs, psd = welch(channel, sfreq, nperseg=min(256, len(channel)))
        feature_vector.extend([psd.mean(), psd.std()])
    feature_vector.extend(eeg_sample.mean(axis=1).tolist())
    feature_vector.extend(eeg_sample.std(axis=1).tolist())
    feature_vector.extend(skew(eeg_sample, axis=1).tolist())
    feature_vector.extend(kurtosis(eeg_sample, axis=1).tolist())
    return np.array(feature_vector).reshape(1, -1)

while True:  
    current_files = set(os.listdir(buffer_dir))
    new_files = current_files - processed_files

    if new_files:
        for selected_file in sorted(new_files):
            file_path = os.path.join(buffer_dir, selected_file)
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                print("Error reading file", selected_file, ":", e, flush=True)
                continue

            timestamps = df.iloc[:, 0].values
            eeg_data = df.iloc[:, 1:].to_numpy().T
            snippet_length = int(256 * 2.5)
            n_channels, n_timepoints = eeg_data.shape

            if n_timepoints > snippet_length:
                start_idx = random.randint(0, n_timepoints - snippet_length)
                snippet = eeg_data[:, start_idx:start_idx + snippet_length]
            else:
                snippet = eeg_data

            sfreq = 256
            
            # Start timing before processing
            start_time = time.time()

            # Use the trained filter selector model to choose a filter and process the snippet
            snippet, chosen_filter = apply_filter_to_snippet(snippet, sfreq)
            print("Chosen Filter:", chosen_filter, flush=True)
            
            # Extract the full feature vector
            features = extract_features_from_sample(snippet, sfreq)
            
            predicted_numeric = clf.predict(features)
            mapping = {0: "Biting", 1: "Blink", 2: "Eyebrow", 3: "Jaw Clench"}
            predicted_action = mapping[predicted_numeric[0]]
            print("Predicted Action:", predicted_action, flush=True)

            # End timing after prediction
            end_time = time.time()

            # Calculate and print latency in milliseconds
            latency_ms = (end_time - start_time) * 1000
            print(f"End-to-end processing latency: {latency_ms:.2f} ms\n", flush=True)

            processed_files.add(selected_file)
    
    time.sleep(1)
