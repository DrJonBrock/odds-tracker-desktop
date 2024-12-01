#!/usr/bin/env python3
"""
Main entry point for the Odds Tracker Desktop application.
Initializes all components and starts the user interface.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.data_collection.odds_collector import OddsCollector
from src.analysis.arbitrage_detector import ArbitrageDetector
from src.database.database import init_database

# Configure logging
def setup_logging():
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
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Odds Tracker Desktop Application")
    
    try:
        # Initialize database
        init_database()
        
        # Initialize core components
        odds_collector = OddsCollector()
        arbitrage_detector = ArbitrageDetector()
        
        # Start Qt application
        app = QApplication(sys.argv)
        
        # Create and show main window
        main_window = MainWindow(odds_collector, arbitrage_detector)
        main_window.show()
        
        # Start application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()