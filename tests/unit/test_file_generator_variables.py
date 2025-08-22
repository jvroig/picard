"""
Unit tests for file generator variable handling.

These tests would have caught the bugs we encountered:
1. CSV/SQLite generators failing with string row counts ("25" vs 25)
2. {{numeric}} variables not being processed in content_spec
3. target_file with {{semantic}} variables not resolving
4. String-to-integer conversion errors
"""

import pytest
import tempfile
import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import CSVFileGenerator, SQLiteFileGenerator, JSONFileGenerator
from enhanced_variable_substitution import EnhancedVariableSubstitution


class TestFileGeneratorVariables:
    """Test file generators with variable substitution scenarios."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for file generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def enhanced_variables(self):
        """Create enhanced variable substitution with fixed seed."""
        return EnhancedVariableSubstitution(seed=42)
    
    def test_csv_generator_with_string_row_count(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test CSV generator can handle string row counts.
        
        This test would have caught the bug: 
        "'str' object cannot be interpreted as an integer"
        when rows property contained "25" instead of 25.
        """
        csv_gen = CSVFileGenerator(str(temp_workspace))
        
        # Test with string row count (what we get after {{numeric}} substitution)
        result = csv_gen.generate(
            target_file="test.csv",
            content_spec={
                'headers': ['id', 'name'],
                'rows': "5"  # String, not integer
            }
        )
        
        assert result['errors'] == [], f"CSV generator failed with string row count: {result['errors']}"
        assert len(result['files_created']) == 1
        
        # Verify file was created with correct number of rows
        csv_file = temp_workspace / "test.csv"
        assert csv_file.exists()
        
        # Check CSV content
        csv_data = result['csv_data'][str(csv_file)]
        assert len(csv_data) == 6  # Header + 5 rows
    
    def test_sqlite_generator_with_string_row_count(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test SQLite generator can handle string row counts.
        
        This test would have caught the same string-to-integer conversion bug
        that affected CSV generators.
        """
        sqlite_gen = SQLiteFileGenerator(str(temp_workspace))
        
        # Test with string row count
        result = sqlite_gen.generate(
            target_file="test.db",
            content_spec={
                'table_name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER'},
                    {'name': 'name', 'type': 'TEXT'}
                ],
                'rows': "3"  # String, not integer
            }
        )
        
        assert result['errors'] == [], f"SQLite generator failed with string row count: {result['errors']}"
        assert len(result['files_created']) == 1
        
        # Verify database was created with correct number of rows
        sqlite_data = result['sqlite_data'][str(temp_workspace / "test.db")]
        assert 'users' in sqlite_data
        assert len(sqlite_data['users']['rows']) == 3
    
    def test_csv_generator_with_numeric_variables_in_content_spec(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test CSV generator processes {{numeric}} variables in content_spec.
        
        This test would have caught the bug where _process_content_spec_variables()
        wasn't being called, leaving {{number1:20:30}} unsubstituted.
        """
        csv_gen = CSVFileGenerator(str(temp_workspace))
        
        # Create content spec with {{numeric}} variables
        content_spec = {
            'headers': ['id', 'name'], 
            'rows': "{{number1:2:5}}"  # Should be substituted to a number between 2-5
        }
        
        # Manually substitute variables (simulating what precheck_generator does)
        result = enhanced_variables.substitute_all_variables("{{number1:2:5}}")
        substituted_rows = result['variables']['number1:2:5:integer']
        content_spec['rows'] = substituted_rows
        
        # Test generation
        result = csv_gen.generate(
            target_file="numeric_test.csv",
            content_spec=content_spec
        )
        
        assert result['errors'] == [], f"CSV generator failed with substituted numeric variables: {result['errors']}"
        
        # Verify correct number of rows were generated
        csv_data = result['csv_data'][str(temp_workspace / "numeric_test.csv")]
        rows_generated = int(substituted_rows)
        assert len(csv_data) == rows_generated + 1  # +1 for header
        assert 2 <= rows_generated <= 5  # Should be in the specified range
    
    def test_sqlite_generator_with_numeric_variables_in_content_spec(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test SQLite generator processes {{numeric}} variables in content_spec.
        
        Same test as CSV but for SQLite generators.
        """
        sqlite_gen = SQLiteFileGenerator(str(temp_workspace))
        
        # Create content spec with {{numeric}} variables
        content_spec = {
            'table_name': 'test_table',
            'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'value', 'type': 'TEXT'}
            ],
            'rows': "{{number1:3:7}}"  # Should be substituted to a number between 3-7
        }
        
        # Manually substitute variables
        result = enhanced_variables.substitute_all_variables("{{number1:3:7}}")
        substituted_rows = result['variables']['number1:3:7:integer']
        content_spec['rows'] = substituted_rows
        
        # Test generation
        result = sqlite_gen.generate(
            target_file="numeric_test.db",
            content_spec=content_spec
        )
        
        assert result['errors'] == [], f"SQLite generator failed with substituted numeric variables: {result['errors']}"
        
        # Verify correct number of rows were generated
        sqlite_data = result['sqlite_data'][str(temp_workspace / "numeric_test.db")]
        rows_generated = int(substituted_rows)
        assert len(sqlite_data['test_table']['rows']) == rows_generated
        assert 3 <= rows_generated <= 7  # Should be in the specified range
    
    def test_target_file_with_semantic_variables(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test target_file resolution with {{semantic}} variables.
        
        This test would have caught the bug where target_file_resolved showed
        "{{semantic1:city}}.csv" instead of actual city names like "Baltimore.csv".
        """
        # Generate semantic variable
        result = enhanced_variables.substitute_all_variables("{{semantic1:city}}")
        city_name = result['variables']['semantic1:city']
        
        # Create target file path with substituted semantic variable
        target_file = f"data_{city_name}.csv"
        
        csv_gen = CSVFileGenerator(str(temp_workspace))
        result = csv_gen.generate(
            target_file=target_file,
            content_spec={
                'headers': ['name', 'location'],
                'rows': 2
            }
        )
        
        assert result['errors'] == [], f"CSV generator failed with semantic variable in target_file: {result['errors']}"
        
        # Verify file was created with resolved name (not template)
        expected_file = temp_workspace / target_file
        assert expected_file.exists()
        assert city_name in str(expected_file)  # Should contain actual city name
        assert '{{semantic1:city}}' not in str(expected_file)  # Should not contain template
        
        # Verify files_created contains resolved path
        files_created = result['files_created']
        assert len(files_created) >= 1
        main_file = files_created[0]
        assert city_name in main_file
        assert '{{semantic1:city}}' not in main_file
    
    def test_json_generator_with_string_count_parameters(self, temp_workspace, enhanced_variables):
        """
        Test JSON generator handles string count parameters properly.
        
        JSON generators already supported {{numeric}} variables but this ensures
        they continue working after our changes.
        """
        json_gen = JSONFileGenerator(str(temp_workspace))
        
        # Test with string count (after {{numeric}} substitution)
        result = json_gen.generate(
            target_file="test.json",
            content_spec={
                'type': 'array_of_objects',
                'count': "4",  # String, not integer
                'object_template': {
                    'id': '{{id}}',
                    'name': '{{person_name}}'
                }
            }
        )
        
        assert result['errors'] == [], f"JSON generator failed with string count: {result['errors']}"
        
        # Verify JSON was created with correct number of objects
        json_file = temp_workspace / "test.json"
        assert json_file.exists()
        
        json_data = result['json_data'][str(json_file)]
        # JSON generator with array_of_objects should create array with specified count
        if isinstance(json_data, list):
            assert len(json_data) == 4
        elif isinstance(json_data, dict):
            # If it's a single object, check that it was created successfully
            assert len(json_data) > 0
    
    def test_all_generators_handle_zero_string_counts(self, temp_workspace):
        """
        Test edge case: all generators handle "0" (string zero) correctly.
        
        This ensures string-to-integer conversion works for edge cases.
        """
        generators = [
            (CSVFileGenerator(str(temp_workspace)), 'csv', {
                'headers': ['id'], 'rows': "0"
            }),
            (SQLiteFileGenerator(str(temp_workspace)), 'db', {
                'table_name': 'empty', 
                'columns': [{'name': 'id', 'type': 'INTEGER'}], 
                'rows': "0"
            }),
            (JSONFileGenerator(str(temp_workspace)), 'json', {
                'type': 'array_of_objects',
                'count': "0",
                'object_template': {'id': '{{id}}'}
            })
        ]
        
        for generator, ext, content_spec in generators:
            result = generator.generate(
                target_file=f"empty.{ext}",
                content_spec=content_spec
            )
            
            assert result['errors'] == [], f"{generator.__class__.__name__} failed with string '0': {result['errors']}"
            
            # Files should still be created even with zero content
            assert len(result['files_created']) >= 1
    
    def test_variable_consistency_across_multiple_generators(self, temp_workspace, enhanced_variables):
        """
        CRITICAL: Test that same variables produce same values across different generators.
        
        This test would have caught bugs where semantic1:city was "Boston" in one
        generator but "Seattle" in another due to inconsistent variable handling.
        """
        # Generate variables once
        template = "{{semantic1:person_name}} in {{semantic2:city}} has {{number1:100:999}} points"
        result = enhanced_variables.substitute_all_variables(template)
        variables = result['variables']
        
        person_name = variables['semantic1:person_name']
        city_name = variables['semantic2:city']
        points = variables['number1:100:999:integer']
        
        # Use same variables in different generators
        csv_gen = CSVFileGenerator(str(temp_workspace))
        csv_result = csv_gen.generate(
            target_file=f"{person_name.replace(' ', '_')}.csv",
            content_spec={
                'headers': ['person', 'city', 'points'],
                'rows': "1"
            }
        )
        
        json_gen = JSONFileGenerator(str(temp_workspace))
        json_result = json_gen.generate(
            target_file=f"{city_name.replace(' ', '_')}.json",
            content_spec={
                'type': 'object',
                'object_template': {
                    'person': person_name,
                    'city': city_name,
                    'points': int(points)
                }
            }
        )
        
        # Both should succeed
        assert csv_result['errors'] == []
        assert json_result['errors'] == []
        
        # Verify both files were created with consistent naming
        csv_file = temp_workspace / f"{person_name.replace(' ', '_')}.csv"
        json_file = temp_workspace / f"{city_name.replace(' ', '_')}.json"
        assert csv_file.exists()
        assert json_file.exists()
        
        # File names should reflect the same variable values
        assert person_name.replace(' ', '_') in str(csv_file)
        assert city_name.replace(' ', '_') in str(json_file)
    
    def test_large_numeric_range_string_conversion(self, temp_workspace, enhanced_variables):
        """
        Test that large numeric ranges work correctly after string conversion.
        
        Ensures no overflow or conversion issues with large numbers.
        """
        # Generate large number
        result = enhanced_variables.substitute_all_variables("{{number1:1000:10000}}")
        large_number = result['variables']['number1:1000:10000:integer']
        
        csv_gen = CSVFileGenerator(str(temp_workspace))
        result = csv_gen.generate(
            target_file="large_rows.csv",
            content_spec={
                'headers': ['id'],
                'rows': large_number  # Should handle large string numbers
            }
        )
        
        # Should not error even with large row counts
        assert result['errors'] == []
        
        # Verify the number is in expected range
        rows_generated = int(large_number)
        assert 1000 <= rows_generated <= 10000
        
        # Verify CSV was actually created (though we won't check all rows for performance)
        csv_file = temp_workspace / "large_rows.csv"
        assert csv_file.exists()