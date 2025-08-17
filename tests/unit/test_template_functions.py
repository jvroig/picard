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
from test_definition_parser import ComponentSpec


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
    
    def test_json_aggregation_functions(self, template_functions, temp_workspace):
        """Test new JSON aggregation functions: sum, avg, max, min."""
        # Create test JSON with numeric data
        test_data = {
            "projects": [
                {"name": "Project A", "budget": 50000, "team_size": 5},
                {"name": "Project B", "budget": 75000, "team_size": 3},
                {"name": "Project C", "budget": 25000, "team_size": 8}
            ],
            "departments": [
                {"name": "Engineering", "budget": 100000},
                {"name": "Marketing", "budget": 50000}
            ]
        }
        
        json_file = temp_workspace / "aggregation_test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test json_sum
        result = template_functions.evaluate_all_functions(f"{{{{json_sum:$.projects[*].budget:{json_file}}}}}")
        assert result == "150000.0"  # 50000 + 75000 + 25000
        
        # Test json_avg
        result = template_functions.evaluate_all_functions(f"{{{{json_avg:$.projects[*].budget:{json_file}}}}}")
        assert result == "50000.0"  # 150000 / 3
        
        # Test json_max
        result = template_functions.evaluate_all_functions(f"{{{{json_max:$.projects[*].budget:{json_file}}}}}")
        assert result == "75000.0"
        
        # Test json_min
        result = template_functions.evaluate_all_functions(f"{{{{json_min:$.projects[*].budget:{json_file}}}}}")
        assert result == "25000.0"
        
        # Test with different field
        result = template_functions.evaluate_all_functions(f"{{{{json_sum:$.projects[*].team_size:{json_file}}}}}")
        assert result == "16.0"  # 5 + 3 + 8
    
    def test_json_collection_functions(self, template_functions, temp_workspace):
        """Test json_collect function for gathering values."""
        test_data = {
            "teams": [
                {"name": "Alpha", "members": ["Alice", "Bob"]},
                {"name": "Beta", "members": ["Charlie", "Diana", "Eve"]}
            ],
            "projects": [
                {"title": "Project X", "status": "active"},
                {"title": "Project Y", "status": "completed"},
                {"title": "Project Z", "status": "active"}
            ]
        }
        
        json_file = temp_workspace / "collection_test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test collecting team names
        result = template_functions.evaluate_all_functions(f"{{{{json_collect:$.teams[*].name:{json_file}}}}}")
        assert result == "Alpha,Beta"
        
        # Test collecting project titles
        result = template_functions.evaluate_all_functions(f"{{{{json_collect:$.projects[*].title:{json_file}}}}}")
        assert result == "Project X,Project Y,Project Z"
        
        # Test collecting nested array values
        result = template_functions.evaluate_all_functions(f"{{{{json_collect:$.teams[*].members[*]:{json_file}}}}}")
        assert result == "Alice,Bob,Charlie,Diana,Eve"
    
    def test_json_filtering_functions(self, template_functions, temp_workspace):
        """Test json_count_where and json_filter functions."""
        test_data = {
            "employees": [
                {"name": "Alice", "salary": 70000, "department": "Engineering"},
                {"name": "Bob", "salary": 55000, "department": "Marketing"},
                {"name": "Charlie", "salary": 85000, "department": "Engineering"},
                {"name": "Diana", "salary": 45000, "department": "Sales"},
                {"name": "Eve", "salary": 90000, "department": "Engineering"}
            ]
        }
        
        json_file = temp_workspace / "filtering_test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test json_count_where with numeric filter
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.employees[?salary>60000]:{json_file}}}}}")
        assert result == "3"  # Alice, Charlie, Eve
        
        # Test json_count_where with string filter
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.employees[?department==Engineering]:{json_file}}}}}")
        assert result == "3"  # Alice, Charlie, Eve
        
        # Test json_filter to get names of high earners
        result = template_functions.evaluate_all_functions(f"{{{{json_filter:$.employees[?salary>60000].name:{json_file}}}}}")
        assert result == "Alice,Charlie,Eve"
        
        # Test json_filter with string comparison
        result = template_functions.evaluate_all_functions(f"{{{{json_filter:$.employees[?department==Engineering].name:{json_file}}}}}")
        assert result == "Alice,Charlie,Eve"
        
        # Test multiple filter conditions
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.employees[?salary<60000]:{json_file}}}}}")
        assert result == "2"  # Bob, Diana
    
    def test_json_wildcard_edge_cases(self, template_functions, temp_workspace):
        """Test edge cases for wildcard functionality."""
        test_data = {
            "empty_array": [],
            "mixed_data": [
                {"value": 10},
                {"value": "20"},  # String that can be numeric
                {"value": "abc"},  # Non-numeric string
                {"other": 30}  # Missing 'value' field
            ],
            "nested": {
                "level1": [
                    {"level2": [{"value": 1}, {"value": 2}]},
                    {"level2": [{"value": 3}]}
                ]
            }
        }
        
        json_file = temp_workspace / "wildcard_test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test with empty array
        result = template_functions.evaluate_all_functions(f"{{{{json_sum:$.empty_array[*].value:{json_file}}}}}")
        assert result == "0"
        
        # Test with mixed data types
        result = template_functions.evaluate_all_functions(f"{{{{json_sum:$.mixed_data[*].value:{json_file}}}}}")
        assert result == "30.0"  # 10 + 20 (string that converts to number)
        
        # Test deeply nested wildcards
        result = template_functions.evaluate_all_functions(f"{{{{json_sum:$.nested.level1[*].level2[*].value:{json_file}}}}}")
        assert result == "6.0"  # 1 + 2 + 3
    
    def test_json_filter_operators(self, template_functions, temp_workspace):
        """Test different filter operators."""
        test_data = {
            "products": [
                {"name": "Widget", "price": 10.50, "category": "tools"},
                {"name": "Gadget", "price": 25.00, "category": "electronics"},
                {"name": "Super Widget", "price": 15.75, "category": "tools"},
                {"name": "Mega Gadget", "price": 5.25, "category": "toys"}
            ]
        }
        
        json_file = temp_workspace / "operators_test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test >= operator
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.products[?price>=15]:{json_file}}}}}")
        assert result == "2"  # Gadget, Super Widget
        
        # Test <= operator
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.products[?price<=10.50]:{json_file}}}}}")
        assert result == "2"  # Widget, Mega Gadget
        
        # Test != operator
        result = template_functions.evaluate_all_functions(f"{{{{json_count_where:$.products[?category!=tools]:{json_file}}}}}")
        assert result == "2"  # Gadget, Mega Gadget
        
        # Test contains operator
        result = template_functions.evaluate_all_functions(f"{{{{json_filter:$.products[?name contains Widget].name:{json_file}}}}}")
        assert result == "Widget,Super Widget"


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
    """Test TARGET_FILE[component_name] keyword substitution."""
    
    def test_target_file_component_substitution(self, temp_workspace, create_text_file):
        """Test that TARGET_FILE[component_name] is properly substituted."""
        lines = ["First line", "Second line"]
        text_file = create_text_file("test.txt", lines)
        
        # Create a component for TARGET_FILE resolution
        component = ComponentSpec(
            type="create_text",
            name="test_comp", 
            target_file=text_file
        )
        
        # Create TemplateFunctions with the component
        tf = TemplateFunctions(str(temp_workspace), components=[component])
        
        # Test with TARGET_FILE[component_name] keyword
        result = tf.evaluate_all_functions("{{file_line:1:TARGET_FILE[test_comp]}}")
        assert result == "First line"
        
        result = tf.evaluate_all_functions("{{file_line_count:TARGET_FILE[test_comp]}}")
        assert result == "2"
    
    def test_target_file_errors(self, temp_workspace):
        """Test TARGET_FILE error cases."""
        # Create a dummy component for the "component not found" test
        dummy_component = ComponentSpec(
            type="create_text",
            name="dummy", 
            target_file="dummy.txt"
        )
        
        tf_with_components = TemplateFunctions(str(temp_workspace), components=[dummy_component])
        tf_empty = TemplateFunctions(str(temp_workspace), components=[])
        
        # Test bare TARGET_FILE (should fail)
        with pytest.raises(TemplateFunctionError, match="TARGET_FILE requires component name"):
            tf_empty.evaluate_all_functions("{{file_line:1:TARGET_FILE}}")
        
        # Test invalid component name when components exist
        with pytest.raises(TemplateFunctionError, match="Component 'nonexistent' not found"):
            tf_with_components.evaluate_all_functions("{{file_line:1:TARGET_FILE[nonexistent]}}")
        
        # Test TARGET_FILE[component] with empty components list
        with pytest.raises(TemplateFunctionError, match="No components provided"):
            tf_empty.evaluate_all_functions("{{file_line:1:TARGET_FILE[test]}}")


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