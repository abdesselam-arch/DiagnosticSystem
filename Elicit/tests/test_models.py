import unittest
from models.rule import Rule
from models.diagnostic_pathway import DiagnosticPathway

class TestRule(unittest.TestCase):
    def test_rule_creation(self):
        """Test creating a rule and accessing its properties."""
        rule = Rule(
            text="IF condition = true, THEN action",
            conditions=[{"param": "condition", "operator": "=", "value": "true"}],
            actions=[{"type": "Apply", "target": "action", "sequence": 1}]
        )
        
        self.assertEqual(rule.text, "IF condition = true, THEN action")
        self.assertEqual(len(rule.conditions), 1)
        self.assertEqual(len(rule.actions), 1)
        self.assertEqual(rule.is_complex, True)
        self.assertEqual(rule.use_count, 0)
    
    def test_rule_to_dict(self):
        """Test converting a rule to dictionary."""
        rule = Rule(
            text="Test Rule",
            conditions=[{"param": "condition", "operator": "=", "value": "true"}],
            actions=[{"type": "Apply", "target": "action", "sequence": 1}]
        )
        
        rule_dict = rule.to_dict()
        
        self.assertIsInstance(rule_dict, dict)
        self.assertEqual(rule_dict["text"], "Test Rule")
        self.assertEqual(len(rule_dict["conditions"]), 1)
        self.assertEqual(rule_dict["use_count"], 0)
    
    def test_rule_from_dict(self):
        """Test creating a rule from dictionary."""
        rule_dict = {
            "text": "Test Rule",
            "is_complex": True,
            "conditions": [{"param": "condition", "operator": "=", "value": "true"}],
            "actions": [{"type": "Apply", "target": "action", "sequence": 1}],
            "use_count": 5,
            "created": "2023-01-01T12:00:00"
        }
        
        rule = Rule.from_dict(rule_dict)
        
        self.assertEqual(rule.text, "Test Rule")
        self.assertEqual(rule.use_count, 5)
        self.assertEqual(rule.created, "2023-01-01T12:00:00")

class TestDiagnosticPathway(unittest.TestCase):
    def test_pathway_creation(self):
        """Test creating a diagnostic pathway."""
        pathway_data = {
            "nodes": {
                "1": {"node_id": "1", "node_type": "problem", "content": "Test Problem"},
                "2": {"node_id": "2", "node_type": "check", "content": "Test Check"}
            },
            "connections": [["1", "2"]]
        }
        
        pathway = DiagnosticPathway(pathway_data)
        
        self.assertEqual(len(pathway.nodes), 2)
        self.assertEqual(len(pathway.connections), 1)
        self.assertEqual(pathway.get_problem_nodes()[0]["content"], "Test Problem")
    
    def test_convert_to_rule(self):
        """Test converting a pathway to a rule."""
        pathway_data = {
            "nodes": {
                "1": {"node_id": "1", "node_type": "problem", "content": "Test Problem"},
                "2": {"node_id": "2", "node_type": "check", "content": "Test Check"},
                "3": {"node_id": "3", "node_type": "condition", "content": "Test Condition"},
                "4": {"node_id": "4", "node_type": "action", "content": "Test Action"}
            },
            "connections": [["1", "2"], ["2", "3"], ["3", "4"]]
        }
        
        pathway = DiagnosticPathway(pathway_data)
        rule = pathway.to_rule()
        
        self.assertIn("Test Problem", rule.text)
        self.assertIn("Test Condition", rule.text)
        self.assertIn("Test Action", rule.text)
        self.assertEqual(len(rule.conditions), 2)  # Problem and condition
        self.assertEqual(len(rule.actions), 1)