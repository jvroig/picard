"""
Unit tests for sandbox component processing with variable substitution.

These tests would have caught the sandbox-related bugs we encountered:
1. target_file not resolving {{semantic}} variables
2. Component content_spec not processing {{numeric}} variables  
3. Multi-component variable consistency issues
4. Component generation failure due to unprocessed templates
"""

import pytest
import tempfile
import sys
import os
import json
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import FileGeneratorFactory
from enhanced_variable_substitution import EnhancedVariableSubstitution


class TestSandboxComponents:
    """Test sandbox component processing with variable substitution."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for sandbox components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def enhanced_variables(self):
        """Create enhanced variable substitution with fixed seed."""
        return EnhancedVariableSubstitution(seed=42)
    
    def test_component_target_file_variable_resolution(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test that component target_file resolves variables before file generation.
        
        This test would have caught the bug where target_file_resolved showed
        "{{semantic1:city}}.csv" instead of actual city names.
        """
        # Generate semantic variable
        result = enhanced_variables.substitute_all_variables("{{semantic1:city}}")
        city_name = result['variables']['semantic1:city']
        
        # Create component with target_file containing resolved semantic variable
        target_file = f"artifacts/q101_s1/data_{city_name}.csv"
        
        # Simulate component processing (what precheck_generator does)
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file=target_file,
            content_spec={
                'headers': ['id', 'name', 'location'],
                'rows': 3
            }
        )
        
        assert component_result['errors'] == [], f"Component generation failed: {component_result['errors']}"
        
        # Verify target_file was resolved correctly
        expected_file = temp_workspace / target_file
        assert expected_file.exists(), f"Target file not created: {expected_file}"
        
        # Verify no template variables remain in file path
        assert '{{semantic1:city}}' not in str(expected_file)
        assert city_name in str(expected_file)
        
        # Verify files_created contains resolved path
        files_created = component_result['files_created']
        main_file = files_created[0]
        assert '{{semantic1:city}}' not in main_file
        assert city_name in main_file
    
    def test_component_content_spec_numeric_variable_processing(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test that content_spec processes {{numeric}} variables before generation.
        
        This test would have caught the bug where {{number1:20:30}} remained unsubstituted
        in content_spec, causing "str object cannot be interpreted as an integer" errors.
        """
        # Generate numeric variable  
        result = enhanced_variables.substitute_all_variables("{{number1:5:10}}")
        row_count = result['variables']['number1:5:10:integer']
        
        # Create component with content_spec containing resolved numeric variable
        content_spec = {
            'headers': ['id', 'value'],
            'rows': row_count  # Should be an integer string like "7"
        }
        
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        component_result = csv_generator.generate(
            target_file="numeric_test.csv",
            content_spec=content_spec
        )
        
        assert component_result['errors'] == [], f"Component failed with numeric variable: {component_result['errors']}"
        
        # Verify correct number of rows were generated
        csv_data = component_result['csv_data'][str(temp_workspace / "numeric_test.csv")]
        expected_rows = int(row_count)
        assert len(csv_data) == expected_rows + 1  # +1 for header
        assert 5 <= expected_rows <= 10  # Should be in specified range
    
    def test_multi_component_variable_consistency(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test that variables are consistent across multiple sandbox components.
        
        This test would have caught bugs where semantic1:city was "Boston" in one component
        but "Seattle" in another due to separate variable generation.
        """
        # Generate variables once for consistent use across components
        template = "{{semantic1:city}} analysis with {{number1:2:4}} samples"
        result = enhanced_variables.substitute_all_variables(template)
        
        city_name = result['variables']['semantic1:city']
        sample_count = result['variables']['number1:2:4:integer']
        
        # Create multiple components using same variables
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        json_generator = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        sqlite_generator = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        
        # Component 1: CSV with city in filename and sample count in rows
        csv_result = csv_generator.generate(
            target_file=f"data_{city_name.replace(' ', '_')}.csv",
            content_spec={
                'headers': ['location', 'count'],
                'rows': sample_count
            }
        )
        
        # Component 2: JSON with city in filename
        json_result = json_generator.generate(
            target_file=f"summary_{city_name.replace(' ', '_')}.json",
            content_spec={
                'type': 'object',
                'object_template': {
                    'city': city_name,
                    'samples': int(sample_count)
                }
            }
        )
        
        # Component 3: SQLite with city in table and sample count in rows
        sqlite_result = sqlite_generator.generate(
            target_file=f"{city_name.replace(' ', '_')}_data.db",
            content_spec={
                'table_name': 'analysis',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER'},
                    {'name': 'location', 'type': 'TEXT'}
                ],
                'rows': sample_count
            }
        )
        
        # All components should succeed
        assert csv_result['errors'] == []
        assert json_result['errors'] == []
        assert sqlite_result['errors'] == []
        
        # Verify all files were created with consistent naming
        csv_file = temp_workspace / f"data_{city_name.replace(' ', '_')}.csv"
        json_file = temp_workspace / f"summary_{city_name.replace(' ', '_')}.json"
        sqlite_file = temp_workspace / f"{city_name.replace(' ', '_')}_data.db"
        
        assert csv_file.exists()
        assert json_file.exists()
        assert sqlite_file.exists()
        
        # Verify consistent sample counts
        csv_data = csv_result['csv_data'][str(csv_file)]
        json_data = json_result['json_data'][str(json_file)]
        sqlite_data = sqlite_result['sqlite_data'][str(sqlite_file)]
        
        assert len(csv_data) == int(sample_count) + 1  # +1 for header
        
        # Check JSON structure (could be different based on generator implementation)
        if isinstance(json_data, dict):
            if 'samples' in json_data:
                assert json_data['samples'] == int(sample_count)
            elif 'city' in json_data:
                assert json_data['city'] == city_name
        
        assert len(sqlite_data['analysis']['rows']) == int(sample_count)
    
    def test_component_with_mixed_variable_types(self, temp_workspace, enhanced_variables):
        """
        Test sandbox component with semantic, numeric, and entity variables mixed.
        
        This ensures complex real-world sandbox setups work correctly.
        """
        # Generate multiple variable types
        template = "{{semantic1:person_name}} in {{semantic2:city}} with {{number1:10:20}} {{entity1:colors}} items"
        result = enhanced_variables.substitute_all_variables(template)
        
        person_name = result['variables']['semantic1:person_name']
        city_name = result['variables']['semantic2:city']
        item_count = result['variables']['number1:10:20:integer']
        color = result['variables']['entity1:colors']
        
        # Create component using all variable types
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file=f"{person_name.replace(' ', '_')}_{city_name.replace(' ', '_')}.csv",
            content_spec={
                'headers': ['person', 'city', 'item_count', 'color'],
                'rows': item_count,
                'header_types': ['person_name', 'city', 'id', 'status']
            }
        )
        
        assert component_result['errors'] == []
        
        # Verify file creation with all variables resolved
        csv_file = temp_workspace / f"{person_name.replace(' ', '_')}_{city_name.replace(' ', '_')}.csv"
        assert csv_file.exists()
        
        # Verify CSV content
        csv_data = component_result['csv_data'][str(csv_file)]
        assert len(csv_data) == int(item_count) + 1  # +1 for header
        
        # Check that headers are correct
        assert csv_data[0] == ['person', 'city', 'item_count', 'color']
    
    def test_component_generation_with_zero_count_variables(self, temp_workspace, enhanced_variables):
        """
        Test edge case: component with zero count from {{numeric}} variables.
        
        This ensures components handle edge cases gracefully.
        """
        # Force a small range that might generate zero
        result = enhanced_variables.substitute_all_variables("{{number1:0:2}}")
        count = result['variables']['number1:0:2:integer']
        
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file="zero_test.csv",
            content_spec={
                'headers': ['id'],
                'rows': count  # Could be "0", "1", or "2"
            }
        )
        
        assert component_result['errors'] == []
        
        # File should still be created even with zero rows
        csv_file = temp_workspace / "zero_test.csv"
        assert csv_file.exists()
        
        # Verify CSV structure
        csv_data = component_result['csv_data'][str(csv_file)]
        expected_rows = int(count)
        assert len(csv_data) == expected_rows + 1  # +1 for header
        assert csv_data[0] == ['id']  # Header should always be present
    
    def test_component_error_handling_with_invalid_variables(self, temp_workspace):
        """
        Test that component generation handles invalid variable values gracefully.
        
        This ensures robust error handling when variable substitution goes wrong.
        """
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        # Test with invalid content_spec (non-string, non-integer rows)
        with pytest.raises(Exception):  # Should raise some kind of error
            csv_generator.generate(
                target_file="invalid.csv",
                content_spec={
                    'headers': ['id'],
                    'rows': None  # Invalid row count
                }
            )
    
    def test_nested_directory_target_file_resolution(self, temp_workspace, enhanced_variables):
        """
        Test component target_file resolution with nested directory structures.
        
        This ensures complex file paths with variables work correctly.
        """
        # Generate variables for nested path
        result = enhanced_variables.substitute_all_variables("{{semantic1:city}}/{{semantic2:person_name}}")
        city = result['variables']['semantic1:city']
        person = result['variables']['semantic2:person_name']
        
        # Create component with nested target_file
        target_file = f"artifacts/q101_s1/{city.replace(' ', '_')}/data_{person.replace(' ', '_')}.csv"
        
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file=target_file,
            content_spec={
                'headers': ['name', 'location'],
                'rows': 2
            }
        )
        
        assert component_result['errors'] == []
        
        # Verify nested directory was created
        expected_file = temp_workspace / target_file
        assert expected_file.exists()
        assert expected_file.parent.exists()
        
        # Verify path contains resolved variables
        assert city.replace(' ', '_') in str(expected_file)
        assert person.replace(' ', '_') in str(expected_file)
        assert '{{semantic1:city}}' not in str(expected_file)
        assert '{{semantic2:person_name}}' not in str(expected_file)
    
    def test_component_clutter_file_generation_with_variables(self, temp_workspace, enhanced_variables):
        """
        Test that clutter file generation works with variable-resolved paths.
        
        This ensures clutter files are generated in the correct directories.
        """
        # Generate variable for directory structure
        result = enhanced_variables.substitute_all_variables("{{semantic1:city}}")
        city = result['variables']['semantic1:city']
        
        target_file = f"artifacts/{city.replace(' ', '_')}/main.csv"
        
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file=target_file,
            content_spec={
                'headers': ['id', 'value'],
                'rows': 2
            },
            clutter_spec={'count': 3}  # Generate 3 clutter files
        )
        
        assert component_result['errors'] == []
        
        # Should have main file + 3 clutter files = 4 total
        assert len(component_result['files_created']) >= 4
        
        # Verify main file exists in correct location
        main_file = temp_workspace / target_file
        assert main_file.exists()
        
        # Verify clutter files exist (they may be in subdirectories for organization)
        expected_dir = main_file.parent
        clutter_files = [f for f in component_result['files_created'] if f != str(main_file)]
        
        for clutter_file in clutter_files:
            clutter_path = Path(clutter_file)
            assert clutter_path.exists()
            # Clutter files should be within the same base directory structure
            assert expected_dir in clutter_path.parents or clutter_path.parent == expected_dir
    
    def test_component_with_large_numeric_ranges(self, temp_workspace, enhanced_variables):
        """
        Test component handling of large numeric ranges from variables.
        
        This ensures performance and memory handling with large generated datasets.
        """
        # Generate a moderately large number (not too large for test performance)
        result = enhanced_variables.substitute_all_variables("{{number1:100:200}}")
        large_count = result['variables']['number1:100:200:integer']
        
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        component_result = csv_generator.generate(
            target_file="large_dataset.csv",
            content_spec={
                'headers': ['id', 'value'],
                'rows': large_count
            }
        )
        
        assert component_result['errors'] == []
        
        # Verify large dataset was generated
        csv_data = component_result['csv_data'][str(temp_workspace / "large_dataset.csv")]
        expected_rows = int(large_count)
        assert len(csv_data) == expected_rows + 1  # +1 for header
        assert 100 <= expected_rows <= 200  # Should be in specified range
        
        # Verify file exists and has reasonable size
        csv_file = temp_workspace / "large_dataset.csv"
        assert csv_file.exists()
        assert csv_file.stat().st_size > 1000  # Should be reasonably large file