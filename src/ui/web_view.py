from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import json
import logging

logger = logging.getLogger(__name__)

class Bridge(QObject):
    """A bridge class that handles communication between Python and JavaScript.
    This class uses Qt's signals and slots mechanism for safe cross-thread communication."""
    
    # Define signals for different types of messages
    messageReceived = pyqtSignal(str)
    
    @pyqtSlot(str)
    def receive_message(self, message):
        """Receive messages from JavaScript and emit them as signals.
        This method is called by JavaScript code through the Qt WebChannel."""
        self.messageReceived.emit(message)

class WebView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_bridge()
    
    def setup_ui(self):
        """Set up the basic UI structure.
        Creates a QWebEngineView and configures it to display our React application."""
        layout = QVBoxLayout(self)
        
        # Create the web view
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)
        
        # In development mode, load from the Vite dev server
        self.web_view.setUrl(QUrl('http://localhost:3000'))
        
        # Remove margins to make the web view fill the entire space
        layout.setContentsMargins(0, 0, 0, 0)
    
    def setup_bridge(self):
        """Set up the communication bridge between Python and JavaScript.
        This creates a two-way communication channel using Qt's WebChannel."""
        self.bridge = Bridge()
        self.bridge.messageReceived.connect(self.handle_message)
        
        # Make bridge available to JavaScript
        self.page = self.web_view.page()
        self.page.runJavaScript("""
            window.pythonBridge = {
                sendMessage: function(message) {
                    window.bridge.receive_message(JSON.stringify(message));
                }
            };
            // Notify React that bridge is ready
            window.dispatchEvent(new Event('python_bridge_ready'));
        """)
    
    def handle_message(self, message):
        """Handle messages received from JavaScript.
        This method processes messages and performs appropriate actions."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            payload = data.get('payload')
            
            logger.info(f'Received message of type: {message_type}')
            
            if message_type == 'REQUEST_INITIAL_DATA':
                self.send_initial_data()
            elif message_type == 'UPDATE_SETTINGS':
                self.handle_settings_update(payload)
            else:
                logger.warning(f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError:
            logger.error('Failed to parse message from JavaScript')
        except Exception as e:
            logger.error(f'Error handling message: {str(e)}')
    
    def send_to_js(self, message_type, payload):
        """Send a message to JavaScript.
        This method safely serializes and sends data to the React application."""
        try:
            message = json.dumps({
                'type': message_type,
                'payload': payload
            })
            
            js_code = f'window.dispatchEvent(new CustomEvent("python_message", '
            js_code += f'{{ detail: {message} }}))'
            
            self.page.runJavaScript(js_code)
            logger.info(f'Sent message of type: {message_type}')
            
        except Exception as e:
            logger.error(f'Error sending message to JavaScript: {str(e)}')
    
    def send_initial_data(self):
        """Send initial application data to the React frontend.
        This is called when the React application first loads."""
        initial_data = {
            'settings': {
                'dataSources': ['Betfair', 'OddsJet', 'Odds.com.au'],
                'refreshInterval': 5000,
                'minimumProfit': 2.0
            }
        }
        self.send_to_js('INITIAL_DATA', initial_data)
    
    def handle_settings_update(self, settings):
        """Handle settings updates from the React frontend.
        This will be expanded to persist settings and update the backend configuration."""
        logger.info(f'Received settings update: {settings}')
        # TODO: Implement settings persistence and backend configuration