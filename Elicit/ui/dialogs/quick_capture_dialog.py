"""
Diagnostic Collection System - Quick Capture Dialog

This module provides a dialog for quick contextual capture of troubleshooting steps,
allowing users to rapidly document problems, diagnostic checks, observations, and solutions.
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QGroupBox,
    QListWidget, QLineEdit, QRadioButton, QButtonGroup, QScrollArea, QWidget,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

logger = logging.getLogger(__name__)

class ContextualCaptureDialog(QDialog):
    """Dialog for quick contextual capture of troubleshooting steps."""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Quick Problem Capture")
        self.setGeometry(200, 200, 600, 750)
        
        # Create a scroll area to handle potential overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Main container widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # === 1. Problem Description ===
        problem_group = QGroupBox("1. Describe the Problem")
        problem_group.setFont(QFont("Arial", 10, QFont.Bold))
        problem_layout = QVBoxLayout()
        
        # Instructions
        problem_instructions = QLabel(
            "Provide a clear description of the problem or situation you encountered:"
        )
        problem_instructions.setWordWrap(True)
        problem_layout.addWidget(problem_instructions)
        
        # Text input
        self.problem_input = QTextEdit()
        self.problem_input.setPlaceholderText("Describe what you observed...")
        self.problem_input.setMinimumHeight(100)
        problem_layout.addWidget(self.problem_input)
        
        # Problem categorization
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Problem Type:"))
        
        self.problem_type = QComboBox()
        self.problem_type.addItems([
            "Select type...", 
            "Quality Issue", 
            "Machine Stoppage", 
            "Setup Problem",
            "Material Handling", 
            "Tool Wear", 
            "Software Error",
            "Electrical Fault",
            "Safety Concern",
            "Other"
        ])
        tag_layout.addWidget(self.problem_type)
        
        tag_layout.addWidget(QLabel("Severity:"))
        self.severity = QComboBox()
        self.severity.addItems(["Low", "Medium", "High", "Critical"])
        self.severity.setCurrentIndex(1)  # Default to Medium
        tag_layout.addWidget(self.severity)
        
        problem_layout.addLayout(tag_layout)
        problem_group.setLayout(problem_layout)
        layout.addWidget(problem_group)
        
        # === 2. Diagnostic Steps ===
        diagnostic_group = QGroupBox("2. What did you check?")
        diagnostic_group.setFont(QFont("Arial", 10, QFont.Bold))
        diagnostic_layout = QVBoxLayout()
        
        diagnostic_instructions = QLabel(
            "List the diagnostic steps or checks you performed to investigate the problem:"
        )
        diagnostic_instructions.setWordWrap(True)
        diagnostic_layout.addWidget(diagnostic_instructions)
        
        self.checks_list = QListWidget()
        diagnostic_layout.addWidget(self.checks_list)
        
        check_controls = QHBoxLayout()
        self.new_check_input = QLineEdit()
        self.new_check_input.setPlaceholderText("Enter a diagnostic step you performed...")
        check_controls.addWidget(self.new_check_input)
        
        self.add_check_btn = QPushButton("Add")
        self.add_check_btn.clicked.connect(self.add_check)
        check_controls.addWidget(self.add_check_btn)
        
        diagnostic_layout.addLayout(check_controls)
        diagnostic_group.setLayout(diagnostic_layout)
        layout.addWidget(diagnostic_group)
        
        # === 3. Observations ===
        observation_group = QGroupBox("3. What did you observe?")
        observation_group.setFont(QFont("Arial", 10, QFont.Bold))
        observation_layout = QVBoxLayout()
        
        observation_instructions = QLabel(
            "Record what you observed during your diagnostic checks:"
        )
        observation_instructions.setWordWrap(True)
        observation_layout.addWidget(observation_instructions)
        
        self.observations_list = QListWidget()
        observation_layout.addWidget(self.observations_list)
        
        observation_controls = QHBoxLayout()
        self.new_observation_input = QLineEdit()
        self.new_observation_input.setPlaceholderText("Enter what you observed...")
        observation_controls.addWidget(self.new_observation_input)
        
        self.add_observation_btn = QPushButton("Add")
        self.add_observation_btn.clicked.connect(self.add_observation)
        observation_controls.addWidget(self.add_observation_btn)
        
        observation_layout.addLayout(observation_controls)
        observation_group.setLayout(observation_layout)
        layout.addWidget(observation_group)
        
        # === 4. Solution Steps ===
        solution_group = QGroupBox("4. What actions did you take to solve it?")
        solution_group.setFont(QFont("Arial", 10, QFont.Bold))
        solution_layout = QVBoxLayout()
        
        solution_instructions = QLabel(
            "Describe the actions you took to resolve the problem:"
        )
        solution_instructions.setWordWrap(True)
        solution_layout.addWidget(solution_instructions)
        
        self.solutions_list = QListWidget()
        solution_layout.addWidget(self.solutions_list)
        
        solution_controls = QHBoxLayout()
        self.new_solution_input = QLineEdit()
        self.new_solution_input.setPlaceholderText("Enter an action you took...")
        solution_controls.addWidget(self.new_solution_input)
        
        self.add_solution_btn = QPushButton("Add")
        self.add_solution_btn.clicked.connect(self.add_solution)
        solution_controls.addWidget(self.add_solution_btn)
        
        solution_layout.addLayout(solution_controls)
        solution_group.setLayout(solution_layout)
        layout.addWidget(solution_group)
        
        # === 5. Effectiveness Rating ===
        effectiveness_group = QGroupBox("5. How well did your solution work?")
        effectiveness_group.setFont(QFont("Arial", 10, QFont.Bold))
        effectiveness_layout = QVBoxLayout()
        
        rating_instructions = QLabel(
            "Rate the effectiveness of your solution:"
        )
        effectiveness_layout.addWidget(rating_instructions)
        
        self.effectiveness_buttons = QButtonGroup()
        
        effectiveness_options = [
            ("Completely solved the issue", "The problem was fully resolved and has not recurred"),
            ("Temporarily fixed the issue", "The problem was solved but may return in the future"),
            ("Partially improved the situation", "The problem was improved but not fully resolved"),
            ("Did not help", "The actions taken did not improve the situation")
        ]
        
        for i, (label, tooltip) in enumerate(effectiveness_options):
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            self.effectiveness_buttons.addButton(radio, i)
            effectiveness_layout.addWidget(radio)
            
        # Default to "Completely solved"
        self.effectiveness_buttons.button(0).setChecked(True)
        
        effectiveness_group.setLayout(effectiveness_layout)
        layout.addWidget(effectiveness_group)
        
        # === Bottom Buttons ===
        buttons_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Rule")
        self.preview_btn.setToolTip("Preview how this capture will be stored as a rule")
        self.preview_btn.clicked.connect(self.preview_rule)
        buttons_layout.addWidget(self.preview_btn)
        
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Capture")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.validate_and_accept)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Set the main widget as the scroll area's widget
        scroll_area.setWidget(main_widget)
        
        # Create the main layout to hold the scroll area
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # Connect enter key for quick addition
        self.new_check_input.returnPressed.connect(self.add_check)
        self.new_observation_input.returnPressed.connect(self.add_observation)
        self.new_solution_input.returnPressed.connect(self.add_solution)
        
        logger.debug("Quick capture dialog initialized")
        
    def add_check(self):
        """Add a new diagnostic check to the list."""
        check_text = self.new_check_input.text().strip()
        if check_text:
            self.checks_list.addItem(check_text)
            self.new_check_input.clear()
            self.new_check_input.setFocus()
            
    def add_observation(self):
        """Add a new observation to the list."""
        observation_text = self.new_observation_input.text().strip()
        if observation_text:
            self.observations_list.addItem(observation_text)
            self.new_observation_input.clear()
            self.new_observation_input.setFocus()
            
    def add_solution(self):
        """Add a new solution to the list."""
        solution_text = self.new_solution_input.text().strip()
        if solution_text:
            self.solutions_list.addItem(solution_text)
            self.new_solution_input.clear()
            self.new_solution_input.setFocus()
    
    def validate_and_accept(self):
        """Validate inputs before accepting the dialog."""
        # Check if problem description is provided
        if not self.problem_input.toPlainText().strip():
            QMessageBox.warning(self, "Missing Information", 
                              "Please provide a problem description.")
            self.problem_input.setFocus()
            return
        
        # Check if at least one solution is provided
        if self.solutions_list.count() == 0:
            QMessageBox.warning(self, "Missing Information", 
                              "Please add at least one solution action.")
            self.new_solution_input.setFocus()
            return
        
        # All validation passed, accept the dialog
        self.accept()
            
    def preview_rule(self):
        """Preview the rule that would be generated."""
        rule_text = self.generate_rule_text()
        
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Rule Preview")
        preview_dialog.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "This is how your captured information will be stored as a diagnostic rule:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Preview text
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setText(rule_text)
        layout.addWidget(preview_text)
        
        # Explanation
        explanation = QLabel(
            "The rule follows an IF-THEN structure where conditions represent the problem "
            "and checks, while actions represent the solutions you applied."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)
        
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()
        
    def generate_rule_text(self):
        """Generate rule text from the captured information."""
        # Problem statement
        problem_text = self.problem_input.toPlainText().strip()
        problem_type = self.problem_type.currentText()
        if problem_type and problem_type != "Select type...":
            problem_description = f"{problem_type}: {problem_text}"
        else:
            problem_description = problem_text
            
        # Gather checks and observations
        conditions = []
        
        for i in range(self.checks_list.count()):
            check = self.checks_list.item(i).text()
            
            # Try to find matching observations
            if i < self.observations_list.count():
                observation = self.observations_list.item(i).text()
                conditions.append(f"{check} shows {observation}")
            else:
                conditions.append(check)
                
        # Add any remaining observations
        for i in range(self.checks_list.count(), self.observations_list.count()):
            observation = self.observations_list.item(i).text()
            conditions.append(f"Observed {observation}")
            
        # Build the IF part
        if_conditions = []
        if problem_description:
            if_conditions.append(f"problem is '{problem_description}'")
        if_conditions.extend(conditions)
        
        if_part = "IF " + " AND ".join(if_conditions)
        
        # Build the THEN part with actions
        then_part = "THEN"
        for i in range(self.solutions_list.count()):
            solution = self.solutions_list.item(i).text()
            then_part += f"\n  {i+1}. {solution}"
            
        # Combine into final rule
        return f"{if_part},\n{then_part}"
        
    def get_rule(self):
        """Get the rule in structured format for storage.
        
        Returns:
            dict: Structured rule data with conditions, actions, and metadata.
        """
        rule_text = self.generate_rule_text()
        
        # Create structured data
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
                    actions.append(action)
        
        # Add effectiveness rating
        effectiveness_id = self.effectiveness_buttons.checkedId()
        effectiveness_map = {
            0: "Complete Solution",
            1: "Temporary Fix",
            2: "Partial Improvement",
            3: "Ineffective"
        }
        
        # Create metadata
        metadata = {
            "effectiveness": effectiveness_map.get(effectiveness_id, "Unknown"),
            "severity": self.severity.currentText(),
            "problem_type": self.problem_type.currentText(),
            "capture_date": datetime.now().isoformat()
        }
        
        # Create full rule structure
        return {
            "text": rule_text,
            "conditions": conditions,
            "actions": actions,
            "is_complex": True,
            "metadata": metadata
        }