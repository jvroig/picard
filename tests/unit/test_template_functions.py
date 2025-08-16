"""
Unit tests for TemplateFunctions.

Migrated from the main() function in src/template_functions.py
"""
import pytest
import json
import csv
import sqlite3
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from template_functions import TemplateFunctions, TemplateFunctionError


@pytest.mark.unit
@pytest.mark.template_functions
class TestFileTemplateFunctions:
    """Test file content extraction functions."""
    
    def test_file_line_extraction(self, template_functions, create_text_file):
        """Test {{file_line:N:path}} function."""
        lines = ["First line", "Second line", "Third line with data", "Fourth line", "Last line"]
        text_file = create_text_file("test.txt", lines)
        
        # Test various line extractions
        result = template_functions.evaluate_all_functions(f"{{{{file_line:3:{text_file}}}}}")
        assert result == "Third line with data"
        
        result = template_functions.evaluate_all_functions(f"{{{{file_line:1:{text_file}}}}}")
        assert result == "First line"
        
        result = template_functions.evaluate_all_functions(f"{{{{file_line:5:{text_file}}}}}")
        assert result == "Last line"
    
    def test_file_word_extraction(self, template_functions, create_text_file):
        """Test {{file_word:N:path}} function."""
        lines = ["Line 1", "Line 2", "Line 3"]
        text_file = create_text_file("test.txt", lines)
        
        # First word should be "Line"
        result = template_functions.evaluate_all_functions(f"{{{{file_word:1:{text_file}}}}}")
        assert result == "Line"
        
        # Fourth word should be "2"
        result = template_functions.evaluate_all_functions(f"{{{{file_word:4:{text_file}}}}}")
        assert result == "2"
    
    def test_file_counts(self, template_functions, create_text_file):
        """Test file_line_count and file_word_count functions."""
        lines = ["First line with multiple words", "Second line", "Third"]
        text_file = create_text_file("test.txt", lines)
        
        # Line count
        result = template_functions.evaluate_all_functions(f"{{{{file_line_count:{text_file}}}}}")
        assert result == "3"
        
        # Word count: "First line with multiple words" (5) + "Second line" (2) + "Third" (1) = 8 words
        result = template_functions.evaluate_all_functions(f"{{{{file_word_count:{text_file}}}}}")
        assert result == "8"
    
    def test_file_function_errors(self, template_functions, create_text_file):
        """Test error handling for file functions."""
        text_file = create_text_file("test.txt", ["Line 1", "Line 2"])
        
        # Line out of range
        with pytest.raises(TemplateFunctionError, match="Line number 5 out of range"):
            template_functions.evaluate_all_functions(f"{{{{file_line:5:{text_file}}}}}")
        
        # Word out of range  
        with pytest.raises(TemplateFunctionError, match="Word number 10 out of range"):
            template_functions.evaluate_all_functions(f"{{{{file_word:10:{text_file}}}}}")


