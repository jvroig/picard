"""
Test Sandbox Setup Parser Compatibility

Tests both legacy syntax and new multi-component syntax to ensure backwards compatibility.
"""
import pytest
from src.test_definition_parser import SandboxSetupParser, ComponentSpec


class TestSandboxParserCompatibility:
    """Test backwards compatibility and new multi-component syntax."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SandboxSetupParser()
    
    def test_legacy_syntax_still_works(self):
        """Ensure existing tests don't break."""
        # Legacy CSV syntax
        legacy_config = {
            "type": "create_csv",
            "target_file": "{{artifacts}}/{{qs_id}}/data.csv",
            "content": {
                "headers": ["name", "email", "age"],
                "rows": 10
            },
            "clutter": {"debug": True}
        }
        
        components = self.parser.parse_sandbox_setup(legacy_config)
        
        assert len(components) == 1
        component = components[0]
        assert component.type == "create_csv"
        assert component.target_file == "{{artifacts}}/{{qs_id}}/data.csv"
        assert component.content == {"headers": ["name", "email", "age"], "rows": 10}
        assert component.config == {"debug": True}  # clutter mapped to config
        assert component.depends_on is None
    
    def test_legacy_json_syntax(self):
        """Test legacy JSON generator syntax."""
        legacy_config = {
            "type": "create_json",
            "target_file": "{{artifacts}}/{{qs_id}}/config.json",
            "content": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "data_type": "person_name"},
                        "active": {"type": "boolean", "data_type": "boolean"}
                    }
                }
            }
        }
        
        components = self.parser.parse_sandbox_setup(legacy_config)
        
        assert len(components) == 1
        component = components[0]
        assert component.type == "create_json"
        assert component.target_file == "{{artifacts}}/{{qs_id}}/config.json"
        assert "schema" in component.content
    
    def test_legacy_sqlite_syntax(self):
        """Test legacy SQLite generator syntax."""
        legacy_config = {
            "type": "create_sqlite",
            "target_file": "{{artifacts}}/{{qs_id}}/database.db",
            "content": {
                "table_name": "employees",
                "columns": [
                    {"name": "id", "type": "auto_id"},
                    {"name": "name", "type": "TEXT", "data_type": "person_name"}
                ],
                "rows": 20
            }
        }
        
        components = self.parser.parse_sandbox_setup(legacy_config)
        
        assert len(components) == 1
        component = components[0]
        assert component.type == "create_sqlite"
        assert component.content["table_name"] == "employees"
        assert len(component.content["columns"]) == 2
    
    def test_new_multi_component_syntax(self):
        """Validate new multi-component functionality."""
        multi_config = {
            "components": [
                {
                    "type": "create_csv",
                    "target_file": "{{artifacts}}/{{qs_id}}/source_data.csv",
                    "content": {
                        "headers": ["id", "name", "amount"],
                        "rows": 100
                    }
                },
                {
                    "type": "create_json",
                    "target_file": "{{artifacts}}/{{qs_id}}/config.json",
                    "content": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "database_url": {"type": "string", "data_type": "entity_pool"}
                            }
                        }
                    },
                    "depends_on": ["source_data"]
                }
            ]
        }
        
        components = self.parser.parse_sandbox_setup(multi_config)
        
        assert len(components) == 2
        
        # First component
        csv_component = components[0]
        assert csv_component.type == "create_csv"
        assert csv_component.target_file == "{{artifacts}}/{{qs_id}}/source_data.csv"
        assert csv_component.depends_on is None
        
        # Second component
        json_component = components[1]
        assert json_component.type == "create_json"
        assert json_component.target_file == "{{artifacts}}/{{qs_id}}/config.json"
        assert json_component.depends_on == ["source_data"]
    
    def test_mixed_component_types(self):
        """Test CSV + JSON + YAML combinations."""
        mixed_config = {
            "components": [
                {
                    "type": "create_csv",
                    "target_file": "{{artifacts}}/{{qs_id}}/employees.csv",
                    "content": {
                        "headers": ["id", "name", "department", "salary"],
                        "rows": 50
                    }
                },
                {
                    "type": "create_json",
                    "target_file": "{{artifacts}}/{{qs_id}}/pipeline_config.json",
                    "content": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "source_file": {"type": "string", "value": "employees.csv"},
                                "total_records": {"type": "number", "value": "{{csv_count:id:employees.csv}}"}
                            }
                        }
                    }
                },
                {
                    "type": "create_yaml", 
                    "target_file": "{{artifacts}}/{{qs_id}}/app_config.yaml",
                    "content": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "environment": {"type": "string", "data_type": "status"},
                                "database": {
                                    "type": "object",
                                    "properties": {
                                        "host": {"type": "string", "data_type": "city"},
                                        "port": {"type": "integer", "value": 5432}
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        components = self.parser.parse_sandbox_setup(mixed_config)
        
        assert len(components) == 3
        types = [comp.type for comp in components]
        assert "create_csv" in types
        assert "create_json" in types
        assert "create_yaml" in types
    
    def test_component_validation(self):
        """Test component validation logic."""
        # Missing type should raise error
        with pytest.raises(ValueError, match="must have 'type' field"):
            self.parser._parse_component({"target_file": "test.csv"})
        
        # File types without target_file should raise error
        with pytest.raises(ValueError, match="'target_file' required"):
            ComponentSpec(type="create_csv", content={"headers": ["id"]})
    
    def test_invalid_sandbox_config(self):
        """Test error handling for invalid configurations."""
        # Missing both 'type' and 'components'
        invalid_config = {
            "target_file": "test.csv",
            "content": {"headers": ["id"]}
        }
        
        with pytest.raises(ValueError, match="must have 'type' or 'components'"):
            self.parser.parse_sandbox_setup(invalid_config)
    
    def test_component_to_dict(self):
        """Test ComponentSpec to_dict conversion."""
        component = ComponentSpec(
            type="create_csv",
            target_file="test.csv",
            content={"headers": ["id", "name"]},
            config={"debug": True},
            depends_on=["other_component"]
        )
        
        result = component.to_dict()
        
        expected = {
            "type": "create_csv",
            "target_file": "test.csv", 
            "content": {"headers": ["id", "name"]},
            "config": {"debug": True},
            "depends_on": ["other_component"]
        }
        
        assert result == expected
    
    def test_component_to_dict_minimal(self):
        """Test ComponentSpec to_dict with minimal fields."""
        component = ComponentSpec(type="run_service")
        
        result = component.to_dict()
        
        assert result == {"type": "run_service"}
        assert "target_file" not in result
        assert "content" not in result
        assert "config" not in result
        assert "depends_on" not in result