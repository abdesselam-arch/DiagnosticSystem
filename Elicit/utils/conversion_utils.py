"""
Diagnostic Collection System - Conversion Utilities

This module provides utility functions for data conversion and transformation
operations commonly needed throughout the diagnostic collection system.
"""

import json
import csv
import re
import io
import yaml
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Set


def dict_to_json(data: Dict[str, Any], indent: int = 2) -> str:
    """Convert a dictionary to a JSON string.
    
    Args:
        data (dict): Dictionary to convert.
        indent (int, optional): Indentation level. Defaults to 2.
        
    Returns:
        str: JSON string representation.
    """
    return json.dumps(data, indent=indent)


def json_to_dict(json_str: str) -> Dict[str, Any]:
    """Convert a JSON string to a dictionary.
    
    Args:
        json_str (str): JSON string to convert.
        
    Returns:
        dict: Dictionary representation.
        
    Raises:
        json.JSONDecodeError: If the JSON is invalid.
    """
    return json.loads(json_str)


def dict_to_csv(data: List[Dict[str, Any]], field_names: List[str] = None) -> str:
    """Convert a list of dictionaries to a CSV string.
    
    Args:
        data (list): List of dictionaries to convert.
        field_names (list, optional): List of field names to include. 
                                    Defaults to None (use all fields from first dict).
        
    Returns:
        str: CSV string representation.
    """
    if not data:
        return ""
    
    # Determine field names if not provided
    if field_names is None:
        field_names = list(data[0].keys())
    
    # Write CSV to string buffer
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=field_names, extrasaction='ignore')
    writer.writeheader()
    
    for row in data:
        # Clean row data for CSV compatibility
        clean_row = {}
        for key, value in row.items():
            if key in field_names:
                if isinstance(value, (dict, list)):
                    clean_row[key] = json.dumps(value)
                else:
                    clean_row[key] = value
        writer.writerow(clean_row)
    
    return output.getvalue()


def csv_to_dict(csv_str: str) -> List[Dict[str, str]]:
    """Convert a CSV string to a list of dictionaries.
    
    Args:
        csv_str (str): CSV string to convert.
        
    Returns:
        list: List of dictionaries.
    """
    if not csv_str.strip():
        return []
    
    # Read CSV from string buffer
    input_buffer = io.StringIO(csv_str)
    reader = csv.DictReader(input_buffer)
    
    return list(reader)


def dict_to_yaml(data: Dict[str, Any]) -> str:
    """Convert a dictionary to a YAML string.
    
    Args:
        data (dict): Dictionary to convert.
        
    Returns:
        str: YAML string representation.
    """
    return yaml.dump(data, sort_keys=False, default_flow_style=False)


def yaml_to_dict(yaml_str: str) -> Dict[str, Any]:
    """Convert a YAML string to a dictionary.
    
    Args:
        yaml_str (str): YAML string to convert.
        
    Returns:
        dict: Dictionary representation.
    """
    return yaml.safe_load(yaml_str)


def dict_to_xml(data: Dict[str, Any], root_name: str = "root") -> str:
    """Convert a dictionary to an XML string.
    
    Args:
        data (dict): Dictionary to convert.
        root_name (str, optional): Name of the root element. Defaults to "root".
        
    Returns:
        str: XML string representation.
    """
    def _dict_to_xml_element(data, parent):
        """Recursively convert dictionary to XML elements."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith('@'):
                    # Handle attributes
                    parent.set(key[1:], str(value))
                elif key == '#text':
                    # Handle text content
                    parent.text = str(value)
                else:
                    # Create subelement
                    child = ET.SubElement(parent, key)
                    _dict_to_xml_element(value, child)
        elif isinstance(data, list):
            for item in data:
                # Create "item" subelement for each list item
                child = ET.SubElement(parent, "item")
                _dict_to_xml_element(item, child)
        else:
            # Set element text
            parent.text = str(data)
    
    # Create root element
    root = ET.Element(root_name)
    _dict_to_xml_element(data, root)
    
    # Convert to string with pretty formatting
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")


def xml_to_dict(xml_str: str) -> Dict[str, Any]:
    """Convert an XML string to a dictionary.
    
    Args:
        xml_str (str): XML string to convert.
        
    Returns:
        dict: Dictionary representation.
    """
    def _element_to_dict(element):
        """Recursively convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        for key, value in element.attrib.items():
            result[f"@{key}"] = value
        
        # Add children
        for child in element:
            child_dict = _element_to_dict(child)
            child_tag = child.tag
            
            if child_tag in result:
                # If the key already exists, convert to list if needed
                if not isinstance(result[child_tag], list):
                    result[child_tag] = [result[child_tag]]
                result[child_tag].append(child_dict)
            else:
                result[child_tag] = child_dict
        
        # Add text content if no children
        if not result and element.text and element.text.strip():
            return element.text.strip()
        
        # Add text content as special key if has children
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()
            
        return result
    
    # Parse XML
    root = ET.fromstring(xml_str)
    
    # Convert to dict
    return {root.tag: _element_to_dict(root)}


