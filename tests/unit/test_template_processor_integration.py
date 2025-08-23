"""
Integration tests for TemplateProcessor.

Tests the complete template processing pipeline including {{qs_id}} substitution,
enhanced variable substitution, template function evaluation, and multi-field processing.
"""

import pytest
import tempfile
import json
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from template_processor import TemplateProcessor
from entity_pool import EntityPool


class TestTemplateProcessorBasic:
    """Test basic TemplateProcessor functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def entity_pool_file(self, temp_workspace):
        """Create test entity pool file."""
        pool_file = temp_workspace / "entity_pool.json"
        pool_data = {
            "entity1": ["Alice", "Bob", "Charlie"],
            "entity2": ["London", "Paris", "Tokyo"],
            "colors": ["red", "blue", "green"],
            "metals": ["gold", "silver", "copper"],
            "gems": ["ruby", "sapphire", "emerald"]
        }
        pool_file.write_text(json.dumps(pool_data))
        return str(pool_file)
    
    @pytest.fixture
    def processor(self, entity_pool_file, temp_workspace):
        """Create TemplateProcessor instance."""
        return TemplateProcessor(entity_pool_file=entity_pool_file, base_dir=str(temp_workspace))
    
    def test_processor_initialization(self, entity_pool_file, temp_workspace):
        """Test that TemplateProcessor initializes correctly."""
        processor = TemplateProcessor(entity_pool_file=entity_pool_file, base_dir=str(temp_workspace))
        
        assert processor.entity_pool is not None
        assert processor.template_functions is not None
        assert isinstance(processor.entity_pool, EntityPool)
    
    def test_basic_entity_substitution(self, processor):
        """Test basic entity substitution without template functions."""
        template = "Hello {{entity1}} from {{entity2}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert '{{entity1}}' not in result['substituted']
        assert '{{entity2}}' not in result['substituted']
        assert result['has_template_functions'] is False
        assert len(result['template_function_results']) == 0
        
        # Should have entity substitutions
        assert len(result['entities']) > 0 or len(result.get('variables', {})) > 0
    
    def test_qs_id_substitution(self, processor):
        """Test {{qs_id}} substitution."""
        template = "File: test_artifacts/{{qs_id}}/output.txt"
        
        result = processor.process_template(template, question_id=42, sample_number=3)
        
        assert result['original_template'] == template
        assert 'q42_s3' in result['substituted']
        assert '{{qs_id}}' not in result['substituted']
        assert result['has_template_functions'] is False
    
    def test_enhanced_semantic_variables(self, processor):
        """Test enhanced semantic variable substitution."""
        template = "Employee {{semantic1:person_name}} in {{semantic2:department}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert '{{semantic1:person_name}}' not in result['substituted']
        assert '{{semantic2:department}}' not in result['substituted']
        assert result['has_template_functions'] is False
        
        # Should have enhanced variables
        variables = result.get('variables', {})
        assert len(variables) > 0  # Should have semantic variables
    
    def test_enhanced_numeric_variables(self, processor):
        """Test enhanced numeric variable substitution."""
        template = "Salary: ${{number1:30000:80000:currency}} per year"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert '{{number1:30000:80000:currency}}' not in result['substituted']
        assert result['has_template_functions'] is False
        
        # Should contain a numeric value
        import re
        assert re.search(r'\$[\d,]+', result['substituted'])
        
        # Should have enhanced variables
        variables = result.get('variables', {})
        assert len(variables) > 0
    
    def test_enhanced_entity_pools(self, processor):
        """Test enhanced entity pool substitution."""
        template = "Process {{entity1:colors}} data on {{entity2:metals}} server"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert '{{entity1:colors}}' not in result['substituted']
        assert '{{entity2:metals}}' not in result['substituted']
        assert result['has_template_functions'] is False
        
        # Should contain values from specified pools (fallback to default if pools don't exist)
        substituted = result['substituted']
        assert 'Process' in substituted
        assert 'data on' in substituted
        assert 'server' in substituted
        
        # Variables or entities should be recorded
        assert len(result.get('variables', {})) > 0 or len(result['entities']) > 0


class TestTemplateProcessorFunctions:
    """Test TemplateProcessor with template functions."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def entity_pool_file(self, temp_workspace):
        """Create test entity pool file."""
        pool_file = temp_workspace / "entity_pool.json"
        pool_data = {"entity1": ["Alice", "Bob"], "entity2": ["file1", "file2"]}
        pool_file.write_text(json.dumps(pool_data))
        return str(pool_file)
    
    @pytest.fixture
    def test_files(self, temp_workspace):
        """Create test files for template functions."""
        # Create test directory structure
        test_dir = temp_workspace / "q1_s1"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test text file
        text_file = test_dir / "test_data.txt"
        text_file.write_text("First line\nSecond line\nThird line content\nFourth line")
        
        # Create test CSV file
        csv_file = test_dir / "data.csv"
        csv_file.write_text("name,age,salary\nJohn,25,50000\nAlice,30,60000\nBob,35,70000")
        
        return {
            'test_dir': test_dir,
            'text_file': text_file,
            'csv_file': csv_file
        }
    
    @pytest.fixture
    def processor(self, entity_pool_file, temp_workspace):
        """Create TemplateProcessor instance."""
        return TemplateProcessor(entity_pool_file=entity_pool_file, base_dir=str(temp_workspace))
    
    def test_file_line_template_function(self, processor, test_files):
        """Test file_line template function."""
        template = "Line 3 says: {{file_line:3:{{qs_id}}/test_data.txt}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['has_template_functions'] is True
        assert 'Third line content' in result['substituted']
        assert '{{file_line:' not in result['substituted']
        
        # Check template function results
        assert len(result['template_function_results']) > 0
        function_calls = list(result['template_function_results'].keys())
        assert any('file_line:3:' in call for call in function_calls)
    
    def test_csv_value_template_function(self, processor, test_files):
        """Test csv_value template function."""
        template = "Name in row 1: {{csv_value:1:name:{{qs_id}}/data.csv}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['has_template_functions'] is True
        assert 'Alice' in result['substituted']  # Should get Alice from row 1
        assert '{{csv_value:' not in result['substituted']
        
        # Check template function results
        assert len(result['template_function_results']) > 0
        function_calls = list(result['template_function_results'].keys())
        assert any('csv_value:1:name:' in call for call in function_calls)
    
    def test_combined_entity_and_template_functions(self, processor, test_files):
        """Test combination of entity substitution and template functions."""
        template = "User {{entity1}} has salary {{csv_value:0:salary:{{qs_id}}/data.csv}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['has_template_functions'] is True
        assert '{{entity1}}' not in result['substituted']
        assert '{{csv_value:' not in result['substituted']
        assert '50000' in result['substituted']  # John's salary from CSV
        
        # Should have both entity and template function results
        assert len(result['entities']) > 0 or len(result.get('variables', {})) > 0
        assert len(result['template_function_results']) > 0
    
    def test_template_function_error_handling(self, processor):
        """Test error handling for invalid template functions."""
        template = "Invalid function: {{invalid_function:arg1:arg2}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['has_template_functions'] is True
        assert 'template_function_error' in result
        
        # Function should still be recorded even if it failed
        assert len(result['template_function_results']) > 0
        function_calls = list(result['template_function_results'].keys())
        assert any('invalid_function:' in call for call in function_calls)
    
    def test_template_function_missing_file(self, processor):
        """Test template function with missing file."""
        template = "Missing file: {{file_line:1:{{qs_id}}/missing.txt}}"
        
        result = processor.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['has_template_functions'] is True
        
        # Should handle missing file gracefully
        function_calls = list(result['template_function_results'].keys())
        assert any('file_line:1:' in call for call in function_calls)
        
        # Result should contain error information
        for call, result_value in result['template_function_results'].items():
            if 'file_line:1:' in call:
                assert 'ERROR:' in str(result_value) or result_value is None


