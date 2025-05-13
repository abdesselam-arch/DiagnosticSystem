"""
Diagnostic Collection System - Diagnostic Pathway Model

This module defines the DiagnosticPathway model class, which represents a complete
diagnostic pathway with a collection of nodes and their connections.
"""

import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime

from models.diagnostic_node import DiagnosticNode


class DiagnosticPathway:
    """Model representing a complete diagnostic pathway with nodes and connections."""
    
    def __init__(self, pathway_id: str = None, name: str = ""):
        """Initialize a diagnostic pathway.
        
        Args:
            pathway_id (str, optional): Unique identifier for the pathway. Generated if not provided.
            name (str, optional): Name of the pathway. Defaults to "".
        """
        # Core properties
        self.pathway_id = pathway_id if pathway_id else str(uuid.uuid4())
        self.name = name
        self.description = ""
        
        # Nodes and connections
        self.nodes = {}  # Dict of node_id -> DiagnosticNode
        self.connections = []  # List of (source_id, target_id) tuples
        
        # Metadata
        self.created_date = datetime.now().isoformat()
        self.last_modified_date = self.created_date
        
        # Layout settings
        self.layout_settings = {
            "column_width": 250,
            "node_margin": 20,
            "column_margin": 50,
            "initial_x": 50,
            "initial_y": 50
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiagnosticPathway':
        """Create a DiagnosticPathway instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing pathway data.
            
        Returns:
            DiagnosticPathway: A new DiagnosticPathway instance populated with the data.
        """
        pathway = cls(
            pathway_id=data.get('pathway_id'),
            name=data.get('name', '')
        )
        
        # Load core properties
        pathway.description = data.get('description', '')
        
        # Load metadata
        pathway.created_date = data.get('created_date', pathway.created_date)
        pathway.last_modified_date = data.get('last_modified_date', pathway.last_modified_date)
        
        # Load layout settings
        if 'layout_settings' in data:
            pathway.layout_settings.update(data['layout_settings'])
        
        # Load nodes
        if 'nodes' in data:
            for node_id, node_data in data['nodes'].items():
                # Ensure node_id is in the data
                if isinstance(node_data, dict):
                    node_data['node_id'] = node_id
                    pathway.nodes[node_id] = DiagnosticNode.from_dict(node_data)
        
        # Load connections
        if 'connections' in data:
            pathway.connections = data['connections']
            
            # Update node connections for backwards compatibility
            for source_id, target_id in pathway.connections:
                if source_id in pathway.nodes:
                    source_node = pathway.nodes[source_id]
                    if target_id not in source_node.connections:
                        source_node.add_connection(target_id)
                
        return pathway
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the pathway to a dictionary.
        
        Returns:
            dict: Dictionary representation of the pathway.
        """
        return {
            'pathway_id': self.pathway_id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date,
            'last_modified_date': self.last_modified_date,
            'layout_settings': self.layout_settings,
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'connections': self.connections
        }
    
    def add_node(self, node_type: str, position: Dict[str, int] = None) -> DiagnosticNode:
        """Add a new node to the pathway.
        
        Args:
            node_type (str): Type of node to add.
            position (dict, optional): Position of the node as {x, y}.
                                      If None, position will be calculated automatically.
        
        Returns:
            DiagnosticNode: The newly created node.
        """
        # Create a new node
        node = DiagnosticNode(node_type=node_type)
        
        # Set position if provided
        if position:
            node.set_position(position['x'], position['y'])
        else:
            # Calculate position based on node type and layout
            calculated_position = self.calculate_node_position(node_type)
            node.set_position(calculated_position['x'], calculated_position['y'])
        
        # Add to nodes dictionary
        self.nodes[node.node_id] = node
        
        # Update modification date
        self.last_modified_date = datetime.now().isoformat()
        
        return node
    
    def calculate_node_position(self, node_type: str) -> Dict[str, int]:
        """Calculate the position for a new node based on its type and layout.
        
        Args:
            node_type (str): The type of node.
            
        Returns:
            dict: The calculated position as {x, y}.
        """
        # Node type to column mapping
        column_map = {
            "problem": 0,
            "check": 1,
            "condition": 2,
            "action": 3
        }
        
        column = column_map.get(node_type, 0)
        x_position = self.layout_settings['initial_x'] + column * (
            self.layout_settings['column_width'] + self.layout_settings['column_margin']
        )
        
        # Find the lowest y-position of existing nodes in this column
        max_y = self.layout_settings['initial_y']
        for node in self.nodes.values():
            if node.node_type == node_type:
                node_pos = node.get_position()
                node_bottom = node_pos['y'] + 120  # Approximate node height
                max_y = max(max_y, node_bottom + self.layout_settings['node_margin'])
        
        return {'x': x_position, 'y': max_y}
    
    def get_node(self, node_id: str) -> Optional[DiagnosticNode]:
        """Get a node by ID.
        
        Args:
            node_id (str): ID of the node to get.
            
        Returns:
            DiagnosticNode: The node, or None if not found.
        """
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node and its connections.
        
        Args:
            node_id (str): ID of the node to remove.
            
        Returns:
            bool: True if the node was removed, False if it wasn't found.
        """
        if node_id not in self.nodes:
            return False
        
        # Remove the node
        del self.nodes[node_id]
        
        # Remove connections involving this node
        self.connections = [
            (source, target) for source, target in self.connections
            if source != node_id and target != node_id
        ]
        
        # Update connection lists in other nodes
        for node in self.nodes.values():
            if node_id in node.connections:
                node.remove_connection(node_id)
        
        # Update modification date
        self.last_modified_date = datetime.now().isoformat()
        
        return True
    
    def connect_nodes(self, source_id: str, target_id: str) -> bool:
        """Create a connection between nodes.
        
        Args:
            source_id (str): ID of the source node.
            target_id (str): ID of the target node.
            
        Returns:
            bool: True if the connection was created, False if it already exists or nodes don't exist.
        """
        # Check if nodes exist
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        # Check if connection already exists
        if (source_id, target_id) in self.connections:
            return False
        
        # Add connection
        self.connections.append((source_id, target_id))
        
        # Update source node's connections
        source_node = self.nodes[source_id]
        source_node.add_connection(target_id)
        
        # Update modification date
        self.last_modified_date = datetime.now().isoformat()
        
        return True
    
    def disconnect_nodes(self, source_id: str, target_id: str) -> bool:
        """Remove a connection between nodes.
        
        Args:
            source_id (str): ID of the source node.
            target_id (str): ID of the target node.
            
        Returns:
            bool: True if the connection was removed, False if it didn't exist.
        """
        # Check if connection exists
        if (source_id, target_id) not in self.connections:
            return False
        
        # Remove connection
        self.connections.remove((source_id, target_id))
        
        # Update source node's connections
        if source_id in self.nodes:
            source_node = self.nodes[source_id]
            source_node.remove_connection(target_id)
        
        # Update modification date
        self.last_modified_date = datetime.now().isoformat()
        
        return True
    
    def get_all_nodes(self) -> Dict[str, DiagnosticNode]:
        """Get all nodes in the pathway.
        
        Returns:
            dict: Dictionary of node_id -> DiagnosticNode.
        """
        return self.nodes
    
    def get_nodes_by_type(self, node_type: str) -> Dict[str, DiagnosticNode]:
        """Get all nodes of a specific type.
        
        Args:
            node_type (str): Type of nodes to get.
            
        Returns:
            dict: Dictionary of node_id -> DiagnosticNode for nodes of the specified type.
        """
        return {
            node_id: node for node_id, node in self.nodes.items()
            if node.node_type == node_type
        }
    
    def get_connections(self) -> List[Tuple[str, str]]:
        """Get all connections in the pathway.
        
        Returns:
            list: List of (source_id, target_id) tuples.
        """
        return self.connections
    
    def convert_to_rule_text(self) -> str:
        """Convert the pathway to rule text format.
        
        Returns:
            str: The rule text representation of the pathway.
        """
        # Find starting nodes (nodes with no incoming connections)
        incoming_connections = set()
        for source, target in self.connections:
            incoming_connections.add(target)
            
        starting_nodes = [node_id for node_id in self.nodes.keys() if node_id not in incoming_connections]
        
        # If no clear starting point, use any problem node or just the first node
        if not starting_nodes:
            problem_nodes = [node_id for node_id, node in self.nodes.items() if node.node_type == "problem"]
            starting_nodes = problem_nodes if problem_nodes else list(self.nodes.keys())[:1]
            
        # Traverse the pathway to build the rule
        conditions = []
        actions = []
        
        # Process each starting point
        for start_node_id in starting_nodes:
            self._process_node_for_rule(start_node_id, conditions, actions, set())
            
        # Build the IF part
        if_part = "IF " + " AND ".join(conditions)
        
        # Build the THEN part
        then_part = "THEN"
        for i, action in enumerate(actions):
            then_part += f"\n  {i+1}. {action}"
            
        # Combine into final rule
        return f"{if_part},\n{then_part}"
    
    def _process_node_for_rule(self, node_id: str, conditions: List[str], 
                              actions: List[str], visited: Set[str]) -> None:
        """Process a node and its children for rule conversion.
        
        Args:
            node_id (str): The ID of the node to process.
            conditions (list): List to collect condition strings.
            actions (list): List to collect action strings.
            visited (set): Set of already visited nodes to prevent cycles.
        """
        if node_id in visited:
            return
            
        visited.add(node_id)
        node = self.nodes.get(node_id)
        if not node:
            return
            
        content = node.get_content().strip()
        if not content:
            content = f"[Empty {node.node_type.capitalize()}]"
            
        # Process based on node type
        if node.node_type == "problem":
            conditions.append(f"problem is '{content}'")
        elif node.node_type == "check":
            check_type = node.get_check_type()
            if check_type:
                conditions.append(f"{check_type} shows '{content}'")
            else:
                conditions.append(f"check shows '{content}'")
        elif node.node_type == "condition":
            severity = node.get_condition_severity()
            if severity:
                conditions.append(f"{severity} condition: {content}")
            else:
                conditions.append(content)
        elif node.node_type == "action":
            impact = node.get_action_impact()
            if impact:
                actions.append(f"{impact}: {content}")
            else:
                actions.append(content)
                
        # Process child nodes
        for source, target in self.connections:
            if source == node_id:
                self._process_node_for_rule(target, conditions, actions, visited)
    
    def convert_to_structured_data(self) -> Dict[str, Any]:
        """Convert pathway to structured format for the rule model.
        
        Returns:
            dict: Structured data representing the rule.
        """
        rule_text = self.convert_to_rule_text()
        
        # Find all conditions and actions
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
                    
                    # Try to further parse if possible
                    if ": " in action_text:
                        parts = action_text.split(": ", 1)
                        action["type"] = parts[0]
                        action["target"] = parts[1]
                    
                    actions.append(action)
        
        return {
            "text": rule_text,
            "conditions": conditions,
            "actions": actions,
            "is_complex": True,
            "name": self.name,
            "description": self.description,
            "pathway_data": self.to_dict()
        }
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate the pathway for completeness and correctness.
        
        Returns:
            dict: Dictionary with validation issues by category.
        """
        issues = {
            "nodes": [],
            "connections": [],
            "structure": []
        }
        
        # Check for empty nodes
        for node_id, node in self.nodes.items():
            node_issues = node.validate()
            if node_issues:
                for issue in node_issues:
                    issues["nodes"].append(f"Node {node_id[:8]}: {issue}")
        
        # Check for disconnected nodes
        connected_nodes = set()
        for source, target in self.connections:
            connected_nodes.add(source)
            connected_nodes.add(target)
            
        disconnected_nodes = [
            node_id for node_id in self.nodes.keys() if node_id not in connected_nodes
        ]
        
        if disconnected_nodes:
            for node_id in disconnected_nodes:
                node = self.nodes[node_id]
                issues["connections"].append(
                    f"{node.node_type.capitalize()} node {node_id[:8]} is disconnected"
                )
        
        # Check for logical flow
        problem_nodes = self.get_nodes_by_type("problem")
        action_nodes = self.get_nodes_by_type("action")
        
        if not problem_nodes:
            issues["structure"].append("No problem statement defined")
        if not action_nodes:
            issues["structure"].append("No action steps defined")
        
        # Check for terminal nodes without actions
        terminal_nodes = set()
        for node_id in self.nodes.keys():
            has_outgoing = False
            for source, _ in self.connections:
                if source == node_id:
                    has_outgoing = True
                    break
            if not has_outgoing:
                terminal_nodes.add(node_id)
        
        for terminal_id in terminal_nodes:
            if terminal_id in self.nodes and self.nodes[terminal_id].node_type != "action":
                node = self.nodes[terminal_id]
                issues["structure"].append(
                    f"{node.node_type.capitalize()} node {terminal_id[:8]} ends pathway without an action"
                )
        
        # Check for cycles
        cycles = self._detect_cycles()
        if cycles:
            issues["structure"].append(f"Pathway contains {len(cycles)} cycle(s)")
        
        return issues
    
    def _detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the pathway.
        
        Returns:
            list: List of cycles, each represented as a list of node IDs.
        """
        # Create adjacency list
        graph = {node_id: [] for node_id in self.nodes.keys()}
        for source, target in self.connections:
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
    
    def auto_layout(self) -> None:
        """Automatically arrange nodes in a columnar layout."""
        # Group nodes by type
        nodes_by_type = {
            "problem": [],
            "check": [],
            "condition": [],
            "action": []
        }
        
        for node_id, node in self.nodes.items():
            if node.node_type in nodes_by_type:
                nodes_by_type[node.node_type].append(node)
        
        # Reset layout positions
        column_y_positions = {
            "problem": self.layout_settings['initial_y'],
            "check": self.layout_settings['initial_y'],
            "condition": self.layout_settings['initial_y'],
            "action": self.layout_settings['initial_y']
        }
        
        # Position each node according to type
        for node_type, nodes in nodes_by_type.items():
            column_map = {
                "problem": 0,
                "check": 1,
                "condition": 2,
                "action": 3
            }
            column = column_map.get(node_type, 0)
            x_position = self.layout_settings['initial_x'] + column * (
                self.layout_settings['column_width'] + self.layout_settings['column_margin']
            )
            
            for node in nodes:
                y_position = column_y_positions[node_type]
                node.set_position(x_position, y_position)
                
                # Update next Y position
                column_y_positions[node_type] += 120 + self.layout_settings['node_margin']
        
        # Update modification date
        self.last_modified_date = datetime.now().isoformat()
    
    def clear(self) -> None:
        """Clear all nodes and connections from the pathway."""
        self.nodes = {}
        self.connections = []
        self.last_modified_date = datetime.now().isoformat()
    
    def duplicate(self) -> 'DiagnosticPathway':
        """Create a duplicate of this pathway with a new ID.
        
        Returns:
            DiagnosticPathway: A new DiagnosticPathway instance with the same data but a new ID.
        """
        pathway_dict = self.to_dict()
        # Generate a new ID
        pathway_dict['pathway_id'] = str(uuid.uuid4())
        # Update dates
        pathway_dict['created_date'] = datetime.now().isoformat()
        pathway_dict['last_modified_date'] = pathway_dict['created_date']
        # Update name
        if self.name:
            pathway_dict['name'] = f"Copy of {self.name}"
        
        return DiagnosticPathway.from_dict(pathway_dict)