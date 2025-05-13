import unittest
import json
import os
import tempfile
from datetime import datetime
from services.storage_service import StorageService

class TestStorageService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.rules_path = os.path.join(self.temp_dir.name, "test_rules.json")
        self.logs_path = os.path.join(self.temp_dir.name, "test_logs.json")
        self.storage = StorageService(self.rules_path, self.logs_path)
        
        # Sample test data
        self.test_rules = [
            {
                "text": "Test Rule 1",
                "is_complex": True,
                "conditions": [{"param": "condition", "operator": "=", "value": "true"}],
                "actions": [{"type": "Apply", "target": "action", "sequence": 1}],
                "created": datetime.now().isoformat(),
                "use_count": 0
            },
            {
                "text": "Test Rule 2",
                "is_complex": False,
                "conditions": [],
                "actions": [],
                "created": datetime.now().isoformat(),
                "use_count": 5
            }
        ]
    
    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_save_and_load_rules(self):
        """Test that rules can be saved and loaded correctly."""
        # Save rules
        self.storage.save_rules(self.test_rules)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.rules_path))
        
        # Load rules
        loaded_rules = self.storage.load_rules()
        
        # Verify loaded rules match original
        self.assertEqual(len(loaded_rules), len(self.test_rules))
        self.assertEqual(loaded_rules[0]["text"], self.test_rules[0]["text"])
        self.assertEqual(loaded_rules[1]["use_count"], self.test_rules[1]["use_count"])
    
    def test_load_rules_nonexistent_file(self):
        """Test loading rules when file doesn't exist returns empty list."""
        # Use a non-existent path
        nonexistent_path = os.path.join(self.temp_dir.name, "nonexistent.json")
        storage = StorageService(nonexistent_path, self.logs_path)
        
        # Should return empty list, not raise exception
        rules = storage.load_rules()
        self.assertEqual(rules, [])
    
    def test_log_interaction(self):
        """Test that interaction logging works."""
        # Create a log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "rule_id": 0,
            "rule_text": "Test Rule",
            "problem_description": "Test Problem"
        }
        
        # Log it
        self.storage.log_interaction(log_entry)
        
        # Verify log file exists
        self.assertTrue(os.path.exists(self.logs_path))
        
        # Read the log file directly to verify
        with open(self.logs_path, 'r') as f:
            logs = json.load(f)
        
        # Verify log entry was saved
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[-1]["rule_text"], log_entry["rule_text"])