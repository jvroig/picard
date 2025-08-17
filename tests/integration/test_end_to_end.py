"""
Integration tests for end-to-end PICARD workflows.

These tests verify complete workflows from file generation to template function extraction,
simulating real PICARD usage scenarios.
"""
import pytest
import json
import yaml
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


@pytest.mark.integration
class TestYAMLWorkflows:
    """Test complete YAML generation → extraction workflows."""
    
    def test_yaml_configuration_workflow(self, temp_workspace):
        """Test: Generate YAML config → Extract values → Verify structure."""
        yaml_generator = FileGeneratorFactory.create_generator('create_yaml', str(temp_workspace))
        
        # Generate complex YAML configuration
        result = yaml_generator.generate(
            target_file="app_config.yaml",
            content_spec={
                'schema': {
                    'database': {
                        'host': 'city',
                        'port': {'type': 'integer', 'minimum': 1000, 'maximum': 9999},
                        'name': 'company'
                    },
                    'services': {
                        'type': 'array',
                        'count': [2, 4],
                        'items': {
                            'name': 'product',
                            'enabled': {'type': 'boolean'},
                            'config': {
                                'timeout': {'type': 'integer', 'minimum': 10, 'maximum': 120},
                                'retries': {'type': 'integer', 'minimum': 1, 'maximum': 5}
                            }
                        }
                    },
                    'metadata': {
                        'version': 'version',
                        'created': 'date',
                        'environment': 'category'
                    }
                }
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test basic value extraction
        db_host = tf.evaluate_all_functions("{{yaml_value:database.host:app_config.yaml}}")
        db_port = tf.evaluate_all_functions("{{yaml_value:database.port:app_config.yaml}}")
        
        assert len(db_host) > 0
        assert 1000 <= int(db_port) <= 9999
        
        # Test array operations
        service_count = int(tf.evaluate_all_functions("{{yaml_count:$.services:app_config.yaml}}"))
        assert 2 <= service_count <= 4
        
        # Test path navigation
        first_service = tf.evaluate_all_functions("{{yaml_path:$.services[0].name:app_config.yaml}}")
        first_service_enabled = tf.evaluate_all_functions("{{yaml_path:$.services[0].enabled:app_config.yaml}}")
        
        assert len(first_service) > 0
        assert first_service_enabled in ['True', 'False']
        
        # Test aggregation functions
        timeout_sum = float(tf.evaluate_all_functions("{{yaml_sum:$.services[*].config.timeout:app_config.yaml}}"))
        timeout_avg = float(tf.evaluate_all_functions("{{yaml_avg:$.services[*].config.timeout:app_config.yaml}}"))
        
        assert timeout_sum > 0
        assert 10 <= timeout_avg <= 120
        
        # Test key extraction
        db_keys = tf.evaluate_all_functions("{{yaml_keys:$.database:app_config.yaml}}")
        keys = set(db_keys.split(','))
        expected_keys = {'host', 'port', 'name'}
        assert keys == expected_keys
    
    def test_yaml_array_operations(self, temp_workspace):
        """Test complex YAML array operations and filtering."""
        yaml_generator = FileGeneratorFactory.create_generator('create_yaml', str(temp_workspace))
        
        # Generate YAML with filterable array data
        result = yaml_generator.generate(
            target_file="teams.yaml",
            content_spec={
                'schema': {
                    'teams': {
                        'type': 'array',
                        'count': 5,
                        'items': {
                            'name': 'product',
                            'budget': {'type': 'integer', 'minimum': 50000, 'maximum': 200000},
                            'members': {'type': 'integer', 'minimum': 2, 'maximum': 8},
                            'active': {'type': 'boolean'}
                        }
                    },
                    'company': {
                        'total_budget': {'type': 'integer', 'minimum': 500000, 'maximum': 1000000}
                    }
                }
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test array aggregations
        total_budget = float(tf.evaluate_all_functions("{{yaml_sum:$.teams[*].budget:teams.yaml}}"))
        avg_budget = float(tf.evaluate_all_functions("{{yaml_avg:$.teams[*].budget:teams.yaml}}"))
        max_budget = float(tf.evaluate_all_functions("{{yaml_max:$.teams[*].budget:teams.yaml}}"))
        min_budget = float(tf.evaluate_all_functions("{{yaml_min:$.teams[*].budget:teams.yaml}}"))
        
        assert total_budget > 0
        assert 50000 <= avg_budget <= 200000
        assert 50000 <= max_budget <= 200000
        assert 50000 <= min_budget <= 200000
        assert min_budget <= avg_budget <= max_budget
        
        # Test collection functions
        team_names = tf.evaluate_all_functions("{{yaml_collect:$.teams[*].name:teams.yaml}}")
        names = team_names.split(',')
        assert len(names) == 5
        assert all(len(name.strip()) > 0 for name in names)
        
        # Test filtering operations (high budget teams)
        high_budget_count = tf.evaluate_all_functions("{{yaml_count_where:$.teams[?budget>100000]:teams.yaml}}")
        high_budget_names = tf.evaluate_all_functions("{{yaml_filter:$.teams[?budget>100000].name:teams.yaml}}")
        
        assert int(high_budget_count) >= 0
        if int(high_budget_count) > 0:
            high_names = high_budget_names.split(',')
            assert len(high_names) == int(high_budget_count)
    
    def test_yaml_to_json_comparison(self, temp_workspace):
        """Test that YAML and JSON with same data structure produce equivalent results."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Define same schema for both formats
        schema = {
            'users': {
                'type': 'array',
                'count': 3,
                'items': {
                    'id': {'type': 'integer', 'minimum': 1, 'maximum': 1000},
                    'name': 'person_name',
                    'score': {'type': 'integer', 'minimum': 0, 'maximum': 100}
                }
            },
            'settings': {
                'max_users': {'type': 'integer', 'minimum': 10, 'maximum': 20}
            }
        }
        
        # Generate YAML version
        yaml_gen = FileGeneratorFactory.create_generator('create_yaml', str(temp_workspace))
        yaml_result = yaml_gen.generate(
            target_file="data.yaml",
            content_spec={'schema': schema}
        )
        
        # Generate JSON version with same schema
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        json_result = json_gen.generate(
            target_file="data.json", 
            content_spec={'schema': schema}
        )
        
        assert yaml_result['errors'] == []
        assert json_result['errors'] == []
        
        # Compare equivalent operations
        yaml_user_count = int(tf.evaluate_all_functions("{{yaml_count:$.users:data.yaml}}"))
        json_user_count = int(tf.evaluate_all_functions("{{json_count:$.users:data.json}}"))
        assert yaml_user_count == json_user_count == 3
        
        yaml_max_users = tf.evaluate_all_functions("{{yaml_value:settings.max_users:data.yaml}}")
        json_max_users = tf.evaluate_all_functions("{{json_value:settings.max_users:data.json}}")
        assert 10 <= int(yaml_max_users) <= 20
        assert 10 <= int(json_max_users) <= 20
        
        # Compare aggregation functions
        yaml_score_sum = float(tf.evaluate_all_functions("{{yaml_sum:$.users[*].score:data.yaml}}"))
        json_score_sum = float(tf.evaluate_all_functions("{{json_sum:$.users[*].score:data.json}}"))
        
        # Both should be valid ranges (won't be equal since data is random)
        assert 0 <= yaml_score_sum <= 300  # 3 users * max 100 score
        assert 0 <= json_score_sum <= 300


@pytest.mark.integration
class TestXMLWorkflows:
    """Test complete XML generation → extraction workflows."""
    
    def test_xml_enterprise_configuration_workflow(self, temp_workspace):
        """Test: Generate XML enterprise config → Extract values → Verify structure."""
        xml_generator = FileGeneratorFactory.create_generator('create_xml', str(temp_workspace))
        
        # Generate enterprise XML configuration
        result = xml_generator.generate(
            target_file="enterprise_config.xml",
            content_spec={
                'schema': {
                    'company': {
                        'name': 'company',
                        'departments': {
                            'type': 'array',
                            'count': [3, 5],
                            'items': {
                                'name': 'department',
                                'budget': {'type': 'integer', 'minimum': 100000, 'maximum': 500000},
                                'employees': {
                                    'type': 'array',
                                    'count': [2, 6],
                                    'items': {
                                        'name': 'person_name',
                                        'role': 'category',
                                        'salary': 'salary'
                                    }
                                }
                            }
                        }
                    },
                    'settings': {
                        'environment': 'category',
                        'debug': {'type': 'boolean'},
                        'max_connections': {'type': 'integer', 'minimum': 10, 'maximum': 1000}
                    }
                },
                'root_element': 'enterprise'
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test basic value extraction
        company_name = tf.evaluate_all_functions("{{xpath_value:company/name:enterprise_config.xml}}")
        environment = tf.evaluate_all_functions("{{xpath_value:settings/environment:enterprise_config.xml}}")
        debug_setting = tf.evaluate_all_functions("{{xpath_value:settings/debug:enterprise_config.xml}}")
        
        assert len(company_name) > 0
        assert len(environment) > 0
        assert debug_setting in ['True', 'False']
        
        # Test count operations
        dept_count = int(tf.evaluate_all_functions("{{xpath_count:company/departments/item:enterprise_config.xml}}"))
        assert 3 <= dept_count <= 5
        
        # Test aggregation functions
        total_budget = float(tf.evaluate_all_functions("{{xpath_sum:company/departments/item/budget:enterprise_config.xml}}"))
        avg_budget = float(tf.evaluate_all_functions("{{xpath_avg:company/departments/item/budget:enterprise_config.xml}}"))
        max_budget = float(tf.evaluate_all_functions("{{xpath_max:company/departments/item/budget:enterprise_config.xml}}"))
        
        assert total_budget > 0
        assert 100000 <= avg_budget <= 500000
        assert 100000 <= max_budget <= 500000
        assert avg_budget <= max_budget
        
        # Test collection functions
        dept_names = tf.evaluate_all_functions("{{xpath_collect:company/departments/item/name:enterprise_config.xml}}")
        names = dept_names.split(',')
        assert len(names) == dept_count
        assert all(len(name.strip()) > 0 for name in names)
        
        # Test employee aggregations across all departments
        total_employees = int(tf.evaluate_all_functions("{{xpath_count:company/departments/item/employees/item:enterprise_config.xml}}"))
        assert total_employees >= dept_count * 2  # At least 2 employees per department
        
        total_salary_cost = float(tf.evaluate_all_functions("{{xpath_sum:company/departments/item/employees/item/salary:enterprise_config.xml}}"))
        avg_employee_salary = float(tf.evaluate_all_functions("{{xpath_avg:company/departments/item/employees/item/salary:enterprise_config.xml}}"))
        
        assert total_salary_cost > 0
        assert 30000 <= avg_employee_salary <= 150000  # salary data type range
    
    def test_xml_document_processing_workflow(self, temp_workspace):
        """Test XML document processing with mixed content types."""
        xml_generator = FileGeneratorFactory.create_generator('create_xml', str(temp_workspace))
        
        # Generate XML with mixed content
        result = xml_generator.generate(
            target_file="documents.xml",
            content_spec={
                'schema': {
                    'metadata': {
                        'total_docs': {'type': 'integer', 'minimum': 5, 'maximum': 15},
                        'created_date': 'date',
                        'version': 'version'
                    },
                    'documents': {
                        'type': 'array',
                        'count': 8,
                        'items': {
                            'title': 'product',
                            'author': 'person_name',
                            'category': 'category',
                            'size_kb': {'type': 'integer', 'minimum': 10, 'maximum': 5000},
                            'is_public': {'type': 'boolean'},
                            'tags': {
                                'type': 'array',
                                'count': [1, 4],
                                'items': 'lorem_word'
                            }
                        }
                    }
                },
                'root_element': 'library'
            }
        )
        
        assert result['errors'] == []
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Test metadata extraction
        total_docs = tf.evaluate_all_functions("{{xpath_value:metadata/total_docs:documents.xml}}")
        created_date = tf.evaluate_all_functions("{{xpath_value:metadata/created_date:documents.xml}}")
        
        assert 5 <= int(total_docs) <= 15
        assert len(created_date) == 10  # YYYY-MM-DD format
        
        # Test document count
        doc_count = int(tf.evaluate_all_functions("{{xpath_count:documents/item:documents.xml}}"))
        assert doc_count == 8
        
        # Test document size statistics
        total_size = float(tf.evaluate_all_functions("{{xpath_sum:documents/item/size_kb:documents.xml}}"))
        avg_size = float(tf.evaluate_all_functions("{{xpath_avg:documents/item/size_kb:documents.xml}}"))
        max_size = float(tf.evaluate_all_functions("{{xpath_max:documents/item/size_kb:documents.xml}}"))
        min_size = float(tf.evaluate_all_functions("{{xpath_min:documents/item/size_kb:documents.xml}}"))
        
        assert total_size > 0
        assert 10 <= avg_size <= 5000
        assert 10 <= max_size <= 5000
        assert 10 <= min_size <= 5000
        assert min_size <= avg_size <= max_size
        
        # Test author and title collection
        authors = tf.evaluate_all_functions("{{xpath_collect:documents/item/author:documents.xml}}")
        titles = tf.evaluate_all_functions("{{xpath_collect:documents/item/title:documents.xml}}")
        
        author_list = authors.split(',')
        title_list = titles.split(',')
        
        assert len(author_list) == 8
        assert len(title_list) == 8
        assert all(len(author.strip()) > 0 for author in author_list)
        assert all(len(title.strip()) > 0 for title in title_list)
        
        # Test boolean field verification
        public_docs = int(tf.evaluate_all_functions("{{xpath_count:documents/item[is_public='True']:documents.xml}}"))
        private_docs = int(tf.evaluate_all_functions("{{xpath_count:documents/item[is_public='False']:documents.xml}}"))
        
        assert public_docs + private_docs == 8
        assert public_docs >= 0
        assert private_docs >= 0
        
        # Test nested tag structure
        total_tags = int(tf.evaluate_all_functions("{{xpath_count:documents/item/tags/item:documents.xml}}"))
        assert 8 <= total_tags <= 32  # 8 docs * 1-4 tags each
    
    def test_xml_to_other_formats_comparison(self, temp_workspace):
        """Test XML data extraction compared to equivalent JSON/YAML operations."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Define same schema for XML, JSON, and YAML
        schema = {
            'products': {
                'type': 'array',
                'count': 5,
                'items': {
                    'id': {'type': 'integer', 'minimum': 1, 'maximum': 100},
                    'name': 'product',
                    'price': {'type': 'number', 'minimum': 10.0, 'maximum': 1000.0},
                    'in_stock': {'type': 'boolean'}
                }
            },
            'summary': {
                'total_products': {'type': 'integer', 'minimum': 5, 'maximum': 5}
            }
        }
        
        # Generate XML version
        xml_gen = FileGeneratorFactory.create_generator('create_xml', str(temp_workspace))
        xml_result = xml_gen.generate(
            target_file="products.xml",
            content_spec={'schema': schema, 'root_element': 'catalog'}
        )
        
        # Generate JSON version
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        json_result = json_gen.generate(
            target_file="products.json",
            content_spec={'schema': schema}
        )
        
        # Generate YAML version
        yaml_gen = FileGeneratorFactory.create_generator('create_yaml', str(temp_workspace))
        yaml_result = yaml_gen.generate(
            target_file="products.yaml",
            content_spec={'schema': schema}
        )
        
        assert xml_result['errors'] == []
        assert json_result['errors'] == []
        assert yaml_result['errors'] == []
        
        # Compare equivalent operations across formats
        
        # Count operations
        xml_product_count = int(tf.evaluate_all_functions("{{xpath_count:products/item:products.xml}}"))
        json_product_count = int(tf.evaluate_all_functions("{{json_count:$.products:products.json}}"))
        yaml_product_count = int(tf.evaluate_all_functions("{{yaml_count:$.products:products.yaml}}"))
        
        assert xml_product_count == json_product_count == yaml_product_count == 5
        
        # Summary value extraction
        xml_summary = tf.evaluate_all_functions("{{xpath_value:summary/total_products:products.xml}}")
        json_summary = tf.evaluate_all_functions("{{json_value:summary.total_products:products.json}}")
        yaml_summary = tf.evaluate_all_functions("{{yaml_value:summary.total_products:products.yaml}}")
        
        assert xml_summary == json_summary == yaml_summary == "5"
        
        # Aggregation comparisons (values will differ due to randomness, but ranges should be consistent)
        xml_price_sum = float(tf.evaluate_all_functions("{{xpath_sum:products/item/price:products.xml}}"))
        json_price_sum = float(tf.evaluate_all_functions("{{json_sum:$.products[*].price:products.json}}"))
        yaml_price_sum = float(tf.evaluate_all_functions("{{yaml_sum:$.products[*].price:products.yaml}}"))
        
        # All should be in valid ranges
        assert 50.0 <= xml_price_sum <= 5000.0  # 5 products * 10-1000 price range
        assert 50.0 <= json_price_sum <= 5000.0
        assert 50.0 <= yaml_price_sum <= 5000.0
        
        # Collection operations
        xml_names = tf.evaluate_all_functions("{{xpath_collect:products/item/name:products.xml}}")
        json_names = tf.evaluate_all_functions("{{json_collect:$.products[*].name:products.json}}")
        yaml_names = tf.evaluate_all_functions("{{yaml_collect:$.products[*].name:products.yaml}}")
        
        xml_name_list = xml_names.split(',')
        json_name_list = json_names.split(',')
        yaml_name_list = yaml_names.split(',')
        
        assert len(xml_name_list) == len(json_name_list) == len(yaml_name_list) == 5
        assert all(len(name.strip()) > 0 for name in xml_name_list)
        assert all(len(name.strip()) > 0 for name in json_name_list)
        assert all(len(name.strip()) > 0 for name in yaml_name_list)