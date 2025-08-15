import numpy as np
import mne
import pyqtgraph as pg
from pylsl import resolve_byprop, StreamInlet
from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel
from PyQt5.QtCore import QTimer, QSize

class ChannelContainer(QWidget):
    """
    Wraps a widget (here a PlotWidget) and enforces a fixed aspect ratio.
    The inner widget can be hidden/shown without affecting the container's size.
    """
    def __init__(self, inner_widget, aspect_ratio=1.0, parent=None):
        super().__init__(parent)
        self.aspect_ratio = aspect_ratio  # width / height
        self.inner_widget = inner_widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.inner_widget)

    def sizeHint(self):
        # Provide a size hint based on the inner widget
        base_hint = self.inner_widget.sizeHint()
        width = base_hint.width() if base_hint.width() > 0 else 200
        return QSize(width, int(width / self.aspect_ratio))

    def heightForWidth(self, width):
        return int(width / self.aspect_ratio)

    def hasHeightForWidth(self):
        return True

    def setPlotVisible(self, visible):
        # Show or hide the inner plot while keeping the container visible.
        self.inner_widget.setVisible(visible)

class LiveBandsWidget(QWidget):
    def __init__(self, fs=256, buffer_duration=8, update_interval=250, parent=None):
        super().__init__(parent)
        self.fs = fs
        self.buffer_duration = buffer_duration
        self.buffer_length = int(fs * buffer_duration)
        self.update_interval = update_interval
        self.n_channels = 4
        self.channel_names = ["AF7", "TP9", "TP10", "AF8"]

        # Define frequency bands.
        self.bands = {
            'Delta': (0.5, 4),
            'Theta': (4, 8),
            'Alpha': (8, 12),
            'Beta':  (12, 30),
            'Gamma': (30, 40)
        }

        # Dictionaries to hold the toggle status.
        self.enabled_bands = {band: True for band in self.bands.keys()}
        self.enabled_channels = {ch: True for ch in self.channel_names}

        # Create buffers for each channel.
        self.buffers = [np.zeros(self.buffer_length) for _ in range(self.n_channels)]
        
        # Create a single horizontal layout for both band and channel toggles.
        self.toggle_layout = QHBoxLayout()
        
        # Label and checkboxes for frequency bands.
        bands_label = QLabel("Bands:")
        self.toggle_layout.addWidget(bands_label)
        self.band_checkboxes = {}
        for band in self.bands.keys():
            checkbox = QCheckBox(band)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.update_band_visibility)
            self.toggle_layout.addWidget(checkbox)
            self.band_checkboxes[band] = checkbox

        # Add a separator.
        separator_label = QLabel("   |   ")
        self.toggle_layout.addWidget(separator_label)
        
        # Label and checkboxes for channels.
        channels_label = QLabel("Channels:")
        self.toggle_layout.addWidget(channels_label)
        self.channel_checkboxes = {}
        for channel in self.channel_names:
            checkbox = QCheckBox(channel)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.update_channel_visibility)
            self.toggle_layout.addWidget(checkbox)
            self.channel_checkboxes[channel] = checkbox

        # Create a grid layout (2x2) for the channel plots.
        self.grid_layout = QGridLayout()
        self.channel_plots = []      # List of PlotWidgets.
        self.channel_containers = [] # Wrappers that enforce fixed aspect ratio.
        self.channel_curves = []     # For each channel, a dict mapping band names to curves.
        colors = {'Delta': 'b', 'Theta': 'g', 'Alpha': 'r', 'Beta': 'y', 'Gamma': 'm'}
        for ch in range(self.n_channels):
            # Create the PlotWidget and lock its view aspect.
            plot = pg.PlotWidget(title=f"Channel {self.channel_names[ch]}")
            plot.addLegend()
            plot.getViewBox().setAspectLocked(True)
            curves = {}
            for band, color in colors.items():
                curves[band] = plot.plot(pen=color, name=band)
            self.channel_plots.append(plot)
            self.channel_curves.append(curves)
            # Wrap the PlotWidget in a container that fixes the aspect ratio (e.g. 1:1).
            container = ChannelContainer(plot, aspect_ratio=1.0)
            self.channel_containers.append(container)
            row = ch // 2
            col = ch % 2
            self.grid_layout.addWidget(container, row, col)

        # Main layout: toggle panel on top then the grid.
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.toggle_layout)
        main_layout.addLayout(self.grid_layout)
        self.setLayout(main_layout)
        
        # Connect to the EEG stream.
        self.inlet = None
        self.connect_to_stream()
        
        # Set up a timer to update the plots.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(self.update_interval)
    
    def update_band_visibility(self):
        # Update each band curve's visibility based on the corresponding checkbox.
        for band, checkbox in self.band_checkboxes.items():
            visible = checkbox.isChecked()
            self.enabled_bands[band] = visible
            for ch in range(self.n_channels):
                self.channel_curves[ch][band].setVisible(visible)
    
    def update_channel_visibility(self):
        # Update each channel's inner plot visibility; the container remains to keep grid structure.
        for i, channel in enumerate(self.channel_names):
            visible = self.channel_checkboxes[channel].isChecked()
            self.enabled_channels[channel] = visible
            self.channel_containers[i].setPlotVisible(visible)
    
    def connect_to_stream(self):
        streams = resolve_byprop('type', 'EEG', timeout=5)
        if streams:
            self.inlet = StreamInlet(streams[0])
        else:
            self.inlet = None
    
    def update_plots(self):
        if self.inlet is None:
            return
        
        chunk, _ = self.inlet.pull_chunk(timeout=0.0, max_samples=self.fs)
        if chunk:
            chunk = np.array(chunk)  # shape: (n_samples, n_channels)
            for ch in range(self.n_channels):
                if ch >= chunk.shape[1]:
                    continue
                new_data = chunk[:, ch]
                self.buffers[ch] = np.concatenate((self.buffers[ch], new_data))
                if len(self.buffers[ch]) > self.buffer_length:
                    self.buffers[ch] = self.buffers[ch][-self.buffer_length:]
            # Update only the enabled channels and bands.
            for ch in range(self.n_channels):
                if not self.enabled_channels[self.channel_names[ch]]:
                    continue
                for band, (l_freq, h_freq) in self.bands.items():
                    if not self.enabled_bands[band]:
                        continue
                    filtered = mne.filter.filter_data(self.buffers[ch], sfreq=self.fs,
                                                      l_freq=l_freq, h_freq=h_freq, verbose=False)
                    self.channel_curves[ch][band].setData(filtered)
    
    def reset_layout(self):
        # In a grid layout, we can simply update the geometry.
        self.updateGeometry()
