import unittest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys

from ui.widgets.diagnostic_node import DiagnosticNodeWidget
from ui.widgets.diagnostic_canvas import DiagnosticPathwayCanvas

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

class TestDiagnosticCanvas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create Qt application for the tests
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        self.canvas = DiagnosticPathwayCanvas()
    
    def test_add_node(self):
        """Test adding a node to the canvas."""
        node = self.canvas.addNode("problem")
        
        self.assertIn(node.node_id, self.canvas.nodes)
        self.assertEqual(len(self.canvas.nodes), 1)
    
    def test_add_connected_node(self):
        """Test adding a connected node."""
        source_node = self.canvas.addNode("problem")
        target_node = self.canvas.add_connected_node(source_node, "check")
        
        self.assertEqual(len(self.canvas.connections), 1)
        self.assertEqual(self.canvas.connections[0][0], source_node.node_id)
        self.assertEqual(self.canvas.connections[0][1], target_node.node_id)
    
    def test_delete_node(self):
        """Test deleting a node."""
        node = self.canvas.addNode("problem")
        node_id = node.node_id
        
        self.canvas.deleteNode(node)
        
        self.assertNotIn(node_id, self.canvas.nodes)
        self.assertEqual(len(self.canvas.nodes), 0)
    
    def test_pathway_data(self):
        """Test getting and setting pathway data."""
        # Create a simple pathway
        node1 = self.canvas.addNode("problem")
        node2 = self.canvas.addNode("check")
        self.canvas.connections.append((node1.node_id, node2.node_id))
        
        # Get pathway data
        data = self.canvas.get_pathway_data()
        
        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["connections"]), 1)
        
        # Clear canvas
        self.canvas.nodes = {}
        self.canvas.connections = []
        
        # Set pathway data
        self.canvas.set_pathway_data(data)
        
        self.assertEqual(len(self.canvas.nodes), 2)
        self.assertEqual(len(self.canvas.connections), 1)