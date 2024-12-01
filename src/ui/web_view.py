from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import json
import logging

logger = logging.getLogger(__name__)

class WebView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the web view component"""
        layout = QVBoxLayout(self)
        
        # Create web view for React app
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)
        
        # In development, connect to Vite dev server
        self.web_view.setUrl(QUrl('http://localhost:3000'))
        
        # Connect JavaScript bridge
        self.setup_js_bridge()
    
    def setup_js_bridge(self):
        """Set up the communication bridge between Python and JavaScript"""
        self.web_view.page().runJavaScript("""
            window.pythonApi = {
                sendToPython: function(channel, data) {
                    window.qt.webChannelTransport.send({
                        channel: channel,
                        data: JSON.stringify(data)
                    });
                }
            };
        """)
    
    @pyqtSlot(str)
    def handle_js_message(self, message):
        """Handle messages from JavaScript"""
        try:
            data = json.loads(message)
            channel = data.get('channel')
            payload = json.loads(data.get('data', '{}'))
            
            logger.info(f'Received message on channel {channel}')
            
            if channel == 'odds_update':
                self.handle_odds_update(payload)
            elif channel == 'alert_settings':
                self.handle_alert_settings(payload)
            
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse message from JavaScript: {e}')
        except Exception as e:
            logger.error(f'Error handling JavaScript message: {e}')
    
    def handle_odds_update(self, data):
        """Handle odds update requests from the UI"""
        # Implementation will connect to the odds collection service
        pass
    
    def handle_alert_settings(self, data):
        """Handle alert settings updates from the UI"""
        # Implementation will update alert configuration
        pass
    
    def send_to_js(self, channel, data):
        """Send data to JavaScript"""
        message = json.dumps({
            'channel': channel,
            'data': data
        })
        self.web_view.page().runJavaScript(f'window.handlePythonMessage({message})')
