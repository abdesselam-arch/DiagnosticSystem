"""
Diagnostic Collection System - Diagnostic Node Model

This module defines the DiagnosticNode model class, which represents a single
node in a diagnostic pathway, such as a problem, check, condition, or action.
"""

import uuid
from typing import List, Dict, Any, Optional, Set


class DiagnosticNode:
    """Model representing a single node in a diagnostic pathway."""

    # Valid node types
    VALID_TYPES = {"problem", "check", "condition", "action"}

    # Default properties for each node type
    DEFAULT_PROPERTIES = {
        "problem": {},
        "check": {"check_type": "Visual Inspection"},
        "condition": {"severity": "Normal"},
        "action": {"impact": "Adjustment", "effectiveness": 3}
    }

    def __init__(self, node_type: str = "check", node_id: str = None):
        """Initialize a diagnostic node.
        
        Args:
            node_type (str, optional): Type of node (problem, check, condition, action).
                                      Defaults to "check".
            node_id (str, optional): Unique identifier for the node. Generated if not provided.
        """
        # Validate node type
        if node_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid node type: {node_type}. Must be one of {self.VALID_TYPES}")
            
        # Core properties
        self.node_id = node_id if node_id else str(uuid.uuid4())
        self.node_type = node_type
        self.content = ""
        self.connections = []  # List of connected node IDs
        
        # Type-specific properties with defaults
        self.properties = self.DEFAULT_PROPERTIES.get(node_type, {}).copy()
        
        # Position information (used for layout)
        self.position = {"x": 0, "y": 0}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiagnosticNode':
        """Create a DiagnosticNode instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing node data.
            
        Returns:
            DiagnosticNode: A new DiagnosticNode instance populated with the data.
        """
        node = cls(
            node_type=data.get('node_type', 'check'),
            node_id=data.get('node_id')
        )
        
        # Load core properties
        node.content = data.get('content', '')
        node.connections = data.get('connections', [])
        
        # Load position
        if 'position' in data:
            node.position = data.get('position')
        elif 'x' in data and 'y' in data:
            # Support for older format
            node.position = {
                'x': data.get('x', 0),
                'y': data.get('y', 0)
            }
            
        # Load type-specific properties
        if node.node_type == 'check' and 'check_type' in data:
            node.properties['check_type'] = data.get('check_type')
            
        elif node.node_type == 'condition' and 'severity' in data:
            node.properties['severity'] = data.get('severity')
            
        elif node.node_type == 'action':
            if 'impact' in data:
                node.properties['impact'] = data.get('impact')
            if 'effectiveness' in data:
                node.properties['effectiveness'] = data.get('effectiveness')
                
        # Also check for properties object
        if 'properties' in data and isinstance(data['properties'], dict):
            for key, value in data['properties'].items():
                node.properties[key] = value
                
        return node
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary.
        
        Returns:
            dict: Dictionary representation of the node.
        """
        data = {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'content': self.content,
            'connections': self.connections,
            'position': self.position,
            'properties': self.properties
        }
        
        # Also include individual properties for backwards compatibility
        if self.node_type == 'check' and 'check_type' in self.properties:
            data['check_type'] = self.properties['check_type']
            
        elif self.node_type == 'condition' and 'severity' in self.properties:
            data['severity'] = self.properties['severity']
            
        elif self.node_type == 'action':
            if 'impact' in self.properties:
                data['impact'] = self.properties['impact']
            if 'effectiveness' in self.properties:
                data['effectiveness'] = self.properties['effectiveness']
                
        return data
    
    def set_content(self, content: str) -> None:
        """Set the content text for this node.
        
        Args:
            content (str): Text content for the node.
        """
        self.content = content
    
    def get_content(self) -> str:
        """Get the content text for this node.
        
        Returns:
            str: The current content text.
        """
        return self.content
    
    def set_position(self, x: int, y: int) -> None:
        """Set the position of this node.
        
        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
        """
        self.position = {"x": x, "y": y}
    
    def get_position(self) -> Dict[str, int]:
        """Get the position of this node.
        
        Returns:
            dict: Dictionary with x and y coordinates.
        """
        return self.position
    
    def add_connection(self, target_node_id: str) -> bool:
        """Add a connection to another node.
        
        Args:
            target_node_id (str): ID of the target node.
            
        Returns:
            bool: True if the connection was added, False if it already exists.
        """
        if target_node_id not in self.connections:
            self.connections.append(target_node_id)
            return True
        return False
    
    def remove_connection(self, target_node_id: str) -> bool:
        """Remove a connection to another node.
        
        Args:
            target_node_id (str): ID of the target node.
            
        Returns:
            bool: True if the connection was removed, False if it didn't exist.
        """
        if target_node_id in self.connections:
            self.connections.remove(target_node_id)
            return True
        return False
    
    def has_connection(self, target_node_id: str) -> bool:
        """Check if this node has a connection to the specified target.
        
        Args:
            target_node_id (str): ID of the target node.
            
        Returns:
            bool: True if the connection exists, False otherwise.
        """
        return target_node_id in self.connections
    
    def clear_connections(self) -> None:
        """Clear all connections from this node."""
        self.connections = []
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a property for this node.
        
        Args:
            key (str): Property name.
            value: Property value.
        """
        self.properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value.
        
        Args:
            key (str): Property name.
            default: Default value if property doesn't exist.
            
        Returns:
            The property value, or the default if not found.
        """
        return self.properties.get(key, default)
    
    def set_check_type(self, check_type: str) -> None:
        """Set the check type for a check node.
        
        Args:
            check_type (str): The check type to set.
        """
        if self.node_type == "check":
            self.set_property("check_type", check_type)
    
    def get_check_type(self) -> Optional[str]:
        """Get the check type for a check node.
        
        Returns:
            str: The current check type, or None if not applicable.
        """
        if self.node_type == "check":
            return self.get_property("check_type")
        return None
    
    def set_condition_severity(self, severity: str) -> None:
        """Set the severity for a condition node.
        
        Args:
            severity (str): The severity level to set.
        """
        if self.node_type == "condition":
            self.set_property("severity", severity)
    
    def get_condition_severity(self) -> Optional[str]:
        """Get the severity for a condition node.
        
        Returns:
            str: The current severity level, or None if not applicable.
        """
        if self.node_type == "condition":
            return self.get_property("severity")
        return None
    
    def set_action_impact(self, impact: str) -> None:
        """Set the impact type for an action node.
        
        Args:
            impact (str): The impact type to set.
        """
        if self.node_type == "action":
            self.set_property("impact", impact)
    
    def get_action_impact(self) -> Optional[str]:
        """Get the impact type for an action node.
        
        Returns:
            str: The current impact type, or None if not applicable.
        """
        if self.node_type == "action":
            return self.get_property("impact")
        return None
    
    def set_effectiveness(self, value: int) -> None:
        """Set the effectiveness value for an action node.
        
        Args:
            value (int): The effectiveness value (1-5).
        """
        if self.node_type == "action":
            self.set_property("effectiveness", value)
    
    def get_effectiveness(self) -> Optional[int]:
        """Get the effectiveness value for an action node.
        
        Returns:
            int: The current effectiveness value, or None if not applicable.
        """
        if self.node_type == "action":
            return self.get_property("effectiveness")
        return None
    
    def change_type(self, new_type: str) -> bool:
        """Change the type of this node.
        
        Args:
            new_type (str): The new node type.
            
        Returns:
            bool: True if the type was changed, False if the new type is invalid.
        """
        if new_type not in self.VALID_TYPES:
            return False
            
        self.node_type = new_type
        
        # Initialize properties for the new type
        self.properties = self.DEFAULT_PROPERTIES.get(new_type, {}).copy()
        
        return True
    
    def validate(self) -> List[str]:
        """Validate this node for completeness and correctness.
        
        Returns:
            list: List of validation issues.
        """
        issues = []
        
        # Check for basic requirements
        if not self.node_id:
            issues.append("Node ID is missing")
            
        if not self.content:
            issues.append("Node content is empty")
            
        # Validate type-specific properties
        if self.node_type == "check":
            if not self.get_check_type():
                issues.append("Check type is not specified")
                
        elif self.node_type == "condition":
            if not self.get_condition_severity():
                issues.append("Condition severity is not specified")
                
        elif self.node_type == "action":
            if not self.get_action_impact():
                issues.append("Action impact is not specified")
                
        return issues
    
    def duplicate(self) -> 'DiagnosticNode':
        """Create a duplicate of this node with a new ID.
        
        Returns:
            DiagnosticNode: A new DiagnosticNode instance with the same data but a new ID.
        """
        node_dict = self.to_dict()
        # Generate a new ID
        node_dict['node_id'] = str(uuid.uuid4())
        # Clear connections as they will not apply to the duplicate
        node_dict['connections'] = []
        
        return DiagnosticNode.from_dict(node_dict)
    
    def __str__(self) -> str:
        """Get a string representation of this node.
        
        Returns:
            str: String representation.
        """
        return f"{self.node_type.capitalize()} ({self.node_id[:8]}): {self.content[:30]}..."