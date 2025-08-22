"""
Unit tests for precheck generation - catches integration bugs between components.

These tests would have caught the major bugs we encountered:
1. Circular dependency in enhanced variable substitution
2. {{semantic}} variables not substituting in expected_content
3. target_file not resolving {{semantic}} variables in sandbox generation
4. Variable inconsistency across properties
"""

import pytest
import tempfile
import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from precheck_generator import PrecheckGenerator


class TestPrecheckGenerator:
    """Test precheck generation with enhanced variable substitution."""
    
    @pytest.fixture
    def minimal_entity_pool_file(self):
        """Create a minimal entity pool for testing."""
        content = """# Test entity pool
red
blue
green
yellow
test
data
sample
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            return f.name
    
    @pytest.fixture
    def variable_test_config_file(self):
        """Create a test configuration file with enhanced variables."""
        config_content = """
name: "Variable Substitution Test"
test_id: "var_test"

tests:
  - question_id: 999
    samples: 1
    template: "Analyze {{semantic1:city}} data with {{semantic2:person_name}}"
    scoring_type: "readfile_stringmatch"
    file_to_read: "{{artifacts}}/{{qs_id}}/result_{{semantic1:city}}.txt"
    expected_content: "City: {{semantic1:city}}, Person: {{semantic2:person_name}}"
    files_to_check:
      - "{{artifacts}}/{{qs_id}}/check_{{semantic1:city}}.log"
    expected_structure:
      - "{{artifacts}}/{{qs_id}}/data_{{semantic1:city}}/"
    expected_response: "{{semantic2:person_name}} lives in {{semantic1:city}}"
    
    sandbox_setup:
      components:
        - type: "create_csv"
          name: "test_data"
          target_file: "{{artifacts}}/{{qs_id}}/data_{{semantic1:city}}.csv"
          content:
            headers: ["name", "city"]
            rows: "{{number1:20:30}}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            return f.name
    
    def test_enhanced_substitution_can_be_imported(self, minimal_entity_pool_file):
        """
        CRITICAL: Test that enhanced variable substitution can be imported and used.
        
        This test would have caught the circular dependency issue that prevented
        enhanced substitution from loading.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                base_dir=temp_dir
            )
            
            # Test that entity pool can load enhanced substitution
            enhanced_sub = generator.entity_pool._get_enhanced_substitution()
            assert enhanced_sub is not None, "Enhanced variable substitution failed to load - circular dependency issue!"
            
            # Test that it can actually substitute variables
            template = "Test {{semantic1:city}} and {{number1:10:20}}"
            result = enhanced_sub.substitute_all_variables(template)
            
            assert result['substituted'] != template
            assert 'semantic1:city' in result['variables']
            assert 'number1:10:20:integer' in result['variables']
    
    def test_semantic_variables_substitute_in_all_properties(self, minimal_entity_pool_file, variable_test_config_file):
        """
        CRITICAL: Test that {{semantic}} variables are substituted in ALL properties.
        
        This test would have caught the bug where expected_content, file_to_read,
        and other properties still contained unsubstituted {{semantic1:city}}.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                test_definitions_file=variable_test_config_file,
                base_dir=temp_dir
            )
            
            entries = generator.generate_precheck_entries()
            assert len(entries) == 1
            
            entry = entries[0]
            
            # Extract semantic variables from substituted question to verify they work
            substituted_question = entry['substituted_question']
            assert '{{semantic1:city}}' not in substituted_question, "semantic1:city not substituted in template!"
            assert '{{semantic2:person_name}}' not in substituted_question, "semantic2:person_name not substituted in template!"
            
            # CRITICAL: Verify all properties have variables substituted (these were the bugs)
            assert '{{semantic1:city}}' not in entry['file_to_read'], "semantic1:city not substituted in file_to_read!"
            assert '{{semantic2:person_name}}' not in entry['expected_content'], "semantic2:person_name not substituted in expected_content!"
            assert '{{semantic1:city}}' not in entry['expected_content'], "semantic1:city not substituted in expected_content!"
            
            # Check files_to_check
            files_to_check = entry.get('files_to_check', [])
            for file_path in files_to_check:
                assert '{{semantic1:city}}' not in file_path, f"semantic1:city not substituted in files_to_check: {file_path}"
            
            # Check expected_structure -> expected_paths
            expected_paths = entry.get('expected_paths', [])
            for path in expected_paths:
                assert '{{semantic1:city}}' not in path, f"semantic1:city not substituted in expected_structure: {path}"
            
            # Check expected_response
            expected_response = entry.get('expected_response', '')
            assert '{{semantic1:city}}' not in expected_response, "semantic1:city not substituted in expected_response!"
            assert '{{semantic2:person_name}}' not in expected_response, "semantic2:person_name not substituted in expected_response!"
    
    def test_sandbox_target_file_resolution(self, minimal_entity_pool_file, variable_test_config_file):
        """
        CRITICAL: Test that target_file in sandbox components resolves variables properly.
        
        This test would have caught the bug where target_file_resolved showed
        "{{semantic1:city}}.csv" instead of actual city names like "Baltimore.csv".
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                test_definitions_file=variable_test_config_file,
                base_dir=temp_dir
            )
            
            entries = generator.generate_precheck_entries()
            entry = entries[0]
            
            # Check sandbox generation results
            sandbox_generation = entry.get('sandbox_generation', {})
            components = sandbox_generation.get('components', [])
            
            assert len(components) == 1, "Should have one sandbox component"
            component = components[0]
            
            # CRITICAL: Verify target_file_resolved has no unsubstituted variables
            target_file_resolved = component.get('target_file_resolved', '')
            assert '{{semantic1:city}}' not in target_file_resolved, f"target_file not resolved: {target_file_resolved}"
            assert target_file_resolved.endswith('.csv'), f"target_file should end with .csv: {target_file_resolved}"
            assert len(target_file_resolved) > 10, f"target_file seems too short (not resolved): {target_file_resolved}"
            
            # Verify files_created match target_file_resolved
            files_created = component.get('files_created', [])
            assert len(files_created) == 1, "Should have created one file"
            assert '{{semantic1:city}}' not in files_created[0], f"files_created contains unresolved variable: {files_created[0]}"
    
    def test_variable_consistency_across_properties(self, minimal_entity_pool_file, variable_test_config_file):
        """
        CRITICAL: Test that same semantic variables have same values across all properties.
        
        This test would have caught bugs where semantic1:city was "Boston" in the question
        but "Seattle" in expected_content due to inconsistent variable generation.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                test_definitions_file=variable_test_config_file,
                base_dir=temp_dir
            )
            
            entries = generator.generate_precheck_entries()
            entry = entries[0]
            
            # Extract city and person from different properties and verify they're consistent
            substituted_question = entry['substituted_question']
            expected_content = entry['expected_content']
            expected_response = entry['expected_response']
            
            # Find the city name in the question (after "Analyze " and before " data")
            import re
            city_match = re.search(r'Analyze ([A-Za-z ]+) data', substituted_question)
            person_match = re.search(r'with ([A-Za-z ]+)', substituted_question)
            
            assert city_match and person_match, f"Could not extract variables from: {substituted_question}"
            city_from_question = city_match.group(1)
            person_from_question = person_match.group(1)
            
            # Verify same values appear in all properties
            assert city_from_question in expected_content, f"City '{city_from_question}' from question not in expected_content: {expected_content}"
            assert person_from_question in expected_content, f"Person '{person_from_question}' from question not in expected_content: {expected_content}"
            assert city_from_question in expected_response, f"City '{city_from_question}' from question not in expected_response: {expected_response}"
            assert person_from_question in expected_response, f"Person '{person_from_question}' from question not in expected_response: {expected_response}"
            assert city_from_question in entry['file_to_read'], f"City '{city_from_question}' from question not in file_to_read: {entry['file_to_read']}"
    
    def test_numeric_variables_in_sandbox_generation(self, minimal_entity_pool_file, variable_test_config_file):
        """
        CRITICAL: Test that {{numeric}} variables work in sandbox content specs.
        
        This test would have caught the bug where CSV generators failed with
        "'str' object cannot be interpreted as an integer" when using {{number1:20:30}}.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                test_definitions_file=variable_test_config_file,
                base_dir=temp_dir
            )
            
            entries = generator.generate_precheck_entries()
            entry = entries[0]
            
            # Check that sandbox generation succeeded
            sandbox_generation = entry.get('sandbox_generation', {})
            assert sandbox_generation.get('generation_successful', False), "Sandbox generation should succeed"
            
            # Verify no errors from {{numeric}} variable processing
            errors = sandbox_generation.get('errors', [])
            numeric_errors = [e for e in errors if 'str' in str(e) and 'integer' in str(e)]
            assert len(numeric_errors) == 0, f"Found numeric conversion errors: {numeric_errors}"
            
            # Verify files were actually created
            components = sandbox_generation.get('components', [])
            if components:
                files_created = components[0].get('files_created', [])
                assert len(files_created) > 0, "Should have created at least one file"
    
    def test_simple_config_without_sandbox(self, minimal_entity_pool_file):
        """
        Test precheck generation with no sandbox components.
        
        This ensures our changes don't break simple configurations.
        """
        config_content = """
name: "Simple Test"
test_id: "simple"

tests:
  - question_id: 100
    samples: 1
    template: "Simple test with {{semantic1:city}}"
    scoring_type: "stringmatch"
    expected_response: "Test response for {{semantic1:city}}"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PrecheckGenerator(
                entity_pool_file=minimal_entity_pool_file,
                test_definitions_file=config_file,
                base_dir=temp_dir
            )
            
            entries = generator.generate_precheck_entries()
            assert len(entries) == 1
            
            entry = entries[0]
            
            # Should have substituted template and expected_response
            assert '{{semantic1:city}}' not in entry['substituted_question']
            assert '{{semantic1:city}}' not in entry['expected_response']
            
            # Should not have sandbox-related keys or they should be empty
            sandbox_gen = entry.get('sandbox_generation', {})
            if sandbox_gen:
                # If present, should be empty or have no components
                components = sandbox_gen.get('components', [])
                assert len(components) == 0
        
        # Clean up
        os.unlink(config_file)