import unittest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys

from ui.widgets.diagnostic_node import DiagnosticNodeWidget
from ui.widgets.diagnostic_canvas import DiagnosticPathwayCanvas
from models.rule import Rule

class TestDiagnosticNodeWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create Qt application for the tests
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        self.node = DiagnosticNodeWidget(node_type="problem")
    
    def test_node_creation(self):
        """Test creating a node with different types."""
        problem_node = DiagnosticNodeWidget(node_type="problem")
        check_node = DiagnosticNodeWidget(node_type="check")
        condition_node = DiagnosticNodeWidget(node_type="condition")
        action_node = DiagnosticNodeWidget(node_type="action")
        
        self.assertEqual(problem_node.node_type, "problem")
        self.assertEqual(check_node.node_type, "check")
        self.assertEqual(condition_node.node_type, "condition")
        self.assertEqual(action_node.node_type, "action")
    
    def test_node_content(self):
        """Test setting and getting node content."""
        test_content = "Test node content"
        self.node.content_edit.setPlainText(test_content)
        
        self.assertEqual(self.node.content_edit.toPlainText(), test_content)
    
    def test_get_data(self):
        """Test getting node data."""
        self.node.content_edit.setPlainText("Test Content")
        data = self.node.get_data()
        
        self.assertEqual(data["node_type"], "problem")
        self.assertEqual(data["content"], "Test Content")
        self.assertIsInstance(data["node_id"], int)
    
    def test_set_data(self):
        """Test setting node data."""
        test_data = {
            "node_id": 12345,
            "node_type": "problem",
            "content": "Imported Content",
            "connections": [67890]
        }
        
        self.node.set_data(test_data)
        
        self.assertEqual(self.node.node_id, 12345)
        self.assertEqual(self.node.content_edit.toPlainText(), "Imported Content")
        self.assertEqual(self.node.connections, [67890])