@pytest.mark.unit
@pytest.mark.template_functions
class TestCSVTemplateFunctions:
    """Test CSV extraction functions."""
    
    def test_csv_cell_extraction(self, template_functions, create_csv_file):
        """Test {{csv_cell:row:column:path}} function."""
        csv_file = create_csv_file("test.csv")
        
        # Extract specific cells (0-indexed)
        result = template_functions.evaluate_all_functions(f"{{{{csv_cell:1:1:{csv_file}}}}}")
        assert result == "John Doe"  # Row 1, Column 1 (name)
        
        result = template_functions.evaluate_all_functions(f"{{{{csv_cell:2:2:{csv_file}}}}}")
        assert result == "30"  # Row 2, Column 2 (age)
    
    def test_csv_row_extraction(self, template_functions, create_csv_file):
        """Test {{csv_row:N:path}} function."""
        csv_file = create_csv_file("test.csv")
        
        # Extract entire row
        result = template_functions.evaluate_all_functions(f"{{{{csv_row:1:{csv_file}}}}}")
        assert result == "1,John Doe,25,New York,active"
    
    def test_csv_column_extraction(self, template_functions, create_csv_file):
        """Test {{csv_column:header:path}} function."""
        csv_file = create_csv_file("test.csv")
        
        # Extract entire column by header
        result = template_functions.evaluate_all_functions(f"{{{{csv_column:name:{csv_file}}}}}")
        assert result == "John Doe,Jane Smith,Bob Johnson,Alice Brown"
        
        result = template_functions.evaluate_all_functions(f"{{{{csv_column:age:{csv_file}}}}}")
        assert result == "25,30,35,28"
    
    def test_csv_value_extraction(self, template_functions, create_csv_file):
        """Test {{csv_value:row:header:path}} function."""
        csv_file = create_csv_file("test.csv")
        
        # Extract by row and column header
        result = template_functions.evaluate_all_functions(f"{{{{csv_value:0:name:{csv_file}}}}}")
        assert result == "John Doe"
        
        result = template_functions.evaluate_all_functions(f"{{{{csv_value:2:city:{csv_file}}}}}")
        assert result == "Chicago"
    
    def test_csv_aggregation_functions(self, template_functions, create_csv_file):
        """Test CSV aggregation functions (sum, avg, count)."""
        csv_file = create_csv_file("test.csv")
        
        # Sum ages: 25+30+35+28 = 118
        result = template_functions.evaluate_all_functions(f"{{{{csv_sum:age:{csv_file}}}}}")
        assert result == "118.0"
        
        # Average age: 118/4 = 29.5
        result = template_functions.evaluate_all_functions(f"{{{{csv_avg:age:{csv_file}}}}}")
        assert result == "29.5"
        
        # Count names (non-empty values)
        result = template_functions.evaluate_all_functions(f"{{{{csv_count:name:{csv_file}}}}}")
        assert result == "4"
    
    def test_csv_filtered_aggregation(self, template_functions, create_csv_file):
        """Test CSV filtered aggregation functions."""
        csv_file = create_csv_file("test.csv")
        
        # Sum ages where status is active (John: 25, Bob: 35, Alice: 28 = 88)
        result = template_functions.evaluate_all_functions(f"{{{{csv_sum_where:age:status:==:active:{csv_file}}}}}")
        assert result == "88.0"
        
        # Average age where status is active: 88/3 = 29.33...
        result = template_functions.evaluate_all_functions(f"{{{{csv_avg_where:age:status:==:active:{csv_file}}}}}")
        assert float(result) == pytest.approx(29.33, abs=0.1)
        
        # Count people where status contains 'active'
        result = template_functions.evaluate_all_functions(f"{{{{csv_count_where:name:status:==:active:{csv_file}}}}}")
        assert result == "3"
    
    def test_csv_function_errors(self, template_functions, create_csv_file):
        """Test error handling for CSV functions.""" 
        csv_file = create_csv_file("test.csv")
        
        # Invalid column header
        with pytest.raises(TemplateFunctionError, match="Header 'nonexistent' not found"):
            template_functions.evaluate_all_functions(f"{{{{csv_column:nonexistent:{csv_file}}}}}")
        
        # Row out of range
        with pytest.raises(TemplateFunctionError, match="Row 10 out of range"):
            template_functions.evaluate_all_functions(f"{{{{csv_cell:10:0:{csv_file}}}}}")


@pytest.mark.unit
@pytest.mark.template_functions
class TestJSONTemplateFunctions:
    """Test JSON extraction functions."""
    
    def test_json_path_extraction(self, template_functions, create_json_file):
        """Test {{json_path:$.path:file}} function."""
        json_file = create_json_file("test.json")
        
        # Extract user array elements
        result = template_functions.evaluate_all_functions(f"{{{{json_path:$.users[0].name:{json_file}}}}}")
        assert result == "John"
        
        result = template_functions.evaluate_all_functions(f"{{{{json_path:$.users[1].age:{json_file}}}}}")
        assert result == "30"
        
        # Extract nested metadata
        result = template_functions.evaluate_all_functions(f"{{{{json_path:$.metadata.total:{json_file}}}}}")
        assert result == "3"
    
    def test_json_value_extraction(self, template_functions, create_json_file):
        """Test {{json_value:key.path:file}} function."""
        json_file = create_json_file("test.json")
        
        # Simple key navigation
        result = template_functions.evaluate_all_functions(f"{{{{json_value:metadata.total:{json_file}}}}}")
        assert result == "3"
        
        result = template_functions.evaluate_all_functions(f"{{{{json_value:config.settings.debug:{json_file}}}}}")
        assert result == "True"
        
        result = template_functions.evaluate_all_functions(f"{{{{json_value:config.settings.timeout:{json_file}}}}}")
        assert result == "30"
    
    def test_json_count_function(self, template_functions, create_json_file):
        """Test {{json_count:$.path:file}} function."""
        json_file = create_json_file("test.json")
        
        # Count array elements
        result = template_functions.evaluate_all_functions(f"{{{{json_count:$.users:{json_file}}}}}")
        assert result == "3"
        
        # Count object keys
        result = template_functions.evaluate_all_functions(f"{{{{json_count:$.metadata:{json_file}}}}}")
        assert result == "3"  # total, version, created
        
        result = template_functions.evaluate_all_functions(f"{{{{json_count:$.config.settings:{json_file}}}}}")
        assert result == "3"  # debug, timeout, max_retries
    
    def test_json_keys_function(self, template_functions, create_json_file):
        """Test {{json_keys:$.path:file}} function."""
        json_file = create_json_file("test.json")
        
        # Get object keys
        result = template_functions.evaluate_all_functions(f"{{{{json_keys:$.metadata:{json_file}}}}}")
        assert result == "total,version,created"
        
        result = template_functions.evaluate_all_functions(f"{{{{json_keys:$.config.settings:{json_file}}}}}")
        assert result == "debug,timeout,max_retries"
    
    def test_json_function_errors(self, template_functions, create_json_file):
        """Test error handling for JSON functions."""
        json_file = create_json_file("test.json")
        
        # Invalid path
        with pytest.raises(TemplateFunctionError, match="Key 'nonexistent' not found"):
            template_functions.evaluate_all_functions(f"{{{{json_value:nonexistent:{json_file}}}}}")
        
        # Array index out of range
        with pytest.raises(TemplateFunctionError, match="Array index 10 out of range"):
            template_functions.evaluate_all_functions(f"{{{{json_path:$.users[10].name:{json_file}}}}}")


