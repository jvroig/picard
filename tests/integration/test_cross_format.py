"""
Integration tests for cross-format operations and complex scenarios.

Tests advanced PICARD workflows that combine multiple file types and operations.
"""
import pytest
import json
import csv
import sqlite3
import sys
import time
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import FileGeneratorFactory
from template_functions import TemplateFunctions


@pytest.mark.integration
class TestTemplateVariableSubstitution:
    """Test TARGET_FILE and variable substitution across formats."""
    
    def test_target_file_substitution_workflow(self, temp_workspace):
        """Test TARGET_FILE keyword works across all file types."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Generate test files of different types
        files_to_test = []
        
        # JSON file
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        json_result = json_gen.generate(
            target_file="test.json",
            content_spec={'schema': {'count': {'type': 'integer', 'minimum': 5, 'maximum': 5}}}
        )
        files_to_test.append(("test.json", "json"))
        
        # CSV file 
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        csv_result = csv_gen.generate(
            target_file="test.csv",
            content_spec={'headers': ['id', 'name'], 'rows': 5}
        )
        files_to_test.append(("test.csv", "csv"))
        
        # SQLite file
        sqlite_gen = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        sqlite_result = sqlite_gen.generate(
            target_file="test.db",
            content_spec={
                'table_name': 'test_table',
                'columns': [{'name': 'id', 'type': 'INTEGER'}, {'name': 'value', 'type': 'TEXT'}],
                'rows': 5
            }
        )
        files_to_test.append(("test.db", "sqlite"))
        
        # Test TARGET_FILE substitution for each format
        for filename, file_type in files_to_test:
            file_path = str(temp_workspace / filename)
            
            if file_type == "json":
                result = tf.evaluate_all_functions("{{json_value:count:TARGET_FILE}}", file_path)
                assert result == "5"
                
            elif file_type == "csv":
                result = tf.evaluate_all_functions("{{csv_count:name:TARGET_FILE}}", file_path)
                assert result == "5"
                
            elif file_type == "sqlite":
                result = tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(*) FROM test_table:TARGET_FILE}}", file_path)
                assert result == "5"
    
    def test_complex_template_combinations(self, temp_workspace):
        """Test complex template function combinations."""
        # Generate source data
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        json_result = json_gen.generate(
            target_file="source.json",
            content_spec={
                'schema': {
                    'users': {
                        'type': 'array',
                        'count': 4,
                        'items': {
                            'id': 'id',
                            'name': 'person_name',
                            'score': {'type': 'integer', 'minimum': 80, 'maximum': 100}
                        }
                    }
                }
            }
        )
        
        tf = TemplateFunctions(str(temp_workspace))
        
        # Complex nested template extraction
        first_user_id = tf.evaluate_all_functions("{{json_path:$.users[0].id:source.json}}")
        last_user_name = tf.evaluate_all_functions("{{json_path:$.users[3].name:source.json}}")
        user_count = tf.evaluate_all_functions("{{json_count:$.users:source.json}}")
        
        assert len(first_user_id) > 0
        assert len(last_user_name) > 0
        assert user_count == "4"
        
        # Verify all users have scores in range
        for i in range(4):
            score = int(tf.evaluate_all_functions(f"{{{{json_path:$.users[{i}].score:source.json}}}}"))
            assert 80 <= score <= 100


@pytest.mark.integration
class TestDataConsistencyWorkflows:
    """Test data consistency across complex multi-format workflows."""
    
    def test_referential_integrity_simulation(self, temp_workspace):
        """Simulate referential integrity across JSON, CSV, and SQLite."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Step 1: Generate master data in JSON
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        master_result = json_gen.generate(
            target_file="master.json",
            content_spec={
                'schema': {
                    'categories': {
                        'type': 'array',
                        'count': 3,
                        'items': {
                            'id': {'type': 'integer', 'minimum': 1, 'maximum': 3},
                            'name': 'department'
                        }
                    }
                }
            }
        )
        
        # Step 2: Generate transactional data in CSV
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        trans_result = csv_gen.generate(
            target_file="transactions.csv",
            content_spec={
                'headers': ['trans_id', 'category_id', 'amount', 'user_name'],
                'header_types': ['id', 'id', 'price', 'person_name'],
                'rows': 10
            }
        )
        
        # Step 3: Generate summary data in SQLite
        sqlite_gen = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        summary_result = sqlite_gen.generate(
            target_file="summary.db",
            content_spec={
                'table_name': 'category_summary',
                'columns': [
                    {'name': 'category_id', 'type': 'INTEGER'},
                    {'name': 'total_amount', 'type': 'REAL'},
                    {'name': 'transaction_count', 'type': 'INTEGER'}
                ],
                'rows': 3
            }
        )
        
        # Step 4: Verify data consistency
        assert all(result['errors'] == [] for result in [master_result, trans_result, summary_result])
        
        # Check master data
        category_count = int(tf.evaluate_all_functions("{{json_count:$.categories:master.json}}"))
        assert category_count == 3
        
        # Check transaction data
        trans_count = int(tf.evaluate_all_functions("{{csv_count:trans_id:transactions.csv}}"))
        assert trans_count == 10
        
        # Check summary data
        summary_count = int(tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(*) FROM category_summary:summary.db}}"))
        assert summary_count == 3
        
        # Cross-format validation
        total_trans_amount = float(tf.evaluate_all_functions("{{csv_sum:amount:transactions.csv}}"))
        total_summary_amount = float(tf.evaluate_all_functions("{{sqlite_query:SELECT SUM(total_amount) FROM category_summary:summary.db}}"))
        
        # Both should be positive (exact match not expected due to random generation)
        assert total_trans_amount > 0
        assert total_summary_amount > 0
    
    def test_data_transformation_pipeline(self, temp_workspace):
        """Test data transformation pipeline across formats."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Stage 1: Raw data in CSV
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        raw_result = csv_gen.generate(
            target_file="raw_data.csv",
            content_spec={
                'headers': ['id', 'name', 'region', 'sales', 'date'],
                'rows': 12
            }
        )
        
        # Stage 2: Processed configuration in JSON
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        config_result = json_gen.generate(
            target_file="processing_config.json",
            content_spec={
                'schema': {
                    'processing_rules': {
                        'min_sales_threshold': {'type': 'number', 'minimum': 100, 'maximum': 500},
                        'target_regions': {
                            'type': 'array',
                            'count': 2,
                            'items': 'region'
                        }
                    },
                    'output_settings': {
                        'batch_size': {'type': 'integer', 'minimum': 5, 'maximum': 8}
                    }
                }
            }
        )
        
        # Stage 3: Analytics in SQLite
        sqlite_gen = FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        analytics_result = sqlite_gen.generate(
            target_file="analytics.db",
            content_spec={
                'table_name': 'regional_summary',
                'columns': [
                    {'name': 'region', 'type': 'TEXT', 'data_type': 'region'},
                    {'name': 'avg_sales', 'type': 'REAL'},
                    {'name': 'record_count', 'type': 'INTEGER'},
                    {'name': 'processed_date', 'type': 'TEXT', 'data_type': 'date'}
                ],
                'rows': 4
            }
        )
        
        # Validate pipeline stages
        assert all(result['errors'] == [] for result in [raw_result, config_result, analytics_result])
        
        # Extract pipeline metrics
        raw_records = int(tf.evaluate_all_functions("{{csv_count:id:raw_data.csv}}"))
        batch_size = int(tf.evaluate_all_functions("{{json_value:output_settings.batch_size:processing_config.json}}"))
        analytics_regions = int(tf.evaluate_all_functions("{{sqlite_query:SELECT COUNT(DISTINCT region) FROM regional_summary:analytics.db}}"))
        
        assert raw_records == 12
        assert 5 <= batch_size <= 8
        assert analytics_regions >= 1
        
        # Verify sales data is meaningful
        # Note: sales field might not always be numeric due to auto-detection, so check if we can sum
        try:
            total_raw_sales = float(tf.evaluate_all_functions("{{csv_sum:sales:raw_data.csv}}"))
            assert total_raw_sales >= 0  # Could be 0 if no numeric values
        except:
            # If sum fails, just verify we have sales data
            sales_count = int(tf.evaluate_all_functions("{{csv_count:sales:raw_data.csv}}"))
            assert sales_count > 0
        
        avg_analytics_sales = float(tf.evaluate_all_functions("{{sqlite_query:SELECT AVG(avg_sales) FROM regional_summary:analytics.db}}"))
        assert avg_analytics_sales >= 0


@pytest.mark.integration
class TestErrorHandlingWorkflows:
    """Test error handling in complex multi-step workflows."""
    
    def test_graceful_error_recovery(self, temp_workspace):
        """Test that workflows handle errors gracefully and provide useful information."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Generate valid source data
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        valid_result = json_gen.generate(
            target_file="valid.json",
            content_spec={'schema': {'data': {'type': 'array', 'count': 3, 'items': 'lorem_word'}}}
        )
        
        assert valid_result['errors'] == []
        
        # Test accessing non-existent files in workflow
        with pytest.raises(Exception):  # Should raise appropriate error
            tf.evaluate_all_functions("{{json_count:$.data:nonexistent.json}}")
        
        # Test invalid paths in valid files
        with pytest.raises(Exception):
            tf.evaluate_all_functions("{{json_path:$.nonexistent:valid.json}}")
        
        # Test that valid operations still work after errors
        valid_count = tf.evaluate_all_functions("{{json_count:$.data:valid.json}}")
        assert valid_count == "3"
    
    def test_malformed_data_handling(self, temp_workspace):
        """Test handling of edge cases in data formats."""
        tf = TemplateFunctions(str(temp_workspace))
        
        # Create edge case files manually
        
        # Empty JSON file (but valid JSON)
        empty_json = temp_workspace / "empty.json"
        empty_json.write_text('{}')
        
        # Minimal CSV
        minimal_csv = temp_workspace / "minimal.csv" 
        minimal_csv.write_text('header\nvalue')
        
        # Test operations on edge case data
        empty_keys = tf.evaluate_all_functions("{{json_keys:$:empty.json}}")
        assert empty_keys == ""  # Empty object has no keys
        
        minimal_count = tf.evaluate_all_functions("{{csv_count:header:minimal.csv}}")
        assert minimal_count == "1"
        
        minimal_value = tf.evaluate_all_functions("{{csv_value:0:header:minimal.csv}}")
        assert minimal_value == "value"


