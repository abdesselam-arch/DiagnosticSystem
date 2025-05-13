"""
Diagnostic Collection System - Storage Service

This module provides services for persistent storage and retrieval of diagnostic
rules, pathways and related data, acting as an intermediary between the
application and the filesystem.
"""

import os
import json
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

from models.collection import Collection
from models.rule import Rule
from models.diagnostic_pathway import DiagnosticPathway

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing persistent storage of diagnostic rules and pathways."""
    
    def __init__(self, config):
        """Initialize the storage service with configuration.
        
        Args:
            config: Configuration object with data paths and settings.
        """
        self.config = config
        self.collection = None
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the storage service, ensuring data directories exist and loading the collection."""
        try:
            # Ensure data directories exist
            os.makedirs(self.config.DATA_DIR, exist_ok=True)
            os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
            
            # Load the collection
            self.load_collection()
            
            logger.info("Storage service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing storage service: {str(e)}")
            # Create a new empty collection if loading fails
            self.collection = Collection()
    
    def load_collection(self) -> None:
        """Load the diagnostic collection from the rules file."""
        try:
            if os.path.exists(self.config.RULES_FILE):
                self.collection = Collection.load_from_file(self.config.RULES_FILE)
                if not self.collection:
                    logger.warning("Rules file exists but couldn't be loaded. Creating new collection.")
                    self.collection = Collection()
            else:
                logger.info("Rules file does not exist. Creating new collection.")
                self.collection = Collection()
                
            logger.info(f"Loaded collection with {len(self.collection.get_all_rules())} rules")
        except Exception as e:
            logger.error(f"Error loading collection: {str(e)}")
            self.collection = Collection()
    
    def save_collection(self) -> bool:
        """Save the diagnostic collection to the rules file.
        
        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            # Create a backup first
            self._create_backup()
            
            # Save the collection
            success = self.collection.save_to_file(self.config.RULES_FILE)
            
            if success:
                logger.info(f"Saved collection with {len(self.collection.get_all_rules())} rules")
            else:
                logger.error("Failed to save collection")
                
            return success
        except Exception as e:
            logger.error(f"Error saving collection: {str(e)}")
            return False
    
    def _create_backup(self) -> bool:
        """Create a backup of the rules file if it exists.
        
        Returns:
            bool: True if the backup was created, False otherwise.
        """
        try:
            if os.path.exists(self.config.RULES_FILE):
                # Create backups directory if it doesn't exist
                backup_dir = os.path.join(self.config.DATA_DIR, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                
                # Generate backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(
                    backup_dir, 
                    f"rules_backup_{timestamp}.json"
                )
                
                # Copy the file
                shutil.copy2(self.config.RULES_FILE, backup_file)
                logger.info(f"Created backup at {backup_file}")
                
                # Manage backup rotation (keep last 10 backups)
                self._rotate_backups(backup_dir)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False
    
    def _rotate_backups(self, backup_dir: str, max_backups: int = 10) -> None:
        """Rotate backups, keeping only the most recent ones.
        
        Args:
            backup_dir (str): Directory containing backups.
            max_backups (int, optional): Maximum number of backups to keep. Defaults to 10.
        """
        try:
            # Get list of backup files with full paths
            backup_files = [
                os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
                if f.startswith("rules_backup_") and f.endswith(".json")
            ]
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda f: os.path.getmtime(f))
            
            # Remove oldest backups if we have too many
            while len(backup_files) > max_backups:
                oldest = backup_files.pop(0)
                os.remove(oldest)
                logger.info(f"Removed old backup: {oldest}")
        except Exception as e:
            logger.error(f"Error rotating backups: {str(e)}")
    
    def load_rules(self) -> List[Dict[str, Any]]:
        """Load all rules from the collection.
        
        Returns:
            list: List of rule dictionaries.
        """
        if not self.collection:
            self.load_collection()
            
        # Convert rules to dictionaries for the UI
        rules = []
        for rule_id, rule in self.collection.get_all_rules().items():
            rule_dict = rule.to_dict()
            rules.append(rule_dict)
            
        return rules
    
    def save_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """Save rules to the collection.
        
        Args:
            rules (list): List of rule dictionaries.
            
        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            # Create a new collection 
            new_collection = Collection(
                collection_id=self.collection.collection_id,
                name=self.collection.name
            )
            new_collection.description = self.collection.description
            
            # Add each rule
            for rule_data in rules:
                rule = Rule.from_dict(rule_data)
                new_collection.add_rule(rule)
            
            # Replace the current collection
            self.collection = new_collection
            
            # Save to disk
            return self.save_collection()
        except Exception as e:
            logger.error(f"Error saving rules: {str(e)}")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a rule by ID.
        
        Args:
            rule_id (str): ID of the rule to get.
            
        Returns:
            dict: Rule dictionary, or None if not found.
        """
        rule = self.collection.get_rule(rule_id)
        if rule:
            return rule.to_dict()
        return None
    
    def add_rule(self, rule_data: Dict[str, Any]) -> str:
        """Add a new rule to the collection.
        
        Args:
            rule_data (dict): Rule dictionary.
            
        Returns:
            str: ID of the added rule.
        """
        try:
            rule = Rule.from_dict(rule_data)
            rule_id = self.collection.add_rule(rule)
            self.save_collection()
            return rule_id
        except Exception as e:
            logger.error(f"Error adding rule: {str(e)}")
            return ""
    
    def update_rule(self, rule_data: Dict[str, Any]) -> bool:
        """Update an existing rule in the collection.
        
        Args:
            rule_data (dict): Rule dictionary.
            
        Returns:
            bool: True if the rule was updated, False otherwise.
        """
        try:
            rule = Rule.from_dict(rule_data)
            success = self.collection.update_rule(rule)
            if success:
                self.save_collection()
            return success
        except Exception as e:
            logger.error(f"Error updating rule: {str(e)}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule from the collection.
        
        Args:
            rule_id (str): ID of the rule to delete.
            
        Returns:
            bool: True if the rule was deleted, False otherwise.
        """
        try:
            success = self.collection.remove_rule(rule_id)
            if success:
                self.save_collection()
            return success
        except Exception as e:
            logger.error(f"Error deleting rule: {str(e)}")
            return False
    
    def record_rule_usage(self, rule_id: str) -> bool:
        """Record that a rule has been used.
        
        Args:
            rule_id (str): ID of the rule that was used.
            
        Returns:
            bool: True if the usage was recorded, False otherwise.
        """
        try:
            success = self.collection.record_rule_usage(rule_id)
            if success:
                self.save_collection()
            return success
        except Exception as e:
            logger.error(f"Error recording rule usage: {str(e)}")
            return False
    
    def search_rules(self, query: str, rule_type: str = None, 
                     advanced_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for rules matching the criteria.
        
        Args:
            query (str): Search query.
            rule_type (str, optional): Rule type filter. Defaults to None.
            advanced_criteria (dict, optional): Additional search criteria. Defaults to None.
            
        Returns:
            list: List of matching rule dictionaries.
        """
        try:
            # Extract case sensitivity from advanced criteria
            case_sensitive = False
            if advanced_criteria and "match_case" in advanced_criteria:
                case_sensitive = advanced_criteria.get("match_case", False)
                
            # Perform the search
            matching_rules = self.collection.search_rules(
                query, 
                case_sensitive=case_sensitive,
                rule_type=rule_type, 
                advanced_criteria=advanced_criteria
            )
            
            # Convert to dictionaries
            return [rule.to_dict() for rule in matching_rules.values()]
        except Exception as e:
            logger.error(f"Error searching rules: {str(e)}")
            return []
    
    def export_rules(self, rule_ids: List[str] = None, file_path: str = None) -> bool:
        """Export rules to a file.
        
        Args:
            rule_ids (list, optional): List of rule IDs to export. Defaults to None (all rules).
            file_path (str, optional): Path to save the export. Defaults to None (default location).
            
        Returns:
            bool: True if the export was successful, False otherwise.
        """
        try:
            # Export rules
            export_data = self.collection.export_rules(rule_ids)
            
            # Determine file path if not provided
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(
                    self.config.EXPORT_DIR, 
                    f"rules_export_{timestamp}.json"
                )
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Exported rules to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting rules: {str(e)}")
            return False
    
    def import_rules(self, file_path: str) -> Tuple[int, int]:
        """Import rules from a file.
        
        Args:
            file_path (str): Path to the file to import.
            
        Returns:
            tuple: (Number of rules added, number of rules updated)
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import rules
            added, updated = self.collection.import_rules(import_data)
            
            # Save the updated collection
            if added > 0 or updated > 0:
                self.save_collection()
                
            logger.info(f"Imported rules: {added} added, {updated} updated")
            return added, updated
        except Exception as e:
            logger.error(f"Error importing rules: {str(e)}")
            return 0, 0
    
    def duplicate_rule(self, rule_id: str) -> Optional[str]:
        """Create a duplicate of a rule.
        
        Args:
            rule_id (str): ID of the rule to duplicate.
            
        Returns:
            str: ID of the new rule, or None if duplication failed.
        """
        try:
            new_rule_id = self.collection.duplicate_rule(rule_id)
            if new_rule_id:
                self.save_collection()
            return new_rule_id
        except Exception as e:
            logger.error(f"Error duplicating rule: {str(e)}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection.
        
        Returns:
            dict: Dictionary with statistics.
        """
        try:
            return self.collection.get_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "total_rules": 0,
                "error": str(e)
            }
    
    def get_recently_used_rules(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently used rules.
        
        Args:
            count (int, optional): Maximum number of rules to return. Defaults to 10.
            
        Returns:
            list: List of recently used rule dictionaries.
        """
        try:
            recent_rules = self.collection.get_recently_used_rules(count)
            return [rule.to_dict() for rule in recent_rules]
        except Exception as e:
            logger.error(f"Error getting recently used rules: {str(e)}")
            return []
    
    def log_interaction(self, log_entry: Dict[str, Any]) -> bool:
        """Log a user interaction with the system.
        
        Args:
            log_entry (dict): Dictionary with interaction data.
            
        Returns:
            bool: True if the log was successful, False otherwise.
        """
        try:
            # Ensure log file directory exists
            log_file = self.config.INTERACTION_LOG
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Load existing log
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Invalid interaction log file. Creating new log.")
                        logs = []
            
            # Add new entry
            logs.append(log_entry)
            
            # Write updated log
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            return False