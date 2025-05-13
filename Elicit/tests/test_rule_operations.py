import unittest
from services.search_service import SearchService
from models.rule import Rule

class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.search_service = SearchService()
        
        # Create test rules
        self.rules = [
            Rule(
                text="IF machine overheats, THEN check cooling system",
                conditions=[{"param": "machine", "operator": "=", "value": "overheats"}],
                actions=[{"type": "check", "target": "cooling system", "sequence": 1}],
                metadata={"problem_type": "Machine Stoppage"}
            ),
            Rule(
                text="IF product has defects, THEN inspect tooling",
                conditions=[{"param": "product", "operator": "has", "value": "defects"}],
                actions=[{"type": "inspect", "target": "tooling", "sequence": 1}],
                metadata={"problem_type": "Quality Issue"}
            ),
            Rule(
                text="IF material jams, THEN clean feed mechanism",
                conditions=[{"param": "material", "operator": "=", "value": "jams"}],
                actions=[{"type": "clean", "target": "feed mechanism", "sequence": 1}],
                metadata={"problem_type": "Material Handling"}
            )
        ]
    
    def test_search_by_text(self):
        """Test searching rules by text."""
        results = self.search_service.search_by_text(self.rules, "overheat")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "IF machine overheats, THEN check cooling system")
    
    def test_search_by_metadata(self):
        """Test searching rules by metadata."""
        results = self.search_service.search_by_metadata(self.rules, "Quality Issue")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["problem_type"], "Quality Issue")
    
    def test_search_by_condition(self):
        """Test searching rules by condition."""
        results = self.search_service.search_by_condition(self.rules, "material")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "IF material jams, THEN clean feed mechanism")
    
    def test_search_by_action(self):
        """Test searching rules by action."""
        results = self.search_service.search_by_action(self.rules, "inspect")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "IF product has defects, THEN inspect tooling")
    
    def test_search_all(self):
        """Test comprehensive search."""
        results = self.search_service.search(self.rules, "machine", include_metadata=True)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "IF machine overheats, THEN check cooling system")