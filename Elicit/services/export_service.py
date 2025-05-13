"""
Diagnostic Collection System - Export Service

This module provides specialized services for importing and exporting diagnostic
knowledge in various formats, with additional features beyond basic storage operations.
"""

import os
import json
import csv
import logging
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, TextIO

from models.collection import Collection
from models.rule import Rule
from models.diagnostic_pathway import DiagnosticPathway

logger = logging.getLogger(__name__)


class ExportService:
    """Service for advanced import and export operations of diagnostic knowledge."""
    
    # Supported export formats
    EXPORT_FORMATS = ["json", "csv", "json-pretty", "zip"]
    
    # Export templates for different use cases
    EXPORT_TEMPLATES = {
        "standard": {
            "description": "Standard export with all rule data",
            "fields": ["rule_id", "text", "conditions", "actions", "created_date", "last_used", "use_count"]
        },
        "minimal": {
            "description": "Minimal export with just essential rule data",
            "fields": ["rule_id", "text", "created_date"]
        },
        "usage": {
            "description": "Usage-focused export with statistics",
            "fields": ["rule_id", "text", "last_used", "use_count", "metadata"]
        },
        "full": {
            "description": "Complete export with all available data",
            "fields": None  # None means include everything
        }
    }
    
    def __init__(self, config, storage_service):
        """Initialize the export service with configuration.
        
        Args:
            config: Configuration object with data paths and settings.
            storage_service: Storage service for accessing rule data.
        """
        self.config = config
        self.storage_service = storage_service
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the export service, ensuring export directories exist."""
        try:
            # Ensure export directories exist
            os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
            
            # Create subdirectories for different export types
            os.makedirs(os.path.join(self.config.EXPORT_DIR, "json"), exist_ok=True)
            os.makedirs(os.path.join(self.config.EXPORT_DIR, "csv"), exist_ok=True)
            os.makedirs(os.path.join(self.config.EXPORT_DIR, "zip"), exist_ok=True)
            
            logger.info("Export service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing export service: {str(e)}")
    
    def get_available_export_formats(self) -> List[str]:
        """Get the list of available export formats.
        
        Returns:
            list: List of supported export format names.
        """
        return self.EXPORT_FORMATS
    
    def get_available_export_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get the available export templates.
        
        Returns:
            dict: Dictionary of template name -> template info.
        """
        return self.EXPORT_TEMPLATES
    
    def export_rules(self, rule_ids: List[str] = None, export_format: str = "json", 
                     template: str = "standard", file_path: str = None,
                     include_metadata: bool = True) -> Tuple[bool, str]:
        """Export rules to a file in the specified format.
        
        Args:
            rule_ids (list, optional): List of rule IDs to export. Defaults to None (all rules).
            export_format (str, optional): Format to export in. Defaults to "json".
            template (str, optional): Export template to use. Defaults to "standard".
            file_path (str, optional): Path to save the export. Defaults to None (auto-generated).
            include_metadata (bool, optional): Whether to include metadata. Defaults to True.
            
        Returns:
            tuple: (Success flag, path to exported file or error message)
        """
        try:
            # Validate export format
            if export_format not in self.EXPORT_FORMATS:
                return False, f"Unsupported export format: {export_format}"
            
            # Validate template
            if template not in self.EXPORT_TEMPLATES:
                return False, f"Unknown export template: {template}"
            
            # Get rules to export
            if rule_ids:
                rules_data = {}
                for rule_id in rule_ids:
                    rule_data = self.storage_service.get_rule(rule_id)
                    if rule_data:
                        rules_data[rule_id] = rule_data
            else:
                # Get all rules
                rules = self.storage_service.load_rules()
                rules_data = {rule["rule_id"]: rule for rule in rules}
            
            # Apply template filtering
            if template != "full":
                template_fields = self.EXPORT_TEMPLATES[template]["fields"]
                for rule_id, rule_data in rules_data.items():
                    rules_data[rule_id] = {k: v for k, v in rule_data.items() if k in template_fields}
            
            # Add export metadata
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "format": export_format,
                    "template": template,
                    "rule_count": len(rules_data)
                },
                "rules": rules_data
            }
            
            # Generate file path if not provided
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"rules_export_{timestamp}"
                
                # Create path based on format
                if export_format == "json" or export_format == "json-pretty":
                    file_path = os.path.join(self.config.EXPORT_DIR, "json", f"{filename}.json")
                elif export_format == "csv":
                    file_path = os.path.join(self.config.EXPORT_DIR, "csv", f"{filename}.csv")
                elif export_format == "zip":
                    file_path = os.path.join(self.config.EXPORT_DIR, "zip", f"{filename}.zip")
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Export based on format
            if export_format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f)
                    
            elif export_format == "json-pretty":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                    
            elif export_format == "csv":
                self._export_to_csv(rules_data.values(), file_path, template)
                    
            elif export_format == "zip":
                self._export_to_zip(export_data, file_path)
            
            logger.info(f"Exported {len(rules_data)} rules to {file_path}")
            return True, file_path
            
        except Exception as e:
            error_msg = f"Error exporting rules: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _export_to_csv(self, rules: List[Dict[str, Any]], file_path: str, template: str) -> None:
        """Export rules to a CSV file.
        
        Args:
            rules (list): List of rule dictionaries.
            file_path (str): Path to save the CSV file.
            template (str): Export template name.
        """
        # Get fields to export
        if template == "full":
            # For full template, we need to determine fields from the data
            fields = set()
            for rule in rules:
                fields.update(rule.keys())
            fields = sorted(list(fields))
        else:
            fields = self.EXPORT_TEMPLATES[template]["fields"]
        
        # Write CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            
            for rule in rules:
                # Handle complex fields (convert to string)
                row = {}
                for field in fields:
                    if field in rule:
                        if isinstance(rule[field], (dict, list)):
                            row[field] = json.dumps(rule[field])
                        else:
                            row[field] = rule[field]
                    else:
                        row[field] = ""
                        
                writer.writerow(row)
    
    def _export_to_zip(self, export_data: Dict[str, Any], file_path: str) -> None:
        """Export rules to a ZIP archive containing JSON files.
        
        Args:
            export_data (dict): Dictionary with export information and rules.
            file_path (str): Path to save the ZIP file.
        """
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add export info
            zipf.writestr('export_info.json', json.dumps(export_data['export_info'], indent=2))
            
            # Add each rule as a separate file
            for rule_id, rule_data in export_data['rules'].items():
                # Use shortened rule ID for filename
                short_id = rule_id[:8]
                
                # Get rule type for folder organization
                rule_type = "rule"
                if 'pathway_data' in rule_data:
                    rule_type = "pathway"
                elif 'metadata' in rule_data and 'problem_type' in rule_data['metadata']:
                    rule_type = "capture"
                
                # Create file path within ZIP
                rule_path = f"{rule_type}/{short_id}.json"
                
                # Add rule file
                zipf.writestr(rule_path, json.dumps(rule_data, indent=2))
    
    def import_rules(self, file_path: str, validate_only: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Import rules from a file.
        
        Args:
            file_path (str): Path to the file to import.
            validate_only (bool, optional): Whether to only validate without importing. Defaults to False.
            
        Returns:
            tuple: (Success flag, results or error message)
        """
        try:
            # Determine file type from extension
            _, ext = os.path.splitext(file_path)
            
            results = {
                "status": "unknown",
                "added": 0,
                "updated": 0,
                "errors": [],
                "validated": True if validate_only else False
            }
            
            # Handle different file types
            if ext.lower() == '.json':
                import_results = self._import_from_json(file_path, validate_only)
                results.update(import_results)
                
            elif ext.lower() == '.csv':
                import_results = self._import_from_csv(file_path, validate_only)
                results.update(import_results)
                
            elif ext.lower() == '.zip':
                import_results = self._import_from_zip(file_path, validate_only)
                results.update(import_results)
                
            else:
                return False, {"status": "error", "message": f"Unsupported file type: {ext}"}
            
            # Update status
            if not results.get("status"):
                if results.get("errors"):
                    results["status"] = "error"
                else:
                    results["status"] = "success"
            
            if not validate_only:
                logger.info(
                    f"Imported rules from {file_path}: "
                    f"{results.get('added', 0)} added, {results.get('updated', 0)} updated"
                )
            else:
                logger.info(f"Validated rules from {file_path}: {results.get('errors', 0)} errors")
                
            return len(results.get("errors", [])) == 0, results
            
        except Exception as e:
            error_msg = f"Error importing rules: {str(e)}"
            logger.error(error_msg)
            return False, {"status": "error", "message": error_msg}
    
    def _import_from_json(self, file_path: str, validate_only: bool) -> Dict[str, Any]:
        """Import rules from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file.
            validate_only (bool): Whether to only validate without importing.
            
        Returns:
            dict: Import results.
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # Extract rules data
        rules_data = None
        if isinstance(import_data, dict) and "rules" in import_data:
            rules_data = import_data["rules"]
        else:
            # Try to interpret the data as either a single rule or a list of rules
            if isinstance(import_data, dict):
                # Single rule
                rules_data = {import_data.get("rule_id", str(datetime.now().timestamp())): import_data}
            elif isinstance(import_data, list):
                # List of rules
                rules_data = {}
                for rule in import_data:
                    if isinstance(rule, dict) and "rule_id" in rule:
                        rules_data[rule["rule_id"]] = rule
                    else:
                        # Skip invalid rules
                        continue
        
        if not rules_data:
            return {
                "status": "error",
                "message": "No valid rules found in the JSON file",
                "added": 0,
                "updated": 0,
                "errors": ["No valid rules found"]
            }
        
        # Validate rules
        validation_errors = []
        for rule_id, rule_data in rules_data.items():
            try:
                # Create Rule object to validate
                rule = Rule.from_dict(rule_data)
                issues = rule.validate()
                
                # Check for validation issues
                if any(issues.values()):
                    for category, category_issues in issues.items():
                        for issue in category_issues:
                            validation_errors.append(f"Rule {rule_id}: {category} - {issue}")
            except Exception as e:
                validation_errors.append(f"Rule {rule_id}: Error parsing rule data - {str(e)}")
        
        if validation_errors:
            return {
                "status": "error" if validate_only else "warning",
                "errors": validation_errors,
                "added": 0,
                "updated": 0
            }
        
        # If only validating, return success
        if validate_only:
            return {
                "status": "valid",
                "message": f"All {len(rules_data)} rules are valid",
                "errors": [],
                "rule_count": len(rules_data)
            }
        
        # Import the rules
        added, updated = self.storage_service.collection.import_rules(rules_data)
        
        # Save the collection
        if added > 0 or updated > 0:
            self.storage_service.save_collection()
        
        return {
            "status": "success",
            "added": added,
            "updated": updated,
            "errors": []
        }
    
    def _import_from_csv(self, file_path: str, validate_only: bool) -> Dict[str, Any]:
        """Import rules from a CSV file.
        
        Args:
            file_path (str): Path to the CSV file.
            validate_only (bool): Whether to only validate without importing.
            
        Returns:
            dict: Import results.
        """
        # Read CSV file
        rules_data = {}
        errors = []
        
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for i, row in enumerate(reader):
                try:
                    # Extract rule ID or generate one
                    rule_id = row.get('rule_id', f"csv_import_{i}_{datetime.now().timestamp()}")
                    
                    # Process row data
                    rule_data = {}
                    for field, value in row.items():
                        # Try to parse JSON fields
                        if field in ['conditions', 'actions', 'metadata', 'pathway_data']:
                            try:
                                if value:
                                    rule_data[field] = json.loads(value)
                                else:
                                    rule_data[field] = [] if field in ['conditions', 'actions'] else {}
                            except json.JSONDecodeError:
                                # If not valid JSON, store as string
                                rule_data[field] = value
                                errors.append(f"Row {i+2}: Field '{field}' contains invalid JSON: {value}")
                        else:
                            rule_data[field] = value
                    
                    # Store rule data
                    rules_data[rule_id] = rule_data
                    
                except Exception as e:
                    errors.append(f"Row {i+2}: Error processing row - {str(e)}")
        
        if not rules_data:
            return {
                "status": "error",
                "message": "No valid rules found in the CSV file",
                "added": 0,
                "updated": 0,
                "errors": ["No valid rules found"] + errors
            }
        
        # Validate rules
        validation_errors = []
        for rule_id, rule_data in rules_data.items():
            try:
                # Ensure required fields are present
                if 'text' not in rule_data or not rule_data['text']:
                    validation_errors.append(f"Rule {rule_id}: Missing required field 'text'")
                    continue
                
                # Create Rule object to validate
                rule = Rule.from_dict(rule_data)
                issues = rule.validate()
                
                # Check for validation issues
                if any(issues.values()):
                    for category, category_issues in issues.items():
                        for issue in category_issues:
                            validation_errors.append(f"Rule {rule_id}: {category} - {issue}")
            except Exception as e:
                validation_errors.append(f"Rule {rule_id}: Error parsing rule data - {str(e)}")
        
        # Combine all errors
        all_errors = errors + validation_errors
        
        if all_errors and validate_only:
            return {
                "status": "error",
                "errors": all_errors,
                "added": 0,
                "updated": 0
            }
        
        # If only validating, return success
        if validate_only:
            return {
                "status": "valid",
                "message": f"All {len(rules_data)} rules are valid",
                "errors": all_errors if all_errors else [],
                "rule_count": len(rules_data)
            }
        
        # Import the rules
        added, updated = self.storage_service.collection.import_rules(rules_data)
        
        # Save the collection
        if added > 0 or updated > 0:
            self.storage_service.save_collection()
        
        return {
            "status": "success" if not all_errors else "warning",
            "added": added,
            "updated": updated,
            "errors": all_errors
        }
    
    def _import_from_zip(self, file_path: str, validate_only: bool) -> Dict[str, Any]:
        """Import rules from a ZIP archive.
        
        Args:
            file_path (str): Path to the ZIP file.
            validate_only (bool): Whether to only validate without importing.
            
        Returns:
            dict: Import results.
        """
        rules_data = {}
        errors = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # List all files in the zip
                file_list = zipf.namelist()
                
                # Process each JSON file
                for file_name in file_list:
                    if file_name.endswith('.json') and file_name != 'export_info.json':
                        try:
                            # Read file content
                            with zipf.open(file_name) as f:
                                rule_data = json.load(f)
                                
                                # Get rule ID
                                if 'rule_id' in rule_data:
                                    rule_id = rule_data['rule_id']
                                else:
                                    # Generate ID if missing
                                    rule_id = f"zip_import_{file_name}_{datetime.now().timestamp()}"
                                    rule_data['rule_id'] = rule_id
                                
                                # Store rule data
                                rules_data[rule_id] = rule_data
                                
                        except Exception as e:
                            errors.append(f"File {file_name}: Error processing file - {str(e)}")
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error opening ZIP file: {str(e)}",
                "added": 0,
                "updated": 0,
                "errors": [f"Error opening ZIP file: {str(e)}"]
            }
        
        if not rules_data:
            return {
                "status": "error",
                "message": "No valid rules found in the ZIP file",
                "added": 0,
                "updated": 0,
                "errors": ["No valid rules found"] + errors
            }
        
        # Validate rules
        validation_errors = []
        for rule_id, rule_data in rules_data.items():
            try:
                # Create Rule object to validate
                rule = Rule.from_dict(rule_data)
                issues = rule.validate()
                
                # Check for validation issues
                if any(issues.values()):
                    for category, category_issues in issues.items():
                        for issue in category_issues:
                            validation_errors.append(f"Rule {rule_id}: {category} - {issue}")
            except Exception as e:
                validation_errors.append(f"Rule {rule_id}: Error parsing rule data - {str(e)}")
        
        # Combine all errors
        all_errors = errors + validation_errors
        
        if all_errors and validate_only:
            return {
                "status": "error",
                "errors": all_errors,
                "added": 0,
                "updated": 0
            }
        
        # If only validating, return success
        if validate_only:
            return {
                "status": "valid",
                "message": f"All {len(rules_data)} rules are valid",
                "errors": all_errors if all_errors else [],
                "rule_count": len(rules_data)
            }
        
        # Import the rules
        added, updated = self.storage_service.collection.import_rules(rules_data)
        
        # Save the collection
        if added > 0 or updated > 0:
            self.storage_service.save_collection()
        
        return {
            "status": "success" if not all_errors else "warning",
            "added": added,
            "updated": updated,
            "errors": all_errors
        }
    
    def export_template(self, template_name: str, rule_type: str = None) -> Optional[Dict[str, Any]]:
        """Get a template structure for creating export files.
        
        Args:
            template_name (str): Name of the template to get.
            rule_type (str, optional): Rule type filter for the template. Defaults to None.
            
        Returns:
            dict: Template structure, or None if template not found.
        """
        if template_name not in self.EXPORT_TEMPLATES:
            return None
        
        template = self.EXPORT_TEMPLATES[template_name].copy()
        
        # Example rule based on template
        example_rule = {
            "rule_id": "example-rule-id",
            "text": "IF condition is true, THEN\n  1. Take action",
            "created_date": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        if rule_type == "Pathway":
            example_rule["pathway_data"] = {"nodes": {}, "connections": []}
        elif rule_type == "Capture":
            example_rule["metadata"] = {"problem_type": "Example Problem", "severity": "Medium"}
        
        template["example"] = {
            k: v for k, v in example_rule.items() 
            if template["fields"] is None or k in template["fields"]
        }
        
        return template