"""
Unit tests for YAML template functions.

Tests YAML path navigation, value extraction, and aggregation functions.
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from template_functions import TemplateFunctions, TemplateFunctionError


@pytest.mark.unit
@pytest.mark.template_functions
class TestYAMLTemplateFunctions:
    """Test YAML template function functionality."""
    
    def test_yaml_path_extraction(self, template_functions, create_yaml_file):
        """Test {{yaml_path:$.path:file}} function."""
        yaml_file = create_yaml_file("test.yaml")
        
        # Extract user array elements
        result = template_functions.evaluate_all_functions(f"{{{{yaml_path:$.users[0].name:{yaml_file}}}}}")
        assert result == "John"
        
        # Extract nested values
        result = template_functions.evaluate_all_functions(f"{{{{yaml_path:$.config.settings.debug:{yaml_file}}}}}")
        assert result == "True"
        
        # Extract database info
        result = template_functions.evaluate_all_functions(f"{{{{yaml_path:$.database.host:{yaml_file}}}}}")
        assert result == "postgres-server"
        
        # Extract array length
        result = template_functions.evaluate_all_functions(f"{{{{yaml_path:$.users:{yaml_file}}}}}")
        users_str = result
        assert "John" in users_str and "Alice" in users_str
    
    def test_yaml_value_extraction(self, template_functions, create_yaml_file):
        """Test {{yaml_value:key.path:file}} function."""
        yaml_file = create_yaml_file("test.yaml")
        
        # Simple key navigation
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:metadata.total:{yaml_file}}}}}")
        assert result == "3"
        
        # Database configuration
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:database.port:{yaml_file}}}}}")
        assert result == "5432"
        
        # Nested configuration
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:config.settings.timeout:{yaml_file}}}}}")
        assert result == "30"
    
    def test_yaml_count_function(self, template_functions, create_yaml_file):
        """Test {{yaml_count:$.path:file}} function."""
        yaml_file = create_yaml_file("test.yaml")
        
        # Count array elements
        result = template_functions.evaluate_all_functions(f"{{{{yaml_count:$.users:{yaml_file}}}}}")
        assert int(result) == 3
        
        # Count object keys
        result = template_functions.evaluate_all_functions(f"{{{{yaml_count:$.database:{yaml_file}}}}}")
        assert int(result) == 3  # host, port, name
        
        # Count nested object keys
        result = template_functions.evaluate_all_functions(f"{{{{yaml_count:$.config.settings:{yaml_file}}}}}")
        assert int(result) == 3  # debug, timeout, max_retries
    
    def test_yaml_keys_function(self, template_functions, create_yaml_file):
        """Test {{yaml_keys:$.path:file}} function.""" 
        yaml_file = create_yaml_file("test.yaml")
        
        # Get object keys
        result = template_functions.evaluate_all_functions(f"{{{{yaml_keys:$.metadata:{yaml_file}}}}}")
        keys = set(result.split(','))
        expected_keys = {'total', 'version', 'created'}
        assert keys == expected_keys
        
        # Get database keys
        result = template_functions.evaluate_all_functions(f"{{{{yaml_keys:$.database:{yaml_file}}}}}")
        keys = set(result.split(','))
        expected_keys = {'host', 'port', 'name'}
        assert keys == expected_keys
    
    def test_yaml_aggregation_functions(self, template_functions, create_yaml_file):
        """Test YAML aggregation functions (sum, avg, max, min)."""
        # Create YAML with numeric data
        data = {
            "projects": [
                {"name": "Project A", "budget": 100.0, "priority": 1},
                {"name": "Project B", "budget": 200.0, "priority": 2}, 
                {"name": "Project C", "budget": 150.0, "priority": 3}
            ],
            "metrics": {
                "values": [10, 20, 30, 40, 50]
            }
        }
        yaml_file = create_yaml_file("numbers.yaml", data)
        
        # Test sum
        result = template_functions.evaluate_all_functions(f"{{{{yaml_sum:$.projects[*].budget:{yaml_file}}}}}")
        assert float(result) == 450.0
        
        # Test average  
        result = template_functions.evaluate_all_functions(f"{{{{yaml_avg:$.projects[*].budget:{yaml_file}}}}}")
        assert float(result) == 150.0
        
        # Test max
        result = template_functions.evaluate_all_functions(f"{{{{yaml_max:$.projects[*].budget:{yaml_file}}}}}")
        assert float(result) == 200.0
        
        # Test min
        result = template_functions.evaluate_all_functions(f"{{{{yaml_min:$.projects[*].budget:{yaml_file}}}}}")
        assert float(result) == 100.0
    
    def test_yaml_collect_function(self, template_functions, create_yaml_file):
        """Test {{yaml_collect:$.path:file}} function."""
        yaml_file = create_yaml_file("test.yaml")
        
        # Collect user names
        result = template_functions.evaluate_all_functions(f"{{{{yaml_collect:$.users[*].name:{yaml_file}}}}}")
        names = result.split(',')
        assert set(names) == {'John', 'Alice', 'Bob'}
        
        # Collect cities
        result = template_functions.evaluate_all_functions(f"{{{{yaml_collect:$.users[*].city:{yaml_file}}}}}")
        cities = result.split(',')
        assert len(cities) == 3
        assert 'New York' in cities
        assert 'Los Angeles' in cities
        assert 'Chicago' in cities
    
    def test_yaml_filter_functions(self, template_functions, create_yaml_file):
        """Test YAML filtering functions."""
        # Create YAML with filterable data
        data = {
            "employees": [
                {"name": "John", "salary": 60000, "department": "Engineering"},
                {"name": "Alice", "salary": 70000, "department": "Marketing"},
                {"name": "Bob", "salary": 80000, "department": "Engineering"},
                {"name": "Carol", "salary": 55000, "department": "Sales"}
            ]
        }
        yaml_file = create_yaml_file("employees.yaml", data)
        
        # Count where
        result = template_functions.evaluate_all_functions(f"{{{{yaml_count_where:$.employees[?salary>65000]:{yaml_file}}}}}")
        assert result == "2"  # Alice and Bob
        
        # Filter and collect names
        result = template_functions.evaluate_all_functions(f"{{{{yaml_filter:$.employees[?salary>65000].name:{yaml_file}}}}}")
        names = result.split(',')
        assert set(names) == {'Alice', 'Bob'}
        
        # Filter by department  
        result = template_functions.evaluate_all_functions(f"{{{{yaml_count_where:$.employees[?department==Engineering]:{yaml_file}}}}}")
        assert result == "2"  # John and Bob
    
    def test_yaml_function_errors(self, template_functions, create_yaml_file):
        """Test error handling for YAML functions."""
        yaml_file = create_yaml_file("test.yaml")
        
        # Invalid path
        with pytest.raises(TemplateFunctionError, match="Key 'nonexistent' not found"):
            template_functions.evaluate_all_functions(f"{{{{yaml_value:nonexistent.key:{yaml_file}}}}}")
        
        # Missing file
        with pytest.raises(TemplateFunctionError, match="YAML file not found"):
            template_functions.evaluate_all_functions("{{yaml_path:$.test:/nonexistent/file.yaml}}")
        
        # Wrong argument count
        with pytest.raises(TemplateFunctionError, match="yaml_path requires exactly 2 arguments"):
            template_functions.evaluate_all_functions(f"{{{{yaml_path:$.test:{yaml_file}:extra}}}}")
    
    def test_yaml_complex_paths(self, template_functions, create_yaml_file):
        """Test complex YAML path expressions."""
        # Create nested YAML structure
        data = {
            "organization": {
                "departments": [
                    {
                        "name": "Engineering",
                        "teams": [
                            {"name": "Backend", "size": 5, "budget": 100000},
                            {"name": "Frontend", "size": 3, "budget": 75000}
                        ]
                    },
                    {
                        "name": "Marketing", 
                        "teams": [
                            {"name": "Digital", "size": 4, "budget": 80000},
                            {"name": "Content", "size": 2, "budget": 50000}
                        ]
                    }
                ]
            }
        }
        yaml_file = create_yaml_file("complex.yaml", data)
        
        # Navigate deep paths
        result = template_functions.evaluate_all_functions(f"{{{{yaml_path:$.organization.departments[0].name:{yaml_file}}}}}")
        assert result == "Engineering"
        
        # Collect all team names
        result = template_functions.evaluate_all_functions(f"{{{{yaml_collect:$.organization.departments[*].teams[*].name:{yaml_file}}}}}")
        teams = result.split(',')
        expected_teams = {'Backend', 'Frontend', 'Digital', 'Content'}
        assert set(teams) == expected_teams
        
        # Sum all budgets
        result = template_functions.evaluate_all_functions(f"{{{{yaml_sum:$.organization.departments[*].teams[*].budget:{yaml_file}}}}}")
        assert float(result) == 305000.0
    
    def test_yaml_data_types(self, template_functions, create_yaml_file):
        """Test YAML functions with different data types."""
        data = {
            "mixed_data": {
                "string_val": "hello world",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": True,
                "null_val": None,
                "array_val": [1, 2, 3, 4, 5],
                "nested": {
                    "inner_string": "nested value",
                    "inner_array": ["a", "b", "c"]
                }
            }
        }
        yaml_file = create_yaml_file("types.yaml", data)
        
        # String value
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:mixed_data.string_val:{yaml_file}}}}}")
        assert result == "hello world"
        
        # Integer value
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:mixed_data.int_val:{yaml_file}}}}}")
        assert result == "42"
        
        # Boolean value
        result = template_functions.evaluate_all_functions(f"{{{{yaml_value:mixed_data.bool_val:{yaml_file}}}}}")
        assert result == "True"
        
        # Array operations
        result = template_functions.evaluate_all_functions(f"{{{{yaml_sum:$.mixed_data.array_val[*]:{yaml_file}}}}}")
        assert float(result) == 15.0
        
        # Nested array
        result = template_functions.evaluate_all_functions(f"{{{{yaml_collect:$.mixed_data.nested.inner_array[*]:{yaml_file}}}}}")
        assert result == "a,b,c"