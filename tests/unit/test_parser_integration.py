"""
Test Parser Integration

Tests integration between SandboxSetupParser and TestDefinitionParser.
"""
import pytest
from src.test_definition_parser import TestDefinitionParser


class TestParserIntegration:
    """Test integration between components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TestDefinitionParser()
    
    def test_legacy_syntax_integration(self):
        """Test legacy syntax through full parser."""
        yaml_content = """
tests:
  - question_id: 1
    samples: 3
    template: "Create CSV with {{semantic1:person_name}}"
    scoring_type: "readfile_stringmatch"
    file_to_read: "{{artifacts}}/{{qs_id}}/data.csv"
    expected_content: "{{semantic1:person_name}}"
    sandbox_setup:
      type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/data.csv"
      content:
        headers: ["name", "email", "age"]
        rows: 10
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        
        assert len(test_defs) == 1
        test_def = test_defs[0]
        
        # Legacy field should be populated
        assert test_def.sandbox_setup is not None
        assert test_def.sandbox_setup.type == "create_csv"
        
        # New field should also be populated for consistency
        assert test_def.sandbox_components is not None
        assert len(test_def.sandbox_components) == 1
        assert test_def.sandbox_components[0].type == "create_csv"
    
    def test_new_syntax_integration(self):
        """Test new multi-component syntax through full parser."""
        yaml_content = """
tests:
  - question_id: 2
    samples: 5
    template: "Process pipeline with {{semantic1:company}} data"
    scoring_type: "readfile_jsonmatch"
    file_to_read: "{{artifacts}}/{{qs_id}}/result.json"
    expected_content: '{"status": "complete"}'
    sandbox_setup:
      components:
        - type: "create_csv"
          target_file: "{{artifacts}}/{{qs_id}}/source_data.csv"
          content:
            headers: ["id", "name", "amount"]
            rows: 100
        - type: "create_json"
          target_file: "{{artifacts}}/{{qs_id}}/config.json"
          content:
            schema:
              type: "object"
              properties:
                database_url:
                  type: "string"
                  data_type: "entity_pool"
          depends_on: ["source_data"]
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        
        assert len(test_defs) == 1
        test_def = test_defs[0]
        
        # Legacy field should be None for new syntax
        assert test_def.sandbox_setup is None
        
        # New field should be populated
        assert test_def.sandbox_components is not None
        assert len(test_def.sandbox_components) == 2
        
        # Check first component
        csv_comp = test_def.sandbox_components[0]
        assert csv_comp.type == "create_csv"
        assert csv_comp.target_file == "{{artifacts}}/{{qs_id}}/source_data.csv"
        assert csv_comp.depends_on is None
        
        # Check second component
        json_comp = test_def.sandbox_components[1]
        assert json_comp.type == "create_json"
        assert json_comp.target_file == "{{artifacts}}/{{qs_id}}/config.json"
        assert json_comp.depends_on == ["source_data"]
    
    def test_to_dict_with_components(self):
        """Test to_dict serialization with components."""
        yaml_content = """
tests:
  - question_id: 3
    samples: 2
    template: "Multi-format test"
    scoring_type: "stringmatch"
    expected_response: "Success"
    sandbox_setup:
      components:
        - type: "create_csv"
          target_file: "test.csv"
          content:
            headers: ["id", "name"]
            rows: 5
        - type: "create_json"
          target_file: "test.json"
          content:
            schema:
              type: "object"
              properties:
                active:
                  type: "boolean"
                  data_type: "boolean"
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        test_def = test_defs[0]
        
        result = test_def.to_dict()
        
        # Check basic fields
        assert result['question_id'] == 3
        assert result['template'] == "Multi-format test"
        
        # Legacy sandbox_setup should not be present
        assert 'sandbox_setup' not in result
        
        # New sandbox_components should be present
        assert 'sandbox_components' in result
        components = result['sandbox_components']
        assert len(components) == 2
        
        # Check component structure
        csv_comp = components[0]
        assert csv_comp['type'] == "create_csv"
        assert csv_comp['target_file'] == "test.csv"
        
        json_comp = components[1]
        assert json_comp['type'] == "create_json"
        assert json_comp['target_file'] == "test.json"
    
    def test_mixed_tests_in_same_file(self):
        """Test file with both legacy and new syntax tests."""
        yaml_content = """
tests:
  - question_id: 1
    samples: 2
    template: "Legacy test"
    scoring_type: "stringmatch"
    expected_response: "Done"
    sandbox_setup:
      type: "create_csv"
      target_file: "legacy.csv"
      content:
        headers: ["id"]
        rows: 10
  
  - question_id: 2
    samples: 3
    template: "Modern test"
    scoring_type: "stringmatch"
    expected_response: "Complete"
    sandbox_setup:
      components:
        - type: "create_json"
          target_file: "modern.json"
          content:
            schema:
              type: "object"
              properties:
                status:
                  type: "string"
                  data_type: "status"
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        
        assert len(test_defs) == 2
        
        # First test (legacy)
        legacy_test = test_defs[0]
        assert legacy_test.question_id == 1
        assert legacy_test.sandbox_setup is not None
        assert legacy_test.sandbox_setup.type == "create_csv"
        assert legacy_test.sandbox_components is not None
        assert len(legacy_test.sandbox_components) == 1
        
        # Second test (new)
        modern_test = test_defs[1]
        assert modern_test.question_id == 2
        assert modern_test.sandbox_setup is None
        assert modern_test.sandbox_components is not None
        assert len(modern_test.sandbox_components) == 1
        assert modern_test.sandbox_components[0].type == "create_json"
    
    def test_validation_errors_propagate(self):
        """Test that validation errors from components propagate properly."""
        yaml_content = """
tests:
  - question_id: 1
    samples: 1
    template: "Test"
    scoring_type: "stringmatch"
    expected_response: "OK"
    sandbox_setup:
      components:
        - type: "create_csv"
          # Missing target_file - should trigger validation error
          content:
            headers: ["id"]
            rows: 1
"""
        
        with pytest.raises(ValueError, match="'target_file' required"):
            self.parser.parse_yaml_string(yaml_content)