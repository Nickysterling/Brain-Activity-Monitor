import sys, os, re, threading
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QMainWindow,
    QComboBox,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtCore import QProcess, QTimer, pyqtSignal
from pylsl import resolve_byprop
from UI.combined_view import CombinedViewWindow
from UI.settings_window import SettingsWindow
from classifier.record_data import record_raw_snippet
from arduino.send_rc_car_cmd import sendCmdToArduinoCar


def send_command_thread(command):
    try:
        sendCmdToArduinoCar(command)
    except TimeoutError as te:
        print("Warning: Arduino connection timed out. Check the device and try again.")
    except Exception as e:
        print("An error occurred:", e)


class MainWindow(QMainWindow):
    # Custom signals for logging and for when a stream is connected.
    log_signal = pyqtSignal(str)
    stream_connected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._active = True

        # Compute base directory and icons directory dynamically.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "UI", "img")
        self.settings_icon_path = os.path.join(icons_dir, "settings.png")

        self.setWindowTitle("Brain Activity Monitor")
        self.resize(600, 400)

        self.muse_stream_process = None
        self.list_process = None
        self.classifier_process = None  # Process for the classifier.
        self.list_data = ""
        self.connection_check_timer = None
        self.combined_view_window = None  # Reference to the CombinedViewWindow.
        self.monitor_close_initiated = False  # Flag to track close initiation.
        self.predicted_filter = "N/A"  # initialize predicted filter attribute

        # Store a reference for the settings window.
        self.settings_window = None

        self.initUI()

        # Connect signals: log_signal updates the UI and stream_connected updates UI on a successful connection.
        self.log_signal.connect(self.append_log_slot)
        self.stream_connected.connect(self.handle_stream_connected)

        # Start the classifier process.
        self.start_classifier()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Calibri", 12))
        layout.addWidget(self.log_output)

        self.list_button = QPushButton("List Muse Devices")
        self.list_button.setFont(QFont("Segoe UI", 10))
        self.list_button.clicked.connect(self.list_devices)
        layout.addWidget(self.list_button)

        self.device_combo = QComboBox()
        self.device_combo.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.device_combo)

        self.stream_button = QPushButton("Start Stream")
        self.stream_button.setFont(QFont("Segoe UI", 10))
        self.stream_button.clicked.connect(self.toggle_stream)
        layout.addWidget(self.stream_button)

        self.combined_view_button = QPushButton("Launch Brainwave Monitor")
        self.combined_view_button.setFont(QFont("Segoe UI", 10))
        self.combined_view_button.clicked.connect(self.launch_combined_view)
        self.combined_view_button.setEnabled(False)
        layout.addWidget(self.combined_view_button)

        self.record_button = QPushButton("Record Data")
        self.record_button.setFont(QFont("Segoe UI", 10))
        self.record_button.clicked.connect(self.record_snippet)
        self.record_button.setEnabled(False)
        layout.addWidget(self.record_button)

        # Create a horizontal layout for the Predicted Action label and the settings button.
        settings_layout = QHBoxLayout()

        self.predicted_action_label = QLabel("Predicted Action: None")
        self.predicted_action_label.setFont(QFont("Calibri", 12))
        settings_layout.addWidget(self.predicted_action_label)

        # Add a stretch to push the button to the right.
        settings_layout.addStretch()

        # Create the settings button with a square fixed size.
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon(self.settings_icon_path))
        self.settings_button.setFixedSize(30, 30)  # Ensure the button is square.
        settings_layout.addWidget(self.settings_button)

        # Connect the settings button to open the settings window.
        self.settings_button.clicked.connect(self.open_settings_window)

        # Add the horizontal layout to your main vertical layout.
        layout.addLayout(settings_layout)

    def open_settings_window(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def append_log_slot(self, message):
        """Appends a log message to the text box."""
        self.log_output.append(message)

    def append_log(self, message):
        """Emits a log message to be appended in the main thread."""
        self.log_signal.emit(message)

    def list_devices(self):
        self.append_log("Listing Muse devices...")
        self.append_log("Searching for Muses, this may take up to 10 seconds...")
        self.list_button.setEnabled(False)
        self.stream_button.setEnabled(False)
        self.combined_view_button.setEnabled(False)
        self.record_button.setEnabled(False)
        self.device_combo.clear()
        self.list_data = ""

        self.list_process = QProcess(self)
        self.list_process.readyReadStandardOutput.connect(self.handle_list_output)
        self.list_process.readyReadStandardError.connect(self.handle_list_error)
        self.list_process.finished.connect(self.listing_finished)
        self.list_process.start("muselsl list")

    def handle_list_output(self):
        text = bytes(self.list_process.readAllStandardOutput()).decode("utf-8")
        if "Searching for Muses" not in text:
            self.append_log(text)
        self.list_data += text

    def handle_list_error(self):
        error = bytes(self.list_process.readAllStandardError()).decode("utf-8")
        self.append_log("Error: " + error)

    def listing_finished(self, exitCode, exitStatus):
        self.append_log("Finished listing devices.\n")
        # Clear the combo box and insert a blank item.
        self.device_combo.clear()
        self.device_combo.addItem("")  # Blank entry for no specific device.

        lines = self.list_data.splitlines()
        ip_regex = re.compile(r"at\s+(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
        unwanted_msg = "Searching for Muses, this may take up to 10 seconds"
        for line in lines:
            if unwanted_msg in line:
                continue
            match = ip_regex.search(line)
            if match:
                ip = match.group(1)
                self.device_combo.addItem(line, ip)
            else:
                self.device_combo.addItem(line)
        self.list_button.setEnabled(True)
        self.stream_button.setEnabled(True)

    def toggle_stream(self):
        if not self.muse_stream_process:
            # Clear any previous device name.
            self.device_name = None

            selected_ip = self.device_combo.currentData()
            selected_text = self.device_combo.currentText().strip()
            command = (
                f"muselsl stream --address {selected_ip}"
                if selected_ip
                else "muselsl stream"
            )

            self.append_log("Starting stream...")
            if selected_text:
                device_regex = re.compile(r"Found\s+device\s+([^,\s]+)", re.IGNORECASE)
                match = device_regex.search(selected_text)
                if match:
                    self.device_name = match.group(1)
                    self.append_log(f"Connecting to device {self.device_name}...")
                else:
                    self.append_log(f"Connecting to {selected_text}...")
            else:
                self.append_log(
                    "Searching for Muses, this may take up to 10 seconds..."
                )

            self.stream_data = ""
            self.muse_stream_process = QProcess(self)
            self.muse_stream_process.readyReadStandardOutput.connect(
                self.handle_stream_output
            )
            self.muse_stream_process.start(command)

            self.stream_button.setText("Stop Stream")
            self.record_button.setEnabled(False)
            self.combined_view_button.setEnabled(False)
            self.start_connection_check()
        else:
            self.append_log("Stopping stream...")
            self.muse_stream_process.terminate()
            QTimer.singleShot(100, self.check_stream_terminated)
            self.stream_button.setText("Start Stream")
            self.record_button.setEnabled(False)
            self.combined_view_button.setEnabled(False)
            self.stop_connection_check()

    def handle_stream_output(self):
        output = bytes(self.muse_stream_process.readAllStandardOutput()).decode("utf-8")

        # Check for disconnection message.
        if "Disconnected" in output:

            # Log a custom disconnected message.
            if self.device_name:
                self.append_log(f"Device {self.device_name} Disconnected.")
            else:
                self.append_log("Device Disconnected.")

            # Turn the stream off if it is still running.
            if self.muse_stream_process is not None:
                self.muse_stream_process.terminate()
                QTimer.singleShot(100, self.check_stream_terminated)
            # Update UI elements.
            self.stream_button.setText("Start Stream")
            self.record_button.setEnabled(False)
            self.combined_view_button.setEnabled(False)

            # Clear the device combo box and leave only a blank entry.
            self.device_combo.clear()
            self.device_combo.addItem("")
            return

        # Otherwise, filter out the "Searching for Muses" message.
        filtered_text = re.sub(
            r"Searching for Muses,? this may take up to 10 seconds\.{0,3}",
            "",
            output,
            flags=re.IGNORECASE,
        ).strip()
        if filtered_text:
            self.append_log(filtered_text)

        self.stream_data += output
        # If no Muses found while stream is running, toggle the stream.
        if "No Muses found." in output and self.stream_button.text() == "Stop Stream":
            self.toggle_stream()

    def start_connection_check(self):
        """Starts a timer that triggers the stream check every second."""
        self.connection_check_timer = QTimer(self)
        self.connection_check_timer.timeout.connect(self.check_for_stream)
        self.connection_check_timer.start(1000)

    def stop_connection_check(self):
        if self.connection_check_timer:
            self.connection_check_timer.stop()
            self.connection_check_timer = None

    def check_for_stream(self):
        """
        Offloads the blocking resolve_byprop call to a background thread to prevent UI lag.
        """
        threading.Thread(target=self.check_stream_worker, daemon=True).start()

    def check_stream_worker(self):
        """
        Runs in a separate thread. Calls resolve_byprop (a blocking call)
        and emits a signal if a stream is found. It first checks if the main
        window is still active.
        """
        try:
            streams = resolve_byprop("type", "EEG", timeout=1)
            if streams:
                # Only emit the signal if the main window is still active.
                if self._active:
                    self.stream_connected.emit()
        except Exception as e:
            # Only log if active.
            if self._active:
                try:
                    self.append_log("Error checking for stream: " + str(e))
                except Exception:
                    pass

    def check_stream_terminated(self):
        """Checks if the streaming process has terminated and kills it if not."""
        if self.muse_stream_process is not None:
            if self.muse_stream_process.state() != QProcess.NotRunning:
                self.muse_stream_process.kill()
                self.append_log("Stream process was forcibly ended.\n")
            self.muse_stream_process = None

    def handle_stream_connected(self):
        """Slot that runs in the main thread once the EEG stream is detected."""
        self.append_log("Device connected successfully!\n")
        self.record_button.setEnabled(True)
        self.combined_view_button.setEnabled(True)
        self.stop_connection_check()

    def launch_combined_view(self):
        # Toggle between launching and closing the Combined View window.
        if self.combined_view_button.text() == "Launch Brainwave Monitor":
            self.append_log("Launching Brainwave Monitor...")
            QTimer.singleShot(50, self._show_combined_view)
            
        else:
            # Indicate that the close is initiated by the button.
            self.monitor_close_initiated = True
            self.append_log("Closing Brainwave Monitor...")
            if self.combined_view_window is not None:
                self.combined_view_window.destroy_window()
                self.combined_view_window = None
            self.combined_view_button.setText("Launch Brainwave Monitor")
            # Do not log "Brainwave Monitor closed." here; let on_combined_view_closed do it.
            
        # sendCmdToArduinoCar("")
        
    def _show_combined_view(self):
        self.combined_view_window = CombinedViewWindow()
        self.combined_view_window.closed.connect(self.on_combined_view_closed)
        self.combined_view_window.show()
        self.combined_view_button.setText("Close Brainwave Monitor")
        self.append_log("Brainwave Monitor launched.\n")

    def on_combined_view_closed(self):
        # If the close was not initiated by the button, log the closing message.
        if not getattr(self, "monitor_close_initiated", False):
            self.append_log("Closing Brainwave Monitor...")
        self.append_log("Brainwave Monitor closed.\n")
        self.combined_view_button.setText("Launch Brainwave Monitor")
        self.combined_view_window = None
        self.monitor_close_initiated = False

    def record_snippet(self):
        self.append_log("Recording 2.5 second snippet...")
        record_raw_snippet(self.append_log)
        self.append_log("Recording initiated.")

    def start_classifier(self):
        self.classifier_process = QProcess(self)
        self.classifier_process.setProcessChannelMode(QProcess.MergedChannels)
        self.classifier_process.readyReadStandardOutput.connect(
            self.handle_classifier_output
        )
        self.classifier_process.errorOccurred.connect(
            lambda error: self.append_log(
                "Classifier process error: " + self.classifier_process.errorString()
            )
        )
        self.classifier_process.finished.connect(
            lambda code, status: self.append_log(
                "Classifier process finished with code: " + str(code)
            )
        )

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_dir = os.path.join(base_dir, "UI")
        script_path = os.path.join(ui_dir, "real_time.py")
        python_executable = sys.executable

        self.classifier_process.setWorkingDirectory(ui_dir)
        self.classifier_process.start(python_executable, ["-u", script_path])
        self.append_log("Classifier process started.\n")

    def handle_classifier_output(self):
        output = bytes(self.classifier_process.readAllStandardOutput()).decode("utf-8")
        for line in output.splitlines():
            self.append_log(line)
            if "Predicted Action:" in line:
                parts = line.split("Predicted Action:")
                if len(parts) > 1:
                    action = parts[1].strip()
                    self.predicted_action_label.setText("Predicted Action: " + action)
                    # Map the predicted action to the command expected by the Arduino:
                    command_mapping = {
                        "Biting": "bite",
                        "Blink": "blink",
                        "Eyebrow": "brow",
                        "Jaw Clench": "jaw",
                    }
                    command_to_send = command_mapping.get(action, "")
                    if command_to_send:
                        threading.Thread(
                            target=send_command_thread, args=(command_to_send,)
                        ).start()

    def closeEvent(self, event):
        # Prevent any further background processing.
        self._active = False

        # Disconnect and terminate the classifier process, if running.
        if self.classifier_process is not None:
            try:
                self.classifier_process.readyReadStandardOutput.disconnect()
            except Exception:
                pass
            try:
                self.classifier_process.errorOccurred.disconnect()
            except Exception:
                pass
            try:
                self.classifier_process.finished.disconnect()
            except Exception:
                pass
            self.classifier_process.terminate()
            self.classifier_process.waitForFinished(100)
            self.classifier_process = None

        # Disconnect and terminate the muse stream process, if running.
        if self.muse_stream_process is not None:
            try:
                self.muse_stream_process.readyReadStandardOutput.disconnect()
            except Exception:
                pass
            self.muse_stream_process.terminate()
            self.muse_stream_process.waitForFinished(100)
            self.muse_stream_process = None

        # Also close the Brainwave Monitor (CombinedViewWindow) if it's open.
        if self.combined_view_window is not None:
            self.combined_view_window.destroy_window()
            self.combined_view_window = None

        event.accept()


if __name__ == "__main__":
    # Compute the base directory and icons directory dynamically.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(base_dir, "UI", "img")
    app_icon_path = os.path.join(icons_dir, "app_icon.png")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(app_icon_path))
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
