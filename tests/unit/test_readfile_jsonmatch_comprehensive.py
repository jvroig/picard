"""
CRITICAL Comprehensive Tests for ReadFileJsonMatchScorer

This file fills the 58% coverage gap in readfile_jsonmatch.py, focusing on:
1. Deep JSON comparison edge cases (core algorithm validation) 
2. JSON parsing error handling (prevent crashes with malformed JSON)
3. Difference detection accuracy (essential for debugging failed tests)
4. Type coercion edge cases (string vs number scenarios)
5. Performance with large/complex JSON files

These tests are critical for PICARD's "deterministic scoring" promise.
Without them, scoring could give wrong results or crash on edge cases.
"""

import pytest
import json
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from scoring_types.readfile_jsonmatch import ReadFileJsonMatchScorer
from scorer import ScoringResult


class TestReadFileJsonMatchComprehensive:
    """Comprehensive tests for ReadFileJsonMatchScorer covering critical edge cases."""
    
    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return ReadFileJsonMatchScorer()
    
    @pytest.fixture
    def temp_artifacts_dir(self):
        """Create temporary test artifacts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "test_artifacts"
            artifacts_dir.mkdir()
            yield artifacts_dir
    
    def create_json_file(self, artifacts_dir: Path, filename: str, data, encoding='utf-8', write_mode='w'):
        """Helper to create JSON files with specific content and encoding."""
        file_path = artifacts_dir / filename
        with open(file_path, write_mode, encoding=encoding) as f:
            if isinstance(data, str):
                f.write(data)  # Raw string for malformed JSON testing
            else:
                json.dump(data, f)
        return file_path
    
    def create_precheck_entry(self, file_to_read: str, expected_content: str, question_id=1, sample_number=1):
        """Helper to create precheck entries."""
        return {
            'question_id': question_id,
            'sample_number': sample_number,
            'file_to_read': file_to_read,
            'expected_content': expected_content
        }


class TestJSONParsingEdgeCases(TestReadFileJsonMatchComprehensive):
    """Test JSON parsing error handling - prevents crashes with malformed JSON."""
    
    def test_invalid_expected_json_malformed_syntax(self, scorer, temp_artifacts_dir):
        """Test malformed expected JSON with syntax errors."""
        # Create valid actual file
        self.create_json_file(temp_artifacts_dir, "output.json", {"key": "value"})
        
        # Malformed expected JSON - missing quotes around key
        expected_json = '{key: "value"}'  # Invalid JSON syntax
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "Invalid expected JSON" in result.error_message
        assert "parse_error" in result.details
        assert result.details["parse_error"] == "expected_json"
    
    def test_invalid_expected_json_incomplete(self, scorer, temp_artifacts_dir):
        """Test incomplete expected JSON."""
        self.create_json_file(temp_artifacts_dir, "output.json", {"key": "value"})
        
        # Incomplete JSON - missing closing brace
        expected_json = '{"key": "value"'
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "Invalid expected JSON" in result.error_message
        assert result.details["expected_content"] == expected_json
    
    def test_invalid_actual_json_malformed_file(self, scorer, temp_artifacts_dir):
        """Test when actual file contains invalid JSON."""
        # Create file with malformed JSON
        self.create_json_file(temp_artifacts_dir, "output.json", '{"key": value}', write_mode='w')  # Raw string
        
        expected_json = '{"key": "value"}'
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert result.details["parse_error"] == "actual_json"
        assert result.details["expected_json"] == {"key": "value"}
        assert "actual_content" in result.details
    
    def test_invalid_actual_json_empty_file(self, scorer, temp_artifacts_dir):
        """Test when actual file is empty."""
        # Create empty file
        file_path = temp_artifacts_dir / "output.json"
        file_path.touch()
        
        expected_json = '{"key": "value"}'
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert result.details["actual_content"] == ""
    
    def test_json_with_unicode_characters(self, scorer, temp_artifacts_dir):
        """Test JSON with unicode characters."""
        unicode_data = {"message": "Hello 世界", "emoji": "🚀", "currency": "€100"}
        self.create_json_file(temp_artifacts_dir, "output.json", unicode_data)
        
        expected_json = json.dumps(unicode_data, ensure_ascii=False)
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        assert result.details["expected_json"] == unicode_data
        assert result.details["actual_json"] == unicode_data
    
    def test_json_with_escape_sequences(self, scorer, temp_artifacts_dir):
        """Test JSON with various escape sequences."""
        escape_data = {
            "newline": "line1\nline2",
            "tab": "col1\tcol2", 
            "quote": 'He said "Hello"',
            "backslash": "path\\to\\file",
            "unicode": "\u00e9\u00e7\u00e0"
        }
        self.create_json_file(temp_artifacts_dir, "output.json", escape_data)
        
        expected_json = json.dumps(escape_data)
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct


class TestDeepJSONComparisonLogic(TestReadFileJsonMatchComprehensive):
    """Test core JSON comparison algorithm - critical for correct scoring."""
    
    def test_deep_json_compare_type_mismatches(self, scorer, temp_artifacts_dir):
        """Test type mismatches in JSON comparison."""
        # String vs number
        actual_data = {"age": "25"}  # String
        expected_data = {"age": 25}   # Number
        
        self.create_json_file(temp_artifacts_dir, "output.json", actual_data)
        expected_json = json.dumps(expected_data)
        precheck_entry = self.create_precheck_entry("output.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "JSON structures do not match" in result.error_message
        assert "differences" in result.details
        assert any("Expected int, got str" in diff for diff in result.details["differences"])
    
    def test_deep_json_compare_boolean_edge_cases(self, scorer, temp_artifacts_dir):
        """Test boolean comparison edge cases."""
        test_cases = [
            # (actual, expected, should_match)
            ({"flag": True}, {"flag": "true"}, False),     # bool vs string
            ({"flag": True}, {"flag": 1}, False),         # bool vs number  
            ({"flag": False}, {"flag": 0}, False),        # bool vs number
            ({"flag": True}, {"flag": True}, True),       # bool vs bool
            ({"flag": None}, {"flag": False}, False),     # null vs bool
        ]
        
        for i, (actual_data, expected_data, should_match) in enumerate(test_cases):
            self.create_json_file(temp_artifacts_dir, f"output_{i}.json", actual_data)
            expected_json = json.dumps(expected_data)
            precheck_entry = self.create_precheck_entry(f"output_{i}.json", expected_json)
            
            result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
            
            assert result.correct == should_match, f"Test case {i} failed: {actual_data} vs {expected_data}"
    
    def test_deep_json_compare_null_handling(self, scorer, temp_artifacts_dir):
        """Test null value handling in comparisons."""
        test_cases = [
            # (actual, expected, should_match)
            ({"value": None}, {"value": None}, True),
            ({"value": None}, {"value": "null"}, False),    # null vs string "null"
            ({"value": None}, {"value": 0}, False),         # null vs zero
            ({"value": None}, {"value": False}, False),     # null vs false
            ({"value": None}, {}, False),                   # null vs missing key
            ({}, {"value": None}, False),                   # missing key vs null
        ]
        
        for i, (actual_data, expected_data, should_match) in enumerate(test_cases):
            self.create_json_file(temp_artifacts_dir, f"null_test_{i}.json", actual_data)
            expected_json = json.dumps(expected_data)
            precheck_entry = self.create_precheck_entry(f"null_test_{i}.json", expected_json)
            
            result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
            
            assert result.correct == should_match, f"Null test case {i} failed: {actual_data} vs {expected_data}"
    
    def test_deep_json_compare_nested_objects(self, scorer, temp_artifacts_dir):
        """Test deeply nested object comparison."""
        actual_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep_value",
                            "number": 42
                        }
                    }
                }
            }
        }
        
        # Test exact match
        self.create_json_file(temp_artifacts_dir, "nested_match.json", actual_data)
        expected_json = json.dumps(actual_data)
        precheck_entry = self.create_precheck_entry("nested_match.json", expected_json)
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        assert result.correct
        
        # Test deep difference - need deep copy to modify nested structure
        import copy
        expected_different = copy.deepcopy(actual_data)
        expected_different["level1"]["level2"]["level3"]["level4"]["value"] = "different_value"
        
        self.create_json_file(temp_artifacts_dir, "nested_diff.json", actual_data)
        expected_json = json.dumps(expected_different)
        precheck_entry = self.create_precheck_entry("nested_diff.json", expected_json)
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "level1.level2.level3.level4.value" in str(result.details["differences"])
    
    def test_deep_json_compare_array_order_sensitivity(self, scorer, temp_artifacts_dir):
        """Test that array order matters in comparison."""
        actual_data = {"numbers": [1, 2, 3, 4, 5]}
        expected_different_order = {"numbers": [5, 4, 3, 2, 1]}
        
        self.create_json_file(temp_artifacts_dir, "array_order.json", actual_data)
        expected_json = json.dumps(expected_different_order)
        precheck_entry = self.create_precheck_entry("array_order.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "differences" in result.details
        # Should detect differences at multiple array positions
        differences_str = str(result.details["differences"])
        assert "[0]" in differences_str  # First element differs
        assert "[4]" in differences_str  # Last element differs
    
    def test_deep_json_compare_mixed_array_types(self, scorer, temp_artifacts_dir):
        """Test arrays with mixed data types."""
        actual_data = {"mixed": [1, "string", {"key": "value"}, None, True, [1, 2, 3]]}
        
        # Test exact match
        self.create_json_file(temp_artifacts_dir, "mixed_array.json", actual_data)
        expected_json = json.dumps(actual_data)
        precheck_entry = self.create_precheck_entry("mixed_array.json", expected_json)
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        assert result.correct
        
        # Test with type change in array
        expected_different = {"mixed": [1, "string", {"key": "different"}, None, True, [1, 2, 3]]}
        expected_json = json.dumps(expected_different)
        precheck_entry = self.create_precheck_entry("mixed_array.json", expected_json)
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "mixed[2].key" in str(result.details["differences"])


class TestDifferenceDetectionEngine(TestReadFileJsonMatchComprehensive):
    """Test difference reporting logic - essential for debugging failed tests."""
    
    def test_find_json_differences_missing_keys(self, scorer, temp_artifacts_dir):
        """Test detection of missing keys in objects."""
        actual_data = {"key1": "value1"}
        expected_data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        
        self.create_json_file(temp_artifacts_dir, "missing_keys.json", actual_data)
        expected_json = json.dumps(expected_data)
        precheck_entry = self.create_precheck_entry("missing_keys.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        differences = result.details["differences"]
        
        # Should identify missing keys
        missing_keys_diff = next(diff for diff in differences if "Missing keys" in diff)
        assert "key2" in missing_keys_diff
        assert "key3" in missing_keys_diff
    
    def test_find_json_differences_extra_keys(self, scorer, temp_artifacts_dir):
        """Test detection of extra keys in objects."""
        actual_data = {"key1": "value1", "key2": "value2", "extra1": "extra", "extra2": "also_extra"}
        expected_data = {"key1": "value1", "key2": "value2"}
        
        self.create_json_file(temp_artifacts_dir, "extra_keys.json", actual_data)
        expected_json = json.dumps(expected_data)
        precheck_entry = self.create_precheck_entry("extra_keys.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        differences = result.details["differences"]
        
        # Should identify extra keys
        extra_keys_diff = next(diff for diff in differences if "Extra keys" in diff)
        assert "extra1" in extra_keys_diff
        assert "extra2" in extra_keys_diff
    
    def test_find_json_differences_array_length_mismatch(self, scorer, temp_artifacts_dir):
        """Test array length mismatch detection."""
        actual_data = {"items": [1, 2, 3]}
        expected_data = {"items": [1, 2, 3, 4, 5]}
        
        self.create_json_file(temp_artifacts_dir, "array_length.json", actual_data)
        expected_json = json.dumps(expected_data)
        precheck_entry = self.create_precheck_entry("array_length.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        differences = result.details["differences"]
        
        # Should identify length mismatch
        length_diff = next(diff for diff in differences if "Expected array length 5, got 3" in diff)
        assert "items" in length_diff
    
    def test_find_json_differences_complex_path_reporting(self, scorer, temp_artifacts_dir):
        """Test accurate path reporting for nested differences."""
        actual_data = {
            "users": [
                {"id": 1, "profile": {"name": "John", "settings": {"theme": "dark"}}},
                {"id": 2, "profile": {"name": "Jane", "settings": {"theme": "light"}}}
            ]
        }
        
        expected_data = {
            "users": [
                {"id": 1, "profile": {"name": "John", "settings": {"theme": "dark"}}},
                {"id": 2, "profile": {"name": "Jane", "settings": {"theme": "dark"}}}  # Changed theme
            ]
        }
        
        self.create_json_file(temp_artifacts_dir, "complex_path.json", actual_data)
        expected_json = json.dumps(expected_data)
        precheck_entry = self.create_precheck_entry("complex_path.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        differences = result.details["differences"]
        
        # Should identify exact path to difference
        theme_diff = next(diff for diff in differences if "users[1].profile.settings.theme" in diff)
        assert "Expected dark, got light" in theme_diff


class TestFilePathResolutionEdgeCases(TestReadFileJsonMatchComprehensive):
    """Test smart file path resolution logic."""
    
    def test_resolve_file_path_absolute_paths(self, scorer, temp_artifacts_dir):
        """Test absolute path resolution."""
        # Create file with absolute path
        absolute_file = temp_artifacts_dir / "absolute_test.json"
        self.create_json_file(temp_artifacts_dir, "absolute_test.json", {"test": "absolute"})
        
        expected_json = '{"test": "absolute"}'
        precheck_entry = self.create_precheck_entry(str(absolute_file), expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        assert result.details["expected_file"] == str(absolute_file)
    
    def test_resolve_file_path_test_artifacts_prefix(self, scorer, temp_artifacts_dir):
        """Test test_artifacts/ prefix removal."""
        self.create_json_file(temp_artifacts_dir, "prefixed_test.json", {"test": "prefix"})
        
        # Use path with test_artifacts/ prefix
        file_path_with_prefix = "test_artifacts/prefixed_test.json"
        expected_json = '{"test": "prefix"}'
        precheck_entry = self.create_precheck_entry(file_path_with_prefix, expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        # Should resolve to the actual file location
        expected_resolved = str(temp_artifacts_dir / "prefixed_test.json")
        assert result.details["expected_file"] == expected_resolved
    
    def test_resolve_file_path_nested_directories(self, scorer, temp_artifacts_dir):
        """Test nested directory path resolution."""
        # Create nested directory structure
        nested_dir = temp_artifacts_dir / "subdir" / "nested"
        nested_dir.mkdir(parents=True)
        
        nested_file = nested_dir / "nested_test.json"
        with open(nested_file, 'w') as f:
            json.dump({"test": "nested"}, f)
        
        # Test relative path resolution
        relative_path = "subdir/nested/nested_test.json"
        expected_json = '{"test": "nested"}'
        precheck_entry = self.create_precheck_entry(relative_path, expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        assert result.details["expected_file"] == str(nested_file)


class TestPerformanceAndLargeFiles(TestReadFileJsonMatchComprehensive):
    """Test performance with large and complex JSON files."""
    
    def test_large_json_file_performance(self, scorer, temp_artifacts_dir):
        """Test performance with large JSON files (10K+ elements)."""
        # Create large JSON structure
        large_data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "profile": {
                        "age": 20 + (i % 50),
                        "preferences": {
                            "theme": "dark" if i % 2 == 0 else "light",
                            "notifications": i % 3 == 0,
                            "tags": [f"tag{j}" for j in range(i % 5)]
                        }
                    }
                }
                for i in range(1000)  # 1000 users with nested data
            ],
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01",
                "stats": {
                    "total_users": 1000,
                    "active_users": 850,
                    "categories": list(range(100))
                }
            }
        }
        
        self.create_json_file(temp_artifacts_dir, "large_file.json", large_data)
        expected_json = json.dumps(large_data)
        precheck_entry = self.create_precheck_entry("large_file.json", expected_json)
        
        # Measure performance (should complete in reasonable time)
        import time
        start_time = time.time()
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        end_time = time.time()
        
        assert result.correct
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert len(result.details["actual_json"]["users"]) == 1000
    
    def test_deeply_nested_json_structure(self, scorer, temp_artifacts_dir):
        """Test very deeply nested JSON structures."""
        # Create 20-level deep nesting
        def create_deep_structure(depth):
            if depth == 0:
                return {"leaf_value": f"depth_{depth}", "leaf_number": depth}
            return {
                f"level_{depth}": create_deep_structure(depth - 1),
                "current_depth": depth,
                "metadata": {"level": depth, "remaining": 20 - depth}
            }
        
        deep_data = create_deep_structure(20)
        
        self.create_json_file(temp_artifacts_dir, "deep_nested.json", deep_data)
        expected_json = json.dumps(deep_data)
        precheck_entry = self.create_precheck_entry("deep_nested.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        # Verify deep access works
        current = result.details["actual_json"]
        for i in range(20, 0, -1):
            assert f"level_{i}" in current
            assert current["current_depth"] == i
            if i > 1:
                current = current[f"level_{i}"]
    
    def test_json_floating_point_precision(self, scorer, temp_artifacts_dir):
        """Test floating point precision edge cases."""
        precision_data = {
            "pi": 3.14159265359,
            "e": 2.71828182846,
            "very_small": 1e-10,
            "very_large": 1.23456789e15,
            "negative_zero": -0.0,
            "positive_zero": 0.0,
            "infinity_test": float('inf') if scorer else 999999999,  # JSON doesn't support inf
            "scientific": 1.23e-4
        }
        
        # Handle infinity case for JSON serialization
        json_safe_data = precision_data.copy()
        if 'infinity_test' in json_safe_data and json_safe_data['infinity_test'] == float('inf'):
            json_safe_data['infinity_test'] = 999999999
        
        self.create_json_file(temp_artifacts_dir, "precision.json", json_safe_data)
        expected_json = json.dumps(json_safe_data)
        precheck_entry = self.create_precheck_entry("precision.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        # Verify precision is maintained
        assert abs(result.details["actual_json"]["pi"] - 3.14159265359) < 1e-10
        assert abs(result.details["actual_json"]["e"] - 2.71828182846) < 1e-10


class TestErrorRecoveryAndEdgeCases(TestReadFileJsonMatchComprehensive):
    """Test error handling and edge case recovery."""
    
    def test_file_permissions_simulation(self, scorer, temp_artifacts_dir):
        """Simulate file permission issues (where possible)."""
        # Create file then make it harder to read by creating invalid JSON that causes other errors
        self.create_json_file(temp_artifacts_dir, "permission_test.json", "invalid json content")
        
        expected_json = '{"test": "permission"}'
        precheck_entry = self.create_precheck_entry("permission_test.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert result.details["file_exists"] is True
    
    def test_empty_json_file_edge_case(self, scorer, temp_artifacts_dir):
        """Test completely empty JSON file."""
        # Create empty file
        empty_file = temp_artifacts_dir / "empty.json"
        empty_file.touch()
        
        expected_json = '{"should": "not_match"}'
        precheck_entry = self.create_precheck_entry("empty.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert result.details["actual_content"] == ""
        assert result.details["expected_json"] == {"should": "not_match"}
    
    def test_json_file_with_only_whitespace(self, scorer, temp_artifacts_dir):
        """Test JSON file containing only whitespace."""
        whitespace_file = temp_artifacts_dir / "whitespace.json"
        with open(whitespace_file, 'w') as f:
            f.write("   \n\t\r\n   ")  # Various whitespace characters
        
        expected_json = '{"should": "not_match"}'
        precheck_entry = self.create_precheck_entry("whitespace.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert result.details["actual_content"].strip() == ""
    
    def test_json_with_different_encodings(self, scorer, temp_artifacts_dir):
        """Test JSON files with different text encodings."""
        unicode_data = {"message": "Café naïve résumé", "price": "€50"}
        
        # Test UTF-8 with BOM
        utf8_bom_file = temp_artifacts_dir / "utf8_bom.json"
        with open(utf8_bom_file, 'wb') as f:
            # Write UTF-8 BOM followed by JSON
            f.write(b'\xef\xbb\xbf')
            f.write(json.dumps(unicode_data).encode('utf-8'))
        
        expected_json = json.dumps(unicode_data)
        precheck_entry = self.create_precheck_entry("utf8_bom.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        # Current implementation doesn't handle UTF-8 BOM properly (this is a limitation)
        # The test documents this behavior - JSON parser fails with BOM
        assert not result.correct
        assert "File contains invalid JSON" in result.error_message
        assert "Unexpected UTF-8 BOM" in result.error_message
        assert result.details["actual_content"].startswith('\ufeff')  # BOM character present
    
    def test_json_number_edge_cases(self, scorer, temp_artifacts_dir):
        """Test various number format edge cases."""
        number_data = {
            "integer": 42,
            "negative": -17,
            "zero": 0,
            "float": 3.14,
            "scientific": 1.23e-4,
            "large_int": 9223372036854775807,  # Near max int64
            "small_float": 1.175494e-38
        }
        
        self.create_json_file(temp_artifacts_dir, "numbers.json", number_data)
        expected_json = json.dumps(number_data)
        precheck_entry = self.create_precheck_entry("numbers.json", expected_json)
        
        result = scorer.score(precheck_entry, {}, temp_artifacts_dir)
        
        assert result.correct
        # Verify number types are preserved
        actual_data = result.details["actual_json"]
        assert isinstance(actual_data["integer"], int)
        assert isinstance(actual_data["float"], float)
        assert actual_data["large_int"] == 9223372036854775807


if __name__ == "__main__":
    # Run a quick smoke test
    scorer = ReadFileJsonMatchScorer()
    print("✅ ReadFileJsonMatchScorer comprehensive tests ready to run!")
    print("Run with: pytest tests/unit/test_readfile_jsonmatch_comprehensive.py -v")