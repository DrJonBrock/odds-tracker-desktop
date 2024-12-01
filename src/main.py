#!/usr/bin/env python3

import sys
import logging
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile
from src.ui.main_window import MainWindow

def setup_logging():
    """Configure logging to help us track what's happening in our application.
    This will be invaluable for debugging communication issues."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                log_dir / f"odds_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
            logging.StreamHandler()
        ]
    )

def main():
    # Set up logging first so we can track any startup issues
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Odds Tracker Desktop Application")
    
    try:
        # Initialize Qt application
        app = QApplication(sys.argv)
        
        # Configure QtWebEngine profile for development
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        
        # Create main window - we're starting with just the UI shell
        # We'll add the odds collector and arbitrage detector later
        main_window = MainWindow(odds_collector=None, arbitrage_detector=None)
        main_window.show()
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Fatal error during startup: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()