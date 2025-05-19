import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import json

from services.search_service import SearchService

class TestSearchService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for each test."""
        # Create mock config and storage service
        self.config = Mock()
        self.storage_service = Mock()
        
        # Create the search service with mocks
        self.search_service = SearchService(self.config, self.storage_service)
        
        # Sample test rules to use in tests
        self.test_rules = [
            {
                "rule_id": "rule1",
                "text": "IF machine overheats, THEN check cooling system",
                "name": "Overheating Issue",
                "conditions": [{"param": "machine", "operator": "=", "value": "overheats", "connector": ""}],
                "actions": [{"type": "check", "target": "cooling system", "sequence": 1, "value": ""}],
                "metadata": {"problem_type": "Machine Stoppage"},
                "use_count": 5,
                "last_used": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "rule_id": "rule2",
                "text": "IF product has defects, THEN inspect tooling",
                "name": "Quality Check",
                "conditions": [{"param": "product", "operator": "has", "value": "defects", "connector": ""}],
                "actions": [{"type": "inspect", "target": "tooling", "sequence": 1, "value": ""}],
                "metadata": {"problem_type": "Quality Issue"},
                "use_count": 10,
                "last_used": (datetime.now() - timedelta(days=10)).isoformat()
            },
            {
                "rule_id": "rule3",
                "text": "IF material jams, THEN clean feed mechanism",
                "name": "Material Jam",
                "conditions": [{"param": "material", "operator": "=", "value": "jams", "connector": ""}],
                "actions": [{"type": "clean", "target": "feed mechanism", "sequence": 1, "value": ""}],
                "metadata": {"problem_type": "Material Handling"},
                "use_count": 2,
                "last_used": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "rule_id": "rule4",
                "text": "IF temperature > 90, THEN activate cooling",
                "name": "Temperature Control",
                "conditions": [{"param": "temperature", "operator": ">", "value": "90", "connector": ""}],
                "actions": [{"type": "Apply", "target": "cooling", "sequence": 1, "value": ""}],
                "pathway_data": {"nodes": {}, "connections": []},
                "use_count": 15,
                "last_used": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
    
    def test_search(self):
        """Test the search method."""
        # Setup storage_service mock to return test rules
        self.storage_service.search_rules.return_value = self.test_rules
        
        # Test basic search
        results = self.search_service.search("overheats")
        
        # Verify storage_service was called correctly
        self.storage_service.search_rules.assert_called_with("overheats", None, None)
        
        # Verify results (all rules returned since storage_service is mocked)
        self.assertEqual(len(results), 4)
        
        # Test with rule type filter
        self.search_service.search("cooling", rule_type="Pathway")
        self.storage_service.search_rules.assert_called_with("cooling", "Pathway", None)
        
        # Test with advanced criteria
        advanced_criteria = {"match_case": True, "search_fields": ["text", "name"]}
        self.search_service.search("jams", advanced_criteria=advanced_criteria)
        self.storage_service.search_rules.assert_called_with("jams", None, advanced_criteria)
    
    def test_scoring_results(self):
        """Test the result scoring functionality."""
        # Setup rules with different relevances to the query
        query = "temperature"
        
        # Execute scoring
        scored_results = self.search_service._score_results(self.test_rules, query)
        
        # Verify results are sorted by score (highest first)
        self.assertEqual(scored_results[0][1]["rule_id"], "rule4")  # "Temperature Control" should score highest
        
        # Test with case sensitivity
        advanced_criteria = {"match_case": True}
        case_sensitive_results = self.search_service._score_results(
            self.test_rules, "Temperature", advanced_criteria
        )
        
        # When case-sensitive, "Temperature Control" should still be first
        self.assertEqual(case_sensitive_results[0][1]["rule_id"], "rule4")
    
    def test_highlight_matches(self):
        """Test highlighting matches in text."""
        text = "The machine overheats when running at high speed"
        query = "overheat"
        
        highlighted = self.search_service.highlight_matches(text, query)
        
        # Verify matches are highlighted
        self.assertIn('<span class="highlight">overheat</span>', highlighted)
        
        # Test with case sensitivity
        highlighted_case = self.search_service.highlight_matches(text, "Machine", True)
        self.assertNotIn('<span class="highlight">Machine</span>', highlighted_case)
        self.assertNotIn('<span class="highlight">machine</span>', highlighted_case)
        
        highlighted_case_insensitive = self.search_service.highlight_matches(text, "Machine", False)
        self.assertIn('<span class="highlight">machine</span>', highlighted_case_insensitive)
    
    def test_recent_searches(self):
        """Test recent searches functionality."""
        # Initially should be empty
        self.assertEqual(len(self.search_service.get_recent_searches()), 0)
        
        # Add some searches
        self.search_service.search("overheats")
        self.search_service.search("jams")
        self.search_service.search("temperature")
        
        # Verify recent searches
        recent = self.search_service.get_recent_searches()
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0], "temperature")  # Most recent first
        self.assertEqual(recent[2], "overheats")    # Oldest last
        
        # Test adding duplicate search (should move to top)
        self.search_service.search("overheats")
        recent = self.search_service.get_recent_searches()
        self.assertEqual(recent[0], "overheats")
        self.assertEqual(len(recent), 3)  # Should still have 3 items
        
        # Test clearing recent searches
        self.search_service.clear_recent_searches()
        self.assertEqual(len(self.search_service.get_recent_searches()), 0)
    
    def test_popular_searches(self):
        """Test getting popular searches."""
        # Add searches with repeats
        self.search_service.search("overheats")
        self.search_service.search("jams")
        self.search_service.search("temperature")
        self.search_service.search("overheats")  # Repeated
        self.search_service.search("overheats")  # Repeated again
        self.search_service.search("temperature")  # Repeated
        
        # Get popular searches
        popular = self.search_service.get_popular_searches(2)
        
        # Verify results
        self.assertEqual(len(popular), 2)
        self.assertEqual(popular[0][0], "overheats")  # Most popular
        self.assertEqual(popular[0][1], 3)           # Used 3 times
        self.assertEqual(popular[1][0], "temperature")  # Second most popular
        self.assertEqual(popular[1][1], 2)           # Used 2 times
    
    def test_search_suggestions(self):
        """Test search suggestions."""
        # Setup storage to return all rules
        self.storage_service.load_rules.return_value = self.test_rules
        
        # Add some searches for history
        self.search_service.search("overheats")
        self.search_service.search("cooling system")
        self.search_service.search("maintenance")
        
        # Test with partial query matching recent search
        suggestions = self.search_service.get_search_suggestions("over")
        self.assertIn("overheats", suggestions)
        
        # Test with empty query (should return popular searches)
        empty_suggestions = self.search_service.get_search_suggestions("")
        self.assertEqual(len(empty_suggestions), 3)  # Should return all 3 recent searches
        
        # Test with no matches in recent searches but matches in rules
        self.search_service.clear_recent_searches()
        rule_suggestions = self.search_service.get_search_suggestions("temp")
        self.assertGreaterEqual(len(rule_suggestions), 1)
    
    def test_related_searches(self):
        """Test related searches."""
        # Add searches with related terms
        self.search_service.search("machine overheating")
        self.search_service.search("cooling system repair")
        self.search_service.search("temperature control")
        
        # Test finding related searches
        related = self.search_service.get_related_searches("cooling temperature")
        
        # Should find "cooling system repair" and "temperature control" as related
        self.assertEqual(len(related), 2)
        self.assertIn("cooling system repair", related)
        self.assertIn("temperature control", related)
        
        # Test with no related searches
        no_related = self.search_service.get_related_searches("unique query with no relation")
        self.assertEqual(len(no_related), 0)
    
    def test_create_search_summary(self):
        """Test creating search summary."""
        # Test with mixed rule types
        summary = self.search_service.create_search_summary(self.test_rules, "test query", {"filter": "all"})
        
        # Verify summary structure
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["query"], "test query")
        self.assertEqual(summary["type_counts"]["Pathway"], 1)  # One pathway rule
        self.assertEqual(summary["type_counts"]["Capture"], 3)  # Three capture rules
        self.assertGreaterEqual(summary["recently_used"], 3)  # At least 3 used in last 30 days
        
        # Verify latest use date
        self.assertIsNotNone(summary["latest_use"])
    
    def test_get_date_range_options(self):
        """Test getting date range options."""
        options = self.search_service.get_date_range_options()
        
        # Verify all expected options are present
        self.assertIn("today", options)
        self.assertIn("this_week", options)
        self.assertIn("last_30_days", options)
        
        # Verify structure of an option
        today_option = options["today"]
        self.assertEqual(today_option["label"], "Today")
        self.assertIn("from", today_option)
        self.assertIn("to", today_option)
        
        # Test date format
        from_date = today_option["from"]
        try:
            datetime.fromisoformat(from_date)
        except ValueError:
            self.fail("Date format is not valid ISO format")
