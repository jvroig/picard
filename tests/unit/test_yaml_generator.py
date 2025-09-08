"""
Unit tests for YAMLFileGenerator.

Tests YAML file generation functionality with schema-driven generation.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import YAMLFileGenerator


@pytest.mark.unit
@pytest.mark.file_generation
class TestYAMLFileGenerator:
    """Test YAML file generation functionality."""
    
    def test_simple_yaml_generation(self, yaml_generator, temp_workspace):
        """Test basic YAML file generation with simple schema."""
        schema = {
            'message': 'lorem_words',
            'count': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'active': {'type': 'boolean'}
        }
        
        result = yaml_generator.generate(
            target_file="simple.yaml",
            content_spec={'schema': schema}
        )
        
        # Verify generation succeeded
        assert len(result['files_created']) == 1
        assert result['errors'] == []
        
        # Verify file was created
        target_file = temp_workspace / "simple.yaml"
        assert target_file.exists()
        
        # Verify YAML structure
        yaml_data = result['yaml_data'][str(target_file)]
        assert 'message' in yaml_data
        assert 'count' in yaml_data
        assert 'active' in yaml_data
        
        # Verify data types
        assert isinstance(yaml_data['message'], str)
        assert isinstance(yaml_data['count'], int)
        assert isinstance(yaml_data['active'], bool)
        
        # Verify constraints
        assert 1 <= yaml_data['count'] <= 100
        
        # Verify file content is valid YAML
        with open(target_file, 'r') as f:
            file_data = yaml.safe_load(f)
        assert file_data == yaml_data
    
    def test_array_generation(self, yaml_generator, temp_workspace):
        """Test YAML array generation with variable count."""
        schema = {
            'users': {
                'type': 'array',
                'count': '{{number1:2:4}}',  # Between 2-4 items using {{numeric}} variables
                'items': {
                    'id': 'id',
                    'name': 'person_name'
                }
            }
        }
        
        result = yaml_generator.generate(
            target_file="users.yaml", 
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        yaml_data = result['yaml_data'][str(temp_workspace / "users.yaml")]
        users = yaml_data['users']
        
        # Verify array constraints
        assert isinstance(users, list)
        assert 2 <= len(users) <= 4
        
        # Verify each user has required fields
        for user in users:
            assert 'id' in user
            assert 'name' in user
            assert isinstance(user['id'], str)  # Generated as string by data generator
            assert isinstance(user['name'], str)
    
    def test_nested_object_generation(self, yaml_generator, temp_workspace):
        """Test nested object generation."""
        schema = {
            'user': {
                'id': 'id',
                'profile': {
                    'age': 'age',
                    'location': {
                        'city': 'city',
                        'active': {'type': 'boolean'}
                    }
                }
            }
        }
        
        result = yaml_generator.generate(
            target_file="nested.yaml",
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        yaml_data = result['yaml_data'][str(temp_workspace / "nested.yaml")]
        
        # Verify nested structure
        assert 'user' in yaml_data
        user = yaml_data['user']
        
        assert 'id' in user
        assert 'profile' in user
        
        profile = user['profile']
        assert 'age' in profile
        assert 'location' in profile
        
        location = profile['location']
        assert 'city' in location
        assert 'active' in location
        assert isinstance(location['active'], bool)
    
    def test_default_schema_when_none_provided(self, yaml_generator, temp_workspace):
        """Test that default schema is used when none provided."""
        result = yaml_generator.generate(
            target_file="default.yaml",
            content_spec={}  # No schema provided
        )
        
        assert result['errors'] == []
        
        yaml_data = result['yaml_data'][str(temp_workspace / "default.yaml")]
        
        # Should have default fields
        assert 'message' in yaml_data
        assert 'timestamp' in yaml_data
        assert 'id' in yaml_data
        
        assert isinstance(yaml_data['message'], str)
        assert isinstance(yaml_data['timestamp'], str)
        assert isinstance(yaml_data['id'], str)
    
    def test_yaml_formatting_consistency(self, yaml_generator, temp_workspace):
        """Test that generated YAML follows consistent formatting."""
        schema = {
            'database': {
                'host': 'city',
                'port': {'type': 'integer', 'minimum': 1000, 'maximum': 9999},
                'users': {
                    'type': 'array',
                    'count': 2,
                    'items': {
                        'name': 'person_name',
                        'active': {'type': 'boolean'}
                    }
                }
            }
        }
        
        result = yaml_generator.generate(
            target_file="config.yaml",
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        # Read the actual file content
        target_file = temp_workspace / "config.yaml"
        with open(target_file, 'r') as f:
            content = f.read()
        
        # Verify YAML formatting
        assert 'database:' in content  # Block style
        assert '  host:' in content    # 2-space indentation
        assert '  users:' in content
        assert '  - name:' in content  # Array items with dash
        
        # Verify no flow style (no {})
        assert '{' not in content
        assert '}' not in content
        
        # Verify content is valid and parses correctly
        parsed = yaml.safe_load(content)
        assert isinstance(parsed['database']['users'], list)
        assert len(parsed['database']['users']) == 2
    
    def test_clutter_generation(self, yaml_generator, temp_workspace):
        """Test clutter file generation functionality."""
        schema = {'test': 'lorem_words'}
        
        result = yaml_generator.generate(
            target_file="main.yaml",
            content_spec={'schema': schema},
            config={'clutter': {'count': 3}}
        )
        
        assert result['errors'] == []
        
        # Should have main file plus clutter files
        assert len(result['files_created']) >= 4  # 1 main + 3 clutter (minimum)
        
        # Verify clutter files were created
        clutter_files = [f for f in result['files_created'] if 'clutter_' in f]
        assert len(clutter_files) >= 3
        
        # Verify clutter files have expected extensions (random file types)
        valid_extensions = ['.yaml', '.yml', '.txt', '.log']
        for clutter_file in clutter_files:
            assert any(clutter_file.endswith(ext) for ext in valid_extensions), \
                f"Clutter file {clutter_file} has unexpected extension"
        
        # If any YAML clutter files exist, verify they're valid
        yaml_clutter = [f for f in clutter_files if f.endswith('.yaml') or f.endswith('.yml')]
        for yaml_file in yaml_clutter:
            with open(yaml_file, 'r') as f:
                clutter_data = yaml.safe_load(f)
            assert isinstance(clutter_data, dict)
            assert 'id' in clutter_data
            assert 'name' in clutter_data
        
        # Verify all clutter files exist and have content
        for clutter_file in clutter_files:
            assert Path(clutter_file).exists(), f"Clutter file {clutter_file} was not created"
            assert Path(clutter_file).stat().st_size > 0, f"Clutter file {clutter_file} is empty"