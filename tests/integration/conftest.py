import pytest
from PyQt6.QtWidgets import QApplication
import sys
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector

@pytest.fixture(scope='session')
def qt_application():
    """Creates and maintains a QApplication instance for UI testing.
    
    This fixture uses session scope to ensure we only create one
    QApplication instance for all tests, as PyQt only allows one
    instance per process.
    
    Returns:
        QApplication instance for UI testing
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def main_window(qt_application):
    """Creates a MainWindow instance for UI testing.
    
    Args:
        qt_application: The QApplication instance (automatically provided by pytest)
        
    Returns:
        A configured MainWindow instance ready for testing
    """
    from src.ui.main_window import MainWindow
    
    # Create core components
    odds_collector = OddsCollector()
    arbitrage_detector = ArbitrageDetector()
    
    # Create and return window instance
    window = MainWindow(odds_collector, arbitrage_detector)
    return window

@pytest.fixture
def mock_alert_threshold():
    """Provides a standard alert threshold for testing.
    
    Returns:
        float: The threshold value (1.0 = 1% profit)
    """
    return 1.0