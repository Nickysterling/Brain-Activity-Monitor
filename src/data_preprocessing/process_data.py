import os
import csv
import numpy as np
import argparse

def bandpass_filter(signal, fs, lowcut, highcut):
    """
    Zeroes out frequency components outside [lowcut, highcut].

    Parameters:
      signal: 1D NumPy array of time-domain samples.
      fs: Sampling frequency (Hz).
      lowcut: Lower bound of passband (Hz).
      highcut: Upper bound of passband (Hz).

    Returns:
      A time-domain signal (1D NumPy array) whose frequency content
      outside [lowcut, highcut] is set to zero.
    """
    N = len(signal)
    freqs = np.fft.fftfreq(N, d=1.0/fs)
    fft_vals = np.fft.fft(signal)
    passband_mask = (np.abs(freqs) >= lowcut) & (np.abs(freqs) <= highcut)
    fft_vals[~passband_mask] = 0
    filtered_signal = np.fft.ifft(fft_vals)
    return filtered_signal.real

def z_score_normalize(signal):
    """
    Normalizes the signal to have zero mean and unit variance.

    Parameters:
      signal: 1D NumPy array of time-domain samples.

    Returns:
      A normalized signal with mean = 0 and std = 1.
    """
    mean = np.mean(signal)
    std = np.std(signal)
    normalized_signal = (signal - mean) / std  # Zero mean, unit variance
    return normalized_signal


def process_csv(input_file, output_file, lowcut, highcut, fs, normalize=False):
    """
    Reads a CSV file with a header (first column = timestamps, subsequent columns = signal values),
    then applies a bandpass filter to each channel using the specified frequency range.
    The filtered data is written to a new CSV with the same header.
    """
    with open(input_file, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        print(f"Input CSV file {input_file} is empty!")
        return
    
    header = rows[0]  # e.g.: timestamps,TP9,AF7,AF8,TP10,Right AUX
    timestamps = []
    signals = []
    
    for row in rows[1:]:
        if row:
            timestamps.append(float(row[0]))
            signals.append([float(x) for x in row[1:]])
    
    signals = np.array(signals)  # shape: (n_samples, n_channels)
    filtered_signals = np.empty_like(signals)
    
    for ch in range(signals.shape[1]):
        filtered_signals[:, ch] = bandpass_filter(
            signals[:, ch],
            fs=fs,
            lowcut=lowcut,
            highcut=highcut
        )
    
        if normalize == True:
            filtered_signals[:, ch] = z_score_normalize(filtered_signals[:, ch])

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for ts, row in zip(timestamps, filtered_signals):
            writer.writerow([ts] + list(row))
    
    print(f"Filtered data ({lowcut}–{highcut} Hz) saved to {output_file}")

def process_directory(input_dir, output_dir, lowcut, highcut, fs, normalize=False):
    """
    Processes every CSV file in the input directory and writes the filtered
    data to the output directory using the same filename.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
    if not files:
        print("No CSV files found in the input directory!")
        return
    
    for file in files:
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(output_dir, file)
        process_csv(input_file, output_file, lowcut=lowcut, highcut=highcut, fs=fs, normalize=normalize)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Bandpass Filter for EEG Data")
    parser.add_argument("--action", choices=["blink", "jaw", "bite", "brow"], required=True,
                        help="Choose filter type: 'blink' for blinking, 'jaw' for jaw clenching, 'bite' for biting, 'brow' for eyebrow raises.")
    parser.add_argument("--lowcut", type=float, help="Low cutoff frequency in Hz (overrides default)")
    parser.add_argument("--highcut", type=float, help="High cutoff frequency in Hz (overrides default)")
    parser.add_argument("--fs", type=float, default=256, help="Sampling frequency in Hz (default: 256)")
    parser.add_argument("--normalize", action="store_true", help="Normalize the eyebrow signal (Min-Max Normalization)")
    args = parser.parse_args()
    
    if args.action == "blink":
        input_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking/raw"
        output_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking/processed/data"
        default_lowcut, default_highcut = 0.1, 4
    elif args.action == "jaw":
        input_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/jaw_clench/raw"
        output_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/jaw_clench/processed/data"
        default_lowcut, default_highcut = 20, 50
    elif args.action == "bite":
        input_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/biting/raw"
        output_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/biting/processed/data"
        default_lowcut, default_highcut = 20, 50
    elif args.action == "brow":
        input_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/eyebrow/raw"
        output_dir = r"D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/eyebrow/processed/data"
        default_lowcut, default_highcut = 25, 40

    lowcut = args.lowcut if args.lowcut is not None else default_lowcut
    highcut = args.highcut if args.highcut is not None else default_highcut
    fs = args.fs

    print(f"Action: {args.action}")
    print(f"Using filter passband: {lowcut}–{highcut} Hz at {fs} Hz sampling rate")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    process_directory(input_dir, output_dir, lowcut=lowcut, highcut=highcut, fs=fs, normalize=args.normalize)
