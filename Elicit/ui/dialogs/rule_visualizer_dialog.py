"""
Diagnostic Collection System - Rule Visualizer Dialog

This module provides a dialog for visualizing diagnostic rules,
displaying them in a more graphical and comprehensible format.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QWidget, QSplitter, QFrame, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPathItem,
    QGraphicsEllipseItem, QScrollArea, QStyleOptionGraphicsItem
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QPainterPath, QPainter, QLinearGradient

logger = logging.getLogger(__name__)

class RuleFlowGraphicsView(QGraphicsView):
    """Custom graphics view for rule flow visualization."""
    
    def __init__(self, parent=None):
        """Initialize the graphics view."""
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
    def wheelEvent(self, event):
        """Handle zoom in/out with mouse wheel."""
        # Zoom factor
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)

class RuleNodeItem(QGraphicsRectItem):
    """Graphics item for a rule node (condition or action)."""
    
    def __init__(self, text, node_type, x, y, width=200, height=100, parent=None):
        """Initialize the node item."""
        super().__init__(x, y, width, height, parent)
        self.text = text
        self.node_type = node_type
        
        # Set appearance based on node type
        if node_type == "condition":
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, QColor(235, 245, 255))
            gradient.setColorAt(1, QColor(180, 210, 240))
            self.setBrush(QBrush(gradient))
            self.setPen(QPen(QColor(60, 120, 200), 2))
        elif node_type == "action":
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, QColor(255, 245, 230))
            gradient.setColorAt(1, QColor(240, 200, 160))
            self.setBrush(QBrush(gradient))
            self.setPen(QPen(QColor(200, 120, 40), 2))
        else:
            # Default style
            self.setBrush(QBrush(QColor(240, 240, 240)))
            self.setPen(QPen(QColor(60, 60, 60), 1))

        # Set rounded corners
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        # Add text
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(text)
        self.text_item.setTextWidth(width - 20)
        
        # Center text
        text_width = self.text_item.boundingRect().width()
        text_height = self.text_item.boundingRect().height()
        self.text_item.setPos((width - text_width) / 2, (height - text_height) / 2)
        
        # Set text color
        self.text_item.setDefaultTextColor(QColor(30, 30, 30))
        
        # Add header
        self.header_item = QGraphicsRectItem(0, 0, width, 25, self)
        if node_type == "condition":
            self.header_item.setBrush(QBrush(QColor(60, 120, 200)))
        elif node_type == "action":
            self.header_item.setBrush(QBrush(QColor(200, 120, 40)))
        else:
            self.header_item.setBrush(QBrush(QColor(120, 120, 120)))
        
        # Fix: Create a QPen with NoPen style
        self.header_item.setPen(QPen(Qt.PenStyle.NoPen))
        
        # Add header text
        self.header_text = QGraphicsTextItem(self)
        if node_type == "condition":
            self.header_text.setPlainText("IF CONDITION")
        elif node_type == "action":
            self.header_text.setPlainText("THEN ACTION")
        else:
            self.header_text.setPlainText("NODE")
        
        self.header_text.setDefaultTextColor(QColor(255, 255, 255))
        self.header_text.setFont(QFont("Arial", 8, QFont.Bold))
        self.header_text.setPos(10, 5)

class RuleVisualizerDialog(QDialog):
    """Dialog for visualizing diagnostic rules."""
    
    def __init__(self, rule_text, structured_data=None, parent=None):
        """Initialize the dialog with rule text and optional structured data."""
        super().__init__(parent)
        self.rule_text = rule_text
        self.structured_data = structured_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Rule Visualizer")
        self.setGeometry(200, 200, 800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different visualization modes
        self.tab_widget = QTabWidget()
        
        # === Text View Tab ===
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        
        # Formatted text view
        text_group = QGroupBox("Rule Format")
        text_group_layout = QVBoxLayout()
        
        self.rule_text_edit = QTextEdit()
        self.rule_text_edit.setReadOnly(True)
        self.rule_text_edit.setFont(QFont("Courier New", 10))
        self.format_rule_text()
        
        text_group_layout.addWidget(self.rule_text_edit)
        text_group.setLayout(text_group_layout)
        text_layout.addWidget(text_group)
        
        self.tab_widget.addTab(text_tab, "Text View")
        
        # === Structured View Tab ===
        structured_tab = QWidget()
        structured_layout = QVBoxLayout(structured_tab)
        
        if self.structured_data:
            # Add conditions table
            conditions_group = QGroupBox("Conditions")
            conditions_layout = QVBoxLayout()
            
            self.conditions_table = QTableWidget()
            self.conditions_table.setColumnCount(4)
            self.conditions_table.setHorizontalHeaderLabels(["Parameter", "Operator", "Value", "Connector"])
            self.conditions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            # Populate conditions
            conditions = self.structured_data.get("conditions", [])
            self.conditions_table.setRowCount(len(conditions))
            
            for i, condition in enumerate(conditions):
                self.conditions_table.setItem(i, 0, QTableWidgetItem(condition.get("param", "")))
                self.conditions_table.setItem(i, 1, QTableWidgetItem(condition.get("operator", "")))
                self.conditions_table.setItem(i, 2, QTableWidgetItem(condition.get("value", "")))
                self.conditions_table.setItem(i, 3, QTableWidgetItem(condition.get("connector", "")))
            
            conditions_layout.addWidget(self.conditions_table)
            conditions_group.setLayout(conditions_layout)
            structured_layout.addWidget(conditions_group)
            
            # Add actions table
            actions_group = QGroupBox("Actions")
            actions_layout = QVBoxLayout()
            
            self.actions_table = QTableWidget()
            self.actions_table.setColumnCount(4)
            self.actions_table.setHorizontalHeaderLabels(["Type", "Target", "Value", "Sequence"])
            self.actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            
            # Populate actions
            actions = self.structured_data.get("actions", [])
            self.actions_table.setRowCount(len(actions))
            
            for i, action in enumerate(actions):
                self.actions_table.setItem(i, 0, QTableWidgetItem(action.get("type", "")))
                self.actions_table.setItem(i, 1, QTableWidgetItem(action.get("target", "")))
                self.actions_table.setItem(i, 2, QTableWidgetItem(action.get("value", "")))
                self.actions_table.setItem(i, 3, QTableWidgetItem(str(action.get("sequence", i+1))))
            
            actions_layout.addWidget(self.actions_table)
            actions_group.setLayout(actions_layout)
            structured_layout.addWidget(actions_group)
        else:
            # Show message when no structured data is available
            message = QLabel("No structured data available for this rule.")
            message.setAlignment(Qt.AlignCenter)
            structured_layout.addWidget(message)
        
        self.tab_widget.addTab(structured_tab, "Structured View")
        
        # === Flow Chart Tab ===
        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)
        
        self.flow_view = RuleFlowGraphicsView()
        self.flow_scene = QGraphicsScene()
        self.flow_view.setScene(self.flow_scene)
        
        # Create the flow chart visualization
        self.create_flow_chart()
        
        flow_layout.addWidget(self.flow_view)
        
        # Add zoom controls
        zoom_layout = QHBoxLayout()
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self.flow_view.scale(1.2, 1.2))
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self.flow_view.scale(1/1.2, 1/1.2))
        zoom_layout.addWidget(zoom_out_btn)
        
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(self.reset_flow_view)
        zoom_layout.addWidget(reset_view_btn)
        
        flow_layout.addLayout(zoom_layout)
        
        self.tab_widget.addTab(flow_tab, "Flow Chart")
        
        main_layout.addWidget(self.tab_widget)
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        main_layout.addLayout(buttons_layout)
    
    def format_rule_text(self):
        """Format the rule text with syntax highlighting."""
        text = self.rule_text
        
        # Apply minimal formatting to make it more readable
        if "IF " in text and ", THEN" in text:
            if_part = text.split(", THEN")[0]
            then_part = text.split(", THEN")[1]
            
            # Format IF part in blue
            formatted_if = f"<span style='color: #0066CC; font-weight: bold;'>{if_part}</span>"
            
            # Format THEN part in dark orange
            formatted_then = f"<span style='color: #CC6600; font-weight: bold;'>, THEN</span>"
            
            # Format action items
            lines = then_part.split("\n")
            formatted_lines = []
            for line in lines:
                if line.strip():
                    # Highlight sequence numbers
                    if line.strip()[0].isdigit() and ". " in line:
                        seq_end = line.find(". ")
                        seq = line[:seq_end+2]
                        action = line[seq_end+2:]
                        formatted_line = f"<span style='color: #999999;'>{seq}</span><span style='color: #333333;'>{action}</span>"
                    else:
                        formatted_line = f"<span style='color: #333333;'>{line}</span>"
                    formatted_lines.append(formatted_line)
            
            formatted_then_part = "\n".join(formatted_lines)
            
            # Combine formatted parts
            formatted_text = f"{formatted_if}{formatted_then}{formatted_then_part}"
            self.rule_text_edit.setHtml(formatted_text)
        else:
            # No specific formatting if not in standard format
            self.rule_text_edit.setPlainText(text)
    
    def create_flow_chart(self):
        """Create a flow chart visualization of the rule."""
        if not self.structured_data:
            # Parse the rule text if no structured data is provided
            self.parse_rule_text()
        
        if self.structured_data:
            conditions = self.structured_data.get("conditions", [])
            actions = self.structured_data.get("actions", [])
            
            # Start with a clear scene
            self.flow_scene.clear()
            
            # Layout parameters
            node_width = 200
            node_height = 80
            horizontal_spacing = 40
            vertical_spacing = 60
            
            # Calculate layout for conditions
            condition_x = 50
            condition_y = 50
            condition_nodes = []
            
            # Create a container node for IF section
            if_container_width = node_width + 40
            if_container_height = len(conditions) * (node_height + vertical_spacing) + 50
            if_container = QGraphicsRectItem(
                condition_x - 20, 
                condition_y - 20, 
                if_container_width, 
                if_container_height
            )
            if_container.setBrush(QBrush(QColor(245, 250, 255, 100)))
            if_container.setPen(QPen(QColor(100, 150, 200, 150), 2, Qt.DashLine))
            self.flow_scene.addItem(if_container)
            
            # Add IF label
            if_label = QGraphicsTextItem("IF")
            if_label.setFont(QFont("Arial", 12, QFont.Bold))
            if_label.setDefaultTextColor(QColor(60, 120, 200))
            if_label.setPos(condition_x, condition_y - 40)
            self.flow_scene.addItem(if_label)
            
            # Create condition nodes
            for i, condition in enumerate(conditions):
                condition_text = f"{condition.get('param', '')} {condition.get('operator', '=')} {condition.get('value', '')}"
                connector = condition.get("connector", "")
                
                y_pos = condition_y + i * (node_height + vertical_spacing)
                
                node = RuleNodeItem(condition_text, "condition", condition_x, y_pos, node_width, node_height)
                self.flow_scene.addItem(node)
                condition_nodes.append(node)
                
                # Add connector label if not the last condition
                if i < len(conditions) - 1 and connector:
                    connector_label = QGraphicsTextItem(connector)
                    connector_label.setFont(QFont("Arial", 10, QFont.Bold))
                    connector_label.setDefaultTextColor(QColor(60, 60, 60))
                    connector_label.setPos(
                        condition_x + node_width / 2 - connector_label.boundingRect().width() / 2,
                        y_pos + node_height + 10
                    )
                    self.flow_scene.addItem(connector_label)
            
            # Calculate layout for actions
            action_x = condition_x + node_width + horizontal_spacing + 50
            action_y = 50
            action_nodes = []
            
            # Create a container node for THEN section
            then_container_width = node_width + 40
            then_container_height = len(actions) * (node_height + vertical_spacing) + 50
            then_container = QGraphicsRectItem(
                action_x - 20, 
                action_y - 20, 
                then_container_width, 
                then_container_height
            )
            then_container.setBrush(QBrush(QColor(255, 250, 245, 100)))
            then_container.setPen(QPen(QColor(200, 150, 100, 150), 2, Qt.DashLine))
            self.flow_scene.addItem(then_container)
            
            # Add THEN label
            then_label = QGraphicsTextItem("THEN")
            then_label.setFont(QFont("Arial", 12, QFont.Bold))
            then_label.setDefaultTextColor(QColor(200, 120, 40))
            then_label.setPos(action_x, action_y - 40)
            self.flow_scene.addItem(then_label)
            
            # Sort actions by sequence
            sorted_actions = sorted(actions, key=lambda x: x.get("sequence", 1))
            
            # Create action nodes
            for i, action in enumerate(sorted_actions):
                action_text = f"{action.get('type', 'Apply')} {action.get('target', '')}"
                if action.get('value'):
                    action_text += f" to {action.get('value', '')}"
                
                y_pos = action_y + i * (node_height + vertical_spacing)
                
                node = RuleNodeItem(action_text, "action", action_x, y_pos, node_width, node_height)
                self.flow_scene.addItem(node)
                action_nodes.append(node)
                
                # Add sequence number
                seq = action.get("sequence", i+1)
                seq_label = QGraphicsTextItem(f"{seq}.")
                seq_label.setFont(QFont("Arial", 10, QFont.Bold))
                seq_label.setDefaultTextColor(QColor(200, 120, 40))
                seq_label.setPos(action_x - 30, y_pos + node_height / 2 - 10)
                self.flow_scene.addItem(seq_label)
                
                # Add arrow to next action if not the last one
                if i < len(sorted_actions) - 1:
                    arrow = QGraphicsLineItem(
                        action_x + node_width / 2, y_pos + node_height,
                        action_x + node_width / 2, y_pos + node_height + vertical_spacing / 2
                    )
                    arrow.setPen(QPen(QColor(200, 120, 40), 2))
                    self.flow_scene.addItem(arrow)
                    
                    # Add arrowhead
                    arrow_path = QPainterPath()
                    arrow_path.moveTo(action_x + node_width / 2, y_pos + node_height + vertical_spacing / 2)
                    arrow_path.lineTo(action_x + node_width / 2 - 5, y_pos + node_height + vertical_spacing / 2 - 10)
                    arrow_path.lineTo(action_x + node_width / 2 + 5, y_pos + node_height + vertical_spacing / 2 - 10)
                    arrow_path.closeSubpath()
                    
                    arrow_head = QGraphicsPathItem(arrow_path)
                    arrow_head.setBrush(QBrush(QColor(200, 120, 40)))
                    arrow_head.setPen(QPen(QColor(200, 120, 40), 1))
                    self.flow_scene.addItem(arrow_head)
            
            # Create the main flow arrow between conditions and actions
            if condition_nodes and action_nodes:
                # Calculate center points
                condition_center_x = condition_x + node_width
                condition_center_y = condition_y + if_container_height / 2 - 20
                
                action_center_x = action_x
                action_center_y = action_y + then_container_height / 2 - 20
                
                # Create the main arrow
                main_arrow = QGraphicsLineItem(
                    condition_center_x, condition_center_y,
                    action_center_x, action_center_y
                )
                main_arrow.setPen(QPen(QColor(100, 100, 100), 2))
                self.flow_scene.addItem(main_arrow)
                
                # Add arrowhead
                arrow_path = QPainterPath()
                arrow_path.moveTo(action_center_x, action_center_y)
                arrow_path.lineTo(action_center_x - 10, action_center_y - 5)
                arrow_path.lineTo(action_center_x - 10, action_center_y + 5)
                arrow_path.closeSubpath()
                
                arrow_head = QGraphicsPathItem(arrow_path)
                arrow_head.setBrush(QBrush(QColor(100, 100, 100)))
                arrow_head.setPen(QPen(QColor(100, 100, 100), 1))
                self.flow_scene.addItem(arrow_head)
            
            # Set the scene rect to ensure all elements are visible
            self.flow_scene.setSceneRect(self.flow_scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
            
            # Reset view to show the whole scene
            self.reset_flow_view()
        else:
            # If no structured data is available, show a message
            text_item = QGraphicsTextItem("Cannot visualize this rule in flow chart format.")
            text_item.setFont(QFont("Arial", 12))
            text_item.setPos(50, 50)
            self.flow_scene.addItem(text_item)
    
    def parse_rule_text(self):
        """Parse rule text into structured format if no structured data is provided."""
        rule_text = self.rule_text
        
        # Initialize structured data
        self.structured_data = {
            "conditions": [],
            "actions": []
        }
        
        # Simple parsing of IF-THEN format
        if "IF " in rule_text and ", THEN" in rule_text:
            if_part = rule_text.split(", THEN")[0].replace("IF ", "")
            then_part = rule_text.split(", THEN")[1].strip()
            
            # Parse conditions
            conditions = []
            
            # Check for AND or OR operators
            if " AND " in if_part:
                condition_parts = if_part.split(" AND ")
                for i, part in enumerate(condition_parts):
                    condition = self._parse_condition(part)
                    if condition:
                        if i < len(condition_parts) - 1:
                            condition["connector"] = "AND"
                        else:
                            condition["connector"] = ""
                        conditions.append(condition)
            elif " OR " in if_part:
                condition_parts = if_part.split(" OR ")
                for i, part in enumerate(condition_parts):
                    condition = self._parse_condition(part)
                    if condition:
                        if i < len(condition_parts) - 1:
                            condition["connector"] = "OR"
                        else:
                            condition["connector"] = ""
                        conditions.append(condition)
            else:
                # Single condition
                condition = self._parse_condition(if_part)
                if condition:
                    condition["connector"] = ""
                    conditions.append(condition)
            
            # Parse actions
            actions = []
            action_lines = then_part.split("\n")
            for i, line in enumerate(action_lines):
                line = line.strip()
                if line:
                    # Extract sequence number if available
                    seq = i + 1
                    action_text = line
                    if line[0].isdigit() and ". " in line:
                        try:
                            seq_end = line.find(". ")
                            seq = int(line[:seq_end])
                            action_text = line[seq_end+2:]
                        except ValueError:
                            pass
                    
                    # Try to parse action type, target and value
                    action = self._parse_action(action_text, seq)
                    if action:
                        actions.append(action)
            
            self.structured_data["conditions"] = conditions
            self.structured_data["actions"] = actions
    
    def _parse_condition(self, text):
        """Parse a condition string into structured format."""
        text = text.strip()
        if not text:
            return None
        
        # Define possible operators
        operators = ["=", ">", "<", ">=", "<=", "!=", "contains"]
        
        # Try to identify operator
        for op in sorted(operators, key=len, reverse=True):  # Try longer operators first
            if op in text:
                parts = text.split(op, 1)
                if len(parts) == 2:
                    return {
                        "param": parts[0].strip(),
                        "operator": op,
                        "value": parts[1].strip(),
                        "connector": ""
                    }
        
        # If no operator found, assume it's a simple statement
        return {
            "param": text,
            "operator": "=",
            "value": "true",
            "connector": ""
        }
    
    def _parse_action(self, text, sequence=1):
        """Parse an action string into structured format."""
        text = text.strip()
        if not text:
            return None
        
        # Define known action types
        action_types = ["Apply", "Adjust", "Replace", "Clean", "Measure", "Check", "Restart", "Contact"]
        
        # Try to match known action types
        for action_type in sorted(action_types, key=len, reverse=True):  # Try longer types first
            if text.startswith(action_type + " "):
                target_value = text[len(action_type):].strip()
                
                # Check if there's a value specified
                if " to " in target_value:
                    target, value = target_value.split(" to ", 1)
                    return {
                        "type": action_type,
                        "target": target.strip(),
                        "value": value.strip(),
                        "sequence": sequence
                    }
                else:
                    return {
                        "type": action_type,
                        "target": target_value,
                        "value": "",
                        "sequence": sequence
                    }
        
        # If no action type found, use "Apply" as default
        return {
            "type": "Apply",
            "target": text,
            "value": "",
            "sequence": sequence
        }
    
    def reset_flow_view(self):
        """Reset the flow view to show the entire scene."""
        self.flow_view.resetTransform()
        self.flow_view.fitInView(self.flow_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.flow_view.centerOn(self.flow_scene.itemsBoundingRect().center())