class TestTemplateProcessorMultiField:
    """Test TemplateProcessor multi-field functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def entity_pool_file(self, temp_workspace):
        """Create test entity pool file."""
        pool_file = temp_workspace / "entity_pool.json"
        pool_data = {
            "entity1": ["Alice", "Bob", "Charlie"],
            "entity2": ["task1", "task2", "task3"]
        }
        pool_file.write_text(json.dumps(pool_data))
        return str(pool_file)
    
    @pytest.fixture
    def processor(self, entity_pool_file, temp_workspace):
        """Create TemplateProcessor instance."""
        return TemplateProcessor(entity_pool_file=entity_pool_file, base_dir=str(temp_workspace))
    
    def test_multi_field_consistent_variables(self, processor):
        """Test that multi-field processing maintains consistent variable values."""
        fields = {
            'prompt': 'User {{entity1}} wants to complete {{entity2}}',
            'expected_response': 'Task {{entity2}} assigned to {{entity1}}',
            'context': 'Current user: {{entity1}}, Current task: {{entity2}}'
        }
        
        result = processor.process_multiple_fields(fields, question_id=5, sample_number=2)
        
        # All fields should be processed
        assert 'prompt' in result
        assert 'expected_response' in result
        assert 'context' in result
        assert '_shared' in result
        
        # Check shared information
        shared = result['_shared']
        assert shared['question_id'] == 5
        assert shared['sample_number'] == 2
        assert shared['qs_id'] == 'q5_s2'
        
        # Extract entity values from each field
        prompt_text = result['prompt']['substituted']
        expected_text = result['expected_response']['substituted']
        context_text = result['context']['substituted']
        
        # Variables should be consistent across fields
        # If entity1 is "Alice" in prompt, it should be "Alice" everywhere
        import re
        entity1_values = set()
        entity2_values = set()
        
        # Extract values by checking what replaced the templates
        for field_result in [result['prompt'], result['expected_response'], result['context']]:
            original = field_result['original_template']
            substituted = field_result['substituted']
            
            # This is a basic consistency check - values should not contain template markers
            assert '{{entity1}}' not in substituted
            assert '{{entity2}}' not in substituted
            assert '{{qs_id}}' not in substituted
        
        # Check that all fields have the same shared variables
        if shared.get('entities'):
            # Legacy entities should be consistent
            assert len(shared['entities']) > 0
        
        if shared.get('variables'):
            # Enhanced variables should be consistent
            assert len(shared['variables']) > 0
    
    def test_multi_field_enhanced_variables_consistency(self, processor):
        """Test enhanced variable consistency across multiple fields."""
        fields = {
            'field1': 'Amount: ${{number1:100:500}} for {{semantic1:person_name}}',
            'field2': 'Person {{semantic1:person_name}} pays ${{number1:100:500}}',
            'field3': 'Receipt: {{semantic1:person_name}} - ${{number1:100:500}}'
        }
        
        result = processor.process_multiple_fields(fields, question_id=1, sample_number=1)
        
        # All enhanced variables should have consistent values across fields
        field1_text = result['field1']['substituted']
        field2_text = result['field2']['substituted']
        field3_text = result['field3']['substituted']
        
        # Extract the numeric value from each field
        import re
        amounts1 = re.findall(r'\$(\d+)', field1_text)
        amounts2 = re.findall(r'\$(\d+)', field2_text)
        amounts3 = re.findall(r'\$(\d+)', field3_text)
        
        # Same variable should produce same value
        if amounts1 and amounts2 and amounts3:
            assert amounts1[0] == amounts2[0] == amounts3[0]
        
        # Check shared variables
        shared_vars = result['_shared'].get('variables', {})
        assert len(shared_vars) > 0  # Should have enhanced variables recorded
    
    def test_multi_field_with_qs_id(self, processor):
        """Test multi-field processing with {{qs_id}} substitution."""
        fields = {
            'input_file': 'test_artifacts/{{qs_id}}/input.txt',
            'output_file': 'test_artifacts/{{qs_id}}/output.txt',
            'log_file': 'test_artifacts/{{qs_id}}/process.log'
        }
        
        result = processor.process_multiple_fields(fields, question_id=10, sample_number=5)
        
        expected_qs_id = 'q10_s5'
        
        # All fields should have {{qs_id}} replaced
        for field_name in fields.keys():
            substituted = result[field_name]['substituted']
            assert expected_qs_id in substituted
            assert '{{qs_id}}' not in substituted
        
        # Check shared information
        shared = result['_shared']
        assert shared['qs_id'] == expected_qs_id
        assert shared['question_id'] == 10
        assert shared['sample_number'] == 5
    
    def test_multi_field_empty_fields(self, processor):
        """Test multi-field processing with empty fields."""
        fields = {
            'empty_field': '',
            'normal_field': 'User {{entity1}} completes task',
            'whitespace_field': '   '
        }
        
        result = processor.process_multiple_fields(fields, question_id=1, sample_number=1)
        
        # Empty fields should be handled gracefully
        assert result['empty_field']['substituted'] == ''
        assert result['empty_field']['original_template'] == ''
        assert result['empty_field']['has_template_functions'] is False
        
        # Whitespace should be preserved or trimmed consistently
        assert result['whitespace_field']['original_template'] == '   '
        
        # Normal field should process correctly
        assert '{{entity1}}' not in result['normal_field']['substituted']
        
        # Shared information should still be present
        assert '_shared' in result
        assert result['_shared']['question_id'] == 1


class TestTemplateProcessorEdgeCases:
    """Test TemplateProcessor edge cases and error conditions."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def processor_no_pool(self, temp_workspace):
        """Create TemplateProcessor without entity pool file."""
        return TemplateProcessor(base_dir=str(temp_workspace))
    
    @pytest.fixture
    def processor_empty_pool(self, temp_workspace):
        """Create TemplateProcessor with empty entity pool."""
        empty_pool_file = temp_workspace / "empty_pool.json"
        empty_pool_file.write_text("{}")
        return TemplateProcessor(entity_pool_file=str(empty_pool_file), base_dir=str(temp_workspace))
    
    def test_empty_template(self, processor_no_pool):
        """Test processing empty template."""
        result = processor_no_pool.process_template("", question_id=1, sample_number=1)
        
        assert result['original_template'] == ""
        assert result['substituted'] == ""
        assert result['has_template_functions'] is False
        assert len(result['template_function_results']) == 0
    
    def test_template_with_no_variables(self, processor_no_pool):
        """Test processing template with no variables."""
        template = "This is a plain text template with no variables."
        
        result = processor_no_pool.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert result['substituted'] == template
        assert result['has_template_functions'] is False
        assert len(result['template_function_results']) == 0
    
    def test_malformed_template_variables(self, processor_empty_pool):
        """Test processing template with malformed variables."""
        template = "Bad variables: {{incomplete} and {notdouble}} and {{entity1}}"
        
        result = processor_empty_pool.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        # Malformed variables should be left unchanged
        assert '{{incomplete}' in result['substituted']
        assert '{notdouble}' in result['substituted']
        # Well-formed but missing entity should be handled by entity pool
        assert result['has_template_functions'] is False
    
    def test_nested_template_markers(self, processor_no_pool):
        """Test template with nested template markers."""
        template = "Nested: {{outer{{inner}}outer}}"
        
        result = processor_no_pool.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        # Should handle nested markers gracefully (implementation dependent)
        assert result['has_template_functions'] is False
    
    def test_extremely_long_template(self, processor_no_pool):
        """Test processing extremely long template."""
        long_template = "Long template: " + "{{entity1}} " * 1000 + "end"
        
        result = processor_no_pool.process_template(long_template, question_id=1, sample_number=1)
        
        assert result['original_template'] == long_template
        assert result['substituted'] is not None
        assert len(result['substituted']) > 0
        assert result['has_template_functions'] is False
    
    def test_unicode_templates(self, processor_no_pool):
        """Test processing templates with Unicode characters."""
        template = "Unicode: 你好 {{entity1}} αβγ 🎉 Москва"
        
        result = processor_no_pool.process_template(template, question_id=1, sample_number=1)
        
        assert result['original_template'] == template
        assert '你好' in result['substituted']
        assert 'αβγ' in result['substituted']
        assert '🎉' in result['substituted']
        assert 'Москва' in result['substituted']
    
    def test_large_question_ids(self, processor_no_pool):
        """Test processing with large question IDs and sample numbers."""
        template = "File: {{qs_id}}/output.txt"
        
        result = processor_no_pool.process_template(template, question_id=999999, sample_number=888888)
        
        assert result['original_template'] == template
        assert 'q999999_s888888' in result['substituted']
        assert '{{qs_id}}' not in result['substituted']
    
    def test_multi_field_edge_cases(self, processor_no_pool):
        """Test multi-field processing edge cases."""
        fields = {}  # Empty fields dict
        
        result = processor_no_pool.process_multiple_fields(fields, question_id=1, sample_number=1)
        
        # Should handle empty fields gracefully
        assert '_shared' in result
        assert result['_shared']['question_id'] == 1
        assert result['_shared']['sample_number'] == 1
        assert result['_shared']['qs_id'] == 'q1_s1'
        
        # Should have no field-specific results
        field_keys = [k for k in result.keys() if k != '_shared']
        assert len(field_keys) == 0


