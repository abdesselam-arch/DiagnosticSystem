import unittest
from datetime import datetime
from models.rule import Rule
from models.diagnostic_pathway import DiagnosticPathway
from models.diagnostic_node import DiagnosticNode

class TestRule(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create a simple rule for testing
        self.simple_rule = Rule(
            rule_id="test-rule-1",
            text="IF condition = true, THEN action"
        )

        # Create a more complex rule for testing
        self.complex_rule = Rule(
            rule_id="test-rule-2",
            text="IF temperature > 90 AND humidity > 70, THEN\n  1. Apply cooling\n  2. Adjust humidity to 50%"
        )

    def test_rule_creation(self):
        """Test creating a rule and accessing its properties."""
        # Test with initialization parameters
        rule = Rule(
            rule_id="test-123",
            text="IF condition = true, THEN action"
        )
        
        self.assertEqual(rule.rule_id, "test-123")
        self.assertEqual(rule.text, "IF condition = true, THEN action")
        self.assertEqual(rule.is_complex, True)
        self.assertEqual(rule.use_count, 0)
        
        # Test with auto-generated ID
        rule2 = Rule(text="Test rule")
        self.assertIsNotNone(rule2.rule_id)
        self.assertNotEqual(rule2.rule_id, "")
    
    def test_rule_to_dict(self):
        """Test converting a rule to dictionary."""
        rule = Rule(
            rule_id="test-123",
            text="Test Rule"
        )
        rule.add_condition("temperature", ">", "90")
        rule.add_action("cooling", "Apply")
        
        rule_dict = rule.to_dict()
        
        self.assertIsInstance(rule_dict, dict)
        self.assertEqual(rule_dict["rule_id"], "test-123")
        self.assertEqual(rule_dict["text"], "IF temperature > 90,\nTHEN\n  1. Apply cooling")
        self.assertEqual(len(rule_dict["conditions"]), 1)
        self.assertEqual(rule_dict["use_count"], 0)
        self.assertIn("created_date", rule_dict)
    
    def test_rule_from_dict(self):
        """Test creating a rule from dictionary."""
        rule_dict = {
            "rule_id": "test-123",
            "text": "Test Rule",
            "is_complex": True,
            "conditions": [{"param": "condition", "operator": "=", "value": "true", "connector": ""}],
            "actions": [{"type": "Apply", "target": "action", "sequence": 1}],
            "use_count": 5,
            "created_date": "2023-01-01T12:00:00",
            "last_modified_date": "2023-01-02T12:00:00",
            "name": "Test Rule Name",
            "description": "Test description"
        }
        
        rule = Rule.from_dict(rule_dict)
        
        self.assertEqual(rule.rule_id, "test-123")
        self.assertEqual(rule.text, "Test Rule")
        self.assertEqual(rule.use_count, 5)
        self.assertEqual(rule.created_date, "2023-01-01T12:00:00")
        self.assertEqual(rule.last_modified_date, "2023-01-02T12:00:00")
        self.assertEqual(rule.name, "Test Rule Name")
        self.assertEqual(rule.description, "Test description")
    
    def test_json_serialization(self):
        """Test converting rule to and from JSON."""
        original_rule = self.simple_rule
        
        # Convert to JSON
        json_str = original_rule.to_json()
        self.assertIsInstance(json_str, str)
        
        # Convert back from JSON
        restored_rule = Rule.from_json(json_str)
        self.assertEqual(restored_rule.rule_id, original_rule.rule_id)
        self.assertEqual(restored_rule.text, original_rule.text)

    def test_add_condition(self):
        """Test adding conditions to a rule."""
        rule = Rule(rule_id="test-123")
        
        # Add first condition
        rule.add_condition("temperature", ">", "90")
        self.assertEqual(len(rule.conditions), 1)
        self.assertEqual(rule.conditions[0]["param"], "temperature")
        self.assertEqual(rule.conditions[0]["operator"], ">")
        self.assertEqual(rule.conditions[0]["value"], "90")
        self.assertEqual(rule.conditions[0]["connector"], "")
        
        # Add second condition
        rule.add_condition("humidity", ">", "70", "AND")
        self.assertEqual(len(rule.conditions), 2)
        self.assertEqual(rule.conditions[0]["connector"], "AND")
        self.assertEqual(rule.conditions[1]["connector"], "")
        
        # Check if rule text was updated
        self.assertEqual(rule.text, "IF temperature > 90 AND humidity > 70,\nTHEN")
    
    def test_add_action(self):
        """Test adding actions to a rule."""
        rule = Rule(rule_id="test-123")
        
        # Add first action
        rule.add_action("cooling", "Apply")
        self.assertEqual(len(rule.actions), 1)
        self.assertEqual(rule.actions[0]["type"], "Apply")
        self.assertEqual(rule.actions[0]["target"], "cooling")
        self.assertEqual(rule.actions[0]["sequence"], 1)
        
        # Add second action with value and sequence
        rule.add_action("humidity", "Adjust", "50%", 2)
        self.assertEqual(len(rule.actions), 2)
        self.assertEqual(rule.actions[1]["type"], "Adjust")
        self.assertEqual(rule.actions[1]["target"], "humidity")
        self.assertEqual(rule.actions[1]["value"], "50%")
        self.assertEqual(rule.actions[1]["sequence"], 2)
        
        # Check if rule text was updated
        self.assertEqual(rule.text, "IF ,\nTHEN\n  1. Apply cooling\n  2. Adjust humidity to 50%")
    
    def test_set_conditions(self):
        """Test setting all conditions at once."""
        rule = Rule(rule_id="test-123")
        
        conditions = [
            {"param": "temperature", "operator": ">", "value": "90", "connector": "AND"},
            {"param": "humidity", "operator": ">", "value": "70", "connector": ""}
        ]
        
        rule.set_conditions(conditions)
        self.assertEqual(len(rule.conditions), 2)
        self.assertEqual(rule.conditions, conditions)
    
    def test_set_actions(self):
        """Test setting all actions at once."""
        rule = Rule(rule_id="test-123")
        
        actions = [
            {"type": "Apply", "target": "cooling", "value": "", "sequence": 1},
            {"type": "Adjust", "target": "humidity", "value": "50%", "sequence": 2}
        ]
        
        rule.set_actions(actions)
        self.assertEqual(len(rule.actions), 2)
        self.assertEqual(rule.actions, actions)
    
    def test_parse_rule_text(self):
        """Test parsing rule text into conditions and actions."""
        rule = Rule(
            rule_id="test-123",
            text="IF temperature > 90 AND humidity > 70, THEN\n  1. Apply cooling\n  2. Adjust humidity to 50%"
        )
        
        # Parse the rule text
        success = rule.parse_rule_text()
        self.assertTrue(success)
        
        # Check if conditions were parsed correctly
        self.assertEqual(len(rule.conditions), 2)
        self.assertEqual(rule.conditions[0]["param"], "temperature")
        self.assertEqual(rule.conditions[0]["operator"], ">")
        self.assertEqual(rule.conditions[0]["value"], "90")
        self.assertEqual(rule.conditions[0]["connector"], "AND")
        
        self.assertEqual(rule.conditions[1]["param"], "humidity")
        self.assertEqual(rule.conditions[1]["operator"], ">")
        self.assertEqual(rule.conditions[1]["value"], "70")
        self.assertEqual(rule.conditions[1]["connector"], "")
        
        # Check if actions were parsed correctly
        self.assertEqual(len(rule.actions), 2)
        self.assertEqual(rule.actions[0]["type"], "Apply")
        self.assertEqual(rule.actions[0]["target"], "cooling")
        self.assertEqual(rule.actions[0]["sequence"], 1)
        
        self.assertEqual(rule.actions[1]["type"], "Adjust")
        self.assertEqual(rule.actions[1]["target"], "humidity")
        self.assertEqual(rule.actions[1]["value"], "50%")
        self.assertEqual(rule.actions[1]["sequence"], 2)
    
    def test_get_description(self):
        """Test getting a concise description of the rule."""
        # Test rule with name
        rule = Rule(rule_id="test-123", text="IF condition = true, THEN action")
        rule.name = "Test Rule Name"
        self.assertEqual(rule.get_description(), "Test Rule Name")
        
        # Test rule with IF-THEN format
        rule.name = ""
        self.assertEqual(rule.get_description(), "condition = true")
    
    def test_record_usage(self):
        """Test recording rule usage."""
        rule = Rule(rule_id="test-123")
        initial_count = rule.use_count
        
        rule.record_usage()
        self.assertEqual(rule.use_count, initial_count + 1)
        self.assertIsNotNone(rule.last_used)
    
    def test_duplicate(self):
        """Test duplicating a rule."""
        original = Rule(rule_id="test-123")
        original.name = "Original Rule"
        original.add_condition("temperature", ">", "90")
        original.add_action("cooling", "Apply")
        
        duplicate = original.duplicate()
        
        # Check that IDs are different
        self.assertNotEqual(duplicate.rule_id, original.rule_id)
        
        # Check that name indicates it's a copy
        self.assertEqual(duplicate.name, "Copy of Original Rule")
        
        # Check that other properties are preserved
        self.assertEqual(len(duplicate.conditions), len(original.conditions))
        self.assertEqual(len(duplicate.actions), len(original.actions))
        
        # Check that usage stats are reset
        self.assertEqual(duplicate.use_count, 0)
        self.assertIsNone(duplicate.last_used)
    
    def test_validate(self):
        """Test rule validation."""
        # Test valid rule
        valid_rule = Rule(rule_id="test-123")
        valid_rule.add_condition("temperature", ">", "90")
        valid_rule.add_action("cooling", "Apply")
        
        issues = valid_rule.validate()
        self.assertEqual(len(issues["general"]), 0)
        self.assertEqual(len(issues["conditions"]), 0)
        self.assertEqual(len(issues["actions"]), 0)
        
        # Test invalid rule (missing conditions)
        invalid_rule = Rule(rule_id="test-456")
        invalid_rule.add_action("cooling", "Apply")
        
        issues = invalid_rule.validate()
        self.assertEqual(len(issues["conditions"]), 1)
        
        # Test invalid rule (missing actions)
        invalid_rule = Rule(rule_id="test-789")
        invalid_rule.add_condition("temperature", ">", "90")
        
        issues = invalid_rule.validate()
        self.assertEqual(len(issues["actions"]), 1)

class TestDiagnosticPathway(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create a simple pathway for testing
        self.simple_pathway = DiagnosticPathway(pathway_id="simple-pathway", name="Simple Test Pathway")
        
        # Add nodes to simple pathway
        problem_node = self.simple_pathway.add_node("problem")
        problem_node.set_content("Test Problem")
        
        check_node = self.simple_pathway.add_node("check")
        check_node.set_content("Test Check")
        
        # Connect nodes
        self.simple_pathway.connect_nodes(problem_node.node_id, check_node.node_id)
        
        # Create a complex pathway for testing
        self.complex_pathway = DiagnosticPathway(pathway_id="complex-pathway", name="Complex Test Pathway")
        
        # Add nodes to complex pathway
        problem_node = self.complex_pathway.add_node("problem")
        problem_node.set_content("Temperature Issue")
        
        check_node = self.complex_pathway.add_node("check")
        check_node.set_content("Check temperature sensor")
        
        condition_node1 = self.complex_pathway.add_node("condition")
        condition_node1.set_content("Temperature > 90F")
        
        condition_node2 = self.complex_pathway.add_node("condition")
        condition_node2.set_content("Temperature < 32F")
        
        action_node1 = self.complex_pathway.add_node("action")
        action_node1.set_content("Apply cooling system")
        
        action_node2 = self.complex_pathway.add_node("action")
        action_node2.set_content("Apply heating system")
        
        # Connect nodes
        self.complex_pathway.connect_nodes(problem_node.node_id, check_node.node_id)
        self.complex_pathway.connect_nodes(check_node.node_id, condition_node1.node_id)
        self.complex_pathway.connect_nodes(check_node.node_id, condition_node2.node_id)
        self.complex_pathway.connect_nodes(condition_node1.node_id, action_node1.node_id)
        self.complex_pathway.connect_nodes(condition_node2.node_id, action_node2.node_id)
        
        # Save node IDs for testing
        self.node_ids = {
            "problem": problem_node.node_id,
            "check": check_node.node_id,
            "condition1": condition_node1.node_id,
            "condition2": condition_node2.node_id,
            "action1": action_node1.node_id,
            "action2": action_node2.node_id
        }

    def test_pathway_creation(self):
        """Test creating a diagnostic pathway."""
        pathway = self.simple_pathway
        
        # Test basic properties
        self.assertEqual(len(pathway.nodes), 2)
        self.assertEqual(len(pathway.connections), 1)
        
        # Test node content
        problem_node = next(node for node in pathway.nodes.values() if node.node_type == "problem")
        check_node = next(node for node in pathway.nodes.values() if node.node_type == "check")
        
        self.assertEqual(problem_node.get_content(), "Test Problem")
        self.assertEqual(check_node.get_content(), "Test Check")
        
        # Test connection structure
        self.assertEqual(len(pathway.connections), 1)
        source_id, target_id = pathway.connections[0]
        self.assertEqual(pathway.nodes[source_id].node_type, "problem")
        self.assertEqual(pathway.nodes[target_id].node_type, "check")
    
    def test_get_nodes_by_type(self):
        """Test getting nodes by type."""
        pathway = self.complex_pathway
        
        problem_nodes = pathway.get_nodes_by_type("problem")
        condition_nodes = pathway.get_nodes_by_type("condition")
        action_nodes = pathway.get_nodes_by_type("action")
        check_nodes = pathway.get_nodes_by_type("check")
        
        self.assertEqual(len(problem_nodes), 1)
        self.assertEqual(len(condition_nodes), 2)
        self.assertEqual(len(action_nodes), 2)
        self.assertEqual(len(check_nodes), 1)
        
        # Verify content
        for node in problem_nodes.values():
            self.assertEqual(node.get_content(), "Temperature Issue")
        
        condition_contents = {node.get_content() for node in condition_nodes.values()}
        self.assertIn("Temperature > 90F", condition_contents)
        self.assertIn("Temperature < 32F", condition_contents)
        
        action_contents = {node.get_content() for node in action_nodes.values()}
        self.assertIn("Apply cooling system", action_contents)
        self.assertIn("Apply heating system", action_contents)
        
        for node in check_nodes.values():
            self.assertEqual(node.get_content(), "Check temperature sensor")
    
    def test_connections(self):
        """Test connections between nodes."""
        pathway = self.complex_pathway
        
        # Find check node ID
        check_node_id = self.node_ids["check"]
        action_node_id = self.node_ids["action1"]
        
        # Get outgoing connections from check node
        outgoing_connections = [conn for conn in pathway.connections if conn[0] == check_node_id]
        self.assertEqual(len(outgoing_connections), 2)
        
        # Verify targets are condition nodes
        condition_ids = {self.node_ids["condition1"], self.node_ids["condition2"]}
        for _, target_id in outgoing_connections:
            self.assertIn(target_id, condition_ids)
        
        # Get incoming connections to action node
        incoming_connections = [conn for conn in pathway.connections if conn[1] == action_node_id]
        self.assertEqual(len(incoming_connections), 1)
        self.assertEqual(incoming_connections[0][0], self.node_ids["condition1"])
    
    def test_add_node(self):
        """Test adding a new node to the pathway."""
        pathway = DiagnosticPathway()
        
        # Add a new node
        new_node = pathway.add_node("action")
        new_node.set_content("New Action")
        
        # Verify the node was added
        self.assertEqual(len(pathway.nodes), 1)
        self.assertEqual(pathway.nodes[new_node.node_id].get_content(), "New Action")
    
    def test_connect_and_disconnect_nodes(self):
        """Test connecting and disconnecting nodes."""
        pathway = DiagnosticPathway()
        
        # Add two nodes
        node1 = pathway.add_node("problem")
        node2 = pathway.add_node("action")
        
        # Connect nodes
        result = pathway.connect_nodes(node1.node_id, node2.node_id)
        
        # Verify connection was created
        self.assertTrue(result)
        self.assertEqual(len(pathway.connections), 1)
        self.assertEqual(pathway.connections[0], (node1.node_id, node2.node_id))
        
        # Test disconnecting
        disconnect_result = pathway.disconnect_nodes(node1.node_id, node2.node_id)
        
        # Verify disconnect was successful
        self.assertTrue(disconnect_result)
        self.assertEqual(len(pathway.connections), 0)
    
    def test_remove_node(self):
        """Test removing a node from the pathway."""
        pathway = self.complex_pathway
        
        # Get initial counts
        initial_node_count = len(pathway.nodes)
        initial_connection_count = len(pathway.connections)
        
        # Remove a node
        action_node_id = self.node_ids["action1"]
        result = pathway.remove_node(action_node_id)
        
        # Verify the node was removed
        self.assertTrue(result)
        self.assertEqual(len(pathway.nodes), initial_node_count - 1)
        self.assertNotIn(action_node_id, pathway.nodes)
        
        # Verify connections were removed
        self.assertLess(len(pathway.connections), initial_connection_count)
        for source, target in pathway.connections:
            self.assertNotEqual(source, action_node_id)
            self.assertNotEqual(target, action_node_id)
    
    def test_convert_to_rule_text(self):
        """Test converting pathway to rule text."""
        pathway = self.simple_pathway
        
        rule_text = pathway.convert_to_rule_text()
        
        # Verify rule text format
        self.assertIn("IF", rule_text)
        self.assertIn("THEN", rule_text)
        self.assertIn("Test Problem", rule_text)
        self.assertIn("Test Check", rule_text)
    
    def test_convert_to_structured_data(self):
        """Test converting pathway to structured rule data."""
        pathway = self.complex_pathway
        
        structured_data = pathway.convert_to_structured_data()
        
        # Verify structured format
        self.assertIn("text", structured_data)
        self.assertIn("conditions", structured_data)
        self.assertIn("actions", structured_data)
        self.assertIn("pathway_data", structured_data)
        
        # Verify conditions and actions
        self.assertGreaterEqual(len(structured_data["conditions"]), 1)
        self.assertGreaterEqual(len(structured_data["actions"]), 2)
        
        # Verify pathway data
        self.assertEqual(structured_data["pathway_data"]["pathway_id"], pathway.pathway_id)
    
    def test_to_dict(self):
        """Test converting a pathway to a dictionary."""
        pathway = self.complex_pathway
        pathway_dict = pathway.to_dict()
        
        # Verify structure
        self.assertIn("nodes", pathway_dict)
        self.assertIn("connections", pathway_dict)
        self.assertIn("pathway_id", pathway_dict)
        
        # Verify content
        self.assertEqual(len(pathway_dict["nodes"]), len(pathway.nodes))
        self.assertEqual(len(pathway_dict["connections"]), len(pathway.connections))
    
    def test_from_dict(self):
        """Test creating a pathway from a dictionary."""
        # Convert original to dict
        original_dict = self.complex_pathway.to_dict()
        
        # Create new pathway from dict
        new_pathway = DiagnosticPathway.from_dict(original_dict)
        
        # Verify the pathway was created correctly
        self.assertEqual(len(new_pathway.nodes), len(self.complex_pathway.nodes))
        self.assertEqual(len(new_pathway.connections), len(self.complex_pathway.connections))
        
        # Find the problem node and verify content
        problem_nodes = new_pathway.get_nodes_by_type("problem")
        problem_node = next(iter(problem_nodes.values()))
        self.assertEqual(problem_node.get_content(), "Temperature Issue")
    
    def test_validate(self):
        """Test pathway validation."""
        # Test a valid pathway
        issues = self.complex_pathway.validate()
        self.assertEqual(len(issues["structure"]), 0)
        
        # Test an invalid pathway (disconnected node)
        invalid_pathway = DiagnosticPathway()
        invalid_pathway.add_node("problem")  # Disconnected node
        
        invalid_issues = invalid_pathway.validate()
        self.assertGreater(len(invalid_issues["connections"]), 0)
    
    def test_auto_layout(self):
        """Test automatic layout of nodes."""
        pathway = DiagnosticPathway()
        
        # Add nodes of different types
        node1 = pathway.add_node("problem")
        node2 = pathway.add_node("check")
        node3 = pathway.add_node("condition")
        node4 = pathway.add_node("action")
        
        # Apply auto layout
        pathway.auto_layout()
        
        # Verify nodes are positioned in different columns
        positions = {
            "problem": node1.get_position()["x"],
            "check": node2.get_position()["x"],
            "condition": node3.get_position()["x"],
            "action": node4.get_position()["x"]
        }
        
        # Each type should be in a different column (x position)
        unique_x_positions = set(positions.values())
        self.assertEqual(len(unique_x_positions), 4)
    
    def test_duplicate(self):
        """Test duplicating a pathway."""
        original = self.complex_pathway
        duplicate = original.duplicate()
        
        # Verify duplicate has a different ID
        self.assertNotEqual(duplicate.pathway_id, original.pathway_id)
        
        # Verify same structure
        self.assertEqual(len(duplicate.nodes), len(original.nodes))
        self.assertEqual(len(duplicate.connections), len(original.connections))
        
        # Verify name indicates it's a copy
        self.assertTrue(duplicate.name.startswith("Copy of"))