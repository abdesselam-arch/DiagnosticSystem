"""
Diagnostic Collection System - Diagnostic Node Widget

This module defines the widget representing a single node in a diagnostic pathway,
such as a problem, check, condition, or action node.
"""

import logging
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QComboBox, 
    QSlider, QLineEdit, QMenuBar, QMenu, QAction, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QDrag, QPixmap, QCursor

logger = logging.getLogger(__name__)

class DiagnosticNodeWidget(QFrame):
    """Widget representing a single diagnostic node in the pathway."""
    
    # Signal emitted when the node's content changes
    content_changed = pyqtSignal()
    
    def __init__(self, node_type="check", node_id=None, parent=None):
        """Initialize the node widget with a specified type.
        
        Args:
            node_type (str): The type of node - one of "problem", "check", "condition", "action"
            node_id (int, optional): Unique identifier for the node. If None, one will be generated.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.node_type = node_type
        self.node_id = node_id if node_id is not None else id(self)  # Unique identifier
        self.connections = []  # List of connected node IDs
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface for the node."""
        # Set up basic frame appearance
        self.setMinimumSize(200, 120)
        self.setMaximumSize(300, 200)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Different colors based on node type
        color_map = {
            "problem": "#FFD700",  # Gold
            "check": "#87CEEB",    # Sky blue
            "condition": "#98FB98", # Pale green
            "action": "#FFA07A"    # Light salmon
        }
        
        self.setStyleSheet(f"background-color: {color_map.get(self.node_type, '#FFFFFF')};")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title based on node type
        title_map = {
            "problem": "PROBLEM",
            "check": "DIAGNOSTIC CHECK",
            "condition": "CONDITION/OBSERVATION",
            "action": "ACTION"
        }
        
        self.title_label = QLabel(title_map.get(self.node_type, "NODE"))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.title_label)
        
        # Content - what this node represents
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Enter description...")
        self.content_edit.textChanged.connect(self.content_changed.emit)
        layout.addWidget(self.content_edit)
        
        # Node-specific controls
        if self.node_type == "check":
            # Add options for diagnostic checks
            check_layout = QHBoxLayout()
            check_layout.addWidget(QLabel("Type:"))
            
            self.check_type = QComboBox()
            self.check_type.addItems([
                "Visual Inspection", 
                "Measurement", 
                "Test Run", 
                "Parameter Check", 
                "Other"
            ])
            self.check_type.currentIndexChanged.connect(self.content_changed.emit)
            check_layout.addWidget(self.check_type)
            
            layout.addLayout(check_layout)
        
        elif self.node_type == "condition":
            # Add options for conditions
            condition_layout = QHBoxLayout()
            condition_layout.addWidget(QLabel("Severity:"))
            
            self.condition_severity = QComboBox()
            self.condition_severity.addItems([
                "Critical", 
                "Major", 
                "Minor", 
                "Normal"
            ])
            self.condition_severity.currentIndexChanged.connect(self.content_changed.emit)
            condition_layout.addWidget(self.condition_severity)
            
            layout.addLayout(condition_layout)
        
        elif self.node_type == "action":
            # Add options for actions
            action_layout = QHBoxLayout()
            action_layout.addWidget(QLabel("Impact:"))
            
            self.action_impact = QComboBox()
            self.action_impact.addItems([
                "Immediate Fix", 
                "Temporary Solution", 
                "Adjustment", 
                "Investigation"
            ])
            self.action_impact.currentIndexChanged.connect(self.content_changed.emit)
            action_layout.addWidget(self.action_impact)
            
            layout.addLayout(action_layout)
            
            # Add effectiveness rating
            effect_layout = QHBoxLayout()
            effect_layout.addWidget(QLabel("Effectiveness:"))
            
            self.effectiveness = QSlider(Qt.Horizontal)
            self.effectiveness.setMinimum(1)
            self.effectiveness.setMaximum(5)
            self.effectiveness.setValue(3)
            self.effectiveness.setTickPosition(QSlider.TicksBelow)
            self.effectiveness.setTickInterval(1)
            self.effectiveness.valueChanged.connect(self.content_changed.emit)
            effect_layout.addWidget(self.effectiveness)
            
            layout.addLayout(effect_layout)
        
    def mousePressEvent(self, event):
        """Handle mouse press events to initiate drag operations."""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag operations."""
        if not (event.buttons() & Qt.LeftButton):
            return
            
        # Check if the mouse has moved far enough to be a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        # Start drag operation
        drag = QDrag(self)
        
        # Create mime data via parent canvas method
        if self.parent() and hasattr(self.parent(), 'create_mime_data'):
            mime_data = self.parent().create_mime_data(self)
            if mime_data:
                drag.setMimeData(mime_data)
                
                # Create drag pixmap
                pixmap = QPixmap(self.size())
                self.render(pixmap)
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.pos())
                
                # Execute drag operation
                drag.exec_(Qt.MoveAction)
    
    def set_content(self, content):
        """Set the content text for this node.
        
        Args:
            content (str): Text content for the node.
        """
        self.content_edit.setPlainText(content)
    
    def get_content(self):
        """Get the content text for this node.
        
        Returns:
            str: The current content text.
        """
        return self.content_edit.toPlainText()
    
    def set_check_type(self, check_type):
        """Set the check type for a check node.
        
        Args:
            check_type (str): The check type to set.
        """
        if self.node_type == "check" and hasattr(self, "check_type"):
            index = self.check_type.findText(check_type)
            if index >= 0:
                self.check_type.setCurrentIndex(index)
    
    def get_check_type(self):
        """Get the check type for a check node.
        
        Returns:
            str: The current check type, or None if not applicable.
        """
        if self.node_type == "check" and hasattr(self, "check_type"):
            return self.check_type.currentText()
        return None
    
    def set_condition_severity(self, severity):
        """Set the severity for a condition node.
        
        Args:
            severity (str): The severity level to set.
        """
        if self.node_type == "condition" and hasattr(self, "condition_severity"):
            index = self.condition_severity.findText(severity)
            if index >= 0:
                self.condition_severity.setCurrentIndex(index)
    
    def get_condition_severity(self):
        """Get the severity for a condition node.
        
        Returns:
            str: The current severity level, or None if not applicable.
        """
        if self.node_type == "condition" and hasattr(self, "condition_severity"):
            return self.condition_severity.currentText()
        return None
    
    def set_action_impact(self, impact):
        """Set the impact type for an action node.
        
        Args:
            impact (str): The impact type to set.
        """
        if self.node_type == "action" and hasattr(self, "action_impact"):
            index = self.action_impact.findText(impact)
            if index >= 0:
                self.action_impact.setCurrentIndex(index)
    
    def get_action_impact(self):
        """Get the impact type for an action node.
        
        Returns:
            str: The current impact type, or None if not applicable.
        """
        if self.node_type == "action" and hasattr(self, "action_impact"):
            return self.action_impact.currentText()
        return None
    
    def set_effectiveness(self, value):
        """Set the effectiveness value for an action node.
        
        Args:
            value (int): The effectiveness value (1-5).
        """
        if self.node_type == "action" and hasattr(self, "effectiveness"):
            self.effectiveness.setValue(value)
    
    def get_effectiveness(self):
        """Get the effectiveness value for an action node.
        
        Returns:
            int: The current effectiveness value, or None if not applicable.
        """
        if self.node_type == "action" and hasattr(self, "effectiveness"):
            return self.effectiveness.value()
        return None
    
    def get_data(self):
        """Export node data as a dictionary.
        
        Returns:
            dict: Dictionary containing all node data.
        """
        data = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "content": self.get_content(),
            "connections": self.connections
        }
        
        # Add node-specific data
        if self.node_type == "check":
            data["check_type"] = self.get_check_type()
        elif self.node_type == "condition":
            data["severity"] = self.get_condition_severity()
        elif self.node_type == "action":
            data["impact"] = self.get_action_impact()
            data["effectiveness"] = self.get_effectiveness()
            
        return data
        
    def set_data(self, data):
        """Import node data from a dictionary.
        
        Args:
            data (dict): Dictionary containing node data.
        """
        self.node_id = data.get("node_id", self.node_id)
        self.node_type = data.get("node_type", self.node_type)
        self.connections = data.get("connections", [])
        self.set_content(data.get("content", ""))
        
        # Set node-specific data
        if self.node_type == "check":
            self.set_check_type(data.get("check_type", ""))
                
        elif self.node_type == "condition":
            self.set_condition_severity(data.get("severity", ""))
                
        elif self.node_type == "action":
            self.set_action_impact(data.get("impact", ""))
            
            if data.get("effectiveness") is not None:
                self.set_effectiveness(data.get("effectiveness", 3))