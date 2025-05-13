"""
Diagnostic Collection System - Rule Table Widget

This module defines a specialized table widget for displaying and managing diagnostic rules,
providing a rich interface for interacting with the rule collection.
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QHBoxLayout, 
    QPushButton, QMenu, QAction, QAbstractItemView, QStyledItemDelegate,
    QToolTip, QMessageBox, QComboBox, QLabel, QStyle
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor, QBrush

logger = logging.getLogger(__name__)

class ActionButtonsWidget(QWidget):
    """Widget containing action buttons for a table row."""
    
    def __init__(self, parent=None):
        """Initialize the widget with action buttons.
        
        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # View button
        self.view_btn = QPushButton("View")
        self.view_btn.setToolTip("View rule details")
        self.view_btn.setFixedWidth(60)
        layout.addWidget(self.view_btn)
        
        # Edit button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setToolTip("Edit this rule")
        self.edit_btn.setFixedWidth(60)
        layout.addWidget(self.edit_btn)
        
        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setToolTip("Apply this rule")
        self.apply_btn.setFixedWidth(60)
        layout.addWidget(self.apply_btn)

class RuleTypeDelegate(QStyledItemDelegate):
    """Delegate for displaying rule type with appropriate styling."""
    
    def paint(self, painter, option, index):
        """Custom painting for rule type cells.
        
        Args:
            painter: The painter to use
            option: Style options
            index: Model index
        """
        # Get the rule type text
        rule_type = index.data(Qt.DisplayRole)
        
        # Set background color based on rule type
        if rule_type == "Pathway":
            background_color = QColor(220, 240, 255)  # Light blue
        elif rule_type == "Capture":
            background_color = QColor(255, 240, 220)  # Light orange
        else:  # "Rule"
            background_color = QColor(240, 255, 240)  # Light green
        
        # Draw background
        painter.save()
        painter.fillRect(option.rect, background_color)
        
        # Draw text centered in the cell
        painter.setPen(Qt.black)
        painter.drawText(
            option.rect.adjusted(5, 0, -5, 0),
            Qt.AlignCenter | Qt.AlignVCenter,
            rule_type
        )
        
        # Draw border if selected
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.darkBlue, 2))
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            
        painter.restore()
    
    def sizeHint(self, option, index):
        """Provide the size hint for the delegate.
        
        Args:
            option: Style options
            index: Model index
            
        Returns:
            QSize: The size hint
        """
        return QSize(80, 30)

