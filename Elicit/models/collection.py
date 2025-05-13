"""
Diagnostic Collection System - Collection Model

This module defines the Collection model class, which manages a collection
of diagnostic rules and pathways, providing a central data store for 
diagnostic knowledge.
"""

import json
import uuid
import os
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime

from models.rule import Rule
from models.diagnostic_pathway import DiagnosticPathway


class Collection:
    """Model representing a collection of diagnostic rules and pathways."""
    
    def __init__(self, collection_id: str = None, name: str = "Diagnostic Collection"):
        """Initialize a collection.
        
        Args:
            collection_id (str, optional): Unique identifier for the collection. Generated if not provided.
            name (str, optional): Name of the collection. Defaults to "Diagnostic Collection".
        """
        # Core properties
        self.collection_id = collection_id if collection_id else str(uuid.uuid4())
        self.name = name
        self.description = ""
        
        # Storage for rules and pathways
        self.rules = {}  # Dict of rule_id -> Rule
        
        # Metadata
        self.created_date = datetime.now().isoformat()
        self.last_modified_date = self.created_date
        
        # Indexing data for faster searches
        self._rebuild_indices()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Collection':
        """Create a Collection instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing collection data.
            
        Returns:
            Collection: A new Collection instance populated with the data.
        """
        collection = cls(
            collection_id=data.get('collection_id'),
            name=data.get('name', 'Diagnostic Collection')
        )
        
        # Load core properties
        collection.description = data.get('description', '')
        
        # Load metadata
        collection.created_date = data.get('created_date', collection.created_date)
        collection.last_modified_date = data.get('last_modified_date', collection.last_modified_date)
        
        # Load rules
        if 'rules' in data:
            for rule_id, rule_data in data['rules'].items():
                rule = Rule.from_dict(rule_data)
                collection.rules[rule_id] = rule
        
        # Rebuild indices
        collection._rebuild_indices()
        
        return collection
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the collection to a dictionary.
        
        Returns:
            dict: Dictionary representation of the collection.
        """
        return {
            'collection_id': self.collection_id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date,
            'last_modified_date': self.last_modified_date,
            'rules': {rule_id: rule.to_dict() for rule_id, rule in self.rules.items()}
        }
    
    def to_json(self) -> str:
        """Convert the collection to a JSON string.
        
        Returns:
            str: JSON representation of the collection.
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Collection':
        """Create a Collection instance from a JSON string.
        
        Args:
            json_str (str): JSON string containing collection data.
            
        Returns:
            Collection: A new Collection instance populated with the data.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def add_rule(self, rule: Rule) -> str:
        """Add a rule to the collection.
        
        Args:
            rule (Rule): The rule to add.
            
        Returns:
            str: The ID of the added rule.
        """
        # Update last modified date
        self.last_modified_date = datetime.now().isoformat()
        
        # Add the rule
        self.rules[rule.rule_id] = rule
        
        # Update indices
        self._update_index_for_rule(rule)
        
        return rule.rule_id
    
    def update_rule(self, rule: Rule) -> bool:
        """Update an existing rule in the collection.
        
        Args:
            rule (Rule): The rule to update.
            
        Returns:
            bool: True if the rule was updated, False if it wasn't found.
        """
        if rule.rule_id not in self.rules:
            return False
        
        # Update last modified date
        self.last_modified_date = datetime.now().isoformat()
        
        # Update the rule
        self.rules[rule.rule_id] = rule
        
        # Update indices
        self._rebuild_indices()
        
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the collection.
        
        Args:
            rule_id (str): ID of the rule to remove.
            
        Returns:
            bool: True if the rule was removed, False if it wasn't found.
        """
        if rule_id not in self.rules:
            return False
        
        # Update last modified date
        self.last_modified_date = datetime.now().isoformat()
        
        # Remove the rule
        del self.rules[rule_id]
        
        # Update indices
        self._rebuild_indices()
        
        return True
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID.
        
        Args:
            rule_id (str): ID of the rule to get.
            
        Returns:
            Rule: The rule, or None if not found.
        """
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> Dict[str, Rule]:
        """Get all rules in the collection.
        
        Returns:
            dict: Dictionary of rule_id -> Rule.
        """
        return self.rules
    
    def get_rules_by_type(self, rule_type: str) -> Dict[str, Rule]:
        """Get all rules of a specific type.
        
        Args:
            rule_type (str): Type of rules to get ('Pathway', 'Capture', or 'Rule').
            
        Returns:
            dict: Dictionary of rule_id -> Rule for rules of the specified type.
        """
        return {
            rule_id: rule for rule_id, rule in self.rules.items()
            if rule.get_rule_type() == rule_type
        }
    
    def search_rules(self, query: str, case_sensitive: bool = False, 
                    rule_type: str = None, advanced_criteria: Dict[str, Any] = None) -> Dict[str, Rule]:
        """Search for rules matching the query and criteria.
        
        Args:
            query (str): Search query to match against rule text and description.
            case_sensitive (bool, optional): Whether to perform case-sensitive matching. Defaults to False.
            rule_type (str, optional): Filter by rule type. Defaults to None (all types).
            advanced_criteria (dict, optional): Additional search criteria. Defaults to None.
                May include:
                - date_from: ISO date string for earliest creation date
                - date_to: ISO date string for latest creation date
                - usage: Filter by usage pattern (e.g., "Never Used", "Used At Least Once")
                - effectiveness: Filter by action effectiveness
                - search_fields: Limit search to specific fields
            
        Returns:
            dict: Dictionary of rule_id -> Rule for matching rules.
        """
        # Prepare query
        if not case_sensitive:
            query = query.lower()
        
        # Start with all rules or filtered by type
        if rule_type and rule_type != "All Types":
            results = self.get_rules_by_type(rule_type)
        else:
            results = self.rules.copy()
        
        # Filter by query text if provided
        if query:
            filtered_results = {}
            
            for rule_id, rule in results.items():
                # Get text to search in
                searchable_text = []
                
                # Determine which fields to search based on advanced criteria
                search_fields = advanced_criteria.get("search_fields", "All Fields") if advanced_criteria else "All Fields"
                
                if search_fields in ["All Fields", "Description Only"]:
                    # Include rule text and description
                    text = rule.text
                    if not case_sensitive:
                        text = text.lower()
                    searchable_text.append(text)
                    
                    if rule.description:
                        desc = rule.description
                        if not case_sensitive:
                            desc = desc.lower()
                        searchable_text.append(desc)
                
                if search_fields in ["All Fields", "Conditions Only"]:
                    # Include condition text
                    for condition in rule.conditions:
                        cond_text = f"{condition.get('param', '')} {condition.get('operator', '')} {condition.get('value', '')}"
                        if not case_sensitive:
                            cond_text = cond_text.lower()
                        searchable_text.append(cond_text)
                
                if search_fields in ["All Fields", "Actions Only"]:
                    # Include action text
                    for action in rule.actions:
                        action_text = f"{action.get('type', '')} {action.get('target', '')} {action.get('value', '')}"
                        if not case_sensitive:
                            action_text = action_text.lower()
                        searchable_text.append(action_text)
                
                # Check for match in any of the searchable text
                if any(query in text for text in searchable_text):
                    filtered_results[rule_id] = rule
            
            results = filtered_results
        
        # Apply advanced criteria if provided
        if advanced_criteria:
            # Date range filter
            if "date_from" in advanced_criteria:
                date_from = advanced_criteria["date_from"]
                results = {
                    rule_id: rule for rule_id, rule in results.items()
                    if rule.created_date >= date_from
                }
            
            if "date_to" in advanced_criteria:
                date_to = advanced_criteria["date_to"]
                results = {
                    rule_id: rule for rule_id, rule in results.items()
                    if rule.created_date <= date_to
                }
            
            # Usage filter
            if "usage" in advanced_criteria:
                usage_filter = advanced_criteria["usage"]
                
                if usage_filter == "Never Used":
                    results = {
                        rule_id: rule for rule_id, rule in results.items()
                        if rule.use_count == 0
                    }
                elif usage_filter == "Used At Least Once":
                    results = {
                        rule_id: rule for rule_id, rule in results.items()
                        if rule.use_count > 0
                    }
                elif usage_filter == "Frequently Used (5+)":
                    results = {
                        rule_id: rule for rule_id, rule in results.items()
                        if rule.use_count >= 5
                    }
                elif usage_filter == "Recently Used":
                    # Define "recently" as having a last_used timestamp
                    results = {
                        rule_id: rule for rule_id, rule in results.items()
                        if rule.last_used is not None
                    }
            
            # Effectiveness filter
            if "effectiveness" in advanced_criteria:
                effectiveness_filter = advanced_criteria["effectiveness"]
                
                if effectiveness_filter != "Any Effectiveness":
                    filtered_results = {}
                    for rule_id, rule in results.items():
                        # Check metadata for effectiveness
                        if "effectiveness" in rule.metadata:
                            if rule.metadata["effectiveness"] == effectiveness_filter:
                                filtered_results[rule_id] = rule
                    results = filtered_results
        
        return results
    
    def record_rule_usage(self, rule_id: str) -> bool:
        """Record that a rule has been used.
        
        Args:
            rule_id (str): ID of the rule that was used.
            
        Returns:
            bool: True if the usage was recorded, False if the rule wasn't found.
        """
        if rule_id not in self.rules:
            return False
        
        # Update the rule's usage stats
        rule = self.rules[rule_id]
        rule.record_usage()
        
        # Update last modified date
        self.last_modified_date = datetime.now().isoformat()
        
        return True
    
    def import_rules(self, rules_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Tuple[int, int]:
        """Import rules into the collection.
        
        Args:
            rules_data (dict or list): Dictionary or list of dictionaries containing rule data.
            
        Returns:
            tuple: (Number of rules added, number of rules updated)
        """
        added = 0
        updated = 0
        
        # Handle both dictionary and list formats
        if isinstance(rules_data, dict):
            # Extract rules from dict
            if "rules" in rules_data:
                rules_to_import = rules_data["rules"]
            else:
                # Assume the entire dict is a single rule
                rules_to_import = [rules_data]
        else:
            # Assume it's a list of rules
            rules_to_import = rules_data
        
        # Process each rule
        for rule_data in rules_to_import:
            rule = Rule.from_dict(rule_data)
            
            # Check if rule already exists
            if rule.rule_id in self.rules:
                # Update existing rule
                self.update_rule(rule)
                updated += 1
            else:
                # Add new rule
                self.add_rule(rule)
                added += 1
        
        # Update indices
        self._rebuild_indices()
        
        return added, updated
    
    def export_rules(self, rule_ids: List[str] = None) -> Dict[str, Any]:
        """Export rules from the collection.
        
        Args:
            rule_ids (list, optional): List of rule IDs to export. Defaults to None (all rules).
            
        Returns:
            dict: Dictionary containing the exported rules.
        """
        if rule_ids is None:
            # Export all rules
            rules_data = {rule_id: rule.to_dict() for rule_id, rule in self.rules.items()}
        else:
            # Export only specified rules
            rules_data = {
                rule_id: self.rules[rule_id].to_dict() 
                for rule_id in rule_ids if rule_id in self.rules
            }
        
        return {
            "collection_name": self.name,
            "export_date": datetime.now().isoformat(),
            "rules": rules_data
        }
    
    def duplicate_rule(self, rule_id: str) -> Optional[str]:
        """Create a duplicate of a rule with a new ID.
        
        Args:
            rule_id (str): ID of the rule to duplicate.
            
        Returns:
            str: ID of the new rule, or None if the original wasn't found.
        """
        if rule_id not in self.rules:
            return None
        
        # Get the original rule
        original_rule = self.rules[rule_id]
        
        # Create a duplicate
        duplicate_rule = original_rule.duplicate()
        
        # Add the duplicate to the collection
        self.add_rule(duplicate_rule)
        
        return duplicate_rule.rule_id
    
    def get_rule_types(self) -> Set[str]:
        """Get the set of rule types present in the collection.
        
        Returns:
            set: Set of rule types.
        """
        return {rule.get_rule_type() for rule in self.rules.values()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection.
        
        Returns:
            dict: Dictionary with statistics.
        """
        # Count rules by type
        rule_counts = {}
        for rule in self.rules.values():
            rule_type = rule.get_rule_type()
            rule_counts[rule_type] = rule_counts.get(rule_type, 0) + 1
            
        # Count rules by usage
        never_used = 0
        used_once = 0
        used_multiple = 0
        
        for rule in self.rules.values():
            if rule.use_count == 0:
                never_used += 1
            elif rule.use_count == 1:
                used_once += 1
            else:
                used_multiple += 1
        
        # Get date range
        if self.rules:
            earliest_created = min(rule.created_date for rule in self.rules.values())
            latest_created = max(rule.created_date for rule in self.rules.values())
            
            # Get most recent usage
            used_rules = [rule for rule in self.rules.values() if rule.last_used]
            latest_used = max(rule.last_used for rule in used_rules) if used_rules else None
        else:
            earliest_created = None
            latest_created = None
            latest_used = None
        
        return {
            "total_rules": len(self.rules),
            "rule_counts_by_type": rule_counts,
            "usage_stats": {
                "never_used": never_used,
                "used_once": used_once,
                "used_multiple": used_multiple
            },
            "dates": {
                "created": self.created_date,
                "last_modified": self.last_modified_date,
                "earliest_rule": earliest_created,
                "latest_rule": latest_created,
                "latest_usage": latest_used
            }
        }
    
    def save_to_file(self, file_path: str) -> bool:
        """Save the collection to a JSON file.
        
        Args:
            file_path (str): Path to the file.
            
        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving collection: {str(e)}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['Collection']:
        """Load a collection from a JSON file.
        
        Args:
            file_path (str): Path to the file.
            
        Returns:
            Collection: The loaded collection, or None if loading failed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading collection: {str(e)}")
            return None
    
    def _rebuild_indices(self) -> None:
        """Rebuild all search indices."""
        # Currently a placeholder for future optimization
        # This method can be expanded to build more sophisticated indices
        pass
    
    def _update_index_for_rule(self, rule: Rule) -> None:
        """Update search indices for a single rule.
        
        Args:
            rule (Rule): The rule to index.
        """
        # Currently a placeholder for future optimization
        pass
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate all rules in the collection.
        
        Returns:
            dict: Dictionary with validation issues by rule ID.
        """
        validation_results = {}
        
        for rule_id, rule in self.rules.items():
            issues = rule.validate()
            
            # Only include rules with issues
            if any(issues.values()):
                validation_results[rule_id] = issues
        
        return validation_results
    
    def get_recently_used_rules(self, count: int = 10) -> List[Rule]:
        """Get the most recently used rules.
        
        Args:
            count (int, optional): Maximum number of rules to return. Defaults to 10.
            
        Returns:
            list: List of recently used Rule objects.
        """
        # Filter to rules that have been used
        used_rules = [rule for rule in self.rules.values() if rule.last_used]
        
        # Sort by last used date (most recent first)
        used_rules.sort(key=lambda r: r.last_used if r.last_used else "", reverse=True)
        
        # Return the top N
        return used_rules[:count]
    
    def get_frequently_used_rules(self, count: int = 10) -> List[Rule]:
        """Get the most frequently used rules.
        
        Args:
            count (int, optional): Maximum number of rules to return. Defaults to 10.
            
        Returns:
            list: List of frequently used Rule objects.
        """
        # Sort by use count (highest first)
        frequent_rules = sorted(
            self.rules.values(), 
            key=lambda r: r.use_count, 
            reverse=True
        )
        
        # Return the top N
        return frequent_rules[:count]