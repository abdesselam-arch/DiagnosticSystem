"""
Diagnostic Collection System - Search Panel Widget

This module defines a search panel widget for filtering and finding diagnostic rules,
providing a user-friendly interface for searching the rule collection.
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, 
    QPushButton, QLabel, QGroupBox, QRadioButton, QButtonGroup,
    QCheckBox, QDateEdit, QToolButton, QMenu, QAction, QFrame,
    QSizePolicy, QCompleter, QListWidget
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QStringListModel, QDate
from PyQt5.QtGui import QIcon, QFont, QCursor

logger = logging.getLogger(__name__)

class SearchPanel(QWidget):
    """Widget for searching and filtering diagnostic rules."""
    
    # Signal emitted when search criteria change
    search_changed = pyqtSignal(str, str, dict)  # text, type, advanced_criteria
    
    def __init__(self, parent=None):
        """Initialize the search panel widget.
        
        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.search_history = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface for the search panel."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # === Basic Search Section ===
        basic_layout = QHBoxLayout()
        
        # Search input with history
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search diagnostic knowledge...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self.perform_search)
        
        # Set up completer for search history
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_input.setCompleter(self.search_completer)
        
        basic_layout.addWidget(self.search_input, 3)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Pathway", "Capture", "Rule"])
        self.type_filter.setToolTip("Filter rules by type")
        self.type_filter.currentIndexChanged.connect(self.filter_by_type)
        basic_layout.addWidget(self.type_filter, 1)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        basic_layout.addWidget(self.search_button)
        
        # Advanced search toggle button
        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText("▼")
        self.advanced_toggle.setToolTip("Show advanced search options")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.toggled.connect(self.toggle_advanced_search)
        basic_layout.addWidget(self.advanced_toggle)
        
        main_layout.addLayout(basic_layout)
        
        # === Advanced Search Section ===
        self.advanced_group = QGroupBox("Advanced Search")
        self.advanced_group.setVisible(False)
        advanced_layout = QVBoxLayout(self.advanced_group)
        
        # First row - Date filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Time Range:"))
        
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "Any Time", 
            "Last 24 Hours", 
            "Last Week", 
            "Last Month", 
            "Last Year",
            "Custom Range"
        ])
        self.date_filter.currentIndexChanged.connect(self.update_date_range)
        date_layout.addWidget(self.date_filter, 2)
        
        date_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.date_from.setEnabled(False)  # Disabled until "Custom Range" is selected
        date_layout.addWidget(self.date_from, 1)
        
        date_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setEnabled(False)  # Disabled until "Custom Range" is selected
        date_layout.addWidget(self.date_to, 1)
        
        advanced_layout.addLayout(date_layout)
        
        # Second row - Usage filters
        usage_layout = QHBoxLayout()
        usage_layout.addWidget(QLabel("Usage:"))
        
        self.usage_filter = QComboBox()
        self.usage_filter.addItems([
            "Any Usage", 
            "Never Used", 
            "Used At Least Once", 
            "Frequently Used (5+)",
            "Recently Used"
        ])
        usage_layout.addWidget(self.usage_filter, 2)
        
        usage_layout.addWidget(QLabel("Effectiveness:"))
        
        self.effectiveness_filter = QComboBox()
        self.effectiveness_filter.addItems([
            "Any Effectiveness", 
            "Complete Solution", 
            "Temporary Fix", 
            "Partial Improvement",
            "Ineffective"
        ])
        usage_layout.addWidget(self.effectiveness_filter, 2)
        
        advanced_layout.addLayout(usage_layout)
        
        # Third row - Search options
        options_layout = QHBoxLayout()
        
        self.match_case = QCheckBox("Match Case")
        options_layout.addWidget(self.match_case)
        
        self.search_fields = QComboBox()
        self.search_fields.addItems([
            "All Fields", 
            "Description Only", 
            "Actions Only", 
            "Conditions Only"
        ])
        options_layout.addWidget(QLabel("Search In:"))
        options_layout.addWidget(self.search_fields)
        
        options_layout.addStretch(1)
        
        # Reset button
        self.reset_button = QPushButton("Reset Filters")
        self.reset_button.clicked.connect(self.reset_filters)
        options_layout.addWidget(self.reset_button)
        
        advanced_layout.addLayout(options_layout)
        
        main_layout.addWidget(self.advanced_group)
        
        # Add a horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Search history section
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Recent Searches:"))
        
        self.clear_history_btn = QToolButton()
        self.clear_history_btn.setText("Clear")
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.clear_history_btn.setToolTip("Clear search history")
        history_layout.addWidget(self.clear_history_btn)
        
        main_layout.addLayout(history_layout)
        
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(80)
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemClicked.connect(self.use_history_item)
        main_layout.addWidget(self.history_list)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    
    def perform_search(self):
        """Perform a search with the current criteria."""
        search_text = self.search_input.text().strip()
        rule_type = self.type_filter.currentText()
        
        # Only add non-empty searches to history
        if search_text and search_text not in self.search_history:
            self.add_to_history(search_text)
        
        # Collect advanced criteria if visible
        advanced_criteria = {}
        if self.advanced_group.isVisible():
            # Date range
            date_filter = self.date_filter.currentText()
            if date_filter != "Any Time":
                if date_filter == "Custom Range":
                    advanced_criteria["date_from"] = self.date_from.date().toString(Qt.ISODate)
                    advanced_criteria["date_to"] = self.date_to.date().toString(Qt.ISODate)
                else:
                    # Calculate date range based on selection
                    date_ranges = {
                        "Last 24 Hours": timedelta(days=1),
                        "Last Week": timedelta(days=7),
                        "Last Month": timedelta(days=30),
                        "Last Year": timedelta(days=365)
                    }
                    if date_filter in date_ranges:
                        from_date = datetime.now() - date_ranges[date_filter]
                        advanced_criteria["date_from"] = from_date.date().isoformat()
                        advanced_criteria["date_to"] = datetime.now().date().isoformat()
            
            # Usage filter
            usage_filter = self.usage_filter.currentText()
            if usage_filter != "Any Usage":
                advanced_criteria["usage"] = usage_filter
            
            # Effectiveness filter
            effectiveness_filter = self.effectiveness_filter.currentText()
            if effectiveness_filter != "Any Effectiveness":
                advanced_criteria["effectiveness"] = effectiveness_filter
            
            # Search options
            if self.match_case.isChecked():
                advanced_criteria["match_case"] = True
            
            search_fields = self.search_fields.currentText()
            if search_fields != "All Fields":
                advanced_criteria["search_fields"] = search_fields
        
        # Emit signal with search criteria
        self.search_changed.emit(search_text, rule_type, advanced_criteria)
    
    def filter_by_type(self):
        """Filter rules by the selected type."""
        # Trigger a search with the current text and new type filter
        self.perform_search()
    
    def toggle_advanced_search(self, checked):
        """Toggle visibility of advanced search options.
        
        Args:
            checked (bool): Whether the toggle button is checked.
        """
        self.advanced_group.setVisible(checked)
        
        # Update toggle button text
        if checked:
            self.advanced_toggle.setText("▲")
            self.advanced_toggle.setToolTip("Hide advanced search options")
        else:
            self.advanced_toggle.setText("▼")
            self.advanced_toggle.setToolTip("Show advanced search options")
        
        # Adjust widget layout
        self.adjustSize()
    
    def update_date_range(self, index):
        """Update the date range controls based on the selected filter.
        
        Args:
            index (int): Index of the selected date filter.
        """
        # Enable custom date range inputs only when "Custom Range" is selected
        custom_range_selected = self.date_filter.currentText() == "Custom Range"
        self.date_from.setEnabled(custom_range_selected)
        self.date_to.setEnabled(custom_range_selected)
    
    def reset_filters(self):
        """Reset all search filters to their default values."""
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)  # "All Types"
        
        # Reset advanced filters
        self.date_filter.setCurrentIndex(0)  # "Any Time"
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.usage_filter.setCurrentIndex(0)  # "Any Usage"
        self.effectiveness_filter.setCurrentIndex(0)  # "Any Effectiveness"
        self.match_case.setChecked(False)
        self.search_fields.setCurrentIndex(0)  # "All Fields"
        
        # Clear any active filters by performing an empty search
        self.perform_search()
    
    def add_to_history(self, search_text):
        """Add a search term to the history.
        
        Args:
            search_text (str): The search text to add.
        """
        # Limit history size
        MAX_HISTORY = 10
        
        # Add to history if not already present
        if search_text not in self.search_history:
            self.search_history.insert(0, search_text)
            # Trim to maximum size
            if len(self.search_history) > MAX_HISTORY:
                self.search_history = self.search_history[:MAX_HISTORY]
            
            # Update history list widget
            self.update_history_list()
            
            # Update completer model
            self.update_completer()
    
    def update_history_list(self):
        """Update the history list widget."""
        self.history_list.clear()
        for item in self.search_history:
            self.history_list.addItem(item)
    
    def update_completer(self):
        """Update the search input completer with history items."""
        model = QStringListModel()
        model.setStringList(self.search_history)
        self.search_completer.setModel(model)
    
    def use_history_item(self, item):
        """Use a history item as the current search.
        
        Args:
            item (QListWidgetItem): The selected history item.
        """
        search_text = item.text()
        self.search_input.setText(search_text)
        self.perform_search()
    
    def clear_history(self):
        """Clear the search history."""
        self.search_history = []
        self.update_history_list()
        self.update_completer()
        
    def set_available_types(self, types):
        """Set the available rule types for filtering.
        
        Args:
            types (list): List of available rule types.
        """
        # Store current selection
        current_text = self.type_filter.currentText()
        
        # Clear and add new items
        self.type_filter.clear()
        self.type_filter.addItem("All Types")
        
        for type_name in types:
            self.type_filter.addItem(type_name)
        
        # Restore previous selection if possible
        index = self.type_filter.findText(current_text)
        if index >= 0:
            self.type_filter.setCurrentIndex(index)