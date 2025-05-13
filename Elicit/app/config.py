"""
Diagnostic Collection System - Configuration

This module contains configuration settings and constants for the Diagnostic Collection System.
"""

import os
import json
from pathlib import Path

class Config:
    """Configuration settings for the Diagnostic Collection System."""
    
    # Application info
    APP_NAME = "Diagnostic Collection System"
    APP_VERSION = "1.0.0"
    
    # Directory structure
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    EXPORT_DIR = os.path.join(DATA_DIR, "exports")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # File paths
    RULES_FILE = os.path.join(DATA_DIR, "diagnostic_rules.json")
    CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
    INTERACTION_LOG = os.path.join(DATA_DIR, "interaction_log.json")
    
    # UI settings
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    
    # Canvas settings
    CANVAS_WIDTH = 1200
    CANVAS_HEIGHT = 1200
    COLUMN_WIDTH = 250
    NODE_MARGIN = 20
    COLUMN_MARGIN = 50
    INITIAL_X = 50
    INITIAL_Y = 50
    
    # Node types and their column positions
    NODE_TYPES = {
        "problem": {"column": 0, "color": "#FFD700", "title": "PROBLEM"},
        "check": {"column": 1, "color": "#87CEEB", "title": "DIAGNOSTIC CHECK"},
        "condition": {"column": 2, "color": "#98FB98", "title": "CONDITION/OBSERVATION"},
        "action": {"column": 3, "color": "#FFA07A", "title": "ACTION"}
    }
    
    # User preferences - defaults
    PREFERENCES = {
        "auto_save": True,
        "confirm_delete": True,
        "show_tooltips": True,
        "default_view": "table",  # Options: "table", "grid", "tree"
        "theme": "light"  # Options: "light", "dark", "system"
    }
    
    @classmethod
    def load_user_preferences(cls):
        """Load user preferences from config file."""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    user_prefs = json.load(f)
                    # Update preferences with saved values
                    cls.PREFERENCES.update(user_prefs)
        except Exception as e:
            print(f"Error loading user preferences: {str(e)}")
    
    @classmethod
    def save_user_preferences(cls, preferences=None):
        """Save user preferences to config file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cls.CONFIG_FILE), exist_ok=True)
            
            # Use provided preferences or current settings
            prefs_to_save = preferences if preferences else cls.PREFERENCES
            
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(prefs_to_save, f, indent=4)
        except Exception as e:
            print(f"Error saving user preferences: {str(e)}")