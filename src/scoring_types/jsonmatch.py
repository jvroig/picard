"""
JSON Match Scorer - Direct JSON response matching

Compares JSON responses semantically rather than as strings,
handling formatting differences, key ordering, and whitespace.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class JsonMatchScorer(BaseScoringType):
    """Scorer for jsonmatch scoring type - semantic JSON comparison."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on semantic JSON matching (structure and values)."""
        expected_response = precheck_entry.get('expected_response', '').strip()
        actual_response = response_entry.get('response_text', '').strip()
        
        # Parse expected JSON
        try:
            expected_json = json.loads(expected_response)
        except json.JSONDecodeError as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='jsonmatch',
                correct=False,
                error_message=f"Invalid expected JSON: {e}",
                details={
                    'expected_raw': expected_response,
                    'actual_raw': actual_response,
                    'parse_error': 'expected_json'
                }
            )
        
        # Parse actual JSON
        try:
            actual_json = json.loads(actual_response)
        except json.JSONDecodeError as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='jsonmatch',
                correct=False,
                error_message=f"LLM response is not valid JSON: {e}",
                details={
                    'expected_raw': expected_response,
                    'actual_raw': actual_response,
                    'expected_json': expected_json,
                    'parse_error': 'actual_json'
                }
            )
        
        # Compare JSON structures semantically
        correct = self._deep_json_compare(expected_json, actual_json)
        
        details = {
            'expected_raw': expected_response,
            'actual_raw': actual_response,
            'expected_json': expected_json,
            'actual_json': actual_json,
            'comparison_method': 'semantic_json_match'
        }
        
        error_message = None
        if not correct:
            error_message = f"JSON structures do not match"
            details['differences'] = self._find_json_differences(expected_json, actual_json)
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='jsonmatch',
            correct=correct,
            error_message=error_message,
            details=details
        )
    
    def _deep_json_compare(self, expected, actual):
        """
        Deep comparison of JSON structures.
        
        Args:
            expected: Expected JSON object (parsed)
            actual: Actual JSON object (parsed)
            
        Returns:
            True if structures match semantically
        """
        # Handle different types
        if type(expected) != type(actual):
            return False
        
        # Handle None
        if expected is None:
            return actual is None
        
        # Handle primitives (str, int, float, bool)
        if isinstance(expected, (str, int, float, bool)):
            return expected == actual
        
        # Handle lists
        if isinstance(expected, list):
            if len(expected) != len(actual):
                return False
            
            # Compare each element (order matters for lists)
            for i in range(len(expected)):
                if not self._deep_json_compare(expected[i], actual[i]):
                    return False
            return True
        
        # Handle dictionaries
        if isinstance(expected, dict):
            if set(expected.keys()) != set(actual.keys()):
                return False
            
            # Compare each key-value pair (order doesn't matter for dicts)
            for key in expected.keys():
                if not self._deep_json_compare(expected[key], actual[key]):
                    return False
            return True
        
        # Unknown type - fallback to equality
        return expected == actual
    
    def _find_json_differences(self, expected, actual, path="root"):
        """
        Find specific differences between JSON structures for debugging.
        
        Args:
            expected: Expected JSON object
            actual: Actual JSON object
            path: Current path in the JSON structure
            
        Returns:
            List of difference descriptions
        """
        differences = []
        
        # Type mismatch
        if type(expected) != type(actual):
            differences.append(f"{path}: Expected {type(expected).__name__}, got {type(actual).__name__}")
            return differences
        
        # None handling
        if expected is None:
            if actual is not None:
                differences.append(f"{path}: Expected null, got {actual}")
            return differences
        
        # Primitives
        if isinstance(expected, (str, int, float, bool)):
            if expected != actual:
                differences.append(f"{path}: Expected {expected}, got {actual}")
            return differences
        
        # Lists
        if isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append(f"{path}: Expected array length {len(expected)}, got {len(actual)}")
            
            min_len = min(len(expected), len(actual))
            for i in range(min_len):
                differences.extend(self._find_json_differences(
                    expected[i], actual[i], f"{path}[{i}]"
                ))
            return differences
        
        # Dictionaries
        if isinstance(expected, dict):
            expected_keys = set(expected.keys())
            actual_keys = set(actual.keys())
            
            # Missing keys
            missing_keys = expected_keys - actual_keys
            if missing_keys:
                differences.append(f"{path}: Missing keys: {list(missing_keys)}")
            
            # Extra keys
            extra_keys = actual_keys - expected_keys
            if extra_keys:
                differences.append(f"{path}: Extra keys: {list(extra_keys)}")
            
            # Compare common keys
            common_keys = expected_keys & actual_keys
            for key in common_keys:
                differences.extend(self._find_json_differences(
                    expected[key], actual[key], f"{path}.{key}"
                ))
            
            return differences
        
        # Unknown type
        if expected != actual:
            differences.append(f"{path}: Expected {expected}, got {actual}")
        
        return differences
