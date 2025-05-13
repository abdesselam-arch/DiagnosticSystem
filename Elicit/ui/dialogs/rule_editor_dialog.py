"""
Diagnostic Collection System - Rule Editor Dialog

This module provides a dialog for creating and editing diagnostic rules,
allowing users to define conditions and actions in a structured manner.
"""

import logging
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QGroupBox,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox, QFormLayout, QTabWidget,
    QWidget, QScrollArea, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QCheckBox, QMenu
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

logger = logging.getLogger(__name__)

class RuleEditorDialog(QDialog):
    """Dialog for creating and editing diagnostic rules."""
    
    OPERATORS = ["=", ">", "<", ">=", "<=", "!=", "contains"]
    CONNECTORS = ["AND", "OR", ""]
    ACTION_TYPES = ["Apply", "Adjust", "Replace", "Clean", "Measure", "Check", "Restart", "Contact"]
    
    def __init__(self, existing_rule=None, parent=None):
        """Initialize the dialog with an optional existing rule."""
        super().__init__(parent)
        self.existing_rule = existing_rule
        self.conditions = []
        self.actions = []
        
        self.init_ui()
        
        # Load existing rule data if provided
        if self.existing_rule:
            self.load_existing_rule()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Rule Editor")
        self.setGeometry(200, 200, 800, 700)
        
        # Create the main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different editing modes
        self.tab_widget = QTabWidget()
        
        # === Structured Editor Tab ===
        structured_tab = QWidget()
        structured_layout = QVBoxLayout(structured_tab)
        
        # Rule name/title
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Rule Name:"))
        self.rule_name = QLineEdit()
        self.rule_name.setPlaceholderText("Enter a descriptive name for this rule...")
        name_layout.addWidget(self.rule_name)
        structured_layout.addLayout(name_layout)
        
        # Conditions section
        conditions_group = QGroupBox("IF (Conditions)")
        conditions_group.setFont(QFont("Arial", 10, QFont.Bold))
        conditions_layout = QVBoxLayout(conditions_group)
        
        # Table to display conditions
        self.conditions_table = QTableWidget()
        self.conditions_table.setColumnCount(4)
        self.conditions_table.setHorizontalHeaderLabels(["Parameter", "Operator", "Value", "Connector"])
        self.conditions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.conditions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.conditions_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.conditions_table.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.conditions_table, "condition")
        )
        conditions_layout.addWidget(self.conditions_table)
        
        # Add condition button
        conditions_btn_layout = QHBoxLayout()
        self.add_condition_btn = QPushButton("Add Condition")
        self.add_condition_btn.clicked.connect(self.add_condition)
        conditions_btn_layout.addWidget(self.add_condition_btn)
        
        # Edit condition form
        condition_form_layout = QFormLayout()
        self.condition_param = QLineEdit()
        self.condition_param.setPlaceholderText("Parameter or observation")
        condition_form_layout.addRow("Parameter:", self.condition_param)
        
        self.condition_operator = QComboBox()
        self.condition_operator.addItems(self.OPERATORS)
        condition_form_layout.addRow("Operator:", self.condition_operator)
        
        self.condition_value = QLineEdit()
        self.condition_value.setPlaceholderText("Value or state")
        condition_form_layout.addRow("Value:", self.condition_value)
        
        self.condition_connector = QComboBox()
        self.condition_connector.addItems(self.CONNECTORS)
        condition_form_layout.addRow("Connector:", self.condition_connector)
        
        self.update_condition_btn = QPushButton("Update Selected Condition")
        self.update_condition_btn.clicked.connect(self.update_condition)
        self.update_condition_btn.setEnabled(False)
        condition_form_layout.addRow("", self.update_condition_btn)
        
        conditions_layout.addLayout(condition_form_layout)
        conditions_layout.addLayout(conditions_btn_layout)
        structured_layout.addWidget(conditions_group)
        
        # Actions section
        actions_group = QGroupBox("THEN (Actions)")
        actions_group.setFont(QFont("Arial", 10, QFont.Bold))
        actions_layout = QVBoxLayout(actions_group)
        
        # Table to display actions
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(4)
        self.actions_table.setHorizontalHeaderLabels(["Type", "Target", "Value", "Sequence"])
        self.actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.actions_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.actions_table.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.actions_table, "action")
        )
        actions_layout.addWidget(self.actions_table)
        
        # Add action button
        actions_btn_layout = QHBoxLayout()
        self.add_action_btn = QPushButton("Add Action")
        self.add_action_btn.clicked.connect(self.add_action)
        actions_btn_layout.addWidget(self.add_action_btn)
        
        # Edit action form
        action_form_layout = QFormLayout()
        self.action_type = QComboBox()
        self.action_type.addItems(self.ACTION_TYPES)
        action_form_layout.addRow("Type:", self.action_type)
        
        self.action_target = QLineEdit()
        self.action_target.setPlaceholderText("What to act on")
        action_form_layout.addRow("Target:", self.action_target)
        
        self.action_value = QLineEdit()
        self.action_value.setPlaceholderText("Optional value or parameter")
        action_form_layout.addRow("Value:", self.action_value)
        
        self.action_sequence = QSpinBox()
        self.action_sequence.setMinimum(1)
        self.action_sequence.setMaximum(100)
        action_form_layout.addRow("Sequence:", self.action_sequence)
        
        self.update_action_btn = QPushButton("Update Selected Action")
        self.update_action_btn.clicked.connect(self.update_action)
        self.update_action_btn.setEnabled(False)
        action_form_layout.addRow("", self.update_action_btn)
        
        actions_layout.addLayout(action_form_layout)
        actions_layout.addLayout(actions_btn_layout)
        structured_layout.addWidget(actions_group)
        
        self.tab_widget.addTab(structured_tab, "Structured Editor")
        
        # === Text Editor Tab ===
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        
        text_instructions = QLabel(
            "Edit the rule directly in IF-THEN format. Follow the pattern:\n"
            "IF condition1 AND condition2 AND condition3,\n"
            "THEN\n"
            "  1. action1\n"
            "  2. action2\n"
            "  3. action3"
        )
        text_instructions.setWordWrap(True)
        text_layout.addWidget(text_instructions)
        
        self.rule_text = QTextEdit()
        text_layout.addWidget(self.rule_text)
        
        self.update_structured_btn = QPushButton("Update Structured View from Text")
        self.update_structured_btn.clicked.connect(self.update_structured_from_text)
        text_layout.addWidget(self.update_structured_btn)
        
        self.tab_widget.addTab(text_tab, "Text Editor")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Rule")
        self.preview_btn.clicked.connect(self.preview_rule)
        buttons_layout.addWidget(self.preview_btn)
        
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Rule")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.validate_and_accept)
        buttons_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Connect table selection changes
        self.conditions_table.itemSelectionChanged.connect(self.on_condition_selected)
        self.actions_table.itemSelectionChanged.connect(self.on_action_selected)
    
    def show_context_menu(self, position, table, item_type):
        """Show context menu for table items."""
        menu = QMenu()
        
        delete_action = menu.addAction("Delete")
        
        # Get the selected row
        indexes = table.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        
        # Show the menu and handle action
        action = menu.exec_(table.viewport().mapToGlobal(position))
        
        if action == delete_action:
            if item_type == "condition":
                self.delete_condition(row)
            else:
                self.delete_action(row)
    
    def add_condition(self):
        """Add a new condition to the list."""
        param = self.condition_param.text().strip()
        operator = self.condition_operator.currentText()
        value = self.condition_value.text().strip()
        connector = self.condition_connector.currentText()
        
        if not param:
            QMessageBox.warning(self, "Missing Information", "Please enter a parameter for the condition.")
            self.condition_param.setFocus()
            return
        
        condition = {
            "param": param,
            "operator": operator,
            "value": value,
            "connector": connector
        }
        
        self.conditions.append(condition)
        self.update_conditions_table()
        
        # Clear form for next entry
        self.condition_param.clear()
        self.condition_value.clear()
        self.condition_param.setFocus()
    
    def update_condition(self):
        """Update the selected condition."""
        indexes = self.conditions_table.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        if row < 0 or row >= len(self.conditions):
            return
        
        param = self.condition_param.text().strip()
        operator = self.condition_operator.currentText()
        value = self.condition_value.text().strip()
        connector = self.condition_connector.currentText()
        
        if not param:
            QMessageBox.warning(self, "Missing Information", "Please enter a parameter for the condition.")
            self.condition_param.setFocus()
            return
        
        self.conditions[row] = {
            "param": param,
            "operator": operator,
            "value": value,
            "connector": connector
        }
        
        self.update_conditions_table()
        self.update_condition_btn.setEnabled(False)
    
    def delete_condition(self, row):
        """Delete a condition at the specified row."""
        if row < 0 or row >= len(self.conditions):
            return
        
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this condition?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.conditions.pop(row)
            self.update_conditions_table()
            self.update_condition_btn.setEnabled(False)
    
    def update_conditions_table(self):
        """Update the conditions table from the conditions list."""
        self.conditions_table.setRowCount(len(self.conditions))
        
        for i, condition in enumerate(self.conditions):
            self.conditions_table.setItem(i, 0, QTableWidgetItem(condition.get("param", "")))
            self.conditions_table.setItem(i, 1, QTableWidgetItem(condition.get("operator", "")))
            self.conditions_table.setItem(i, 2, QTableWidgetItem(condition.get("value", "")))
            self.conditions_table.setItem(i, 3, QTableWidgetItem(condition.get("connector", "")))
    
    def on_condition_selected(self):
        """Handle selection change in conditions table."""
        indexes = self.conditions_table.selectedIndexes()
        if not indexes:
            self.update_condition_btn.setEnabled(False)
            return
        
        row = indexes[0].row()
        if row < 0 or row >= len(self.conditions):
            self.update_condition_btn.setEnabled(False)
            return
        
        # Load selected condition into form
        condition = self.conditions[row]
        self.condition_param.setText(condition.get("param", ""))
        index = self.condition_operator.findText(condition.get("operator", "="))
        self.condition_operator.setCurrentIndex(max(0, index))
        self.condition_value.setText(condition.get("value", ""))
        index = self.condition_connector.findText(condition.get("connector", ""))
        self.condition_connector.setCurrentIndex(max(0, index))
        
        self.update_condition_btn.setEnabled(True)
    
    def add_action(self):
        """Add a new action to the list."""
        action_type = self.action_type.currentText()
        target = self.action_target.text().strip()
        value = self.action_value.text().strip()
        sequence = self.action_sequence.value()
        
        if not target:
            QMessageBox.warning(self, "Missing Information", "Please enter a target for the action.")
            self.action_target.setFocus()
            return
        
        action = {
            "type": action_type,
            "target": target,
            "value": value,
            "sequence": sequence
        }
        
        self.actions.append(action)
        # Sort actions by sequence
        self.actions.sort(key=lambda x: x.get("sequence", 1))
        self.update_actions_table()
        
        # Clear form for next entry
        self.action_target.clear()
        self.action_value.clear()
        self.action_sequence.setValue(len(self.actions) + 1)
        self.action_target.setFocus()
    
    def update_action(self):
        """Update the selected action."""
        indexes = self.actions_table.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        if row < 0 or row >= len(self.actions):
            return
        
        action_type = self.action_type.currentText()
        target = self.action_target.text().strip()
        value = self.action_value.text().strip()
        sequence = self.action_sequence.value()
        
        if not target:
            QMessageBox.warning(self, "Missing Information", "Please enter a target for the action.")
            self.action_target.setFocus()
            return
        
        self.actions[row] = {
            "type": action_type,
            "target": target,
            "value": value,
            "sequence": sequence
        }
        
        # Sort actions by sequence
        self.actions.sort(key=lambda x: x.get("sequence", 1))
        self.update_actions_table()
        self.update_action_btn.setEnabled(False)
    
    def delete_action(self, row):
        """Delete an action at the specified row."""
        if row < 0 or row >= len(self.actions):
            return
        
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this action?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.actions.pop(row)
            self.update_actions_table()
            self.update_action_btn.setEnabled(False)
    
    def update_actions_table(self):
        """Update the actions table from the actions list."""
        self.actions_table.setRowCount(len(self.actions))
        
        for i, action in enumerate(self.actions):
            self.actions_table.setItem(i, 0, QTableWidgetItem(action.get("type", "")))
            self.actions_table.setItem(i, 1, QTableWidgetItem(action.get("target", "")))
            self.actions_table.setItem(i, 2, QTableWidgetItem(action.get("value", "")))
            self.actions_table.setItem(i, 3, QTableWidgetItem(str(action.get("sequence", 1))))
    
    def on_action_selected(self):
        """Handle selection change in actions table."""
        indexes = self.actions_table.selectedIndexes()
        if not indexes:
            self.update_action_btn.setEnabled(False)
            return
        
        row = indexes[0].row()
        if row < 0 or row >= len(self.actions):
            self.update_action_btn.setEnabled(False)
            return
        
        # Load selected action into form
        action = self.actions[row]
        index = self.action_type.findText(action.get("type", "Apply"))
        self.action_type.setCurrentIndex(max(0, index))
        self.action_target.setText(action.get("target", ""))
        self.action_value.setText(action.get("value", ""))
        self.action_sequence.setValue(action.get("sequence", 1))
        
        self.update_action_btn.setEnabled(True)
    
    def on_tab_changed(self, index):
        """Handle tab change events to sync content between tabs."""
        if index == 1:  # Text Editor tab
            # Update text from structured data
            self.rule_text.setText(self.generate_rule_text())
        elif index == 0:  # Structured Editor tab
            # Text might have been changed, offer to update structured view
            if self.rule_text.document().isModified():
                reply = QMessageBox.question(
                    self, "Update Structured View",
                    "The rule text has been modified. Would you like to update the structured view?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.update_structured_from_text()
    
    def update_structured_from_text(self):
        """Parse rule text and update the structured view."""
        rule_text = self.rule_text.toPlainText().strip()
        
        if not rule_text:
            QMessageBox.warning(self, "Empty Rule", "The rule text is empty.")
            return
        
        # Simple parsing of IF-THEN format
        if "IF " in rule_text and ", THEN" in rule_text:
            if_part = rule_text.split(", THEN")[0].replace("IF ", "")
            then_part = rule_text.split(", THEN")[1].strip()
            
            # Parse conditions
            conditions = []
            # Split by common logical operators
            if " AND " in if_part:
                condition_parts = if_part.split(" AND ")
                for i, part in enumerate(condition_parts):
                    # Parse the condition into components
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
                    # Parse the condition into components
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
            
            # Update the structured view
            self.conditions = conditions
            self.actions = actions
            self.update_conditions_table()
            self.update_actions_table()
            
            self.tab_widget.setCurrentIndex(0)  # Switch to structured view
        else:
            QMessageBox.warning(
                self, "Invalid Format",
                "The rule text does not follow the expected IF-THEN format."
            )
    
    def _parse_condition(self, text):
        """Parse a condition string into structured format."""
        text = text.strip()
        if not text:
            return None
        
        # Try to identify operator
        for op in sorted(self.OPERATORS, key=len, reverse=True):  # Try longer operators first
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
        
        # Try to match known action types
        for action_type in sorted(self.ACTION_TYPES, key=len, reverse=True):  # Try longer types first
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
    
    def load_existing_rule(self):
        """Load data from an existing rule."""
        if not self.existing_rule:
            return
        
        # Load rule name from text if available
        rule_text = self.existing_rule.get("text", "")
        if rule_text.startswith("IF ") and " is '" in rule_text:
            try:
                name_part = rule_text.split(" is '", 1)[1].split("'", 1)[0]
                if ":" in name_part:
                    self.rule_name.setText(name_part)
            except:
                pass
        
        # Load conditions and actions
        self.conditions = self.existing_rule.get("conditions", [])
        self.actions = self.existing_rule.get("actions", [])
        
        # Update UI
        self.update_conditions_table()
        self.update_actions_table()
        self.rule_text.setText(rule_text)
    
    def validate_and_accept(self):
        """Validate inputs before accepting the dialog."""
        # Update from text tab if that's the current tab
        if self.tab_widget.currentIndex() == 1:
            self.update_structured_from_text()
        
        # Ensure we have at least one condition
        if not self.conditions:
            QMessageBox.warning(self, "Missing Conditions", "Please add at least one condition.")
            self.tab_widget.setCurrentIndex(0)  # Switch to structured view
            self.condition_param.setFocus()
            return
        
        # Ensure we have at least one action
        if not self.actions:
            QMessageBox.warning(self, "Missing Actions", "Please add at least one action.")
            self.tab_widget.setCurrentIndex(0)  # Switch to structured view
            self.action_target.setFocus()
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
            "This is how your rule will be stored in the system:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Preview text
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setText(rule_text)
        layout.addWidget(preview_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)
        
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()
    
    def generate_rule_text(self):
        """Generate rule text from the structured data."""
        # Build the IF part with conditions
        if_conditions = []
        for condition in self.conditions:
            param = condition.get("param", "")
            operator = condition.get("operator", "=")
            value = condition.get("value", "")
            
            if operator == "=" and value == "true":
                # Simplified representation for boolean conditions
                if_conditions.append(param)
            else:
                if_conditions.append(f"{param} {operator} {value}")
            
            # Add connector if not the last condition
            if condition != self.conditions[-1] and condition.get("connector"):
                if_conditions.append(condition.get("connector"))
        
        if_part = "IF " + " ".join(if_conditions)
        
        # Build the THEN part with actions
        then_part = "THEN"
        # Sort actions by sequence
        sorted_actions = sorted(self.actions, key=lambda x: x.get("sequence", 1))
        
        for i, action in enumerate(sorted_actions):
            action_type = action.get("type", "Apply")
            target = action.get("target", "")
            value = action.get("value", "")
            
            action_text = f"{action_type} {target}"
            if value:
                action_text += f" to {value}"
                
            then_part += f"\n  {i+1}. {action_text}"
        
        # Combine into final rule
        return f"{if_part},\n{then_part}"
    
    def get_rule(self):
        """Get the rule in structured format for storage.
        
        Returns:
            dict: Structured rule data with conditions, actions, and metadata.
        """
        rule_text = self.generate_rule_text()
        
        # Create full rule structure
        return {
            "text": rule_text,
            "conditions": self.conditions,
            "actions": self.actions,
            "is_complex": True,
            "metadata": {
                "name": self.rule_name.text(),
                "creation_date": datetime.now().isoformat()
            }
        }