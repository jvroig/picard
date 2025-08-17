"""
Test Parser Integration

Tests integration of TestDefinitionParser with current component-based syntax.
"""
import pytest
from src.test_definition_parser import TestDefinitionParser


class TestParserIntegration:
    """Test integration between components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TestDefinitionParser()
    
    def test_single_component_syntax(self):
        """Test single component syntax through full parser."""
        yaml_content = """
tests:
  - question_id: 1
    samples: 3
    template: "Create CSV with {{semantic1:person_name}}"
    scoring_type: "readfile_stringmatch"
    file_to_read: "{{artifacts}}/{{qs_id}}/data.csv"
    expected_content: "{{semantic1:person_name}}"
    sandbox_setup:
      components:
        - type: "create_csv"
          name: "main_data"
          target_file: "{{artifacts}}/{{qs_id}}/data.csv"
          content:
            headers: ["name", "email", "age"]
            rows: 10
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        
        assert len(test_defs) == 1
        test_def = test_defs[0]
        
        # Component should be populated
        assert test_def.sandbox_components is not None
        assert len(test_def.sandbox_components) == 1
        assert test_def.sandbox_components[0].type == "create_csv"
        assert test_def.sandbox_components[0].name == "main_data"
    
    def test_multi_component_syntax(self):
        """Test multi-component syntax through full parser."""
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
          name: "source_data"
          target_file: "{{artifacts}}/{{qs_id}}/source_data.csv"
          content:
            headers: ["id", "name", "amount"]
            rows: 100
        - type: "create_json"
          name: "config_data"
          target_file: "{{artifacts}}/{{qs_id}}/config.json"
          content:
            schema:
              database_url: "entity_pool"
          depends_on: ["source_data"]
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        
        assert len(test_defs) == 1
        test_def = test_defs[0]
        
        # Components should be populated
        assert test_def.sandbox_components is not None
        assert len(test_def.sandbox_components) == 2
        
        # Check first component
        csv_comp = test_def.sandbox_components[0]
        assert csv_comp.type == "create_csv"
        assert csv_comp.name == "source_data"
        assert csv_comp.target_file == "{{artifacts}}/{{qs_id}}/source_data.csv"
        assert csv_comp.depends_on is None
        
        # Check second component
        json_comp = test_def.sandbox_components[1]
        assert json_comp.type == "create_json"
        assert json_comp.name == "config_data"
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
          name: "csv_data"
          target_file: "test.csv"
          content:
            headers: ["id", "name"]
            rows: 5
        - type: "create_json"
          name: "json_config"
          target_file: "test.json"
          content:
            schema:
              active: "boolean"
"""
        
        test_defs = self.parser.parse_yaml_string(yaml_content)
        test_def = test_defs[0]
        
        result = test_def.to_dict()
        
        # Check basic fields
        assert result['question_id'] == 3
        assert result['template'] == "Multi-format test"
        
        # sandbox_components should be present
        assert 'sandbox_components' in result
        components = result['sandbox_components']
        assert len(components) == 2
        
        # Check component structure
        csv_comp = components[0]
        assert csv_comp['type'] == "create_csv"
        assert csv_comp['name'] == "csv_data"
        assert csv_comp['target_file'] == "test.csv"
        
        json_comp = components[1]
        assert json_comp['type'] == "create_json"
        assert json_comp['name'] == "json_config"
        assert json_comp['target_file'] == "test.json"
    
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
          name: "test_data"
          # Missing target_file - should trigger validation error
          content:
            headers: ["id"]
            rows: 1
"""
        
        with pytest.raises(ValueError, match="'target_file' required"):
            self.parser.parse_yaml_string(yaml_content)
    
    def test_missing_component_name_error(self):
        """Test that missing component name triggers validation error."""
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
          # Missing name - should trigger validation error
          target_file: "test.csv"
          content:
            headers: ["id"]
            rows: 1
"""
        
        with pytest.raises(ValueError, match="'name' field required"):
            self.parser.parse_yaml_string(yaml_content)
    
    def test_unsupported_syntax_error(self):
        """Test that old syntax without components array is rejected."""
        yaml_content = """
tests:
  - question_id: 1
    samples: 1
    template: "Test"
    scoring_type: "stringmatch"
    expected_response: "OK"
    sandbox_setup:
      type: "create_csv"
      target_file: "test.csv"
      content:
        headers: ["id"]
        rows: 1
"""
        
        with pytest.raises(ValueError, match="'sandbox_setup' must have 'components' array. Legacy syntax no longer supported."):
            self.parser.parse_yaml_string(yaml_content)