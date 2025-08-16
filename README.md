# Brain-Activity-Monitor

A proof-of-concept Brain-Computer Interface (BCI) system that translates EEG brain signals into real-time control commands for an RC car.

## 1. Overview

The Brain Activity Monitor demonstrates how consumer-grade EEG hardware can be combined with machine learning to create an  affordable, non-invasive, and responsive BCI system. Using the  Muse 2 headset, the system captures EEG signals from facial gestures (blink, jaw clench, bite, eyebrow raise) and translates them into directional controls for an RC car.

## 2. System Architecture

The project was built around four main subsystems:

**1. Data Collection**

* Acquires EEG signals from the Muse 2 headset at 256 Hz.
* Stores EEG samples in CSV format for training and real-time use.
* Applies preprocessing with bandpass filters to isolate gesture-relevant frequency bands.

**2. Machine Learning Pipeline**

* **Filter Selector**: Chooses the appropriate bandpass filter dynamically.
* **Action Classifier**: Identifies gestures using Random Forest model.
* Achieved ~95% classification accuracy with <14 ms processing latency.

**3. User Interface (UI)**

* Built with PyQt5 for clean look and real-time interaction.
* Displays live EEG signals, brainwave frequency bands (Delta, Theta, Alpha, Beta, Gamma).
* Shows predicted gestures and manages communication between software and hardware.

**4. Hardware Components**

* Arduino Uno WiFi Rev2 with motor shield.
* Receives WiFi commands and drives DC motors of the RC car.
* Average command acknowledgment latency: **~49.5 ms**.

![img]()

## 3. Project Structure

```
├── archive/
├── buffer/
├── data/
│ ├── raw/
│ ├── processed/
│ ├── annotations/
│ ├── plots/
│ └── temp/
├── documentation/
├── src/
│ ├── arduino/
│ ├── classifier/
│ ├── data_preprocessing/
│ ├── UI/
│ └── main.py
├── .gitignore
├── README.md
└── requirements.txt
```

## 4. Prerequisites

Before running the Brain Activity Monitor, make sure you have the following:

**Hardware**

* 1x Laptop/PC with Bluetooth + WiFi
* 1x Muse 2 EEG Headset
* 1x Arduino Uno WiFi Rev2
* 1x Motor Shield (Must work with the Arduino)
* 1x USB A to B Cable (For flashing Arduino)
* 1x RC car chassis (Must have 2 DC motors)
* 1x Snap Connector Clip
* 1x 5V 2A Power Adapter (For powering Arduino)
* 1x 4 AA Battery Holder (Must have snap connectors on it)
* 4x AA Batteries

**Software**

* Python 3.9+
* Arduino IDE

**Network Requirements**

* Laptop and Arduino must be on the same WiFi network.
* Muse 2 must be paired to laptop via Bluetooth.

## 5. Installation

### 5.1. Main Project Environment Setup

**1. Clone the repository**

```
git clone https://github.com/Nickysterling/Brain-Activity-Monitor
cd Brain-Activity-Monitor
```

**2. Create a virtual environment**

```
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows
```

**3. Install dependencies**

```
pip install -r requirements.txt
```

### 5.2. Arduino Environment Setup

**1. Install Arduino IDE**

[Download](https://www.arduino.cc/en/software/) the IDE from Arduino’s website and install it.

**2. Install the board package**

* Open **Arduino IDE** → **Tools → Board → Boards Manager…**
* Search **“megaAVR”** and  **install** :  **Arduino megaAVR Boards (by Arduino)**.
* Then set **Tools → Board → Arduino Uno WiFi Rev2**.

**3. Select the correct port**

* Connect the board to the computer via the USB A to B connector.
* **Tools → Port** → choose the COM port (Windows) or `/dev/cu.usbmodem…` (macOS/Linux).

**4. Install libraries**

* **Tools → Manage Libraries…**
* Install **WiFiNINA** (required for the Uno WiFi Rev2).

**5. Update NINA firmware (Optional)**

* If WiFi won’t connect later, use **Tools → WiFi101 / WiFiNINA Firmware Updater** to update the NINA module.

## 6. Running the Project