def flatten_dict(data: Dict[str, Any], separator: str = '.', 
                parent_key: str = '') -> Dict[str, Any]:
    """Flatten a nested dictionary.
    
    Args:
        data (dict): Dictionary to flatten.
        separator (str, optional): Key separator. Defaults to '.'.
        parent_key (str, optional): Parent key prefix. Defaults to ''.
        
    Returns:
        dict: Flattened dictionary.
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, separator, new_key).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, separator, f"{new_key}{separator}{i}").items())
                else:
                    items.append((f"{new_key}{separator}{i}", item))
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """Unflatten a dictionary with nested keys.
    
    Args:
        data (dict): Flattened dictionary to unflatten.
        separator (str, optional): Key separator. Defaults to '.'.
        
    Returns:
        dict: Nested dictionary.
    """
    result = {}
    
    for key, value in data.items():
        parts = key.split(separator)
        current = result
        
        # Navigate to the right level
        for part in parts[:-1]:
            # Create dict if key doesn't exist
            if part not in current:
                current[part] = {}
            # Move to next level
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
    
    return result


def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format a datetime object to string.
    
    Args:
        dt (datetime): Datetime object to format.
        format_str (str, optional): Format string. Defaults to '%Y-%m-%d %H:%M:%S'.
        
    Returns:
        str: Formatted datetime string.
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """Parse a datetime string to datetime object.
    
    Args:
        dt_str (str): Datetime string to parse.
        format_str (str, optional): Format string. Defaults to '%Y-%m-%d %H:%M:%S'.
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails.
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None


def iso_to_datetime(iso_str: str) -> Optional[datetime]:
    """Convert ISO format datetime string to datetime object.
    
    Args:
        iso_str (str): ISO format datetime string.
        
    Returns:
        datetime: Datetime object, or None if parsing fails.
    """
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        return None


def datetime_to_iso(dt: datetime) -> str:
    """Convert datetime object to ISO format string.
    
    Args:
        dt (datetime): Datetime object.
        
    Returns:
        str: ISO format datetime string.
    """
    return dt.isoformat()


def friendly_datetime(dt: Union[datetime, str]) -> str:
    """Convert datetime to a human-friendly string.
    
    Args:
        dt (datetime or str): Datetime object or ISO format string.
        
    Returns:
        str: Human-friendly datetime string.
    """
    # Convert string to datetime if needed
    if isinstance(dt, str):
        dt = iso_to_datetime(dt)
        if dt is None:
            return "Invalid date"
    
    now = datetime.now()
    delta = now - dt
    
    # Today
    if dt.date() == now.date():
        return f"Today at {dt.strftime('%H:%M')}"
    
    # Yesterday
    if dt.date() == (now - timedelta(days=1)).date():
        return f"Yesterday at {dt.strftime('%H:%M')}"
    
    # This week
    if delta.days < 7:
        return f"{dt.strftime('%A')} at {dt.strftime('%H:%M')}"
    
    # This year
    if dt.year == now.year:
        return dt.strftime("%b %d at %H:%M")
    
    # Older
    return dt.strftime("%b %d, %Y at %H:%M")


