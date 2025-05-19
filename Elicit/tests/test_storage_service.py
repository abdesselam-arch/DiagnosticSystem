import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch

from models.collection import Collection
from models.rule import Rule
from services.storage_service import StorageService

class MockConfig:
    """Mock configuration for testing."""
    def __init__(self, base_dir):
        self.DATA_DIR = os.path.join(base_dir, "data")
        self.EXPORT_DIR = os.path.join(base_dir, "exports")
        self.RULES_FILE = os.path.join(self.DATA_DIR, "rules.json")
        self.INTERACTION_LOG = os.path.join(self.DATA_DIR, "logs", "interactions.json")

class TestStorageService(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock config
        self.config = MockConfig(self.temp_dir)
        
        # Create the storage service
        self.storage = StorageService(self.config)
        
        # Ensure testing directories exist
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        os.makedirs(self.config.EXPORT_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.config.INTERACTION_LOG), exist_ok=True)
        
        # Sample test data - rule dictionaries
        self.test_rule_dicts = [
            {
                "rule_id": "test-rule-1",
                "text": "IF condition = true, THEN action",
                "is_complex": True,
                "conditions": [{"param": "condition", "operator": "=", "value": "true", "connector": ""}],
                "actions": [{"type": "Apply", "target": "action", "sequence": 1, "value": ""}],
                "created_date": datetime.now().isoformat(),
                "use_count": 0
            },
            {
                "rule_id": "test-rule-2",
                "text": "IF temperature > 90, THEN cool system",
                "is_complex": True,
                "conditions": [{"param": "temperature", "operator": ">", "value": "90", "connector": ""}],
                "actions": [{"type": "Apply", "target": "cool system", "sequence": 1, "value": ""}],
                "created_date": datetime.now().isoformat(),
                "use_count": 5
            }
        ]
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
    
    def test_initialize(self):
        """Test initialization creates required directories."""
        # Initialize storage service
        self.storage.initialize()
        
        # Verify directories were created
        self.assertTrue(os.path.exists(self.config.DATA_DIR))
        self.assertTrue(os.path.exists(self.config.EXPORT_DIR))
        
        # Verify collection was loaded
        self.assertIsNotNone(self.storage.collection)
    
    def test_save_and_load_collection(self):
        """Test saving and loading the collection."""
        # Create a test rule
        rule = Rule.from_dict(self.test_rule_dicts[0])
        
        # Add rule to collection
        self.storage.collection.add_rule(rule)
        
        # Save collection
        result = self.storage.save_collection()
        
        # Verify save was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.config.RULES_FILE))
        
        # Create a new storage service instance to load the collection
        new_storage = StorageService(self.config)
        
        # Verify rule was loaded
        self.assertEqual(len(new_storage.collection.get_all_rules()), 1)
        loaded_rule = new_storage.collection.get_rule(rule.rule_id)
        self.assertEqual(loaded_rule.text, rule.text)
    
    def test_backup_creation(self):
        """Test backup creation when saving collection."""
        # Add a rule and save
        rule = Rule.from_dict(self.test_rule_dicts[0])
        self.storage.collection.add_rule(rule)
        self.storage.save_collection()
        
        # Modify and save again to trigger backup
        rule.text = "Modified text"
        self.storage.collection.update_rule(rule)
        self.storage.save_collection()
        
        # Check if backup directory exists
        backup_dir = os.path.join(self.config.DATA_DIR, "backups")
        self.assertTrue(os.path.exists(backup_dir))
        
        # Check if at least one backup file exists
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("rules_backup_")]
        self.assertGreater(len(backup_files), 0)
    
    def test_load_rules(self):
        """Test loading rules from the collection."""
        # Add test rules to collection
        for rule_dict in self.test_rule_dicts:
            rule = Rule.from_dict(rule_dict)
            self.storage.collection.add_rule(rule)
        
        # Load rules
        loaded_rules = self.storage.load_rules()
        
        # Verify correct number of rules loaded
        self.assertEqual(len(loaded_rules), len(self.test_rule_dicts))
        
        # Verify rule content
        rule_texts = [r["text"] for r in loaded_rules]
        self.assertIn(self.test_rule_dicts[0]["text"], rule_texts)
        self.assertIn(self.test_rule_dicts[1]["text"], rule_texts)
    
    def test_save_rules(self):
        """Test saving rules to the collection."""
        # Save test rules
        result = self.storage.save_rules(self.test_rule_dicts)
        
        # Verify save was successful
        self.assertTrue(result)
        
        # Verify rules were added to collection
        self.assertEqual(len(self.storage.collection.get_all_rules()), len(self.test_rule_dicts))
        
        # Verify rules file was created
        self.assertTrue(os.path.exists(self.config.RULES_FILE))
    
    def test_get_rule(self):
        """Test getting a rule by ID."""
        # Add a rule to collection
        rule = Rule.from_dict(self.test_rule_dicts[0])
        self.storage.collection.add_rule(rule)
        
        # Get the rule
        loaded_rule = self.storage.get_rule(rule.rule_id)
        
        # Verify rule was retrieved correctly
        self.assertIsNotNone(loaded_rule)
        self.assertEqual(loaded_rule["text"], rule.text)
        
        # Try getting a non-existent rule
        non_existent = self.storage.get_rule("non-existent-id")
        self.assertIsNone(non_existent)
    
    def test_add_rule(self):
        """Test adding a new rule."""
        # Add a rule
        rule_id = self.storage.add_rule(self.test_rule_dicts[0])
        
        # Verify rule was added
        self.assertNotEqual(rule_id, "")
        self.assertEqual(len(self.storage.collection.get_all_rules()), 1)
        
        # Verify rule content
        added_rule = self.storage.collection.get_rule(rule_id)
        self.assertEqual(added_rule.text, self.test_rule_dicts[0]["text"])
    
    def test_update_rule(self):
        """Test updating an existing rule."""
        # Add a rule first
        rule = Rule.from_dict(self.test_rule_dicts[0])
        self.storage.collection.add_rule(rule)
        
        # Modify the rule
        updated_rule = rule.to_dict()
        updated_rule["text"] = "Updated rule text"
        
        # Update the rule
        result = self.storage.update_rule(updated_rule)
        
        # Verify update was successful
        self.assertTrue(result)
        
        # Verify rule was updated
        loaded_rule = self.storage.collection.get_rule(rule.rule_id)
        self.assertEqual(loaded_rule.text, "Updated rule text")
    
    def test_delete_rule(self):
        """Test deleting a rule."""
        # Add a rule first
        rule = Rule.from_dict(self.test_rule_dicts[0])
        rule_id = self.storage.collection.add_rule(rule)
        
        # Delete the rule
        result = self.storage.delete_rule(rule_id)
        
        # Verify deletion was successful
        self.assertTrue(result)
        
        # Verify rule was removed
        self.assertEqual(len(self.storage.collection.get_all_rules()), 0)
    
    def test_record_rule_usage(self):
        """Test recording rule usage."""
        # Add a rule
        rule = Rule.from_dict(self.test_rule_dicts[0])
        rule_id = self.storage.collection.add_rule(rule)
        initial_count = rule.use_count
        
        # Record usage
        result = self.storage.record_rule_usage(rule_id)
        
        # Verify recording was successful
        self.assertTrue(result)
        
        # Verify usage count was incremented
        updated_rule = self.storage.collection.get_rule(rule_id)
        self.assertEqual(updated_rule.use_count, initial_count + 1)
    
    def test_search_rules(self):
        """Test searching for rules."""
        # Add test rules
        for rule_dict in self.test_rule_dicts:
            rule = Rule.from_dict(rule_dict)
            self.storage.collection.add_rule(rule)
        
        # Search for rules
        results = self.storage.search_rules("temperature")
        
        # Verify correct rule was found
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], self.test_rule_dicts[1]["text"])
        
        # Search with no results
        no_results = self.storage.search_rules("nonexistent")
        self.assertEqual(len(no_results), 0)
    
    def test_export_rules(self):
        """Test exporting rules."""
        # Add test rules
        rule_ids = []
        for rule_dict in self.test_rule_dicts:
            rule = Rule.from_dict(rule_dict)
            rule_id = self.storage.collection.add_rule(rule)
            rule_ids.append(rule_id)
        
        # Export specific rule
        export_file = os.path.join(self.config.EXPORT_DIR, "test_export.json")
        result = self.storage.export_rules([rule_ids[0]], export_file)
        
        # Verify export was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_file))
        
        # Verify export contains the correct rule
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
            
        self.assertEqual(len(export_data["rules"]), 1)
        self.assertEqual(export_data["rules"][0]["rule_id"], rule_ids[0])
        
        # Test exporting all rules
        all_export_file = os.path.join(self.config.EXPORT_DIR, "all_export.json")
        self.storage.export_rules(file_path=all_export_file)
        
        with open(all_export_file, 'r', encoding='utf-8') as f:
            all_export_data = json.load(f)
            
        self.assertEqual(len(all_export_data["rules"]), 2)
    
    def test_import_rules(self):
        """Test importing rules."""
        # Create export file
        export_data = {
            "format_version": "1.0",
            "export_date": datetime.now().isoformat(),
            "rules": self.test_rule_dicts
        }
        
        import_file = os.path.join(self.config.EXPORT_DIR, "test_import.json")
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f)
        
        # Import rules
        added, updated = self.storage.import_rules(import_file)
        
        # Verify import was successful
        self.assertEqual(added, 2)
        self.assertEqual(updated, 0)
        self.assertEqual(len(self.storage.collection.get_all_rules()), 2)
        
        # Test updating existing rules
        # Modify rule and re-export
        export_data["rules"][0]["text"] = "Modified rule"
        
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f)
        
        # Import again
        added, updated = self.storage.import_rules(import_file)
        
        # Verify update was counted correctly
        self.assertEqual(added, 0)
        self.assertEqual(updated, 1)
    
    def test_duplicate_rule(self):
        """Test duplicating a rule."""
        # Add a rule
        rule = Rule.from_dict(self.test_rule_dicts[0])
        rule_id = self.storage.collection.add_rule(rule)
        
        # Duplicate the rule
        new_rule_id = self.storage.duplicate_rule(rule_id)
        
        # Verify duplication was successful
        self.assertIsNotNone(new_rule_id)
        self.assertNotEqual(new_rule_id, rule_id)
        
        # Verify new rule is a copy with a different ID
        new_rule = self.storage.collection.get_rule(new_rule_id)
        self.assertEqual(len(self.storage.collection.get_all_rules()), 2)
        self.assertEqual(new_rule.text, rule.text)
        
        # Verify the name indicates it's a copy
        self.assertTrue(new_rule.name.startswith("Copy of"))
    
    def test_log_interaction(self):
        """Test logging user interactions."""
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "view_rule",
            "rule_id": "test-rule-1"
        }
        
        # Log interaction
        result = self.storage.log_interaction(log_entry)
        
        # Verify logging was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.config.INTERACTION_LOG))
        
        # Verify log entry was saved
        with open(self.config.INTERACTION_LOG, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["rule_id"], log_entry["rule_id"])
        
        # Add another log entry
        log_entry2 = {
            "timestamp": datetime.now().isoformat(),
            "action": "edit_rule",
            "rule_id": "test-rule-2"
        }
        
        self.storage.log_interaction(log_entry2)
        
        # Verify both entries are in the log
        with open(self.config.INTERACTION_LOG, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            
        self.assertEqual(len(logs), 2)
    
    def test_get_statistics(self):
        """Test getting collection statistics."""
        # Add test rules
        for rule_dict in self.test_rule_dicts:
            rule = Rule.from_dict(rule_dict)
            self.storage.collection.add_rule(rule)
        
        # Get statistics
        stats = self.storage.get_statistics()
        
        # Verify statistics
        self.assertIn("total_rules", stats)
        self.assertEqual(stats["total_rules"], 2)
    
    def test_get_recently_used_rules(self):
        """Test getting recently used rules."""
        # Add test rules with different use counts
        for rule_dict in self.test_rule_dicts:
            rule = Rule.from_dict(rule_dict)
            self.storage.collection.add_rule(rule)
        
        # Record usage for one rule to make it more recent
        first_rule_id = next(iter(self.storage.collection.get_all_rules().keys()))
        self.storage.record_rule_usage(first_rule_id)
        
        # Get recently used rules
        recent_rules = self.storage.get_recently_used_rules(1)
        
        # Verify the most recently used rule is returned
        self.assertEqual(len(recent_rules), 1)
        self.assertEqual(recent_rules[0]["rule_id"], first_rule_id)