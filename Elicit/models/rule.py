"""
Diagnostic Collection System - Rule Model

This module defines the Rule model class, which represents a diagnostic rule 
in the system with its associated conditions, actions, and metadata.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class Rule:
    """Model representing a diagnostic rule with conditions and actions."""
    
    def __init__(self, rule_id: str = None, text: str = None):
        """Initialize a rule with optional ID and text.
        
        Args:
            rule_id (str, optional): Unique identifier for the rule. Generated if not provided.
            text (str, optional): The rule text in IF-THEN format.
        """
        # Core rule properties
        self.rule_id = rule_id if rule_id else str(uuid.uuid4())
        self.text = text or ""
        self.name = ""
        self.description = ""
        self.is_complex = True
        
        # Structured rule components
        self.conditions = []
        self.actions = []
        
        # Metadata
        self.created_date = datetime.now().isoformat()
        self.last_modified_date = self.created_date
        self.last_used = None
        self.use_count = 0
        
        # Additional data
        self.metadata = {}
        self.pathway_data = None
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create a Rule instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing rule data.
            
        Returns:
            Rule: A new Rule instance populated with the data.
        """
        rule = cls(rule_id=data.get('rule_id'))
        
        # Load core properties
        rule.text = data.get('text', '')
        rule.name = data.get('name', '')
        rule.description = data.get('description', '')
        rule.is_complex = data.get('is_complex', True)
        
        # Load structured components
        rule.conditions = data.get('conditions', [])
        rule.actions = data.get('actions', [])
        
        # Load metadata
        rule.created_date = data.get('created_date', rule.created_date)
        rule.last_modified_date = data.get('last_modified_date', rule.last_modified_date)
        rule.last_used = data.get('last_used')
        rule.use_count = data.get('use_count', 0)
        
        # Load additional data
        rule.metadata = data.get('metadata', {})
        rule.pathway_data = data.get('pathway_data')
        
        return rule
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the rule to a dictionary.
        
        Returns:
            dict: Dictionary representation of the rule.
        """
        return {
            'rule_id': self.rule_id,
            'text': self.text,
            'name': self.name,
            'description': self.description,
            'is_complex': self.is_complex,
            'conditions': self.conditions,
            'actions': self.actions,
            'created_date': self.created_date,
            'last_modified_date': self.last_modified_date,
            'last_used': self.last_used,
            'use_count': self.use_count,
            'metadata': self.metadata,
            'pathway_data': self.pathway_data
        }
    
    def to_json(self) -> str:
        """Convert the rule to a JSON string.
        
        Returns:
            str: JSON representation of the rule.
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Rule':
        """Create a Rule instance from a JSON string.
        
        Args:
            json_str (str): JSON string containing rule data.
            
        Returns:
            Rule: A new Rule instance populated with the data.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_rule_type(self) -> str:
        """Get the type of rule based on its properties.
        
        Returns:
            str: The rule type ('Pathway', 'Capture', or 'Rule').
        """
        if self.pathway_data:
            return "Pathway"
        elif self.metadata.get('problem_type'):
            return "Capture"
        else:
            return "Rule"
    
    def get_description(self, max_length: int = 80) -> str:
        """Get a concise description of the rule.
        
        Args:
            max_length (int, optional): Maximum length of the description. Defaults to 80.
            
        Returns:
            str: A concise description of the rule.
        """
        # Use name or description if available
        if self.name:
            return self._truncate(self.name, max_length)
        
        if self.description:
            return self._truncate(self.description, max_length)
            
        # For visual pathways, try to extract a problem statement
        if self.pathway_data:
            nodes = self.pathway_data.get('nodes', {})
            for node_id, node in nodes.items():
                if node.get('node_type') == 'problem' and node.get('content'):
                    return self._truncate(node.get('content'), max_length)
        
        # For quick captures, use the problem type and description
        if self.metadata.get('problem_type') and self.metadata.get('problem_type') != "Select type...":
            # Try to extract the problem part
            if "problem is '" in self.text:
                try:
                    problem_part = self.text.split("problem is '")[1].split("'")[0]
                    return self._truncate(problem_part, max_length)
                except IndexError:
                    pass
                    
        # Default to the rule text
        # If it's a complex rule with IF-THEN structure, extract the IF part
        if "IF " in self.text and ", THEN" in self.text:
            if_part = self.text.split(", THEN")[0].replace("IF ", "")
            return self._truncate(if_part, max_length)
        
        # Fallback to truncated rule text
        return self._truncate(self.text, max_length)
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to a maximum length, adding ellipsis if necessary.
        
        Args:
            text (str): The text to truncate.
            max_length (int): Maximum length of the result.
            
        Returns:
            str: Truncated text.
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def get_formatted_last_used(self) -> str:
        """Get a formatted representation of the last used date.
        
        Returns:
            str: Formatted last used date or 'Never' if not used.
        """
        if not self.last_used:
            return "Never"
            
        try:
            date_obj = datetime.fromisoformat(self.last_used)
            return date_obj.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return "Unknown"
    
    def record_usage(self) -> None:
        """Record that the rule has been used."""
        self.use_count += 1
        self.last_used = datetime.now().isoformat()
    
    def set_conditions(self, conditions: List[Dict[str, Any]]) -> None:
        """Set the conditions for this rule.
        
        Args:
            conditions (list): List of condition dictionaries.
        """
        self.conditions = conditions
        self.last_modified_date = datetime.now().isoformat()
        self._update_rule_text()
    
    def set_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Set the actions for this rule.
        
        Args:
            actions (list): List of action dictionaries.
        """
        self.actions = actions
        self.last_modified_date = datetime.now().isoformat()
        self._update_rule_text()
    
    def add_condition(self, param: str, operator: str = "=", value: str = "true", connector: str = "AND") -> None:
        """Add a condition to the rule.
        
        Args:
            param (str): Parameter or observation.
            operator (str, optional): Comparison operator. Defaults to "=".
            value (str, optional): Value to compare against. Defaults to "true".
            connector (str, optional): Logical connector (AND/OR). Defaults to "AND".
        """
        condition = {
            "param": param,
            "operator": operator,
            "value": value,
            "connector": connector
        }
        
        self.conditions.append(condition)
        
        # Update the last condition's connector to empty
        if len(self.conditions) > 1:
            self.conditions[-2]["connector"] = connector
        self.conditions[-1]["connector"] = ""
        
        self.last_modified_date = datetime.now().isoformat()
        self._update_rule_text()
    
    def add_action(self, target: str, action_type: str = "Apply", value: str = "", sequence: int = None) -> None:
        """Add an action to the rule.
        
        Args:
            target (str): The target of the action.
            action_type (str, optional): Type of action. Defaults to "Apply".
            value (str, optional): Value for the action. Defaults to "".
            sequence (int, optional): Sequence number. If None, will be assigned automatically.
        """
        # Determine sequence number if not provided
        if sequence is None:
            if self.actions:
                # Use next sequence number after the highest existing one
                sequence = max(action.get("sequence", 0) for action in self.actions) + 1
            else:
                sequence = 1
        
        action = {
            "type": action_type,
            "target": target,
            "value": value,
            "sequence": sequence
        }
        
        self.actions.append(action)
        self.last_modified_date = datetime.now().isoformat()
        self._update_rule_text()
    
    def _update_rule_text(self) -> None:
        """Update the rule text based on conditions and actions."""
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
        self.text = f"{if_part},\n{then_part}"
    
    def parse_rule_text(self) -> bool:
        """Parse rule text to extract conditions and actions.
        
        Returns:
            bool: True if parsing was successful, False otherwise.
        """
        rule_text = self.text.strip()
        
        if not rule_text:
            return False
        
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
            
            # Update the rule with parsed data
            self.conditions = conditions
            self.actions = actions
            self.last_modified_date = datetime.now().isoformat()
            return True
            
        return False
    
    def _parse_condition(self, text: str) -> Optional[Dict[str, str]]:
        """Parse a condition string into a structured format.
        
        Args:
            text (str): The condition text to parse.
            
        Returns:
            dict: Parsed condition dictionary, or None if parsing failed.
        """
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
    
    def _parse_action(self, text: str, sequence: int = 1) -> Optional[Dict[str, Any]]:
        """Parse an action string into a structured format.
        
        Args:
            text (str): The action text to parse.
            sequence (int, optional): The sequence number. Defaults to 1.
            
        Returns:
            dict: Parsed action dictionary, or None if parsing failed.
        """
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
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate the rule for completeness and correctness.
        
        Returns:
            dict: Dictionary with validation issues by category.
        """
        issues = {
            "conditions": [],
            "actions": [],
            "general": []
        }
        
        # Check for basic requirements
        if not self.rule_id:
            issues["general"].append("Rule ID is missing")
        
        if not self.text:
            issues["general"].append("Rule text is empty")
        
        # Validate conditions
        if not self.conditions:
            issues["conditions"].append("No conditions defined")
        else:
            for i, condition in enumerate(self.conditions):
                if not condition.get("param"):
                    issues["conditions"].append(f"Condition {i+1} is missing a parameter")
                
                # Validate connector (last condition should not have a connector)
                if i == len(self.conditions) - 1 and condition.get("connector"):
                    issues["conditions"].append("Last condition should not have a connector")
        
        # Validate actions
        if not self.actions:
            issues["actions"].append("No actions defined")
        else:
            for i, action in enumerate(self.actions):
                if not action.get("target"):
                    issues["actions"].append(f"Action {i+1} is missing a target")
                
                # Check for duplicate sequence numbers
                seq = action.get("sequence", i+1)
                if any(a.get("sequence") == seq for a in self.actions if a != action):
                    issues["actions"].append(f"Duplicate sequence number {seq}")
        
        return issues
    
    def duplicate(self) -> 'Rule':
        """Create a duplicate of this rule with a new ID.
        
        Returns:
            Rule: A new Rule instance with the same data but a new ID.
        """
        rule_dict = self.to_dict()
        # Generate a new ID and update creation/modification dates
        rule_dict['rule_id'] = str(uuid.uuid4())
        rule_dict['created_date'] = datetime.now().isoformat()
        rule_dict['last_modified_date'] = rule_dict['created_date']
        rule_dict['last_used'] = None
        rule_dict['use_count'] = 0
        
        # Update name to indicate it's a copy
        if self.name:
            rule_dict['name'] = f"Copy of {self.name}"
        
        return Rule.from_dict(rule_dict)