@pytest.mark.unit
@pytest.mark.template_functions
class TestSQLiteTemplateFunctions:
    """Test SQLite extraction functions."""
    
    @pytest.fixture
    def sqlite_file(self, temp_workspace):
        """Create a test SQLite database."""
        db_file = temp_workspace / "test.db"
        
        conn = sqlite3.connect(str(db_file))
        try:
            # Create test table
            conn.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    active BOOLEAN
                )
            """)
            
            # Insert test data
            test_data = [
                (1, "John", 25, 1),
                (2, "Alice", 30, 0),
                (3, "Bob", 35, 1)
            ]
            conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", test_data)
            conn.commit()
        finally:
            conn.close()
            
        return str(db_file)
    
    def test_sqlite_query_function(self, template_functions, sqlite_file):
        """Test {{sqlite_query:SQL:file}} function."""
        # Simple SELECT query
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_query:SELECT name FROM users WHERE id=1:{sqlite_file}}}}}")
        assert result == "John"
        
        # Count query
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_query:SELECT COUNT(*) FROM users:{sqlite_file}}}}}")
        assert result == "3"
        
        # Aggregation query
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_query:SELECT AVG(age) FROM users:{sqlite_file}}}}}")
        assert float(result) == pytest.approx(30.0)
    
    def test_sqlite_value_function(self, template_functions, sqlite_file):
        """Test {{sqlite_value:row:column:file}} function."""
        # Extract by row and column index
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_value:0:name:{sqlite_file}}}}}")
        assert result == "John"
        
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_value:1:age:{sqlite_file}}}}}")
        assert result == "30"
        
        # Extract by row and column name
        result = template_functions.evaluate_all_functions(f"{{{{sqlite_value:2:name:{sqlite_file}}}}}")
        assert result == "Bob"


@pytest.mark.unit
@pytest.mark.template_functions
class TestTemplateFunctionEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_file_error(self, template_functions):
        """Test that nonexistent files raise appropriate errors."""
        with pytest.raises(TemplateFunctionError, match="File not found"):
            template_functions.evaluate_all_functions("{{file_line:1:nonexistent.txt}}")
        
        with pytest.raises(TemplateFunctionError, match="CSV file not found"):
            template_functions.evaluate_all_functions("{{csv_cell:0:0:nonexistent.csv}}")
        
        with pytest.raises(TemplateFunctionError, match="JSON file not found"):
            template_functions.evaluate_all_functions("{{json_value:key:nonexistent.json}}")
    
    def test_invalid_function_name(self, template_functions):
        """Test that invalid function names raise errors."""
        with pytest.raises(TemplateFunctionError, match="Unknown template function"):
            template_functions.evaluate_all_functions("{{invalid_function:arg:file}}")
    
    def test_malformed_template_syntax(self, template_functions, create_text_file):
        """Test malformed template syntax."""
        text_file = create_text_file("test.txt", ["Line 1"])
        
        # Missing closing braces - should pass through unchanged
        result = template_functions.evaluate_all_functions(f"{{file_line:1:{text_file}")
        assert result == f"{{file_line:1:{text_file}"
        
        # Incomplete function call - should raise error since it matches pattern but has wrong args
        with pytest.raises(TemplateFunctionError, match="file_line requires exactly 2 arguments"):
            template_functions.evaluate_all_functions("{{file_line:1}}")


@pytest.mark.unit
@pytest.mark.template_functions 
class TestTargetFileSubstitution:
    """Test TARGET_FILE keyword substitution."""
    
    def test_target_file_substitution(self, template_functions, create_text_file):
        """Test that TARGET_FILE is properly substituted."""
        lines = ["First line", "Second line"]
        text_file = create_text_file("test.txt", lines)
        
        # Test with TARGET_FILE keyword
        result = template_functions.evaluate_all_functions("{{file_line:1:TARGET_FILE}}", text_file)
        assert result == "First line"
        
        result = template_functions.evaluate_all_functions("{{file_line_count:TARGET_FILE}}", text_file)
        assert result == "2"


@pytest.mark.unit
@pytest.mark.template_functions
@pytest.mark.parametrize("template,expected", [
    ("{{file_line:1:FILE}}", "Line 1"),
    ("{{file_word:2:FILE}}", "1"), 
    ("{{file_line_count:FILE}}", "3"),
    ("{{file_word_count:FILE}}", "6"),
])
def test_file_functions_parametrized(template_functions, create_text_file, template, expected):
    """Parametrized tests for file functions."""
    lines = ["Line 1", "Line 2", "Line 3"]
    text_file = create_text_file("test.txt", lines)
    
    template_with_file = template.replace("FILE", text_file)
    result = template_functions.evaluate_all_functions(template_with_file)
    assert result == expected