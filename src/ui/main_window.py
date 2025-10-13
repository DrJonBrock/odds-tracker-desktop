from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from .web_view import WebView
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, odds_collector, arbitrage_detector):
        super().__init__()
        self.odds_collector = odds_collector
        self.arbitrage_detector = arbitrage_detector
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle('Odds Tracker')
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create and add web view
        self.web_view = WebView(self)
        layout.addWidget(self.web_view)
        
    def setup_connections(self):
        """Set up connections between components"""
        # Connect odds collector signals
        self.odds_collector.odds_updated.connect(self.handle_odds_update)
        self.odds_collector.error_occurred.connect(self.handle_error)
        
        # Connect arbitrage detector signals
        self.arbitrage_detector.opportunity_found.connect(self.handle_opportunity)
        
    def handle_odds_update(self, odds_data):
        """Handle updated odds data"""
        try:
            # Send updated odds to React UI
            self.web_view.send_to_js('odds_update', odds_data)
            logger.info('Sent odds update to UI')
        except Exception as e:
            logger.error(f'Error sending odds update to UI: {e}')
    
    def handle_opportunity(self, opportunity_data):
        """Handle new arbitrage opportunity"""
        try:
            # Send opportunity to React UI
            self.web_view.send_to_js('new_opportunity', opportunity_data)
            logger.info('Sent new opportunity to UI')
        except Exception as e:
            logger.error(f'Error sending opportunity to UI: {e}')
    
    def handle_error(self, error_info):
        """Handle errors from odds collector"""
        try:
            # Send error to React UI
            self.web_view.send_to_js('error', {
                'message': str(error_info),
                'timestamp': datetime.now().isoformat()
            })
            logger.error(f'Error in odds collector: {error_info}')
        except Exception as e:
            logger.error(f'Error sending error to UI: {e}')