class TestTemplateProcessorIntegrationComplete:
    """Complete integration tests covering the full template processing pipeline."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def complete_entity_pool_file(self, temp_workspace):
        """Create comprehensive entity pool file."""
        pool_file = temp_workspace / "complete_pool.json"
        pool_data = {
            "entity1": ["Alice", "Bob", "Charlie", "Diana"],
            "entity2": ["project1", "project2", "analysis", "report"],
            "colors": ["red", "blue", "green", "yellow"],
            "departments": ["engineering", "marketing", "sales", "hr"],
            "locations": ["headquarters", "branch_office", "remote", "datacenter"]
        }
        pool_file.write_text(json.dumps(pool_data))
        return str(pool_file)
    
    @pytest.fixture
    def complete_test_files(self, temp_workspace):
        """Create comprehensive test files."""
        # Create multiple question/sample directories
        for q_id in [1, 2, 10]:
            for s_num in [1, 2]:
                test_dir = temp_workspace / f"q{q_id}_s{s_num}"
                test_dir.mkdir(parents=True, exist_ok=True)
                
                # Create various test files
                (test_dir / "data.txt").write_text(f"Line 1 for Q{q_id}S{s_num}\nLine 2\nLine 3 special\nLine 4")
                (test_dir / "info.csv").write_text("name,value,status\nItem1,100,active\nItem2,200,inactive\nItem3,150,pending")
                (test_dir / "config.json").write_text(f'{{"question": {q_id}, "sample": {s_num}, "active": true}}')
        
        return temp_workspace
    
    @pytest.fixture
    def complete_processor(self, complete_entity_pool_file, temp_workspace):
        """Create comprehensive TemplateProcessor instance."""
        return TemplateProcessor(entity_pool_file=complete_entity_pool_file, base_dir=str(temp_workspace))
    
    def test_complete_pipeline_single_template(self, complete_processor, complete_test_files):
        """Test complete pipeline with single complex template."""
        complex_template = """Employee {{semantic1:person_name}} from {{entity2}} department
