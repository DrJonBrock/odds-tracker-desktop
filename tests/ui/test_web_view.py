import pytest
from unittest.mock import Mock, patch
from PyQt6.QtCore import QUrl
from src.ui.web_view import WebView
import json

class TestWebView:
    @pytest.fixture
    def web_view(self):
        """Create a WebView instance for testing.
        This fixture provides a clean WebView instance for each test."""
        return WebView()
    
    def test_initialization(self, web_view):
        """Test that the WebView is properly initialized.
        We verify that the basic structure and URL are set correctly."""
        # The URL should be set to our development server
        assert web_view.web_view.url() == QUrl('http://localhost:3000')
        
        # The layout should contain our web view widget
        assert web_view.layout().count() == 1
    
    def test_js_bridge_setup(self, web_view):
        """Test that the JavaScript bridge is properly initialized.
        This ensures our communication channel is established."""
        # Mock the page's runJavaScript method
        mock_page = Mock()
        web_view.web_view.page = Mock(return_value=mock_page)
        
        # Trigger bridge setup
        web_view.setup_js_bridge()
        
        # Verify that the JavaScript was injected
        assert mock_page.runJavaScript.called
        
        # Get the actual JavaScript code that was injected
        js_code = mock_page.runJavaScript.call_args[0][0]
        assert 'window.pythonApi' in js_code
        assert 'sendToPython' in js_code
    
    def test_handle_odds_update(self, web_view):
        """Test handling of odds updates from JavaScript.
        This verifies that our message handling system works correctly."""
        test_data = {
            'channel': 'odds_update',
            'data': json.dumps({
                'market': 'Test Market',
                'odds': 1.5
            })
        }
        
        # Create a mock for the odds update handler
        web_view.handle_odds_update = Mock()
        
        # Send a test message
        web_view.handle_js_message(json.dumps(test_data))
        
        # Verify the handler was called with correct data
        web_view.handle_odds_update.assert_called_once()
        called_data = web_view.handle_odds_update.call_args[0][0]
        assert called_data['market'] == 'Test Market'
        assert called_data['odds'] == 1.5
    
    def test_send_to_js(self, web_view):
        """Test sending messages to JavaScript.
        This ensures we can properly communicate back to the frontend."""
        # Mock the page object
        mock_page = Mock()
        web_view.web_view.page = Mock(return_value=mock_page)
        
        # Test data to send
        test_data = {'test': 'data'}
        
        # Send the data
        web_view.send_to_js('test_channel', test_data)
        
        # Verify the correct JavaScript was executed
        mock_page.runJavaScript.assert_called_once()
        js_call = mock_page.runJavaScript.call_args[0][0]
        assert 'handlePythonMessage' in js_call
        assert 'test_channel' in js_call
        assert 'test_data' in js_call
    
    def test_error_handling(self, web_view):
        """Test error handling in message processing.
        This ensures our system gracefully handles malformed messages."""
        # Test with invalid JSON
        with pytest.raises(json.JSONDecodeError):
            web_view.handle_js_message('invalid json')
        
        # Test with missing channel
        web_view.handle_js_message(json.dumps({}))
        
        # Test with invalid channel
        web_view.handle_js_message(json.dumps({
            'channel': 'invalid_channel',
            'data': '{}'
        }))
