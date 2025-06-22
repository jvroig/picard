"""
Read File JSON Match Scorer - Read JSON file and perform semantic comparison

Reads JSON content from a file and compares it semantically rather than as strings,
handling formatting differences, key ordering, and whitespace.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class ReadFileJsonMatchScorer(BaseScoringType):
    """Scorer for readfile_jsonmatch scoring type - read JSON file and compare semantically."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on reading JSON file contents and semantic comparison."""
        file_to_read = precheck_entry.get('file_to_read', '')
        expected_content = precheck_entry.get('expected_content', '').strip()
        
        if not file_to_read:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_jsonmatch',
                correct=False,
                error_message="No file_to_read specified in precheck entry"
            )
        
        # Smart path resolution - handle both relative and absolute paths
        file_path = self._resolve_file_path(file_to_read, test_artifacts_dir)
        
        # Check if file exists
        if not file_path.exists():
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_jsonmatch',
                correct=False,
                error_message=f"File does not exist: {file_path}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'file_exists': False
                }
            )
        
        # Read file contents
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                actual_content = f.read().strip()
        except Exception as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_jsonmatch',
                correct=False,
                error_message=f"Error reading file {file_path}: {e}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'file_exists': True,
                    'read_error': str(e)
                }
            )
        
        # Parse expected JSON
        try:
            expected_json = json.loads(expected_content)
        except json.JSONDecodeError as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_jsonmatch',
                correct=False,
                error_message=f"Invalid expected JSON: {e}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'actual_content': actual_content,
                    'parse_error': 'expected_json'
                }
            )
        
        # Parse actual JSON from file
        try:
            actual_json = json.loads(actual_content)
        except json.JSONDecodeError as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_jsonmatch',
                correct=False,
                error_message=f"File contains invalid JSON: {e}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'actual_content': actual_content,
                    'expected_json': expected_json,
                    'parse_error': 'actual_json',
                    'file_exists': True
                }
            )
        
        # Compare JSON structures semantically
        correct = self._deep_json_compare(expected_json, actual_json)
        
        details = {
            'expected_file': str(file_path),
            'expected_content': expected_content,
            'actual_content': actual_content,
            'expected_json': expected_json,
            'actual_json': actual_json,
            'file_exists': True,
            'comparison_method': 'semantic_json_match'
        }
        
        error_message = None
        if not correct:
            error_message = f"JSON structures do not match"
            details['differences'] = self._find_json_differences(expected_json, actual_json)
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='readfile_jsonmatch',
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
    
    def _resolve_file_path(self, file_path_str: str, test_artifacts_dir: Path) -> Path:
        """
        Resolve file path intelligently - handle both relative and absolute paths.
        
        Args:
            file_path_str: File path from precheck entry (may be relative or absolute)
            test_artifacts_dir: Test artifacts directory from scorer
            
        Returns:
            Resolved Path object
        """
        file_path = Path(file_path_str)
        
        # If it's already an absolute path, use it directly
        if file_path.is_absolute():
            return file_path
        
        # If it starts with test_artifacts/, remove that prefix and use test_artifacts_dir
        if file_path_str.startswith('test_artifacts/'):
            relative_path = file_path_str[len('test_artifacts/'):]
            return test_artifacts_dir / relative_path
        
        # Otherwise, treat it as relative to test_artifacts_dir
        return test_artifacts_dir / file_path_str