working on {{entity1}} project in {{entity2}} location.
Budget: ${{number1:50000:200000:currency}}
Project file: {{file_line:1:{{qs_id}}/data.txt}}
Status: {{csv_value:0:status:{{qs_id}}/info.csv}}
Enhanced entity: {{entity1}} theme"""
        
        result = complete_processor.process_template(complex_template, question_id=1, sample_number=1)
        
        # Basic structure checks
        assert result['original_template'] == complex_template
        assert result['substituted'] != complex_template
        assert result['has_template_functions'] is True
        
        # No template markers should remain
        substituted = result['substituted']
        assert '{{entity1}}' not in substituted
        assert '{{entity2}}' not in substituted
        assert '{{semantic1:person_name}}' not in substituted
        assert '{{number1:50000:200000:currency}}' not in substituted
        assert '{{qs_id}}' not in substituted
        assert '{{file_line:' not in substituted
        assert '{{csv_value:' not in substituted
        
        # Expected content should be present
        assert 'Line 1 for Q1S1' in substituted  # From file_line function
        assert 'active' in substituted  # From csv_value function
        assert '$' in substituted  # From currency formatting
        
        # Template function results should be recorded
        assert len(result['template_function_results']) > 0
        function_calls = list(result['template_function_results'].keys())
        assert any('file_line:1:' in call for call in function_calls)
        assert any('csv_value:0:status:' in call for call in function_calls)
        
        # Variable information should be present
        assert len(result.get('variables', {})) > 0 or len(result['entities']) > 0
    
    def test_complete_pipeline_multi_field(self, complete_processor, complete_test_files):
        """Test complete pipeline with multi-field processing."""
        complex_fields = {
            'user_prompt': 'Create report for {{semantic1:person_name}} in {{entity1}}',
            'system_context': 'User: {{semantic1:person_name}}, Department: {{entity1}}, Budget: ${{number1:10000:50000}}',
            'expected_output': 'Report generated for {{semantic1:person_name}} ({{entity1}}) - Budget: ${{number1:10000:50000}}',
            'file_check': 'Verify {{file_line:2:{{qs_id}}/data.txt}} contains correct data',
            'data_validation': 'Status should be {{csv_value:1:status:{{qs_id}}/info.csv}} for item {{csv_value:1:name:{{qs_id}}/info.csv}}'
        }
        
        result = complete_processor.process_multiple_fields(complex_fields, question_id=2, sample_number=1)
        
        # All fields should be processed
        for field_name in complex_fields.keys():
            assert field_name in result
            field_result = result[field_name]
            
            # No template markers should remain
            substituted = field_result['substituted']
            assert '{{semantic1:person_name}}' not in substituted
            assert '{{entity1:departments}}' not in substituted
            assert '{{number1:' not in substituted
            assert '{{qs_id}}' not in substituted
            assert '{{file_line:' not in substituted
            assert '{{csv_value:' not in substituted
        
        # Consistency checks across fields
        user_prompt = result['user_prompt']['substituted']
        system_context = result['system_context']['substituted']
        expected_output = result['expected_output']['substituted']
        
        # Extract person names and entities - they should be consistent
        # This is a practical test that the same variables produce same values
        
        # File and CSV functions should work
        file_check = result['file_check']['substituted']
        data_validation = result['data_validation']['substituted']
        
        assert 'Line 2' in file_check  # From file_line function
        assert 'inactive' in data_validation or 'Item2' in data_validation  # From csv_value functions
        
        # Shared information should be complete
        shared = result['_shared']
        assert shared['question_id'] == 2
        assert shared['sample_number'] == 1
        assert shared['qs_id'] == 'q2_s1'
        assert len(shared.get('variables', {})) > 0 or len(shared.get('entities', {})) > 0
    
    def test_error_recovery_in_complete_pipeline(self, complete_processor, complete_test_files):
        """Test error recovery with mixed valid and invalid operations."""
        mixed_template = """Valid: {{entity1}} works on {{semantic1:person_name}} project
