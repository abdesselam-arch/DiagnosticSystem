"""
Diagnostic Collection System - Diagnostic Pathway Canvas

This module defines the canvas widget for building and visualizing diagnostic pathways,
providing a workspace where users can add, connect, and organize diagnostic nodes.
"""

import logging
import numpy as np
from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QApplication, QMessageBox,
    QMenu, QMenuBar, QAction, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QPoint, QMimeData, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QDrag, QPixmap

from ui.widgets.diagnostic_node import DiagnosticNodeWidget

logger = logging.getLogger(__name__)

class DiagnosticPathwayCanvas(QScrollArea):
    """Canvas for creating and visualizing diagnostic pathways with a columnar layout."""
    
    # Signal emitted when the pathway is updated
    pathway_updated = pyqtSignal()
    
    # Node type to column mapping - this defines our visual structure
    NODE_TYPE_COLUMNS = {
        "problem": 0,
        "check": 1,
        "condition": 2, 
        "action": 3
    }
    
    # Visual settings for layout
    COLUMN_WIDTH = 250  # Width of each column
    NODE_MARGIN = 20    # Vertical spacing between nodes
    COLUMN_MARGIN = 50  # Horizontal spacing between columns
    INITIAL_X = 50      # Starting X position
    INITIAL_Y = 50      # Starting Y position
    
    def __init__(self, parent=None):
        """Initialize the canvas widget.
        
        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface for the canvas."""
        # Create a widget to hold the canvas content
        self.canvas_widget = QWidget()
        self.canvas_widget.setMinimumSize(1200, 1200)  # Large canvas area
        
        # Create and set the layout for canvas_widget
        canvas_layout = QVBoxLayout(self.canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setWidget(self.canvas_widget)
        self.setWidgetResizable(True)
        
        # Dictionary to store all nodes by ID
        self.nodes = {}
        
        # Track connections between nodes
        self.connections = []
        
        # Track if we're connecting nodes
        self.connecting = False
        self.source_node = None
        
        # Track if we are currently dragging
        self.dragging = False
        self.current_node = None
        
        # Track the next Y position for each column to enable automatic vertical stacking
        self.column_y_positions = {
            0: self.INITIAL_Y,  # Problem column
            1: self.INITIAL_Y,  # Check column 
            2: self.INITIAL_Y,  # Condition column
            3: self.INITIAL_Y   # Action column
        }
        
        # Set focus policy to enable keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Enable mouse tracking for connection drawing
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """Render the canvas contents, including connections between nodes."""
        super().paintEvent(event)
        
        # This will paint the widget itself, then we'll add our connections
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw column headers
        self._draw_column_headers(painter)
        
        # Draw connections between nodes
        self._draw_connections(painter)
        
        # Draw temporary connection line if in connecting mode
        if self.connecting and self.source_node:
            self._draw_connecting_line(painter)
    
    def _draw_column_headers(self, painter):
        """Draw column headers at the top of each column.
        
        Args:
            painter (QPainter): The painter to use for drawing.
        """
        # Set up text properties
        painter.setFont(QApplication.font())
        
        column_titles = {
            0: "Problems",
            1: "Diagnostic Checks",
            2: "Observations/Conditions",
            3: "Actions"
        }
        
        # Column header colors to match node colors
        column_colors = {
            0: QColor("#FFD700"),  # Gold
            1: QColor("#87CEEB"),  # Sky blue
            2: QColor("#98FB98"),  # Pale green
            3: QColor("#FFA07A")   # Light salmon
        }
        
        for column, title in column_titles.items():
            x_pos = self.INITIAL_X + column * (self.COLUMN_WIDTH + self.COLUMN_MARGIN)
            
            # Create a filled rect for the header
            header_rect = QColor(column_colors[column])
            header_rect.setAlpha(180)  # Semi-transparent
            painter.fillRect(x_pos, 10, self.COLUMN_WIDTH, 30, header_rect)
            
            # Draw border
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.drawRect(x_pos, 10, self.COLUMN_WIDTH, 30)
            
            # Draw text
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(
                x_pos + 10, 
                10, 
                self.COLUMN_WIDTH - 20, 
                30, 
                Qt.AlignCenter, 
                title
            )
    
    def _draw_connections(self, painter):
        """Draw connection lines between nodes.
        
        Args:
            painter (QPainter): The painter to use for drawing.
        """
        for connection in self.connections:
            source_id, target_id = connection
            if source_id in self.nodes and target_id in self.nodes:
                source_node = self.nodes[source_id]
                target_node = self.nodes[target_id]
                
                # Calculate connection points (center of each widget)
                source_pos = source_node.mapTo(self.widget(), QPoint(source_node.width() // 2, source_node.height() // 2))
                target_pos = target_node.mapTo(self.widget(), QPoint(target_node.width() // 2, target_node.height() // 2))
                
                # Adjust for scroll position
                source_pos = source_pos - QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
                target_pos = target_pos - QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
                
                # Draw the arrow
                pen = QPen(QColor(0, 0, 0))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(source_pos, target_pos)
                
                # Draw arrowhead
                arrow_size = 10
                angle = np.arctan2(target_pos.y() - source_pos.y(), target_pos.x() - source_pos.x())
                arrow_p1 = QPoint(
                    int(target_pos.x() - arrow_size * np.cos(angle - np.pi/6)),
                    int(target_pos.y() - arrow_size * np.sin(angle - np.pi/6))
                )
                arrow_p2 = QPoint(
                    int(target_pos.x() - arrow_size * np.cos(angle + np.pi/6)),
                    int(target_pos.y() - arrow_size * np.sin(angle + np.pi/6))
                )
                
                painter.setBrush(QColor(0, 0, 0))
                points = [target_pos, arrow_p1, arrow_p2]
                painter.drawPolygon(*points)
    
    def _draw_connecting_line(self, painter):
        """Draw a temporary line when connecting nodes.
        
        Args:
            painter (QPainter): The painter to use for drawing.
        """
        source_pos = self.source_node.mapTo(self.widget(), QPoint(self.source_node.width() // 2, self.source_node.height() // 2))
        source_pos = source_pos - QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        
        # Get current mouse position in viewport coordinates
        cursor_pos = self.viewport().mapFromGlobal(QCursor.pos())
        
        pen = QPen(QColor(0, 0, 255))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(source_pos, cursor_pos)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
        super().mouseMoveEvent(event)
        
        # Redraw if we're in connection mode to update the temporary line
        if self.connecting:
            self.viewport().update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for connections.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
        super().mouseReleaseEvent(event)
        
        if self.connecting and self.source_node:
            # Check if we're over any node
            for node_id, node in self.nodes.items():
                if node != self.source_node and node.underMouse():
                    # Create a connection
                    self.add_connection(self.source_node.node_id, node.node_id)
                    QMessageBox.information(self, "Connection Created", "Nodes connected successfully!")
                    self.pathway_updated.emit()
                    break
            
            # Reset connection state
            self.connecting = False
            self.source_node = None
            self.viewport().update()  # Redraw to remove the temporary line
    
    def calculate_node_position(self, node_type):
        """Calculate the position for a new node based on its type and layout.
        
        Args:
            node_type (str): The type of node.
            
        Returns:
            QPoint: The calculated position for the node.
        """
        column = self.NODE_TYPE_COLUMNS.get(node_type, 0)
        x_position = self.INITIAL_X + column * (self.COLUMN_WIDTH + self.COLUMN_MARGIN)
        
        # Find the lowest y-position of existing nodes in this column
        max_y = self.INITIAL_Y
        for node in self.nodes.values():
            if node.node_type == node_type:
                node_bottom = node.y() + node.height() + self.NODE_MARGIN
                max_y = max(max_y, node_bottom)
        
        y_position = max_y
        
        # Update the column's next Y position
        self.column_y_positions[column] = y_position + self.NODE_MARGIN + 120
        
        return QPoint(x_position, y_position)
    
    def add_node(self, node_type, position=None):
        """Add a new node to the canvas with automatic positioning.
        
        Args:
            node_type (str): The type of node to add.
            position (QPoint, optional): The position to place the node. If None, 
                                         position will be calculated automatically.
        
        Returns:
            DiagnosticNodeWidget: The newly created node widget.
        """
        new_node = DiagnosticNodeWidget(node_type)
        new_node.setParent(self.canvas_widget)
        
        # If position not provided, calculate based on node type and layout
        if position is None:
            position = self.calculate_node_position(node_type)
            
        new_node.move(position)
        new_node.show()
        
        # Store the node
        self.nodes[new_node.node_id] = new_node
        
        # Right-click context menu for nodes
        new_node.setContextMenuPolicy(Qt.CustomContextMenu)
        new_node.customContextMenuRequested.connect(
            lambda pos, node=new_node: self.show_node_context_menu(pos, node)
        )
        
        # Connect the node's content changed signal
        new_node.content_changed.connect(self.pathway_updated)
        
        self.pathway_updated.emit()
        return new_node
    
    def add_connected_node(self, source_node, target_node_type):
        """Add a new node of specified type and automatically connect it to the source node.
        
        Args:
            source_node (DiagnosticNodeWidget): The source node to connect from.
            target_node_type (str): The type of node to create and connect to.
            
        Returns:
            DiagnosticNodeWidget: The newly created node widget.
        """
        target_node = self.add_node(target_node_type)
        self.add_connection(source_node.node_id, target_node.node_id)
        return target_node
    
    def add_connection(self, source_id, target_id):
        """Add a connection between two nodes.
        
        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            
        Returns:
            bool: True if the connection was added, False if it already exists.
        """
        if (source_id, target_id) in self.connections:
            return False
            
        self.connections.append((source_id, target_id))
        
        # Update the source node's connections list
        if source_id in self.nodes:
            source_node = self.nodes[source_id]
            if target_id not in source_node.connections:
                source_node.connections.append(target_id)
        
        self.pathway_updated.emit()
        self.viewport().update()
        return True
        
    def show_node_context_menu(self, pos, node):
        """Show context menu for a node with enhanced options.
        
        Args:
            pos (QPoint): The position where the menu should appear.
            node (DiagnosticNodeWidget): The node that was right-clicked.
        """
        context_menu = QMenu()
        
        # Add connected node submenu - streamlined workflow
        add_connected_menu = context_menu.addMenu("Add Connected Node")
        
        # Determine which node types make sense to connect to based on current node type
        if node.node_type == "problem":
            next_type = "check"
            add_check_action = add_connected_menu.addAction(f"Add {next_type.capitalize()}")
            add_check_action.triggered.connect(lambda: self.add_connected_node(node, next_type))
            
        elif node.node_type == "check":
            next_type = "condition"
            add_condition_action = add_connected_menu.addAction(f"Add {next_type.capitalize()}")
            add_condition_action.triggered.connect(lambda: self.add_connected_node(node, next_type))
            
        elif node.node_type == "condition":
            next_type = "action"
            add_action_action = add_connected_menu.addAction(f"Add {next_type.capitalize()}")
            add_action_action.triggered.connect(lambda: self.add_connected_node(node, next_type))
        
        # More generic connect option
        connect_action = context_menu.addAction("Connect to Another Node")
        connect_action.triggered.connect(lambda: self.start_connecting(node))
        
        context_menu.addSeparator()
        
        # Delete node
        delete_action = context_menu.addAction("Delete Node")
        delete_action.triggered.connect(lambda: self.delete_node(node))
        
        # Delete connections
        if any(node.node_id in connection for connection in self.connections):
            delete_connections = context_menu.addAction("Delete Connections")
            delete_connections.triggered.connect(lambda: self.delete_node_connections(node))
            
        context_menu.addSeparator()
        
        # Change node type submenu
        change_type_menu = context_menu.addMenu("Change Node Type")
        for node_type in ["problem", "check", "condition", "action"]:
            type_action = change_type_menu.addAction(node_type.capitalize())
            type_action.triggered.connect(lambda checked, nt=node_type: self.change_node_type(node, nt))
            
        context_menu.exec_(node.mapToGlobal(pos))
        
    def start_connecting(self, source_node):
        """Start the connection process from a source node.
        
        Args:
            source_node (DiagnosticNodeWidget): The node to start connecting from.
        """
        self.connecting = True
        self.source_node = source_node
        QMessageBox.information(self, "Connect Nodes", "Now click on another node to connect to it.")
        
    def delete_node(self, node):
        """Delete a node and its connections.
        
        Args:
            node (DiagnosticNodeWidget): The node to delete.
        """
        # Remove from nodes dictionary
        if node.node_id in self.nodes:
            del self.nodes[node.node_id]
        
        # Remove any connections involving this node
        self.connections = [conn for conn in self.connections if node.node_id not in conn]
        
        # Update connections in other nodes
        for _, other_node in self.nodes.items():
            other_node.connections = [conn for conn in other_node.connections if conn != node.node_id]
            
        # Remove from UI
        node.deleteLater()
        self.pathway_updated.emit()
        self.viewport().update()
        
    def delete_node_connections(self, node):
        """Delete all connections for a node.
        
        Args:
            node (DiagnosticNodeWidget): The node whose connections should be deleted.
        """
        # Remove connections from the list
        self.connections = [conn for conn in self.connections if node.node_id not in conn]
        
        # Clear node's own connection list
        node.connections = []
        
        # Update connections in other nodes
        for _, other_node in self.nodes.items():
            other_node.connections = [conn for conn in other_node.connections if conn != node.node_id]
            
        self.pathway_updated.emit()
        self.viewport().update()
        
    def change_node_type(self, node, new_type):
        """Change the type of a node.
        
        Args:
            node (DiagnosticNodeWidget): The node to change.
            new_type (str): The new node type.
        """
        # Create a new node of the desired type
        new_node = DiagnosticNodeWidget(new_type)
        new_node.setParent(self.canvas_widget)
        
        # Copy position and content
        new_node.move(node.pos())
        new_node.set_content(node.get_content())
        new_node.connections = node.connections.copy()
        new_node.show()
        
        # Update connections that point to the old node
        for source_id, target_id in self.connections:
            if source_id == node.node_id:
                self.connections.remove((source_id, target_id))
                self.connections.append((new_node.node_id, target_id))
            elif target_id == node.node_id:
                self.connections.remove((source_id, target_id))
                self.connections.append((source_id, new_node.node_id))
                
        # Update connections in other nodes
        for _, other_node in self.nodes.items():
            if node.node_id in other_node.connections:
                other_node.connections.remove(node.node_id)
                other_node.connections.append(new_node.node_id)
        
        # Store the new node
        self.nodes[new_node.node_id] = new_node
        
        # Set up context menu
        new_node.setContextMenuPolicy(Qt.CustomContextMenu)
        new_node.customContextMenuRequested.connect(
            lambda pos, n=new_node: self.show_node_context_menu(pos, n)
        )
        
        # Connect the node's content changed signal
        new_node.content_changed.connect(self.pathway_updated)
        
        # Remove old node
        del self.nodes[node.node_id]
        node.deleteLater()
        
        self.pathway_updated.emit()
        self.viewport().update()
        
    def create_mime_data(self, node):
        """Create mime data for drag operations.
        
        Args:
            node (DiagnosticNodeWidget): The node being dragged.
            
        Returns:
            QMimeData: The MIME data for the drag operation.
        """
        mime_data = QMimeData()
        mime_data.setText(str(node.node_id))
        return mime_data
        
    def get_pathway_data(self):
        """Export the entire pathway as structured data.
        
        Returns:
            dict: The pathway data, including nodes and connections.
        """
        nodes_data = {}
        for node_id, node in self.nodes.items():
            nodes_data[node_id] = node.get_data()
            
        return {
            "nodes": nodes_data,
            "connections": self.connections
        }
        
    def set_pathway_data(self, data):
        """Import pathway data.
        
        Args:
            data (dict): The pathway data to import.
        """
        # Clear existing nodes and connections
        for node in self.nodes.values():
            node.deleteLater()
        self.nodes = {}
        self.connections = []
        
        # Create nodes
        if "nodes" in data:
            for node_id, node_data in data["nodes"].items():
                node_type = node_data.get("node_type", "check")
                new_node = self.add_node(node_type)
                new_node.set_data(node_data)
                
        # Create connections
        if "connections" in data:
            self.connections = data["connections"]
            
        self.viewport().update()
        self.pathway_updated.emit()
        
    def convert_to_rule_text(self):
        """Convert the pathway to rule text format.
        
        Returns:
            str: The rule text representation of the pathway.
        """
        # Find starting nodes (nodes with no incoming connections)
        incoming_connections = set()
        for source, target in self.connections:
            incoming_connections.add(target)
            
        starting_nodes = [node_id for node_id in self.nodes.keys() if node_id not in incoming_connections]
        
        # If no clear starting point, use any problem node or just the first node
        if not starting_nodes:
            problem_nodes = [node_id for node_id, node in self.nodes.items() if node.node_type == "problem"]
            starting_nodes = problem_nodes if problem_nodes else list(self.nodes.keys())[:1]
            
        # Traverse the pathway to build the rule
        conditions = []
        actions = []
        
        # Process each starting point
        for start_node_id in starting_nodes:
            self._process_node_for_rule(start_node_id, conditions, actions, set())
            
        # Build the IF part
        if_part = "IF " + " AND ".join(conditions)
        
        # Build the THEN part
        then_part = "THEN"
        for i, action in enumerate(actions):
            then_part += f"\n  {i+1}. {action}"
            
        # Combine into final rule
        return f"{if_part},\n{then_part}"
        
    def _process_node_for_rule(self, node_id, conditions, actions, visited):
        """Process a node and its children for rule conversion.
        
        Args:
            node_id: The ID of the node to process.
            conditions (list): List to collect condition strings.
            actions (list): List to collect action strings.
            visited (set): Set of already visited nodes to prevent cycles.
        """
        if node_id in visited:
            return
            
        visited.add(node_id)
        node = self.nodes.get(node_id)
        if not node:
            return
            
        content = node.get_content().strip()
        if not content:
            content = f"[Empty {node.node_type.capitalize()}]"
            
        # Process based on node type
        if node.node_type == "problem":
            conditions.append(f"problem is '{content}'")
        elif node.node_type == "check":
            check_type = node.get_check_type()
            if check_type:
                conditions.append(f"{check_type} shows '{content}'")
            else:
                conditions.append(f"check shows '{content}'")
        elif node.node_type == "condition":
            severity = node.get_condition_severity()
            if severity:
                conditions.append(f"{severity} condition: {content}")
            else:
                conditions.append(content)
        elif node.node_type == "action":
            impact = node.get_action_impact()
            if impact:
                actions.append(f"{impact}: {content}")
            else:
                actions.append(content)
                
        # Process child nodes
        for source, target in self.connections:
            if source == node_id:
                self._process_node_for_rule(target, conditions, actions, visited)
                
    def convert_to_structured_data(self):
        """Convert pathway to structured format for storage.
        
        Returns:
            dict: Structured data representing the rule.
        """
        rule_text = self.convert_to_rule_text()
        
        # Find all conditions and actions
        conditions = []
        actions = []
        
        # Extract from the rule text
        parts = rule_text.split(",\nTHEN")
        if len(parts) == 2:
            if_part = parts[0].replace("IF ", "").strip()
            then_part = parts[1].strip()
            
            # Process conditions
            for condition_text in if_part.split(" AND "):
                condition = {
                    "param": condition_text,
                    "operator": "=",
                    "value": "true",
                    "connector": "AND"
                }
                conditions.append(condition)
                
            # Set the last condition's connector to empty
            if conditions:
                conditions[-1]["connector"] = ""
                
            # Process actions
            for i, action_line in enumerate(then_part.split("\n")):
                action_line = action_line.strip()
                if action_line:
                    # Extract sequence if present
                    seq = i + 1
                    action_text = action_line
                    if action_line[0].isdigit() and ". " in action_line:
                        seq_end = action_line.find(". ")
                        try:
                            seq = int(action_line[:seq_end])
                            action_text = action_line[seq_end+2:]
                        except ValueError:
                            pass
                    
                    # Create action structure
                    action = {
                        "type": "Apply",
                        "target": action_text,
                        "value": "",
                        "sequence": seq
                    }
                    
                    # Try to further parse if possible
                    if ": " in action_text:
                        parts = action_text.split(": ", 1)
                        action["type"] = parts[0]
                        action["target"] = parts[1]
                    
                    actions.append(action)
        
        return {
            "text": rule_text,
            "conditions": conditions,
            "actions": actions,
            "is_complex": True
        }
    
    def reset_layout(self):
        """Reset the column positions for a fresh layout."""
        self.column_y_positions = {
            0: self.INITIAL_Y,
            1: self.INITIAL_Y,
            2: self.INITIAL_Y,
            3: self.INITIAL_Y
        }
        
    def auto_layout(self):
        """Automatically layout existing nodes in columns."""
        # Group nodes by type
        nodes_by_type = {
            "problem": [],
            "check": [],
            "condition": [],
            "action": []
        }
        
        for node_id, node in self.nodes.items():
            if node.node_type in nodes_by_type:
                nodes_by_type[node.node_type].append(node)
        
        # Reset layout positions
        self.reset_layout()
        
        # Position each node according to type
        for node_type, nodes in nodes_by_type.items():
            for node in nodes:
                position = self.calculate_node_position(node_type)
                node.move(position)
        
        self.viewport().update()
        self.pathway_updated.emit()
    
    def clear(self):
        """Clear all nodes and connections from the canvas."""
        # Remove all nodes
        for node in list(self.nodes.values()):
            node.deleteLater()
        
        # Clear internal data structures
        self.nodes = {}
        self.connections = []
        
        # Reset layout
        self.reset_layout()
        
        # Update UI
        self.viewport().update()
        self.pathway_updated.emit()