class TestDiagnosticPathwayCanvas(unittest.TestCase):
    """Test the DiagnosticPathwayCanvas UI component."""
    
    @classmethod
    def setUpClass(cls):
        """Create Qt application for the tests."""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create the canvas with test fixtures
        self.canvas = DiagnosticPathwayCanvas()
        
        # Setup test data
        self.simple_pathway_data = {
            "nodes": {
                "1": {"node_id": "1", "node_type": "problem", "content": "Test Problem"},
                "2": {"node_id": "2", "node_type": "check", "content": "Test Check"}
            },
            "connections": [["1", "2"]]
        }
        
        self.complex_pathway_data = {
            "nodes": {
                "1": {"node_id": "1", "node_type": "problem", "content": "Temperature Issue"},
                "2": {"node_id": "2", "node_type": "check", "content": "Check temperature sensor"},
                "3": {"node_id": "3", "node_type": "condition", "content": "Temperature > 90F"},
                "4": {"node_id": "4", "node_type": "action", "content": "Apply cooling system"},
                "5": {"node_id": "5", "node_type": "condition", "content": "Temperature < 32F"},
                "6": {"node_id": "6", "node_type": "action", "content": "Apply heating system"}
            },
            "connections": [
                ["1", "2"], 
                ["2", "3"], 
                ["2", "5"],
                ["3", "4"],
                ["5", "6"]
            ]
        }
    
    def test_pathway_creation(self):
        """Test creating a diagnostic pathway canvas."""
        # Verify the canvas was created properly
        self.assertEqual(len(self.canvas.nodes), 0)
        self.assertEqual(len(self.canvas.connections), 0)
    
    def test_add_node(self):
        """Test adding a new node to the canvas."""
        # Add a new node
        node = self.canvas.add_node("action")
        
        # Verify the node was added
        self.assertEqual(len(self.canvas.nodes), 1)
        self.assertIn(node.node_id, self.canvas.nodes)
        self.assertEqual(node.node_type, "action")
    
    def test_add_connection(self):
        """Test adding a new connection to the canvas."""
        # Add two nodes
        node1 = self.canvas.add_node("problem")
        node2 = self.canvas.add_node("check")
        
        # Add a connection
        self.canvas.add_connection(node1.node_id, node2.node_id)
        
        # Verify the connection was added
        self.assertEqual(len(self.canvas.connections), 1)
        self.assertEqual(self.canvas.connections[0], (node1.node_id, node2.node_id))
    
    def test_get_node_types(self):
        """Test getting nodes by type through the pathway data."""
        # Set up a complex pathway
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Get pathway data and check nodes by type
        pathway_data = self.canvas.get_pathway_data()
        
        # Count nodes by type
        problem_nodes = [n for n in pathway_data["nodes"].values() if n["node_type"] == "problem"]
        condition_nodes = [n for n in pathway_data["nodes"].values() if n["node_type"] == "condition"]
        action_nodes = [n for n in pathway_data["nodes"].values() if n["node_type"] == "action"]
        check_nodes = [n for n in pathway_data["nodes"].values() if n["node_type"] == "check"]
        
        # Verify counts
        self.assertEqual(len(problem_nodes), 1)
        self.assertEqual(len(condition_nodes), 2)
        self.assertEqual(len(action_nodes), 2)
        self.assertEqual(len(check_nodes), 1)
        
        # Verify content
        problem_content = [n["content"] for n in problem_nodes]
        self.assertIn("Temperature Issue", problem_content)
    
    def test_get_node_connections(self):
        """Test getting connections for nodes."""
        # Set up a complex pathway
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Identify node IDs (we need to convert string IDs to the actual node IDs)
        node_map = {}
        for node_id, node in self.canvas.nodes.items():
            for original_id, data in self.complex_pathway_data["nodes"].items():
                if node.get_content() == data["content"]:
                    node_map[original_id] = node_id
        
        # Find connections from check node (node 2)
        if "2" in node_map:
            check_node_id = node_map["2"]
            connections_from_check = [c for c in self.canvas.connections if c[0] == check_node_id]
            
            # Verify connections count (should have 2 connections)
            self.assertEqual(len(connections_from_check), 2)
    
    def test_remove_node(self):
        """Test removing a node from the canvas."""
        # Set up a pathway
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Get initial counts
        initial_node_count = len(self.canvas.nodes)
        initial_connection_count = len(self.canvas.connections)
        
        # Get a node to remove (we'll use the first node)
        node_to_remove = next(iter(self.canvas.nodes.values()))
        
        # Remove the node
        self.canvas.delete_node(node_to_remove)
        
        # Verify the node was removed
        self.assertEqual(len(self.canvas.nodes), initial_node_count - 1)
        
        # Connections involving the node should also be removed
        self.assertLess(len(self.canvas.connections), initial_connection_count)
    
    def test_remove_connection(self):
        """Test removing a connection from the canvas."""
        # Add two nodes and connect them
        node1 = self.canvas.add_node("problem")
        node2 = self.canvas.add_node("check")
        self.canvas.add_connection(node1.node_id, node2.node_id)
        
        # Initial count
        initial_connection_count = len(self.canvas.connections)
        
        # Remove node connections
        self.canvas.delete_node_connections(node1)
        
        # Verify the connection was removed
        self.assertEqual(len(self.canvas.connections), initial_connection_count - 1)
    
    def test_to_rule_simple(self):
        """Test converting a simple pathway to rule text."""
        # Set up a simple pathway
        node1 = self.canvas.add_node("problem")
        node1.set_content("Test Problem")
        node2 = self.canvas.add_node("action")
        node2.set_content("Test Action")
        self.canvas.add_connection(node1.node_id, node2.node_id)
        
        # Convert to rule text
        rule_text = self.canvas.convert_to_rule_text()
        
        # Check that rule text contains the problem and action
        self.assertIn("Test Problem", rule_text)
        self.assertIn("Test Action", rule_text)
    
    def test_to_rule_complex(self):
        """Test converting a complex pathway to rule text."""
        # Set up a complex pathway
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Convert to rule text
        rule_text = self.canvas.convert_to_rule_text()
        
        # Check that rule text contains key elements
        self.assertIn("Temperature Issue", rule_text)
        self.assertIn("Temperature > 90F", rule_text)
        self.assertIn("Apply cooling system", rule_text)
    
    def test_to_dict(self):
        """Test converting a pathway to a dictionary."""
        # Set up a simple pathway
        node1 = self.canvas.add_node("problem")
        node1.set_content("Test Problem")
        node2 = self.canvas.add_node("check")
        node2.set_content("Test Check")
        self.canvas.add_connection(node1.node_id, node2.node_id)
        
        # Get pathway data
        pathway_dict = self.canvas.get_pathway_data()
        
        # Verify structure
        self.assertIn("nodes", pathway_dict)
        self.assertIn("connections", pathway_dict)
        
        # Verify content
        self.assertEqual(len(pathway_dict["nodes"]), 2)
        self.assertEqual(len(pathway_dict["connections"]), 1)
    
    def test_from_dict(self):
        """Test creating a pathway from a dictionary."""
        # Set initial data
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Verify the pathway was created correctly
        self.assertEqual(len(self.canvas.nodes), len(self.complex_pathway_data["nodes"]))
        self.assertEqual(len(self.canvas.connections), len(self.complex_pathway_data["connections"]))
        
        # Verify node content - we need to check if any node has the expected content
        found_content = False
        for node in self.canvas.nodes.values():
            if node.get_content() == "Temperature Issue":
                found_content = True
                break
        
        self.assertTrue(found_content, "Expected node content not found")
    
    def test_convert_to_structured_data(self):
        """Test converting a pathway to structured rule data."""
        # Set up a complex pathway
        self.canvas.set_pathway_data(self.complex_pathway_data)
        
        # Convert to structured data
        structured_data = self.canvas.convert_to_structured_data()
        
        # Verify structure
        self.assertIn("text", structured_data)
        self.assertIn("conditions", structured_data)
        self.assertIn("actions", structured_data)
        
        # Verify content
        self.assertGreater(len(structured_data["conditions"]), 0)
        self.assertGreater(len(structured_data["actions"]), 0)