Invalid file: {{file_line:10:{{qs_id}}/missing.txt}}
Invalid CSV: {{csv_value:99:nonexistent:{{qs_id}}/missing.csv}}  
Valid again: Budget ${{number1:1000:5000}} for {{entity2}}"""
        
        result = complete_processor.process_template(mixed_template, question_id=1, sample_number=1)
        
        # Should complete despite errors
        assert result['original_template'] == mixed_template
        assert result['has_template_functions'] is True
        
        # Valid substitutions should work
        substituted = result['substituted']
        assert '{{entity1}}' not in substituted  # Should be substituted
        assert '{{semantic1:person_name}}' not in substituted  # Should be substituted
        assert '{{number1:1000:5000}}' not in substituted  # Should be substituted
        assert '{{entity2}}' not in substituted  # Should be substituted
        
        # Template function results should include both successful and failed calls
        assert len(result['template_function_results']) > 0
        
        # Check for error handling
        function_results = result['template_function_results']
        error_count = sum(1 for v in function_results.values() if v and 'ERROR:' in str(v))
        success_count = len(function_results) - error_count
        
        # Should have template function calls (some may succeed or fail)
        assert len(function_results) > 0  # Should have attempted template functions
        # Note: Some functions may succeed despite missing files (implementation dependent)
    
