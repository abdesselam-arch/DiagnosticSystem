#!/usr/bin/env python3
"""
Diagnostic Collection System - Main Application Entry Point

This module initializes and runs the Diagnostic Collection System application,
a tool for capturing, organizing, and retrieving diagnostic knowledge.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diagnostic_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the application environment."""
    from config import Config
    
    # Ensure data directories exist
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.EXPORT_DIR, exist_ok=True)
    
    # Initialize default data files if they don't exist
    if not os.path.exists(Config.RULES_FILE):
        import json
        with open(Config.RULES_FILE, 'w') as f:
            json.dump({"rules": []}, f)
            
    logger.info("Environment setup complete")
    return Config

def main():
    """Main application entry point."""
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Diagnostic Collection System")
        
        # Set up environment and config
        config = setup_environment()
        
        # Import here to avoid circular imports
        from ui.main_window import MainWindow
        from services.storage_service import StorageService
        
        # Initialize services
        storage_service = StorageService(config)
        
        # Create and show main window
        main_window = MainWindow(storage_service)
        main_window.setWindowTitle("Diagnostic Collection System")
        main_window.setGeometry(100, 100, 1200, 800)
        main_window.show()
        
        logger.info("Application started successfully")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()