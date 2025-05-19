import unittest
import sys
import os

# Add the parent directory to path so we can import from the main package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Run all tests."""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    return result

if __name__ == "__main__":
    result = run_tests()
    #sys.exit(not result.wasSuccessful())