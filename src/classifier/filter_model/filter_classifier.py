import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from scipy.signal import welch
from scipy.stats import skew, kurtosis
import matplotlib.pyplot as plt
import seaborn as sns
from filter_dataloader import dataloader

# ---------------- Load Data ----------------
# Use your dataloader to load EEG data and metadata.
X, y, info = dataloader()
fs = info["sfreq"]

# Map action labels to filter names.
# Adjust the mapping if necessary.
filter_mapping = {
    "jaw": "Jaw Clench",
    "bite": "Biting",
    "blink": "Blink",
    "eyebrow": "Eyebrow"
}
# Convert labels to lowercase for consistency.
filter_labels = [filter_mapping[label.lower()] for label in y]

# ---------------- Helper Functions ----------------
def compute_band_power(signal, fs, lowcut, highcut):
    """
    Computes the band power of a signal using Welch's method.
    """
    freqs, psd = welch(signal, fs=fs, nperseg=min(256, len(signal)))
    band_idx = (freqs >= lowcut) & (freqs <= highcut)
    band_power = np.trapz(psd[band_idx], freqs[band_idx])
    return band_power

def extract_filter_features(snippet, fs):
    """
    Extracts features from an EEG snippet for filter selection.
    
    Features:
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

# ---------------- Feature Extraction ----------------
# Extract features for each EEG snippet loaded by the dataloader.
X_features = np.array([extract_filter_features(sample, fs) for sample in X])
print(f"Extracted feature matrix shape: {X_features.shape}")

# Encode filter labels (e.g., "Eyebrow", "Biting", "Blink", "Jaw Clench")
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(filter_labels)

# ---------------- Train-Test Split ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X_features, y_encoded, test_size=0.4, random_state=42, stratify=y_encoded
)

# ---------------- Train the Classifier ----------------
clf_filter = RandomForestClassifier(
    n_estimators=50,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
)
clf_filter.fit(X_train, y_train)

# ---------------- Evaluate the Model ----------------
y_pred = clf_filter.predict(X_test)
print("Filter Selection Classifier Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Plot Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
plt.xlabel("Predicted Filter")
plt.ylabel("True Filter")
plt.title("Filter Selection Confusion Matrix")
plt.show()

# ---------------- Save the Model ----------------
# Save both the classifier and the label encoder for later use in real_time.py.
joblib.dump((clf_filter, label_encoder), 'project_directory/scripts/demo/classifier/models/filter_selector.pkl')
