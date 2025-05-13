"""
Diagnostic Collection System - Pathway Dialog

This module defines the dialog for creating and editing visual diagnostic pathways,
providing an intuitive interface for mapping out diagnostic processes.
"""

import os
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QHeaderView, QListWidget, QGroupBox, QMessageBox, QSplitter, QTabWidget,
    QWidget, QToolButton, QMenu, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

# Import custom widgets
from ui.widgets.diagnostic_canvas import DiagnosticPathwayCanvas

logger = logging.getLogger(__name__)

class DiagnosticPathwayDialog(QDialog):
    """Dialog for creating and editing diagnostic pathways."""
    
    def __init__(self, existing_rule=None, parent=None):
        """Initialize the dialog with an optional existing rule."""
        super().__init__(parent)
        self.existing_rule = existing_rule
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Diagnostic Pathway Builder")
        self.setGeometry(100, 100, 1200, 800)
        
        main_layout = QVBoxLayout()
        
        # Create tabs for builder and preview
        self.tab_widget = QTabWidget()
        
        # ===== Builder Tab =====
        builder_widget = QWidget()
        builder_layout = QVBoxLayout(builder_widget)
        
        # Toolbar with node creation and layout controls
        toolbar_layout = QHBoxLayout()
        
        # Node creation buttons with dropdown menus
        node_group = QGroupBox("Add Nodes")
        node_layout = QHBoxLayout()
        
        # Problem node button
        self.add_problem_btn = QPushButton("Add Problem")
        self.add_problem_btn.setToolTip("Start with a problem description")
        self.add_problem_btn.clicked.connect(lambda: self.add_node("problem"))
        node_layout.addWidget(self.add_problem_btn)
        
        # Check node button
        self.add_check_btn = QPushButton("Add Check")
        self.add_check_btn.setToolTip("Add a diagnostic check step")
        self.add_check_btn.clicked.connect(lambda: self.add_node("check"))
        node_layout.addWidget(self.add_check_btn)
        
        # Condition node button
        self.add_condition_btn = QPushButton("Add Condition")
        self.add_condition_btn.setToolTip("Add an observation or condition")
        self.add_condition_btn.clicked.connect(lambda: self.add_node("condition"))
        node_layout.addWidget(self.add_condition_btn)
        
        # Action node button
        self.add_action_btn = QPushButton("Add Action")
        self.add_action_btn.setToolTip("Add an action or solution step")
        self.add_action_btn.clicked.connect(lambda: self.add_node("action"))
        node_layout.addWidget(self.add_action_btn)
        
        node_group.setLayout(node_layout)
        toolbar_layout.addWidget(node_group)
        
        # Layout controls
        layout_group = QGroupBox("Layout")
        layout_buttons = QHBoxLayout()
        
        self.auto_layout_btn = QPushButton("Auto Arrange")
        self.auto_layout_btn.setToolTip("Automatically arrange nodes in columns")
        self.auto_layout_btn.clicked.connect(self.auto_arrange_nodes)
        layout_buttons.addWidget(self.auto_layout_btn)
        
        self.clear_canvas_btn = QPushButton("Clear Canvas")
        self.clear_canvas_btn.setToolTip("Remove all nodes from the canvas")
        self.clear_canvas_btn.clicked.connect(self.clear_canvas)
        layout_buttons.addWidget(self.clear_canvas_btn)
        
        layout_group.setLayout(layout_buttons)
        toolbar_layout.addWidget(layout_group)
        
        # Template dropdown
        template_group = QGroupBox("Templates")
        template_layout = QHBoxLayout()
        
        self.template_label = QLabel("Select Template:")
        template_layout.addWidget(self.template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Select Template...", 
            "Basic Troubleshooting", 
            "Quality Check", 
            "Setup Process"
        ])
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        toolbar_layout.addWidget(template_group)
        
        builder_layout.addLayout(toolbar_layout)
        
        # Canvas for building the pathway
        self.canvas = DiagnosticPathwayCanvas()
        builder_layout.addWidget(self.canvas)
        
        self.tab_widget.addTab(builder_widget, "Pathway Builder")
        
        # ===== Preview Tab =====
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_splitter = QSplitter(Qt.Horizontal)
        
        # Rule text preview
        preview_group = QGroupBox("Rule Preview")
        preview_group_layout = QVBoxLayout()
        
        preview_instructions = QLabel("This is how your pathway will be represented as a rule:")
        preview_instructions.setWordWrap(True)
        preview_group_layout.addWidget(preview_instructions)
        
        self.rule_preview = QTextEdit()
        self.rule_preview.setReadOnly(True)
        preview_group_layout.addWidget(self.rule_preview)
        
        preview_group.setLayout(preview_group_layout)
        preview_splitter.addWidget(preview_group)
        
        # Validation panel
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout()
        
        validation_instructions = QLabel(
            "Validation results will appear here. Make sure to validate your pathway before saving."
        )
        validation_instructions.setWordWrap(True)
        validation_layout.addWidget(validation_instructions)
        
        self.validation_list = QListWidget()
        validation_layout.addWidget(self.validation_list)
        
        self.validate_btn = QPushButton("Validate Pathway")
        self.validate_btn.clicked.connect(self.validate_pathway)
        validation_layout.addWidget(self.validate_btn)
        
        validation_group.setLayout(validation_layout)
        preview_splitter.addWidget(validation_group)
        
        preview_layout.addWidget(preview_splitter)
        
        self.tab_widget.addTab(preview_widget, "Preview & Validate")
        
        main_layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.update_preview_btn = QPushButton("Update Preview")
        self.update_preview_btn.clicked.connect(self.update_preview)
        button_layout.addWidget(self.update_preview_btn)
        
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Pathway")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Connect update signal
        self.canvas.pathway_updated.connect(self.update_preview)
        
        # Load existing rule if provided
        if self.existing_rule:
            self.load_existing_rule()
        else:
            # Default template if starting fresh
            self.apply_template(1)  # Apply "Basic Troubleshooting" template
    
    def add_node(self, node_type):
        """Add a new node to the canvas."""
        node = self.canvas.add_node(node_type)
        
        # Display a tooltip suggesting the next step
        next_steps = {
            "problem": "Now add a diagnostic check by right-clicking on the problem and selecting 'Add Connected Node'",
            "check": "Now add an observation by right-clicking on the check and selecting 'Add Connected Node'",
            "condition": "Now add an action by right-clicking on the observation and selecting 'Add Connected Node'",
            "action": "You've completed a diagnostic path. Add more paths or validate your pathway."
        }
        
        if node_type in next_steps:
            QMessageBox.information(self, "Next Step", next_steps[node_type])
        
        return node
    
    def auto_arrange_nodes(self):
        """Automatically arrange nodes in columnar layout."""
        self.canvas.auto_layout()
        
    def clear_canvas(self):
        """Clear all nodes from the canvas."""
        confirm = QMessageBox.question(
            self, "Clear Canvas",
            "Are you sure you want to remove all nodes from the canvas?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.canvas.clear()
    
    def update_preview(self):
        """Update the rule preview text."""
        rule_text = self.canvas.convert_to_rule_text()
        self.rule_preview.setText(rule_text)
        
    def validate_pathway(self):
        """Validate the pathway for completeness and consistency."""
        self.validation_list.clear()
        
        pathway_data = self.canvas.get_pathway_data()
        nodes = pathway_data.get("nodes", {})
        connections = pathway_data.get("connections", [])
        
        # Check for empty nodes
        empty_nodes = []
        for node_id, node_data in nodes.items():
            if not node_data.get("content"):
                node_type = node_data.get("node_type", "unknown").capitalize()
                empty_nodes.append(f"{node_type} node is empty")
                
        # Check for disconnected nodes
        connected_nodes = set()
        for source, target in connections:
            connected_nodes.add(source)
            connected_nodes.add(target)
            
        disconnected_nodes = [
            f"{nodes[node_id].get('node_type', 'Unknown').capitalize()} node is disconnected" 
            for node_id in nodes.keys() if node_id not in connected_nodes
        ]
        
        # Check for logical flow
        problem_nodes = [node_id for node_id, data in nodes.items() if data.get("node_type") == "problem"]
        check_nodes = [node_id for node_id, data in nodes.items() if data.get("node_type") == "check"]
        condition_nodes = [node_id for node_id, data in nodes.items() if data.get("node_type") == "condition"]
        action_nodes = [node_id for node_id, data in nodes.items() if data.get("node_type") == "action"]
        
        # Verify we have at least one problem and one action
        flow_issues = []
        if not problem_nodes:
            flow_issues.append("No problem statement defined")
        if not action_nodes:
            flow_issues.append("No action steps defined")
            
        # Check for terminal nodes without actions
        terminal_nodes = set()
        for node_id in nodes.keys():
            has_outgoing = False
            for source, _ in connections:
                if source == node_id:
                    has_outgoing = True
                    break
            if not has_outgoing:
                terminal_nodes.add(node_id)
                
        for terminal_id in terminal_nodes:
            if terminal_id in nodes and nodes[terminal_id].get("node_type") != "action":
                node_type = nodes[terminal_id].get("node_type", "Unknown").capitalize()
                flow_issues.append(f"{node_type} node ends pathway without an action")
                
        # Check for cycles (which might be valid but worth flagging)
        cycles = self._detect_cycles(connections, nodes)
        if cycles:
            flow_issues.append(f"Pathway contains {len(cycles)} cycle(s)")
        
        # Add all issues to the validation list
        for issue in empty_nodes + disconnected_nodes + flow_issues:
            self.validation_list.addItem(issue)
            
        # Summary
        if not (empty_nodes or disconnected_nodes or flow_issues):
            self.validation_list.addItem("✓ Pathway is valid and complete")
            return True
        return False
    
    def _detect_cycles(self, connections, nodes):
        """Detect cycles in the graph."""
        graph = {}
        for node_id in nodes.keys():
            graph[node_id] = []
            
        for source, target in connections:
            if source in graph:
                graph[source].append(target)
                
        # Use depth-first search to find cycles
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs_cycle(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs_cycle(neighbor, path.copy())
                
            rec_stack.remove(node)
            
        for node in graph:
            if node not in visited:
                dfs_cycle(node, [])
                
        return cycles
    
    def apply_template(self, index):
        """Apply a predefined template to the canvas."""
        if index == 0:  # "Select Template..."
            return
            
        # Clear existing nodes
        self.canvas.clear()
        
        if index == 1:  # Basic Troubleshooting
            # Create template nodes with proper column positioning
            problem = self.canvas.add_node("problem")
            
            check1 = self.canvas.add_node("check")
            
            condition1 = self.canvas.add_node("condition")
            
            action1 = self.canvas.add_node("action")
            
            # Create connections
            self.canvas.add_connection(problem.node_id, check1.node_id)
            self.canvas.add_connection(check1.node_id, condition1.node_id)
            self.canvas.add_connection(condition1.node_id, action1.node_id)
            
        elif index == 2:  # Quality Check
            # Create template nodes
            problem = self.canvas.add_node("problem")
            problem.set_content("Quality issue detected")
            if hasattr(problem, "check_type"):
                problem.set_check_type("Visual Inspection")
            
            check1 = self.canvas.add_node("check")
            check1.set_content("Measurement check")
            if hasattr(check1, "check_type"):
                check1.set_check_type("Measurement")
            
            check2 = self.canvas.add_node("check")
            check2.set_content("Visual inspection")
            if hasattr(check2, "check_type"):
                check2.set_check_type("Visual Inspection")
            
            check3 = self.canvas.add_node("check")
            check3.set_content("Parameter verification")
            if hasattr(check3, "check_type"):
                check3.set_check_type("Parameter Check")
            
            condition1 = self.canvas.add_node("condition")
            condition1.set_content("Out of specification")
            if hasattr(condition1, "condition_severity"):
                condition1.set_condition_severity("Critical")
            
            condition2 = self.canvas.add_node("condition")
            condition2.set_content("Surface defect")
            if hasattr(condition2, "condition_severity"):
                condition2.set_condition_severity("Major")
            
            condition3 = self.canvas.add_node("condition")
            condition3.set_content("Incorrect setting")
            if hasattr(condition3, "condition_severity"):
                condition3.set_condition_severity("Major")
            
            action1 = self.canvas.add_node("action")
            action1.set_content("Adjust machine parameters")
            if hasattr(action1, "action_impact"):
                action1.set_action_impact("Immediate Fix")
            
            action2 = self.canvas.add_node("action")
            action2.set_content("Replace component")
            if hasattr(action2, "action_impact"):
                action2.set_action_impact("Immediate Fix")
            
            action3 = self.canvas.add_node("action")
            action3.set_content("Reset parameters to standard")
            if hasattr(action3, "action_impact"):
                action3.set_action_impact("Immediate Fix")
            
            # Create connections
            self.canvas.add_connection(problem.node_id, check1.node_id)
            self.canvas.add_connection(problem.node_id, check2.node_id)
            self.canvas.add_connection(problem.node_id, check3.node_id)
            self.canvas.add_connection(check1.node_id, condition1.node_id)
            self.canvas.add_connection(check2.node_id, condition2.node_id)
            self.canvas.add_connection(check3.node_id, condition3.node_id)
            self.canvas.add_connection(condition1.node_id, action1.node_id)
            self.canvas.add_connection(condition2.node_id, action2.node_id)
            self.canvas.add_connection(condition3.node_id, action3.node_id)
            
        elif index == 3:  # Setup Process
            # Create setup process template
            problem = self.canvas.add_node("problem")
            problem.set_content("Machine setup required")
            
            check1 = self.canvas.add_node("check")
            check1.set_content("Check initial parameters")
            
            check2 = self.canvas.add_node("check")
            check2.set_content("Check material properties")
            
            condition1a = self.canvas.add_node("condition")
            condition1a.set_content("Parameters in range")
            
            condition1b = self.canvas.add_node("condition")
            condition1b.set_content("Parameters out of range")
            
            condition2 = self.canvas.add_node("condition")
            condition2.set_content("Material verified")
            
            action1 = self.canvas.add_node("action")
            action1.set_content("Proceed with setup")
            
            action2 = self.canvas.add_node("action")
            action2.set_content("Adjust parameters")
            
            action3 = self.canvas.add_node("action")
            action3.set_content("Run test cycle")
            
            action4 = self.canvas.add_node("action")
            action4.set_content("Validate adjustments")
            
            action5 = self.canvas.add_node("action")
            action5.set_content("Record material batch")
            
            # Create connections
            self.canvas.add_connection(problem.node_id, check1.node_id)
            self.canvas.add_connection(problem.node_id, check2.node_id)
            self.canvas.add_connection(check1.node_id, condition1a.node_id)
            self.canvas.add_connection(check1.node_id, condition1b.node_id)
            self.canvas.add_connection(check2.node_id, condition2.node_id)
            self.canvas.add_connection(condition1a.node_id, action1.node_id)
            self.canvas.add_connection(condition1b.node_id, action2.node_id)
            self.canvas.add_connection(action1.node_id, action3.node_id)
            self.canvas.add_connection(action2.node_id, action4.node_id)
            self.canvas.add_connection(action4.node_id, action3.node_id)
            self.canvas.add_connection(condition2.node_id, action5.node_id)
            
        # Arrange nodes and update preview
        self.canvas.auto_layout()
        self.update_preview()
        
    def load_existing_rule(self):
        """Load an existing rule into the pathway canvas."""
        if not self.existing_rule:
            return
            
        # Check if the rule already has pathway data
        if self.existing_rule.get("pathway_data"):
            self.canvas.set_pathway_data(self.existing_rule["pathway_data"])
            self.update_preview()
            return
            
        # Otherwise, try to convert from the rule text and structure
        rule_text = self.existing_rule.get("text", "")
        conditions = self.existing_rule.get("conditions", [])
        actions = self.existing_rule.get("actions", [])
        
        # Create a basic pathway
        problem = self.canvas.add_node("problem")
        
        # Extract problem statement
        if rule_text.startswith("IF "):
            problem_text = rule_text.split(",\nTHEN")[0].replace("IF ", "")
            problem.set_content(problem_text)
        else:
            problem.set_content("Imported rule")
            
        # Add condition nodes
        condition_nodes = []
        
        for i, condition in enumerate(conditions):
            condition_node = self.canvas.add_node("condition")
            condition_text = condition.get("param", "") + " " + condition.get("operator", "") + " " + condition.get("value", "")
            condition_node.set_content(condition_text)
            
            # Connect to problem
            self.canvas.add_connection(problem.node_id, condition_node.node_id)
            condition_nodes.append(condition_node)
            
        # Add action nodes
        for i, action in enumerate(sorted(actions, key=lambda x: x.get("sequence", i))):
            action_node = self.canvas.add_node("action")
            
            action_text = action.get("type", "") + " " + action.get("target", "")
            if action.get("value"):
                action_text += " to " + action.get("value", "")
                
            action_node.set_content(action_text)
            
            # Connect to the condition node or problem if no conditions
            if condition_nodes:
                # Try to connect to a relevant condition, or the first one
                connected = False
                for condition_node in condition_nodes:
                    if not connected:
                        self.canvas.add_connection(condition_node.node_id, action_node.node_id)
                        connected = True
            else:
                self.canvas.add_connection(problem.node_id, action_node.node_id)
        
        # Arrange nodes and update preview
        self.canvas.auto_layout()
        self.update_preview()
        
    def get_pathway_data(self):
        """Get the pathway data."""
        return self.canvas.get_pathway_data()
        
    def get_rule(self):
        """Get the rule in structured format."""
        return self.canvas.convert_to_structured_data()