"""
Diagnostic Collection System - Main Window

This module defines the main application window for the Diagnostic Collection System,
providing the primary user interface for managing diagnostic knowledge.
"""

import os
import json
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QTextEdit, QHeaderView, QCheckBox, 
    QLineEdit, QFormLayout, QComboBox, QSplitter, QFrame, QMessageBox, 
    QFileDialog, QGroupBox, QListWidget, QMenu, QAction, QToolBar, QStatusBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from ui.dialogs.pathway_dialog import DiagnosticPathwayDialog
from ui.dialogs.quick_capture_dialog import ContextualCaptureDialog
from ui.dialogs.rule_editor_dialog import RuleEditorDialog
from ui.dialogs.rule_visualizer_dialog import RuleVisualizerDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window for the Diagnostic Collection System application."""
    
    def __init__(self, storage_service):
        """Initialize the main window with the necessary services."""
        super().__init__()
        
        self.storage_service = storage_service
        self.rules = self.storage_service.load_rules()
        
        self.init_ui()
        self.setup_connections()
        self.load_rules_table()
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create splitter for left panel (input) and right panel (rules)
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Input and controls
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(self.left_panel)
        
        # Problem description
        self.label = QLabel("Describe diagnostic situation:")
        left_layout.addWidget(self.label)
        
        self.problem_input = QTextEdit()
        left_layout.addWidget(self.problem_input)
        
        # Search box for existing diagnostics
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Search diagnostics:")
        search_layout.addWidget(self.search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter keywords to search...")
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        search_layout.addWidget(self.search_button)
        
        left_layout.addLayout(search_layout)
        
        # Capture buttons
        capture_group = QGroupBox("Capture Diagnostic Knowledge")
        capture_layout = QVBoxLayout()
        
        self.quick_capture_button = QPushButton("Quick Capture")
        self.quick_capture_button.setToolTip("Quickly capture a problem and solution you've already solved")
        capture_layout.addWidget(self.quick_capture_button)
        
        pathway_layout = QHBoxLayout()
        self.visual_rule_button = QPushButton("Visual Pathway Builder")
        self.visual_rule_button.setToolTip("Create a visual diagnostic pathway")
        pathway_layout.addWidget(self.visual_rule_button)
        
        self.rule_editor_button = QPushButton("Rule Editor")
        self.rule_editor_button.setToolTip("Create or edit a diagnostic rule")
        pathway_layout.addWidget(self.rule_editor_button)
        
        capture_layout.addLayout(pathway_layout)
        capture_group.setLayout(capture_layout)
        left_layout.addWidget(capture_group)
        
        # Export/Import area
        export_import_group = QGroupBox("Export/Import")
        export_import_layout = QHBoxLayout()
        
        self.export_rules_button = QPushButton("Export Rules")
        self.export_rules_button.setToolTip("Export diagnostic knowledge to a file")
        export_import_layout.addWidget(self.export_rules_button)

        self.import_rules_button = QPushButton("Import Rules")
        self.import_rules_button.setToolTip("Import diagnostic knowledge from a file")
        export_import_layout.addWidget(self.import_rules_button)
        
        export_import_group.setLayout(export_import_layout)
        left_layout.addWidget(export_import_group)
        
        # Recent activities list
        activity_group = QGroupBox("Recent Activities")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        activity_group.setLayout(activity_layout)
        left_layout.addWidget(activity_group)
        
        # Right panel - Rules table
        self.right_panel = QFrame()
        self.right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(self.right_panel)
        
        self.rules_label = QLabel("Diagnostic Knowledge Base:")
        self.rules_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(self.rules_label)
        
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Type", "Description", "Actions"])
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rules_table.setColumnWidth(0, 50)  # ID column
        self.rules_table.setColumnWidth(1, 80)  # Type column
        self.rules_table.setColumnWidth(3, 150) # Actions column
        self.rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules_table.setContextMenuPolicy(Qt.CustomContextMenu)
        right_layout.addWidget(self.rules_table)
        
        # Table control buttons
        table_buttons_layout = QHBoxLayout()
        
        self.view_button = QPushButton("View Selected")
        table_buttons_layout.addWidget(self.view_button)
        
        self.edit_button = QPushButton("Edit Selected")
        table_buttons_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Selected")
        table_buttons_layout.addWidget(self.delete_button)
        
        right_layout.addLayout(table_buttons_layout)
        
        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([400, 800])
        
        main_layout.addWidget(self.splitter)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_rules)
        self.toolbar.addAction(refresh_action)
        
        self.toolbar.addSeparator()
        
        # Toolbar filter by type
        self.toolbar.addWidget(QLabel("Filter by type: "))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All Types", "Pathway", "Quick Capture", "Rule"])
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        self.toolbar.addWidget(self.filter_type)
    
    def setup_connections(self):
        """Connect UI elements to their respective handlers."""
        # Search functionality
        self.search_button.clicked.connect(self.search_rules)
        self.search_input.returnPressed.connect(self.search_rules)
        
        # Capture buttons
        self.quick_capture_button.clicked.connect(self.quick_capture_rule)
        self.visual_rule_button.clicked.connect(self.open_visual_rule_builder)
        self.rule_editor_button.clicked.connect(self.open_rule_editor)
        
        # Export/Import buttons
        self.export_rules_button.clicked.connect(self.export_rules)
        self.import_rules_button.clicked.connect(self.import_rules)
        
        # Table controls
        self.view_button.clicked.connect(self.view_selected_rule)
        self.edit_button.clicked.connect(self.edit_selected_rule)
        self.delete_button.clicked.connect(self.delete_selected_rules)
        self.rules_table.customContextMenuRequested.connect(self.show_context_menu)
    
    def load_rules_table(self):
        """Load rules into the table."""
        self.rules_table.setRowCount(len(self.rules))
        
        for i, rule in enumerate(self.rules):
            # ID Column
            id_item = QTableWidgetItem(str(i+1))
            id_item.setData(Qt.UserRole, i)  # Store actual index for retrieval
            self.rules_table.setItem(i, 0, id_item)
            
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
            self.rules_table.setItem(i, 1, type_item)
            
            # Description Column
            description = self._get_rule_description(rule)
            desc_item = QTableWidgetItem(description)
            desc_item.setToolTip(rule.get("text", ""))
            self.rules_table.setItem(i, 2, desc_item)
            
            # Actions Column - using a widget with buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            view_btn = QPushButton("View")
            view_btn.setFixedWidth(60)
            view_btn.clicked.connect(lambda checked, row=i: self.view_rule(row))
            actions_layout.addWidget(view_btn)
            
            apply_btn = QPushButton("Apply")
            apply_btn.setFixedWidth(60)
            apply_btn.clicked.connect(lambda checked, row=i: self.apply_rule(row))
            actions_layout.addWidget(apply_btn)
            
            self.rules_table.setCellWidget(i, 3, actions_widget)
        
        # Update recent activities
        self._update_activity_list()
        
        # Update status bar
        self.status_bar.showMessage(f"Loaded {len(self.rules)} diagnostic rules")
    
    def _get_rule_description(self, rule):
        """Get a concise description of the rule for display."""
        # For visual pathways, try to extract a problem statement
        if rule.get("pathway_data"):
            nodes = rule.get("pathway_data", {}).get("nodes", {})
            for node_id, node in nodes.items():
                if node.get("node_type") == "problem" and node.get("content"):
                    return node.get("content")[:80] + "..." if len(node.get("content")) > 80 else node.get("content")
        
        # For quick captures, use the problem type and description
        metadata = rule.get("metadata", {})
        if metadata.get("problem_type"):
            problem_type = metadata.get("problem_type")
            if problem_type != "Select type...":
                return f"{problem_type}: {rule.get('text', '')[:60]}..."
        
        # Default to the rule text
        text = rule.get("text", "")
        # If it's a complex rule with IF/THEN structure, extract the IF part
        if "IF " in text and ", THEN" in text:
            if_part = text.split(", THEN")[0].replace("IF ", "")
            return if_part[:80] + "..." if len(if_part) > 80 else if_part
        
        # Fallback to truncated rule text
        return text[:80] + "..." if len(text) > 80 else text
    
    def _update_activity_list(self):
        """Update the recent activities list."""
        self.activity_list.clear()
        
        # Sort rules by last_used date, if available
        sorted_rules = sorted(
            [r for r in self.rules if r.get("last_used")],
            key=lambda x: x.get("last_used", ""),
            reverse=True
        )
        
        # Display the 10 most recent activities
        for rule in sorted_rules[:10]:
            last_used = rule.get("last_used", "")
            try:
                # Convert ISO date to human-readable format
                if last_used:
                    date_obj = datetime.fromisoformat(last_used)
                    friendly_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    
                    # Get a short description
                    description = self._get_rule_description(rule)
                    
                    # Add to list
                    self.activity_list.addItem(f"{friendly_date}: {description[:30]}...")
            except Exception as e:
                logger.error(f"Error formatting date {last_used}: {str(e)}")
    
    def quick_capture_rule(self):
        """Open the quick capture dialog to create a new rule."""
        dialog = ContextualCaptureDialog()
        if dialog.exec_():
            # Get rule data
            rule = dialog.get_rule()
            
            if rule:
                # Add created date and initial use count
                rule["created"] = datetime.now().isoformat()
                rule["use_count"] = 0
                rule["last_used"] = None
                
                # Add to rules collection
                self.rules.append(rule)
                
                # Save rules
                self.storage_service.save_rules(self.rules)
                
                # Refresh display
                self.load_rules_table()
                
                QMessageBox.information(self, "Capture Added", "Diagnostic knowledge captured successfully.")
    
    def open_visual_rule_builder(self):
        """Open the visual pathway builder dialog."""
        dialog = DiagnosticPathwayDialog()
        if dialog.exec_():
            # Get rule data
            rule = dialog.get_rule()
            pathway_data = dialog.get_pathway_data()
            
            if rule:
                # Add created date and initial use count
                rule["created"] = datetime.now().isoformat()
                rule["use_count"] = 0
                rule["last_used"] = None
                rule["pathway_data"] = pathway_data  # Store the visual pathway data
                
                # Add to rules
                self.rules.append(rule)
                
                # Save rules
                self.storage_service.save_rules(self.rules)
                
                # Refresh display
                self.load_rules_table()
                
                QMessageBox.information(self, "Pathway Added", "Visual diagnostic pathway added successfully.")
    
    def open_rule_editor(self):
        """Open the rule editor dialog to create or edit a rule."""
        dialog = RuleEditorDialog()
        if dialog.exec_():
            # Get rule data
            rule = dialog.get_rule()
            
            if rule:
                # Add created date and initial use count
                rule["created"] = datetime.now().isoformat()
                rule["use_count"] = 0
                rule["last_used"] = None
                
                # Add to rules
                self.rules.append(rule)
                
                # Save rules
                self.storage_service.save_rules(self.rules)
                
                # Refresh display
                self.load_rules_table()
                
                QMessageBox.information(self, "Rule Added", "Diagnostic rule added successfully.")
    
    def view_rule(self, row):
        """View details of a rule at the specified row."""
        rule_index = int(self.rules_table.item(row, 0).data(Qt.UserRole))
        rule = self.rules[rule_index]
        
        # Check if this was created with a visual pathway
        if rule.get("pathway_data"):
            # Open in the pathway editor for visualization
            dialog = DiagnosticPathwayDialog(rule)
            dialog.exec_()
            return
        
        # Otherwise use the regular visualizer
        if rule.get("is_complex"):
            structured_data = {
                "conditions": rule.get("conditions", []),
                "actions": rule.get("actions", [])
            }
            dialog = RuleVisualizerDialog(rule.get("text", ""), structured_data)
        else:
            dialog = RuleVisualizerDialog(rule.get("text", ""))
        
        dialog.exec_()
    
    def apply_rule(self, row):
        """Mark a rule as applied and log the usage."""
        rule_index = int(self.rules_table.item(row, 0).data(Qt.UserRole))
        rule = self.rules[rule_index]
        
        # Update usage statistics
        rule["use_count"] = rule.get("use_count", 0) + 1
        rule["last_used"] = datetime.now().isoformat()
        
        # Log the application
        problem_description = self.problem_input.toPlainText().strip()
        self._log_rule_application(rule, problem_description)
        
        # Save rules
        self.storage_service.save_rules(self.rules)
        
        # Refresh display
        self.load_rules_table()
        
        QMessageBox.information(self, "Rule Applied", 
                               f"The diagnostic rule has been applied and logged.\n"
                               f"Total times used: {rule['use_count']}")
    
    def _log_rule_application(self, rule, problem_description=""):
        """Log the application of a rule."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rule_id": self.rules.index(rule),
            "rule_text": rule.get("text", ""),
            "problem_description": problem_description,
            "rule_type": "Pathway" if rule.get("pathway_data") else 
                         "Capture" if rule.get("metadata", {}).get("problem_type") else "Rule"
        }
        
        # Add to interaction log
        self.storage_service.log_interaction(log_entry)
    
    def search_rules(self):
        """Search rules based on the search input."""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            # If search is empty, reset filters
            self.filter_type.setCurrentIndex(0)
            self.load_rules_table()
            return
        
        # Get current type filter
        type_filter = self.filter_type.currentText()
        
        # Apply both search and type filter
        matching_rows = []
        
        for i, rule in enumerate(self.rules):
            # Check type filter first
            rule_type = "Pathway" if rule.get("pathway_data") else \
                       "Capture" if rule.get("metadata", {}).get("problem_type") else "Rule"
                       
            if type_filter != "All Types" and type_filter != rule_type:
                continue
            
            # Then check text match
            rule_text = rule.get("text", "").lower()
            description = self._get_rule_description(rule).lower()
            
            # Check for matches in conditions and actions
            conditions_match = any(
                search_text in str(c).lower() 
                for c in rule.get("conditions", [])
            )
            
            actions_match = any(
                search_text in str(a).lower() 
                for a in rule.get("actions", [])
            )
            
            # Check problem/metadata for quick captures
            metadata_match = False
            if rule.get("metadata"):
                for k, v in rule.get("metadata", {}).items():
                    if search_text in str(v).lower():
                        metadata_match = True
                        break
            
            # Check pathway data for visual pathways
            pathway_match = False
            if rule.get("pathway_data"):
                nodes = rule.get("pathway_data", {}).get("nodes", {})
                for node_id, node in nodes.items():
                    if search_text in node.get("content", "").lower():
                        pathway_match = True
                        break
            
            # If any match, add to matching rows
            if (search_text in rule_text or 
                search_text in description or 
                conditions_match or 
                actions_match or 
                metadata_match or 
                pathway_match):
                matching_rows.append(i)
        
        # Hide non-matching rows
        for i in range(self.rules_table.rowCount()):
            self.rules_table.setRowHidden(i, i not in matching_rows)
        
        # Update status
        self.status_bar.showMessage(f"Found {len(matching_rows)} matching rules")
    
    def apply_filters(self):
        """Apply filters to the rules table."""
        type_filter = self.filter_type.currentText()
        
        if type_filter == "All Types":
            # Show all rows
            for i in range(self.rules_table.rowCount()):
                self.rules_table.setRowHidden(i, False)
            return
        
        # Apply type filter
        for i in range(self.rules_table.rowCount()):
            row_type = self.rules_table.item(i, 1).text()
            self.rules_table.setRowHidden(i, row_type != type_filter)
        
        # If there's also a search query, combine filters
        search_text = self.search_input.text().lower().strip()
        if search_text:
            self.search_rules()
    
    def view_selected_rule(self):
        """View the selected rule."""
        selected_rows = self.rules_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a rule to view.")
            return
        
        # Get the first selected row
        row = selected_rows[0].row()
        self.view_rule(row)
    
    def edit_selected_rule(self):
        """Edit the selected rule."""
        selected_rows = self.rules_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a rule to edit.")
            return
        
        # Get the first selected row
        row = selected_rows[0].row()
        rule_index = int(self.rules_table.item(row, 0).data(Qt.UserRole))
        rule = self.rules[rule_index]
        
        # Open the appropriate editor based on rule type
        if rule.get("pathway_data"):
            dialog = DiagnosticPathwayDialog(rule)
            if dialog.exec_():
                # Update rule with edited data
                updated_rule = dialog.get_rule()
                updated_pathway = dialog.get_pathway_data()
                
                # Preserve the original metadata
                updated_rule["created"] = rule.get("created")
                updated_rule["use_count"] = rule.get("use_count", 0)
                updated_rule["last_used"] = rule.get("last_used")
                updated_rule["pathway_data"] = updated_pathway
                
                # Update in the collection
                self.rules[rule_index] = updated_rule
                
                # Save and refresh
                self.storage_service.save_rules(self.rules)
                self.load_rules_table()
        else:
            # Use rule editor for regular rules
            dialog = RuleEditorDialog(rule)
            if dialog.exec_():
                updated_rule = dialog.get_rule()
                
                # Preserve the original metadata
                updated_rule["created"] = rule.get("created")
                updated_rule["use_count"] = rule.get("use_count", 0)
                updated_rule["last_used"] = rule.get("last_used")
                
                # Update in the collection
                self.rules[rule_index] = updated_rule
                
                # Save and refresh
                self.storage_service.save_rules(self.rules)
                self.load_rules_table()
    
    def delete_selected_rules(self):
        """Delete the selected rules."""
        selected_rows = self.rules_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select rules to delete.")
            return
        
        # Get unique rows (when multiple cells in a row are selected)
        selected_row_indexes = set()
        for item in selected_rows:
            selected_row_indexes.add(item.row())
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_row_indexes)} rule(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Convert rows to rule indexes (stored in the ID column's UserRole)
            rule_indices = []
            for row in selected_row_indexes:
                rule_indices.append(int(self.rules_table.item(row, 0).data(Qt.UserRole)))
            
            # Sort in descending order to avoid index shifting during removal
            rule_indices.sort(reverse=True)
            
            # Remove the rules
            for index in rule_indices:
                self.rules.pop(index)
            
            # Save and refresh
            self.storage_service.save_rules(self.rules)
            self.load_rules_table()
            
            QMessageBox.information(self, "Success", f"{len(rule_indices)} rules deleted.")
    
    def show_context_menu(self, position):
        """Show context menu for the rules table."""
        menu = QMenu()
        
        view_action = menu.addAction("View")
        edit_action = menu.addAction("Edit")
        apply_action = menu.addAction("Apply")
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        
        # Get the selected row
        indexes = self.rules_table.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        
        # Show the menu and handle action
        action = menu.exec_(self.rules_table.viewport().mapToGlobal(position))
        
        if action == view_action:
            self.view_rule(row)
        elif action == edit_action:
            self.edit_selected_rule()
        elif action == apply_action:
            self.apply_rule(row)
        elif action == delete_action:
            self.delete_selected_rules()
    
    def export_rules(self):
        """Export rules to a JSON file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Rules", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        
        try:
            # Ensure the filename has .json extension
            if not filename.lower().endswith('.json'):
                filename += '.json'
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({"rules": self.rules}, f, indent=2)
                
            QMessageBox.information(self, "Export Successful", f"Rules exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting rules: {str(e)}")
            QMessageBox.critical(self, "Export Failed", f"Error exporting rules: {str(e)}")
    
    def import_rules(self):
        """Import rules from a JSON file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Rules", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if "rules" not in imported_data:
                QMessageBox.warning(self, "Import Error", 
                                   "The selected file does not contain valid rules data.")
                return
            
            # Get existing rule texts to avoid duplicates
            existing_texts = {rule.get("text") for rule in self.rules}
            
            # Filter out duplicates
            new_rules = [rule for rule in imported_data["rules"] 
                         if rule.get("text") not in existing_texts]
            
            if not new_rules:
                QMessageBox.information(self, "Import Result", 
                                       "No new rules found to import.")
                return
            
            # Add new rules
            self.rules.extend(new_rules)
            
            # Save and refresh
            self.storage_service.save_rules(self.rules)
            self.load_rules_table()
            
            QMessageBox.information(self, "Import Successful", 
                                   f"Imported {len(new_rules)} new rules.")
            
        except Exception as e:
            logger.error(f"Error importing rules: {str(e)}")
            QMessageBox.critical(self, "Import Failed", f"Error importing rules: {str(e)}")
    
    def refresh_rules(self):
        """Refresh the rules table."""
        self.rules = self.storage_service.load_rules()
        self.load_rules_table()
        self.status_bar.showMessage("Rules refreshed")