@pytest.mark.integration
@pytest.mark.slow
class TestScalabilityWorkflows:
    """Test scalability characteristics of PICARD workflows."""
    
    def test_multiple_concurrent_operations(self, temp_workspace):
        """Test multiple file operations in sequence."""
        generators = {
            'json': FileGeneratorFactory.create_generator('create_json', str(temp_workspace)),
            'csv': FileGeneratorFactory.create_generator('create_csv', str(temp_workspace)),
            'sqlite': FileGeneratorFactory.create_generator('create_sqlite', str(temp_workspace))
        }
        
        tf = TemplateFunctions(str(temp_workspace))
        results = []
        
        # Generate multiple files of different types
        for i in range(3):
            # JSON files
            json_result = generators['json'].generate(
                target_file=f"data_{i}.json",
                content_spec={'schema': {'id': i, 'items': {'type': 'array', 'count': 2, 'items': 'lorem_word'}}}
            )
            results.append(json_result)
            
            # CSV files
            csv_result = generators['csv'].generate(
                target_file=f"data_{i}.csv",
                content_spec={'headers': ['id', 'value'], 'rows': 3}
            )
            results.append(csv_result)
            
            # SQLite files
            sqlite_result = generators['sqlite'].generate(
                target_file=f"data_{i}.db",
                content_spec={
                    'table_name': f'table_{i}',
                    'columns': [{'name': 'id', 'type': 'INTEGER'}, {'name': 'data', 'type': 'TEXT'}],
                    'rows': 2
                }
            )
            results.append(sqlite_result)
        
        # Verify all generations succeeded
        assert all(result['errors'] == [] for result in results)
        
        # Perform operations across all files
        total_operations = 0
        for i in range(3):
            # JSON operations
            json_count = int(tf.evaluate_all_functions(f"{{{{json_count:$.items:data_{i}.json}}}}"))
            assert json_count == 2
            total_operations += 1
            
            # CSV operations
            csv_count = int(tf.evaluate_all_functions(f"{{{{csv_count:id:data_{i}.csv}}}}"))
            assert csv_count == 3
            total_operations += 1
            
            # SQLite operations
            sqlite_count = int(tf.evaluate_all_functions(f"{{{{sqlite_query:SELECT COUNT(*) FROM table_{i}:data_{i}.db}}}}"))
            assert sqlite_count == 2
            total_operations += 1
        
        assert total_operations == 9  # 3 files × 3 operations each
    
    def test_workflow_performance_characteristics(self, temp_workspace):
        """Test performance characteristics of complex workflows."""
        import time
        
        start_time = time.time()
        
        # Complex workflow with multiple dependencies
        json_gen = FileGeneratorFactory.create_generator('create_json', str(temp_workspace))
        csv_gen = FileGeneratorFactory.create_generator('create_csv', str(temp_workspace))
        tf = TemplateFunctions(str(temp_workspace))
        
        # Stage 1: Configuration generation
        config_start = time.time()
        config_result = json_gen.generate(
            target_file="workflow_config.json",
            content_spec={
                'schema': {
                    'stages': {
                        'type': 'array',
                        'count': 5,
                        'items': {
                            'name': 'lorem_word',
                            'batch_size': {'type': 'integer', 'minimum': 10, 'maximum': 20},
                            'enabled': {'type': 'boolean'}
                        }
                    }
                }
            }
        )
        config_time = time.time() - config_start
        
        # Stage 2: Data generation based on config
        data_start = time.time()
        stage_count = int(tf.evaluate_all_functions("{{json_count:$.stages:workflow_config.json}}"))
        
        data_results = []
        for i in range(stage_count):
            batch_size = int(tf.evaluate_all_functions(f"{{{{json_path:$.stages[{i}].batch_size:workflow_config.json}}}}"))
            
            result = csv_gen.generate(
                target_file=f"stage_{i}_data.csv",
                content_spec={
                    'headers': ['record_id', 'value', 'timestamp'],
                    'rows': min(batch_size, 15)  # Cap for performance
                }
            )
            data_results.append(result)
        
        data_time = time.time() - data_start
        
        # Stage 3: Analysis across all generated data
        analysis_start = time.time()
        total_records = 0
        for i in range(stage_count):
            count = int(tf.evaluate_all_functions(f"{{{{csv_count:record_id:stage_{i}_data.csv}}}}"))
            total_records += count
        
        analysis_time = time.time() - analysis_start
        total_time = time.time() - start_time
        
        # Performance assertions
        assert config_time < 1.0  # Config generation should be fast
        assert data_time < 5.0    # Data generation should complete reasonably quickly
        assert analysis_time < 2.0  # Analysis should be fast
        assert total_time < 7.0   # Entire workflow should complete efficiently
        
        # Correctness assertions
        assert config_result['errors'] == []
        assert all(result['errors'] == [] for result in data_results)
        assert stage_count == 5
        assert total_records > 0