class RuleTable(QTableWidget):
    """Specialized table widget for displaying diagnostic rules."""
    
    # Signals for rule actions
    view_rule = pyqtSignal(int)      # Signal emitted when a rule should be viewed
    edit_rule = pyqtSignal(int)      # Signal emitted when a rule should be edited
    apply_rule = pyqtSignal(int)     # Signal emitted when a rule should be applied
    delete_rule = pyqtSignal(list)   # Signal emitted when rules should be deleted
    duplicate_rule = pyqtSignal(int) # Signal emitted when a rule should be duplicated
    export_rule = pyqtSignal(int)    # Signal emitted when a rule should be exported
    
    def __init__(self, parent=None):
        """Initialize the rule table widget.
        
        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface for the table."""
        # Set up table structure
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["ID", "Type", "Description", "Last Used", "Actions"])
        
        # Configure table appearance and behavior
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setShowGrid(True)
        
        # Configure column widths
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.setColumnWidth(0, 50)   # ID column
        self.setColumnWidth(1, 80)   # Type column
        self.setColumnWidth(3, 150)  # Last Used column
        self.setColumnWidth(4, 190)  # Actions column
        
        # Set row height
        self.verticalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setVisible(False)
        
        # Set up type delegate for specialized rendering
        self.setItemDelegateForColumn(1, RuleTypeDelegate())
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set tooltip behavior
        self.setMouseTracking(True)
    
    def populate_rules(self, rules):
        """Populate the table with rules.
        
        Args:
            rules (list): List of rule dictionaries.
        """
        # Clear any existing rows
        self.setRowCount(0)
        
        # Add new rows
        for i, rule in enumerate(rules):
            self.add_rule(rule, i)
    
    def add_rule(self, rule, row=None):
        """Add a single rule to the table.
        
        Args:
            rule (dict): Rule dictionary.
            row (int, optional): Row index to insert at. If None, appends to the end.
        """
        if row is None:
            row = self.rowCount()
            self.insertRow(row)
        
        # ID Column
        id_item = QTableWidgetItem(str(row + 1))
        id_item.setData(Qt.UserRole, row)  # Store actual index for retrieval
        id_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 0, id_item)
        
        # Type Column
        type_item = QTableWidgetItem()
        if rule.get("pathway_data"):
            type_item.setText("Pathway")
            type_item.setToolTip("Visual diagnostic pathway")
        elif rule.get("metadata", {}).get("problem_type"):
            type_item.setText("Capture")
            type_item.setToolTip("Quick captured diagnostic")
        else:
            type_item.setText("Rule")
            type_item.setToolTip("Diagnostic rule")
        type_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 1, type_item)
        
        # Description Column
        description = self._get_rule_description(rule)
        desc_item = QTableWidgetItem(description)
        desc_item.setToolTip(rule.get("text", ""))
        self.setItem(row, 2, desc_item)
        
        # Last Used Column
        last_used = rule.get("last_used")
        last_used_item = QTableWidgetItem()
        if last_used:
            try:
                date_obj = datetime.fromisoformat(last_used)
                friendly_date = date_obj.strftime("%Y-%m-%d %H:%M")
                last_used_item.setText(friendly_date)
                
                # Add usage count if available
                use_count = rule.get("use_count", 0)
                if use_count > 0:
                    last_used_item.setToolTip(f"Used {use_count} times")
            except (ValueError, TypeError):
                last_used_item.setText("Unknown")
        else:
            last_used_item.setText("Never")
        self.setItem(row, 3, last_used_item)
        
        # Actions Column - using a widget with buttons
        actions_widget = ActionButtonsWidget()
        
        # Connect button signals
        actions_widget.view_btn.clicked.connect(lambda checked, r=row: self.view_rule.emit(r))
        actions_widget.edit_btn.clicked.connect(lambda checked, r=row: self.edit_rule.emit(r))
        actions_widget.apply_btn.clicked.connect(lambda checked, r=row: self.apply_rule.emit(r))
        
        self.setCellWidget(row, 4, actions_widget)
    
    def _get_rule_description(self, rule):
        """Get a concise description of the rule for display.
        
        Args:
            rule (dict): Rule dictionary.
            
        Returns:
            str: A concise description of the rule.
        """
        # For visual pathways, try to extract a problem statement
        if rule.get("pathway_data"):
            nodes = rule.get("pathway_data", {}).get("nodes", {})
            for node_id, node in nodes.items():
                if node.get("node_type") == "problem" and node.get("content"):
                    content = node.get("content")
                    return content[:80] + "..." if len(content) > 80 else content
        
        # For quick captures, use the problem type and description
        metadata = rule.get("metadata", {})
        if metadata.get("problem_type") and metadata.get("problem_type") != "Select type...":
            problem_text = rule.get("text", "")
            # Try to extract the problem part
            if "problem is '" in problem_text:
                try:
                    problem_part = problem_text.split("problem is '")[1].split("'")[0]
                    return problem_part[:80] + "..." if len(problem_part) > 80 else problem_part
                except IndexError:
                    pass
                    
            # Use the first part of the rule text
            return problem_text[:80] + "..." if len(problem_text) > 80 else problem_text
        
        # Default to the rule text
        text = rule.get("text", "")
        # If it's a complex rule with IF/THEN structure, extract the IF part
        if "IF " in text and ", THEN" in text:
            if_part = text.split(", THEN")[0].replace("IF ", "")
            return if_part[:80] + "..." if len(if_part) > 80 else if_part
        
        # Fallback to truncated rule text
        return text[:80] + "..." if len(text) > 80 else text
    
    def show_context_menu(self, position):
        """Show a context menu for the selected rule(s).
        
        Args:
            position (QPoint): Position where the menu should be displayed.
        """
        # Create menu
        menu = QMenu()
        
        # Get selected rows
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            return
        
        # Single selection actions
        if len(selected_rows) == 1:
            view_action = menu.addAction("View Rule")
            view_action.triggered.connect(lambda: self.view_rule.emit(selected_rows[0]))
            
            edit_action = menu.addAction("Edit Rule")
            edit_action.triggered.connect(lambda: self.edit_rule.emit(selected_rows[0]))
            
            apply_action = menu.addAction("Apply Rule")
            apply_action.triggered.connect(lambda: self.apply_rule.emit(selected_rows[0]))
            
            menu.addSeparator()
            
            duplicate_action = menu.addAction("Duplicate Rule")
            duplicate_action.triggered.connect(lambda: self.duplicate_rule.emit(selected_rows[0]))
            
            export_action = menu.addAction("Export Rule")
            export_action.triggered.connect(lambda: self.export_rule.emit(selected_rows[0]))
        
        # Multi-selection actions
        delete_action = menu.addAction(f"Delete Selected Rule{'' if len(selected_rows) == 1 else 's'}")
        delete_action.triggered.connect(lambda: self.delete_rule.emit(selected_rows))
        
        # Show the menu
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def get_selected_rows(self):
        """Get the list of selected row indices.
        
        Returns:
            list: List of selected row indices.
        """
        selected_rows = []
        for index in self.selectedIndexes():
            row = index.row()
            if row not in selected_rows:
                selected_rows.append(row)
        return selected_rows
    
    def filter_rules(self, text, rule_type=None):
        """Filter the displayed rules based on search text and rule type.
        
        Args:
            text (str): Search text to filter by.
            rule_type (str, optional): Rule type to filter by.
        """
        text = text.lower()
        
        for row in range(self.rowCount()):
            # Get row data
            type_item = self.item(row, 1)
            desc_item = self.item(row, 2)
            
            # Check type filter
            show_row = True
            if rule_type and rule_type != "All Types":
                if type_item.text() != rule_type:
                    show_row = False
            
            # Check text filter if row still visible
            if show_row and text:
                # Check if text is in description
                if text not in desc_item.text().lower():
                    # Also check tooltip (full rule text)
                    if text not in desc_item.toolTip().lower():
                        show_row = False
            
            # Show or hide the row
            self.setRowHidden(row, not show_row)
    
    def clear_filters(self):
        """Clear all filters and show all rows."""
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)
    
    def highlight_row(self, row):
        """Temporarily highlight a specific row.
        
        Args:
            row (int): The row index to highlight.
        """
        if row < 0 or row >= self.rowCount():
            return
            
        # Select the row
        self.selectRow(row)
        
        # Scroll to the row
        self.scrollToItem(self.item(row, 0))
        
        # Flash effect
        for item in [self.item(row, i) for i in range(3)]:  # Skip the actions column
            original_bg = item.background()
            highlight_bg = QBrush(QColor(255, 255, 0, 100))  # Light yellow
            
            item.setBackground(highlight_bg)
            
            # Reset the background after a delay
            QTimer.singleShot(1000, lambda i=item, bg=original_bg: i.setBackground(bg))