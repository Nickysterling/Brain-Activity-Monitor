import time
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QSplitter, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from .muse_util import embedded_view
from .brainwave_bands import LiveBandsWidget

class CombinedViewWindow(QMainWindow):
    # Signal emitted when the window is closed.
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Brainwave Viewer")
        self.resize(1000, 800)
        self._destroyed = False  # Flag to ensure cleanup runs only once.

        # Toolbar with toggle actions and reset layout.
        toolbar = QToolBar("View Options")
        self.addToolBar(toolbar)
        
        self.toggle_muse_action = QAction("Toggle Muse View", self)
        self.toggle_muse_action.setCheckable(True)
        self.toggle_muse_action.setChecked(True)
        self.toggle_muse_action.triggered.connect(lambda checked: self.toggle_muse_view(checked))
        toolbar.addAction(self.toggle_muse_action)
        
        self.toggle_bands_action = QAction("Toggle Brainwave Bands", self)
        self.toggle_bands_action.setCheckable(True)
        self.toggle_bands_action.setChecked(True)
        self.toggle_bands_action.triggered.connect(lambda checked: self.toggle_bands_view(checked))
        toolbar.addAction(self.toggle_bands_action)
        
        reset_action = QAction("Reset Layout", self)
        reset_action.triggered.connect(self.reset_layout)
        toolbar.addAction(reset_action)
        
        # Main vertical splitter for the two panels.
        self.splitter = QSplitter(Qt.Vertical)
        
        # Muse view (top panel).
        try:
            self.muse_view = embedded_view(window=5, scale=100, refresh=0.05, figure="15x6", backend='Qt5Agg')
        except Exception as e:
            print("Error launching Muse View:", e)
            self.muse_view = QWidget()
        
        # Live bands view (bottom panel).
        self.live_bands_view = LiveBandsWidget()
        
        self.splitter.addWidget(self.muse_view)
        self.splitter.addWidget(self.live_bands_view)
        # Set default sizes (e.g., 60% and 40%).
        self.splitter.setSizes([480, 320])
        
        self.setCentralWidget(self.splitter)
    
    def toggle_muse_view(self, checked):
        if checked:
            self.muse_view.show()
        else:
            self.muse_view.hide()
        self.adjust_layout()
    
    def toggle_bands_view(self, checked):
        if checked:
            self.live_bands_view.show()
        else:
            self.live_bands_view.hide()
        self.adjust_layout()
    
    def adjust_layout(self):
        self.centralWidget().updateGeometry()
    
    def reset_layout(self):
        # Reset the main splitter to default sizes.
        self.splitter.setSizes([480, 320])
        # Also reset the LiveBandsWidget's internal layout.
        self.live_bands_view.reset_layout()

    def destroy_window(self):
        """
        Performs cleanup of background resources and deletes the window.
        This is our single point for closing the window, used by both
        the X button and the main window's close button.
        """
        if self._destroyed:
            return
        self._destroyed = True

        # Stop LiveBandsWidget's timer if it exists.
        if hasattr(self.live_bands_view, 'timer') and self.live_bands_view.timer is not None:
            self.live_bands_view.timer.stop()

        # Stop the embedded Muse view's update thread.
        if hasattr(self, 'muse_view') and self.muse_view is not None:
            if hasattr(self.muse_view, 'lslv'):
                try:
                    # Pass the required argument.
                    self.muse_view.lslv.stop(close_event=True)
                except Exception as e:
                    print("Error stopping LSL viewer:", e)
            # Wait a bit to allow the update thread to terminate.
            time.sleep(0.2)
            self.muse_view.close()

        # Emit the closed signal so the main window can update its state.
        self.closed.emit()

        # Call the standard close() and schedule deletion.
        super().close()
        self.deleteLater()

    def closeEvent(self, event):
        # When the user clicks the X button, use the same cleanup logic.
        self.destroy_window()
        event.accept()
