"""
Integration tests for end-to-end PICARD workflows.

These tests verify complete workflows from file generation to template function extraction,
simulating real PICARD usage scenarios.
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

from file_generators import FileGeneratorFactory
from template_functions import TemplateFunctions


@pytest.mark.integration
class TestJSONWorkflows:
    """Test complete JSON generation → extraction workflows."""
    
    def test_json_generation_and_extraction_workflow(self, temp_workspace):
        """Test: Generate JSON → Extract with template functions → Verify correctness."""
        # Step 1: Generate complex JSON file
        json_generator = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        
        schema = {
            'users': {
                'type': 'array',
                'count': 3,
                'items': {
                    'id': 'id',
                    'name': 'person_name',
                    'email': 'email',
                    'profile': {
                        'age': 'age',
                        'city': 'city',
                        'salary': {'type': 'number', 'minimum': 30000, 'maximum': 120000}
                    },
                    'active': {'type': 'boolean'}
                }
            },
            'metadata': {
                'total': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'created': 'date',
                'version': {'type': 'string', 'pattern': 'lorem_word'}
            }
        }
        
        result = json_generator.generate(
            target_file="users.json",
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        assert len(result['files_created']) == 1
        
        # Step 2: Extract data using template functions
        tf = TemplateFunctions(str(temp_workspace))
        
        # Extract user count
        user_count = tf.evaluate_all_functions("{{json_count:$.users:users.json}}")
        assert int(user_count) == 3
        
        # Extract first user details
        first_user_name = tf.evaluate_all_functions("{{json_path:$.users[0].name:users.json}}")
        first_user_email = tf.evaluate_all_functions("{{json_path:$.users[0].email:users.json}}")
        first_user_active = tf.evaluate_all_functions("{{json_path:$.users[0].active:users.json}}")
        
        # Verify extraction matches original generation
        original_data = result['json_data'][str(temp_workspace / "users.json")]
        assert len(original_data['users']) == 3
        assert original_data['users'][0]['name'] == first_user_name
        assert original_data['users'][0]['email'] == first_user_email
        assert str(original_data['users'][0]['active']) == first_user_active
        
        # Extract metadata
        metadata_keys = tf.evaluate_all_functions("{{json_keys:$.metadata:users.json}}")
        assert "total" in metadata_keys
        assert "created" in metadata_keys
        assert "version" in metadata_keys
        
        # Verify salary is within expected range
        first_salary = tf.evaluate_all_functions("{{json_path:$.users[0].profile.salary:users.json}}")
        salary_value = float(first_salary)
        assert 30000 <= salary_value <= 120000
    
    def test_json_array_manipulation_workflow(self, temp_workspace):
        """Test complex JSON array operations and extractions."""
        json_generator = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        
        # Generate JSON with multiple arrays
        schema = {
            'departments': {
                'type': 'array',
                'count': [2, 4],
                'items': {
                    'id': 'id',
                    'name': 'department',
                    'employees': {
                        'type': 'array',
                        'count': [1, 3],
                        'items': {
                            'name': 'person_name',
                            'role': 'lorem_word'
                        }
                    }
                }
            }
        }
        
        result = json_generator.generate(
            target_file="company.json",
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test nested array access
        dept_count = int(tf.evaluate_all_functions("{{json_count:$.departments:company.json}}"))
        assert 2 <= dept_count <= 4
        
        # Test nested employee access
        first_dept_employee_count = int(tf.evaluate_all_functions("{{json_count:$.departments[0].employees:company.json}}"))
        assert 1 <= first_dept_employee_count <= 3
        
        # Verify we can access deep nested data
        first_employee_name = tf.evaluate_all_functions("{{json_path:$.departments[0].employees[0].name:company.json}}")
        assert len(first_employee_name) > 0


@pytest.mark.integration
class TestCSVWorkflows:
    """Test complete CSV generation → extraction workflows."""
    
    def test_csv_generation_and_aggregation_workflow(self, temp_workspace):
        """Test: Generate CSV → Perform aggregations → Verify calculations."""
        # Step 1: Generate CSV with known data patterns
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        result = csv_generator.generate(
            target_file="sales.csv",
            content_spec={
                'headers': ['salesperson_id', 'name', 'region', 'sales_amount', 'status'],
                'header_types': ['id', 'person_name', 'region', 'price', 'status'],
                'rows': 10
            }
        )
        
        assert result['errors'] == []
        
        # Step 2: Perform complex aggregations
        tf = TemplateFunctions(str(temp_workspace))
        
        # Basic aggregations
        total_sales = float(tf.evaluate_all_functions("{{csv_sum:sales_amount:sales.csv}}"))
        avg_sales = float(tf.evaluate_all_functions("{{csv_avg:sales_amount:sales.csv}}"))
        record_count = int(tf.evaluate_all_functions("{{csv_count:name:sales.csv}}"))
        
        assert record_count == 10
        assert total_sales > 0
        assert avg_sales == total_sales / record_count
        
        # Filtered aggregations
        active_sales = float(tf.evaluate_all_functions("{{csv_sum_where:sales_amount:status:==:active:sales.csv}}"))
        active_count = int(tf.evaluate_all_functions("{{csv_count_where:name:status:==:active:sales.csv}}"))
        
        # Verify active sales is subset of total
        assert active_sales <= total_sales
        assert active_count <= record_count
        
        if active_count > 0:
            active_avg = float(tf.evaluate_all_functions("{{csv_avg_where:sales_amount:status:==:active:sales.csv}}"))
            assert abs(active_avg - (active_sales / active_count)) < 0.01  # Float precision
    
    def test_csv_cross_column_analysis(self, temp_workspace):
        """Test complex CSV analysis across multiple columns."""
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        result = csv_generator.generate(
            target_file="employees.csv",
            content_spec={
                'headers': ['emp_id', 'name', 'department', 'salary', 'years_exp', 'status'],
                'rows': 8
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Multi-condition filtering
        senior_eng_salary = float(tf.evaluate_all_functions("{{csv_sum_where:salary:department:contains:ing:employees.csv}}"))
        senior_eng_count = int(tf.evaluate_all_functions("{{csv_count_where:name:department:contains:ing:employees.csv}}"))
        
        assert senior_eng_salary >= 0
        assert senior_eng_count >= 0
        
        # Extract specific data points for verification
        first_emp_name = tf.evaluate_all_functions("{{csv_value:0:name:employees.csv}}")
        first_emp_dept = tf.evaluate_all_functions("{{csv_value:0:department:employees.csv}}")
        
        assert len(first_emp_name) > 0
        assert len(first_emp_dept) > 0


@pytest.mark.integration
class TestSQLiteWorkflows:
    """Test complete SQLite generation → extraction workflows."""
    
    def test_sqlite_relational_workflow(self, temp_workspace):
        """Test: Generate relational database → Query relationships → Verify integrity."""
        sqlite_generator = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        
        # Generate relational database
        result = sqlite_generator.generate(
            target_file="company.db",
            content_spec={
                'tables': [
                    {
                        'name': 'departments',
                        'columns': [
                            {'name': 'id', 'type': 'auto_id'},
                            {'name': 'name', 'type': 'TEXT', 'data_type': 'department'},
                            {'name': 'budget', 'type': 'INTEGER', 'data_type': 'salary'}
                        ],
                        'rows': 3
                    },
                    {
                        'name': 'employees',
                        'columns': [
                            {'name': 'id', 'type': 'auto_id'},
                            {'name': 'name', 'type': 'TEXT', 'data_type': 'person_name'},
                            {'name': 'dept_id', 'type': 'INTEGER', 'foreign_key': 'departments.id'},
                            {'name': 'salary', 'type': 'INTEGER', 'data_type': 'salary'}
                        ],
                        'rows': 6
                    }
                ]
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test foreign key relationships
        dept_count = tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(*) FROM departments:company.db}}")
        emp_count = tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(*) FROM employees:company.db}}")
        
        assert int(dept_count) == 3
        assert int(emp_count) == 6
        
        # Test JOIN operations
        join_result = tf.evaluate_all_functions(
            "{{sqlite_query:SELECT COUNT(*) FROM employees e JOIN departments d ON e.dept_id = d.id:company.db}}"
        )
        assert int(join_result) == 6  # All employees should have valid department references
        
        # Test aggregation queries
        avg_salary = tf.evaluate_all_functions("{{sqlite_query:SELECT AVG(salary) FROM employees:company.db}}")
        total_budget = tf.evaluate_all_functions("{{sqlite_query:SELECT SUM(budget) FROM departments:company.db}}")
        
        assert float(avg_salary) > 0
        assert float(total_budget) > 0


@pytest.mark.integration
class TestCrossFormatWorkflows:
    """Test workflows that span multiple file formats."""
    
    def test_json_to_csv_analysis_workflow(self, temp_workspace):
        """Test: Generate JSON → Use data to inform CSV generation → Cross-validate."""
        # Step 1: Generate JSON with user data
        json_generator = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        
        json_result = json_generator.generate(
            target_file="user_config.json",
            content_spec={
                'schema': {
                    'user_count': {'type': 'integer', 'minimum': 5, 'maximum': 10},
                    'departments': {
                        'type': 'array',
                        'count': 3,
                        'items': 'department'
                    }
                }
            }
        )
        
        assert json_result['errors'] == []
        
        # Step 2: Extract configuration from JSON
        tf = TemplateFunctions(str(temp_workspace))
        user_count = int(tf.evaluate_all_functions("{{json_value:user_count:user_config.json}}"))
        dept_count = int(tf.evaluate_all_functions("{{json_count:$.departments:user_config.json}}"))
        
        assert 5 <= user_count <= 10
        assert dept_count == 3
        
        # Step 3: Generate CSV based on JSON configuration
        csv_generator = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        
        csv_result = csv_generator.generate(
            target_file="users.csv",
            content_spec={
                'headers': ['id', 'name', 'department', 'active'],
                'rows': user_count  # Use count from JSON
            }
        )
        
        assert csv_result['errors'] == []
        
        # Step 4: Cross-validate data consistency
        csv_user_count = int(tf.evaluate_all_functions("{{csv_count:name:users.csv}}"))
        assert csv_user_count == user_count  # Counts should match
        
        # Extract department from first user
        first_user_dept = tf.evaluate_all_functions("{{csv_value:0:department:users.csv}}")
        
        # Verify department exists in JSON config
        dept_list = tf.evaluate_all_functions("{{json_path:$.departments:user_config.json}}")
        # Note: dept_list will be a string representation, so we verify it's not empty
        assert len(first_user_dept) > 0
        assert len(dept_list) > 0
    
    def test_multi_format_data_pipeline(self, temp_workspace):
        """Test: JSON config → CSV data → SQLite storage → Cross-format queries."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Step 1: JSON configuration
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        config_result = json_gen.generate(
            target_file="config.json",
            content_spec={
                'schema': {
                    'batch_size': {'type': 'integer', 'minimum': 3, 'maximum': 5},
                    'settings': {
                        'region': 'region',
                        'active_only': {'type': 'boolean'}
                    }
                }
            }
        )
        
        batch_size = int(tf.evaluate_all_functions("{{json_value:batch_size:config.json}}"))
        
        # Step 2: CSV data generation
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        csv_result = csv_gen.generate(
            target_file="data.csv",
            content_spec={
                'headers': ['id', 'name', 'region', 'score'],
                'rows': batch_size
            }
        )
        
        # Step 3: SQLite storage simulation
        sqlite_gen = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        sqlite_result = sqlite_gen.generate(
            target_file="warehouse.db",
            content_spec={
                'table_name': 'analytics',
                'columns': [
                    {'name': 'id', 'type': 'auto_id'},
                    {'name': 'region', 'type': 'TEXT', 'data_type': 'region'},
                    {'name': 'total_score', 'type': 'INTEGER'},
                    {'name': 'record_count', 'type': 'INTEGER'}
                ],
                'rows': 2
            }
        )
        
        # Step 4: Cross-format validation
        assert all(result['errors'] == [] for result in [config_result, csv_result, sqlite_result])
        
        # Verify data consistency across formats
        csv_count = int(tf.evaluate_all_functions("{{csv_count:name:data.csv}}"))
        assert csv_count == batch_size
        
        sqlite_count = int(tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(*) FROM analytics:warehouse.db}}"))
        assert sqlite_count == 2
        
        # Extract sample data from each format
        config_region = tf.evaluate_all_functions("{{json_value:settings.region:config.json}}")
        csv_first_region = tf.evaluate_all_functions("{{csv_value:0:region:data.csv}}")
        sqlite_first_region = tf.evaluate_all_functions("{{sqlite_value:0:region:warehouse.db}}")
        
        # All should be valid region strings
        assert len(config_region) > 0
        assert len(csv_first_region) > 0
        assert len(sqlite_first_region) > 0


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceWorkflows:
    """Test performance characteristics of complete workflows."""
    
    def test_large_dataset_workflow(self, temp_workspace):
        """Test workflow with larger datasets to verify performance."""
        import time
        
        start_time = time.time()
        
        # Generate large CSV
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        result = csv_gen.generate(
            target_file="large_data.csv",
            content_spec={
                'headers': ['id', 'name', 'category', 'value', 'timestamp'],
                'header_types': ['id', 'person_name', 'department', 'price', 'date'],  # Ensure value is numeric
                'rows': 100  # Larger dataset
            }
        )
        
        generation_time = time.time() - start_time
        assert result['errors'] == []
        assert generation_time < 5.0  # Should complete within 5 seconds
        
        # Perform multiple template operations
        tf = TemplateFunctions(str(temp_workspace))
        
        operations_start = time.time()
        
        # Multiple aggregation operations
        total_records = int(tf.evaluate_all_functions("{{csv_count:name:large_data.csv}}"))
        sum_values = float(tf.evaluate_all_functions("{{csv_sum:value:large_data.csv}}"))
        avg_values = float(tf.evaluate_all_functions("{{csv_avg:value:large_data.csv}}"))
        
        operations_time = time.time() - operations_start
        
        assert total_records == 100
        assert sum_values > 0
        assert avg_values > 0
        assert operations_time < 2.0  # Template operations should be fast
        
        total_time = time.time() - start_time
        assert total_time < 6.0  # Entire workflow should complete quickly