# UI/settings_window.py
import os
import re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QToolBar,
    QAction, QStackedWidget, QComboBox
)
from PyQt5.QtCore import Qt, QTimer

class SettingsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 400)

        # Create a toolbar to act as tabs.
        toolbar = QToolBar("Settings Tabs", self)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Create actions for the toolbar buttons.
        self.stats_action = QAction("Statistics", self)
        self.stats_action.setCheckable(True)
        self.tuning_action = QAction("Model Tuning", self)
        self.tuning_action.setCheckable(True)

        toolbar.addAction(self.stats_action)
        toolbar.addAction(self.tuning_action)

        # Create a QStackedWidget to hold the two pages.
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # Create the Statistics page.
        self.stats_page = QWidget()
        stats_layout = QVBoxLayout(self.stats_page)
        stats_label = QLabel("Statistics Page:\nDisplay the latest buffer item stats here.")
        stats_layout.addWidget(stats_label)
        self.stats_page.setLayout(stats_layout)

        # Create the Model Tuning page.
        self.tuning_page = QWidget()
        tuning_layout = QVBoxLayout(self.tuning_page)
        
        # Add dropdown menu at the top.
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Filter Model", "Action Model"])
        tuning_layout.addWidget(self.model_combo)
        
        # Add a label to display a description message that changes with selection.
        self.tuning_message = QLabel()
        tuning_layout.addWidget(self.tuning_message)
        
        # Add a label to show the latest file in the buffer.
        self.latest_file_label = QLabel("Latest file: N/A")
        tuning_layout.addWidget(self.latest_file_label)
        
        # Add a label to show the prediction (filter or action).
        self.prediction_label = QLabel("Prediction: N/A")
        tuning_layout.addWidget(self.prediction_label)
        
        # Set initial message based on default combo box selection.
        self.update_tuning_message(self.model_combo.currentText())
        
        # Connect the combo box signal to update the message and model info immediately.
        self.model_combo.currentIndexChanged.connect(self.on_model_selection_changed)
        
        self.tuning_page.setLayout(tuning_layout)
        
        # Add pages to the stacked widget.
        self.stacked_widget.addWidget(self.stats_page)
        self.stacked_widget.addWidget(self.tuning_page)

        # Connect actions to switch pages.
        self.stats_action.triggered.connect(self.show_stats_page)
        self.tuning_action.triggered.connect(self.show_tuning_page)

        # Set default page.
        self.stats_action.setChecked(True)
        self.stacked_widget.setCurrentWidget(self.stats_page)
        
        # Set up a timer to update the latest file info periodically.
        self.info_timer = QTimer(self)
        self.info_timer.timeout.connect(self.update_model_info)
        self.info_timer.start(1000)  # update every second

    def on_model_selection_changed(self, index):
        selected_model = self.model_combo.itemText(index)
        self.update_tuning_message(selected_model)
        # Immediately update the file and prediction labels when the selection changes.
        self.update_model_info()

    def update_tuning_message(self, selected_model):
        if selected_model == "Filter Model":
            self.tuning_message.setText("Filter Model Tuning:\nConfigure filter model parameters here.")
        elif selected_model == "Action Model":
            self.tuning_message.setText("Action Model Tuning:\nConfigure action model parameters here.")
        else:
            self.tuning_message.setText("")

    def _get_latest_buffer_file(self):
        """
        Scans the buffer directory for CSV files with names like 'buffer_XX.csv'
        and returns the file with the highest numeric index.
        """
        buffer_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "classifier", "buffer")
        if not os.path.exists(buffer_dir):
            return None
        files = [f for f in os.listdir(buffer_dir) if f.startswith("buffer_") and f.endswith(".csv")]
        if not files:
            return None
        # Sort files by the numeric portion.
        def extract_num(filename):
            match = re.search(r"buffer_(\d+)\.csv", filename)
            if match:
                return int(match.group(1))
            return 0
        files.sort(key=extract_num)
        return files[-1]

    def get_latest_prediction(self, model_type):
        """
        Returns the latest prediction based on the model type.
        For 'Filter Model' it returns the chosen filter from the main window,
        and for 'Action Model' it extracts the predicted action from the main window.
        """
        if model_type == "Filter Model":
            if self.parent() is not None and hasattr(self.parent(), "predicted_filter"):
                return self.parent().predicted_filter
            return "N/A"
        elif model_type == "Action Model":
            if self.parent() is not None and hasattr(self.parent(), "predicted_action_label"):
                text = self.parent().predicted_action_label.text()
                if "Predicted Action:" in text:
                    parts = text.split("Predicted Action:")
                    if len(parts) > 1:
                        return parts[1].strip()
            return "N/A"
        return "N/A"

    def update_model_info(self):
        """
        Updates the latest file name from the buffer and the prediction
        based on the current model selection.
        """
        model_type = self.model_combo.currentText()
        latest_file = self._get_latest_buffer_file()
        if latest_file is None:
            self.latest_file_label.setText("Latest file: None")
        else:
            self.latest_file_label.setText(f"Latest file: {latest_file}")
        
        prediction = self.get_latest_prediction(model_type)
        if model_type == "Filter Model":
            self.prediction_label.setText(f"Predicted Filter: {prediction}")
        elif model_type == "Action Model":
            self.prediction_label.setText(f"Predicted Action: {prediction}")

    def show_stats_page(self):
        self.stats_action.setChecked(True)
        self.tuning_action.setChecked(False)
        self.stacked_widget.setCurrentWidget(self.stats_page)

    def show_tuning_page(self):
        self.tuning_action.setChecked(True)
        self.stats_action.setChecked(False)
        self.stacked_widget.setCurrentWidget(self.tuning_page)
