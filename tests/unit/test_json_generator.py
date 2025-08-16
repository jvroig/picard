"""
Unit tests for JSONFileGenerator.

This is our first pytest test to verify the testing infrastructure works.
"""
import pytest
import json
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import JSONFileGenerator


@pytest.mark.unit
@pytest.mark.file_generation
class TestJSONFileGenerator:
    """Test JSON file generation functionality."""
    
    def test_simple_json_generation(self, json_generator, temp_workspace):
        """Test basic JSON file generation with simple schema."""
        schema = {
            'message': 'lorem_words',
            'count': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'active': {'type': 'boolean'}
        }
        
        result = json_generator.generate(
            target_file="simple.json",
            content_spec={'schema': schema}
        )
        
        # Verify generation succeeded
        assert len(result['files_created']) == 1
        assert result['errors'] == []
        
        # Verify file was created
        target_file = temp_workspace / "simple.json"
        assert target_file.exists()
        
        # Verify JSON structure
        json_data = result['json_data'][str(target_file)]
        assert 'message' in json_data
        assert 'count' in json_data
        assert 'active' in json_data
        
        # Verify data types
        assert isinstance(json_data['message'], str)
        assert isinstance(json_data['count'], int)
        assert isinstance(json_data['active'], bool)
        
        # Verify constraints
        assert 1 <= json_data['count'] <= 100
    
    def test_array_generation(self, json_generator, temp_workspace):
        """Test JSON array generation with variable count."""
        schema = {
            'users': {
                'type': 'array',
                'count': [2, 4],  # Between 2-4 items
                'items': {
                    'id': 'id',
                    'name': 'person_name'
                }
            }
        }
        
        result = json_generator.generate(
            target_file="users.json", 
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        json_data = result['json_data'][str(temp_workspace / "users.json")]
        users = json_data['users']
        
        # Verify array constraints
        assert isinstance(users, list)
        assert 2 <= len(users) <= 4
        
        # Verify each user has required fields
        for user in users:
            assert 'id' in user
            assert 'name' in user
            assert isinstance(user['id'], str)  # Generated as string by data generator
            assert isinstance(user['name'], str)
    
    def test_nested_object_generation(self, json_generator, temp_workspace):
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
        
        result = json_generator.generate(
            target_file="nested.json",
            content_spec={'schema': schema}
        )
        
        assert result['errors'] == []
        
        json_data = result['json_data'][str(temp_workspace / "nested.json")]
        
        # Verify nested structure
        assert 'user' in json_data
        user = json_data['user']
        
        assert 'id' in user
        assert 'profile' in user
        
        profile = user['profile']
        assert 'age' in profile
        assert 'location' in profile
        
        location = profile['location']
        assert 'city' in location
        assert 'active' in location
        assert isinstance(location['active'], bool)
    
    def test_default_schema_when_none_provided(self, json_generator, temp_workspace):
        """Test that default schema is used when none provided."""
        result = json_generator.generate(
            target_file="default.json",
            content_spec={}  # No schema provided
        )
        
        assert result['errors'] == []
        
        json_data = result['json_data'][str(temp_workspace / "default.json")]
        
        # Should have default fields
        assert 'message' in json_data
        assert 'timestamp' in json_data
        assert 'id' in json_data
        
        assert isinstance(json_data['message'], str)
        assert isinstance(json_data['timestamp'], str)
        assert isinstance(json_data['id'], str)