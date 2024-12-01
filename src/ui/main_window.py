from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from .web_view import WebView
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """The main window of our application. Think of this as the frame of our house -
    it provides the structure that holds everything else."""
    
    def __init__(self, odds_collector=None, arbitrage_detector=None):
        super().__init__()
        self.odds_collector = odds_collector
        self.arbitrage_detector = arbitrage_detector
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface components. This is like arranging the furniture
        in our house - we want everything in the right place."""
        # Set window properties
        self.setWindowTitle('Odds Tracker')
        self.resize(1200, 800)  # Give ourselves plenty of room to work
        
        # Create a central widget to hold everything
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create a layout to organize our components
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a cleaner look
        
        # Create and add our web view component
        self.web_view = WebView(self)
        layout.addWidget(self.web_view)
        
        logger.info('Main window UI setup complete')
        
    def handle_bridge_message(self, message_type, data):
        """Handle messages coming from our React application through the bridge.
        This is like having a translator between two people speaking different languages."""
        try:
            if message_type == 'FETCH_ODDS':
                self.fetch_latest_odds()
            elif message_type == 'UPDATE_SETTINGS':
                self.update_settings(data)
            else:
                logger.warning(f'Unknown message type received: {message_type}')
        except Exception as e:
            logger.error(f'Error handling bridge message: {str(e)}')
            
    def fetch_latest_odds(self):
        """Request the latest odds data. This will be implemented when we add
        the odds collection functionality."""
        if self.odds_collector:
            try:
                self.odds_collector.fetch_latest()
            except Exception as e:
                logger.error(f'Error fetching odds: {str(e)}')
        else:
            logger.warning('Odds collector not initialized')
            
    def update_settings(self, settings):
        """Update application settings. This will be expanded when we implement
        the settings management system."""
        try:
            logger.info(f'Updating settings: {settings}')
            # We'll implement settings storage later
            pass
        except Exception as e:
            logger.error(f'Error updating settings: {str(e)}')