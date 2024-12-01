import pytest
from PyQt6.QtWidgets import QApplication
import sys

@pytest.fixture(scope='session')
def qt_application():
    """Creates a QApplication instance for UI testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def main_window(qt_application, odds_collector, arbitrage_detector):
    """Creates a MainWindow instance for UI testing"""
    from src.ui.main_window import MainWindow
    window = MainWindow(odds_collector, arbitrage_detector)
    return window