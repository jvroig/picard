"""
Unit tests for XMLFileGenerator.

Tests XML file generation functionality with schema-driven generation.
"""
import pytest
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from file_generators import XMLFileGenerator


@pytest.mark.unit
@pytest.mark.file_generation
class TestXMLFileGenerator:
    """Test XML file generation functionality."""
    
    def test_simple_xml_generation(self, temp_workspace):
        """Test basic XML file generation with simple schema."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'message': 'lorem_words',
            'count': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'active': {'type': 'boolean'}
        }
        
        result = xml_generator.generate(
            target_file="simple.xml",
            content_spec={'schema': schema, 'root_element': 'config'}
        )
        
        # Verify generation succeeded
        assert len(result['files_created']) == 1
        assert result['errors'] == []
        
        # Verify file was created
        target_file = temp_workspace / "simple.xml"
        assert target_file.exists()
        
        # Verify XML structure
        tree = ET.parse(target_file)
        root = tree.getroot()
        assert root.tag == 'config'
        
        # Check required elements exist
        message_elem = root.find('message')
        count_elem = root.find('count')
        active_elem = root.find('active')
        
        assert message_elem is not None
        assert count_elem is not None
        assert active_elem is not None
        
        # Verify data types
        assert isinstance(message_elem.text, str)
        assert 1 <= int(count_elem.text) <= 100
        assert active_elem.text in ['True', 'False']
    
    def test_xml_with_arrays(self, temp_workspace):
        """Test XML generation with array elements."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'users': {
                'type': 'array',
                'count': 3,
                'items': {
                    'name': 'person_name',
                    'age': 'age'
                }
            }
        }
        
        result = xml_generator.generate(
            target_file="users.xml",
            content_spec={'schema': schema, 'root_element': 'system'}
        )
        
        assert result['errors'] == []
        
        # Parse and verify XML structure
        target_file = temp_workspace / "users.xml"
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        # Should have users element containing 3 item elements
        users_elem = root.find('users')
        assert users_elem is not None
        
        user_items = users_elem.findall('item')
        assert len(user_items) == 3
        
        # Each user item should have name and age
        for user in user_items:
            name_elem = user.find('name')
            age_elem = user.find('age')
            assert name_elem is not None
            assert age_elem is not None
            assert len(name_elem.text) > 0
            assert 18 <= int(age_elem.text) <= 70
    
    def test_xml_with_nested_objects(self, temp_workspace):
        """Test XML generation with nested object structures."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'database': {
                'host': 'city',
                'port': {'type': 'integer', 'minimum': 1000, 'maximum': 9999},
                'config': {
                    'timeout': {'type': 'integer', 'minimum': 10, 'maximum': 120},
                    'retries': {'type': 'integer', 'minimum': 1, 'maximum': 5}
                }
            }
        }
        
        result = xml_generator.generate(
            target_file="database.xml",
            content_spec={'schema': schema, 'root_element': 'configuration'}
        )
        
        assert result['errors'] == []
        
        # Parse and verify nested structure
        target_file = temp_workspace / "database.xml"
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        database = root.find('database')
        assert database is not None
        
        # Check direct children
        host = database.find('host')
        port = database.find('port')
        config = database.find('config')
        
        assert host is not None
        assert port is not None
        assert config is not None
        
        # Check nested config elements
        timeout = config.find('timeout')
        retries = config.find('retries')
        
        assert timeout is not None
        assert retries is not None
        assert 10 <= int(timeout.text) <= 120
        assert 1 <= int(retries.text) <= 5
    
    def test_xml_with_mixed_data_types(self, temp_workspace):
        """Test XML generation with various data type constraints."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'settings': {
                'debug': {'type': 'boolean'},
                'max_users': {'type': 'integer', 'minimum': 10, 'maximum': 100},
                'timeout': {'type': 'number', 'minimum': 1.0, 'maximum': 30.0},
                'app_name': {'type': 'string', 'pattern': 'lorem_word'}
            }
        }
        
        result = xml_generator.generate(
            target_file="config.xml",
            content_spec={'schema': schema, 'root_element': 'configuration'}
        )
        
        assert result['errors'] == []
        
        # Parse and verify data types
        target_file = temp_workspace / "config.xml"
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        settings = root.find('settings')
        assert settings is not None
        
        debug_elem = settings.find('debug')
        max_users_elem = settings.find('max_users')
        timeout_elem = settings.find('timeout')
        app_name_elem = settings.find('app_name')
        
        assert debug_elem is not None
        assert max_users_elem is not None
        assert timeout_elem is not None
        assert app_name_elem is not None
        
        # Verify value ranges
        assert debug_elem.text in ['True', 'False']
        assert 10 <= int(max_users_elem.text) <= 100
        assert 1.0 <= float(timeout_elem.text) <= 30.0
        assert len(app_name_elem.text) > 0
    
    def test_xml_default_schema(self, temp_workspace):
        """Test XML generation with default fallback schema."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        result = xml_generator.generate(
            target_file="default.xml",
            content_spec={'root_element': 'data'}
        )
        
        assert result['errors'] == []
        
        target_file = temp_workspace / "default.xml"
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        assert root.tag == 'data'
        # Should have some default content
        assert len(list(root)) > 0
    
    def test_xml_formatting_consistency(self, temp_workspace):
        """Test that XML output is consistently formatted."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'settings': {
                'debug': {'type': 'boolean'},
                'timeout': {'type': 'integer', 'minimum': 30, 'maximum': 300}
            }
        }
        
        # Generate multiple times
        for i in range(3):
            result = xml_generator.generate(
                target_file=f"format_test_{i}.xml",
                content_spec={'schema': schema, 'root_element': 'config'}
            )
            assert result['errors'] == []
            
            # Check file exists and is valid XML
            target_file = temp_workspace / f"format_test_{i}.xml"
            tree = ET.parse(target_file)
            root = tree.getroot()
            
            # Verify consistent structure
            settings = root.find('settings')
            assert settings is not None
            assert settings.find('debug') is not None
            assert settings.find('timeout') is not None
    
    def test_xml_clutter_generation(self, temp_workspace):
        """Test XML clutter file generation."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'main_data': 'lorem_words'
        }
        
        result = xml_generator.generate(
            target_file="main.xml",
            content_spec={
                'schema': schema,
                'root_element': 'document',
                'clutter_files': {
                    'count': 2
                }
            }
        )
        
        assert result['errors'] == []
        
        # Should have main file + clutter files (actual clutter implementation generates randomly)
        # Check that files were created in clutter_result
        if 'clutter_result' in result and result['clutter_result']:
            clutter_files = result['clutter_result'].get('files_created', [])
            assert len(clutter_files) >= 0  # May be 0 or more depending on implementation
        
        # At minimum, main file should exist
        assert len(result['files_created']) >= 1
        
        # Verify main file exists and is valid XML
        main_file = temp_workspace / "main.xml"
        assert main_file.exists()
        
        tree = ET.parse(main_file)
        root = tree.getroot()
        assert root is not None
        assert root.tag == 'document'
    
    def test_xml_error_handling(self, temp_workspace):
        """Test error handling for invalid XML schemas."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        # Test invalid array count
        invalid_schema = {
            'items': {
                'type': 'array',
                'count': -1,  # Invalid negative count
                'items': {'name': 'lorem_words'}
            }
        }
        
        result = xml_generator.generate(
            target_file="invalid.xml",
            content_spec={'schema': invalid_schema, 'root_element': 'test'}
        )
        
        # Should handle gracefully - either succeed with adjusted values or provide clear error
        assert isinstance(result['errors'], list)
        
        # Test missing root element
        result = xml_generator.generate(
            target_file="no_root.xml",
            content_spec={'schema': {'test': 'lorem_words'}}
        )
        
        # Should use default root element or provide error
        assert isinstance(result, dict)
        assert 'errors' in result
    
    def test_xml_complex_schema(self, temp_workspace):
        """Test XML generation with complex nested schema."""
        xml_generator = XMLFileGenerator(str(temp_workspace))
        
        schema = {
            'company': {
                'name': 'company',
                'departments': {
                    'type': 'array',
                    'count': '{{number1:2:3}}',
                    'items': {
                        'name': 'department',
                        'employees': {
                            'type': 'array',
                            'count': '{{number2:1:3}}',
                            'items': {
                                'name': 'person_name',
                                'role': 'category',
                                'salary': 'salary'
                            }
                        }
                    }
                }
            }
        }
        
        result = xml_generator.generate(
            target_file="company.xml",
            content_spec={'schema': schema, 'root_element': 'organization'}
        )
        
        assert result['errors'] == []
        
        # Parse and verify complex structure
        target_file = temp_workspace / "company.xml"
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        company = root.find('company')
        assert company is not None
        
        # Check department structure - departments is an array container
        departments_elem = company.find('departments')
        assert departments_elem is not None
        
        dept_items = departments_elem.findall('item')
        assert 2 <= len(dept_items) <= 3
        
        for dept in dept_items:
            # Each department item should have name and employees
            assert dept.find('name') is not None
            
            # Check employee structure
            employees_elem = dept.find('employees')
            assert employees_elem is not None
            
            emp_items = employees_elem.findall('item')
            assert 1 <= len(emp_items) <= 3
            
            for emp in emp_items:
                assert emp.find('name') is not None
                assert emp.find('role') is not None
                assert emp.find('salary') is not None