def dict_subset(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Extract a subset of a dictionary with specified keys.
    
    Args:
        data (dict): Original dictionary.
        keys (list): List of keys to include.
        
    Returns:
        dict: Dictionary with only the specified keys.
    """
    return {k: v for k, v in data.items() if k in keys}


def dict_diff(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Find differences between two dictionaries.
    
    Args:
        dict1 (dict): First dictionary.
        dict2 (dict): Second dictionary.
        
    Returns:
        dict: Dictionary of differences {key: (value1, value2)}.
    """
    diff = {}
    
    # Find keys in both dictionaries with different values
    common_keys = set(dict1.keys()) & set(dict2.keys())
    for key in common_keys:
        if dict1[key] != dict2[key]:
            diff[key] = (dict1[key], dict2[key])
    
    # Add keys only in dict1
    for key in set(dict1.keys()) - set(dict2.keys()):
        diff[key] = (dict1[key], None)
    
    # Add keys only in dict2
    for key in set(dict2.keys()) - set(dict1.keys()):
        diff[key] = (None, dict2[key])
    
    return diff


def camel_to_snake(text: str) -> str:
    """Convert CamelCase to snake_case.
    
    Args:
        text (str): CamelCase text.
        
    Returns:
        str: snake_case text.
    """
    # Add underscore before uppercase letters and convert to lowercase
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
    return result


def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """Convert snake_case to camelCase.
    
    Args:
        text (str): snake_case text.
        capitalize_first (bool, optional): Whether to capitalize the first letter. 
                                         Defaults to False.
        
    Returns:
        str: camelCase text.
    """
    # Split by underscore and capitalize each part except the first
    parts = text.split('_')
    result = parts[0] + ''.join(part.title() for part in parts[1:])
    
    # Capitalize first letter if requested (resulting in PascalCase)
    if capitalize_first:
        result = result[0].upper() + result[1:]
    
    return result


def dict_keys_to_camel(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
    """Convert dictionary keys from snake_case to camelCase.
    
    Args:
        data (dict): Dictionary with snake_case keys.
        recursive (bool, optional): Whether to process nested dictionaries. Defaults to True.
        
    Returns:
        dict: Dictionary with camelCase keys.
    """
    result = {}
    
    for key, value in data.items():
        # Convert key to camelCase
        camel_key = snake_to_camel(key)
        
        # Process value if recursive
        if recursive and isinstance(value, dict):
            result[camel_key] = dict_keys_to_camel(value)
        elif recursive and isinstance(value, list):
            result[camel_key] = [
                dict_keys_to_camel(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[camel_key] = value
    
    return result


def dict_keys_to_snake(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
    """Convert dictionary keys from camelCase to snake_case.
    
    Args:
        data (dict): Dictionary with camelCase keys.
        recursive (bool, optional): Whether to process nested dictionaries. Defaults to True.
        
    Returns:
        dict: Dictionary with snake_case keys.
    """
    result = {}
    
    for key, value in data.items():
        # Convert key to snake_case
        snake_key = camel_to_snake(key)
        
        # Process value if recursive
        if recursive and isinstance(value, dict):
            result[snake_key] = dict_keys_to_snake(value)
        elif recursive and isinstance(value, list):
            result[snake_key] = [
                dict_keys_to_snake(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[snake_key] = value
    
    return result


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text.
    
    Args:
        text (str): Text with HTML tags.
        
    Returns:
        str: Text without HTML tags.
    """
    # Remove HTML tags using regex
    return re.sub(r'<[^>]+>', '', text)


def text_to_bool(text: str) -> bool:
    """Convert text to boolean value.
    
    Args:
        text (str): Text to convert.
        
    Returns:
        bool: Boolean value.
    """
    if not text:
        return False
        
    text = text.lower().strip()
    return text in ('true', 'yes', 'y', '1', 'on', 't')


def clean_rule_text(rule_text: str) -> str:
    """Clean rule text for better formatting.
    
    Args:
        rule_text (str): Rule text to clean.
        
    Returns:
        str: Cleaned rule text.
    """
    # Fix spacing and standardize IF-THEN format
    rule_text = rule_text.strip()
    
    # Standardize IF-THEN format
    if "IF " in rule_text and " THEN" in rule_text:
        # Split into IF and THEN parts
        if_part, then_part = rule_text.split(" THEN", 1)
        
        # Clean IF part
        if_part = if_part.replace("IF ", "IF ")
        
        # Standardize connectors
        if_part = re.sub(r'\s+AND\s+', " AND ", if_part)
        if_part = re.sub(r'\s+OR\s+', " OR ", if_part)
        
        # Clean THEN part
        then_part = then_part.strip()
        if then_part.startswith(","):
            then_part = then_part[1:].strip()
        
        # Format the rule
        rule_text = f"IF {if_part.strip()},\nTHEN{then_part}"
        
        # Format action steps
        lines = rule_text.split("\n")
        for i in range(1, len(lines)):
            # Check if line is an action step with a number
            if re.match(r'\s*\d+\.\s+', lines[i]):
                continue
            # Check if line starts with a space, otherwise indent it
            if not lines[i].startswith("  ") and not lines[i].startswith("\t"):
                lines[i] = f"  {lines[i]}"
        
        rule_text = "\n".join(lines)
    
    return rule_text


def parse_rule_text(rule_text: str) -> Dict[str, Any]:
    """Parse rule text into structured components.
    
    Args:
        rule_text (str): Rule text to parse.
        
    Returns:
        dict: Structured rule components.
    """
    rule_data = {
        "text": rule_text,
        "conditions": [],
        "actions": []
    }
    
    # Check if text has IF-THEN structure
    if "IF " in rule_text and ", THEN" in rule_text:
        # Split into conditions and actions
        if_part = rule_text.split(", THEN")[0].replace("IF ", "")
        then_part = rule_text.split(", THEN")[1].strip()
        
        # Parse conditions
        if " AND " in if_part:
            condition_parts = if_part.split(" AND ")
            for i, part in enumerate(condition_parts):
                condition = {
                    "param": part.strip(),
                    "operator": "=",
                    "value": "true",
                    "connector": "AND" if i < len(condition_parts) - 1 else ""
                }
                
                # Try to extract operator and value
                for op in ["=", ">", "<", ">=", "<=", "!=", "contains"]:
                    if f" {op} " in part:
                        param, value = part.split(f" {op} ", 1)
                        condition["param"] = param.strip()
                        condition["operator"] = op
                        condition["value"] = value.strip()
                        break
                
                rule_data["conditions"].append(condition)
        else:
            # Single condition
            condition = {
                "param": if_part.strip(),
                "operator": "=",
                "value": "true",
                "connector": ""
            }
            
            # Try to extract operator and value
            for op in ["=", ">", "<", ">=", "<=", "!=", "contains"]:
                if f" {op} " in if_part:
                    param, value = if_part.split(f" {op} ", 1)
                    condition["param"] = param.strip()
                    condition["operator"] = op
                    condition["value"] = value.strip()
                    break
            
            rule_data["conditions"].append(condition)
        
        # Parse actions
        action_lines = then_part.split("\n")
        for i, line in enumerate(action_lines):
            line = line.strip()
            if line:
                # Extract sequence if present
                seq = i + 1
                action_text = line
                if line[0].isdigit() and ". " in line:
                    seq_end = line.find(". ")
                    try:
                        seq = int(line[:seq_end])
                        action_text = line[seq_end+2:]
                    except ValueError:
                        pass
                
                # Create action structure
                action = {
                    "type": "Apply",
                    "target": action_text,
                    "value": "",
                    "sequence": seq
                }
                
                # Try to extract type and target
                if ": " in action_text:
                    parts = action_text.split(": ", 1)
                    action["type"] = parts[0]
                    action["target"] = parts[1]
                
                rule_data["actions"].append(action)
    
    return rule_data


def generate_rule_text(conditions: List[Dict[str, Any]], actions: List[Dict[str, Any]]) -> str:
    """Generate rule text from structured components.
    
    Args:
        conditions (list): List of condition dictionaries.
        actions (list): List of action dictionaries.
        
    Returns:
        str: Formatted rule text.
    """
    # Build the IF part with conditions
    if_conditions = []
    for condition in conditions:
        param = condition.get("param", "")
        operator = condition.get("operator", "=")
        value = condition.get("value", "")
        
        if operator == "=" and value == "true":
            # Simplified representation for boolean conditions
            if_conditions.append(param)
        else:
            if_conditions.append(f"{param} {operator} {value}")
        
        # Add connector if not the last condition
        if condition != conditions[-1] and condition.get("connector"):
            if_conditions.append(condition.get("connector"))
    
    if_part = "IF " + " ".join(if_conditions)
    
    # Build the THEN part with actions
    then_part = "THEN"
    # Sort actions by sequence
    sorted_actions = sorted(actions, key=lambda x: x.get("sequence", 1))
    
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


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any], 
               overwrite: bool = True) -> Dict[str, Any]:
    """Merge two dictionaries recursively.
    
    Args:
        dict1 (dict): First dictionary.
        dict2 (dict): Second dictionary.
        overwrite (bool, optional): Whether to overwrite values in dict1. Defaults to True.
        
    Returns:
        dict: Merged dictionary.
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_dicts(result[key], value, overwrite)
        elif key not in result or overwrite:
            # Add or overwrite value
            result[key] = value
    
    return result


def sanitize_dict(data: Dict[str, Any], allowed_keys: Set[str] = None,
                 recursive: bool = True) -> Dict[str, Any]:
    """Sanitize a dictionary by removing unwanted keys.
    
    Args:
        data (dict): Dictionary to sanitize.
        allowed_keys (set, optional): Set of allowed keys. Defaults to None (all keys).
        recursive (bool, optional): Whether to process nested dictionaries. Defaults to True.
        
    Returns:
        dict: Sanitized dictionary.
    """
    if allowed_keys is None:
        # If no allowed keys specified, return a copy of the original
        return data.copy()
    
    result = {}
    
    for key, value in data.items():
        if key in allowed_keys:
            if recursive and isinstance(value, dict):
                result[key] = sanitize_dict(value, allowed_keys, recursive)
            elif recursive and isinstance(value, list):
                result[key] = [
                    sanitize_dict(item, allowed_keys, recursive) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
    
    return result