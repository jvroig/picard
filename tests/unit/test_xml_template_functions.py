"""
Unit tests for XML template functions.

Tests XPath-based navigation, value extraction, and aggregation functions.
"""
import pytest
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from template_functions import TemplateFunctions, TemplateFunctionError


@pytest.fixture
def create_xml_file(temp_workspace):
    """Create XML test files with sample data."""
    def _create_xml_file(filename, custom_data=None):
        if custom_data is None:
            # Default test data
            root = ET.Element('system')
            
            # Create users section
            users = ET.SubElement(root, 'users')
            
            user1 = ET.SubElement(users, 'user')
            user1.set('id', '1')
            user1.set('active', 'true')
            ET.SubElement(user1, 'name').text = 'John'
            ET.SubElement(user1, 'city').text = 'New York'
            ET.SubElement(user1, 'age').text = '25'
            ET.SubElement(user1, 'salary').text = '65000'
            
            user2 = ET.SubElement(users, 'user')
            user2.set('id', '2')
            user2.set('active', 'false')
            ET.SubElement(user2, 'name').text = 'Alice'
            ET.SubElement(user2, 'city').text = 'Los Angeles'
            ET.SubElement(user2, 'age').text = '30'
            ET.SubElement(user2, 'salary').text = '75000'
            
            user3 = ET.SubElement(users, 'user')
            user3.set('id', '3')
            user3.set('active', 'true')
            ET.SubElement(user3, 'name').text = 'Bob'
            ET.SubElement(user3, 'city').text = 'Chicago'
            ET.SubElement(user3, 'age').text = '35'
            ET.SubElement(user3, 'salary').text = '80000'
            
            # Create config section
            config = ET.SubElement(root, 'config')
            ET.SubElement(config, 'debug').text = 'true'
            ET.SubElement(config, 'timeout').text = '30'
            ET.SubElement(config, 'max_users').text = '100'
            
            # Create database section
            database = ET.SubElement(root, 'database')
            ET.SubElement(database, 'host').text = 'localhost'
            ET.SubElement(database, 'port').text = '5432'
            ET.SubElement(database, 'name').text = 'testdb'
            
        else:
            root = custom_data
        
        # Write to file
        file_path = temp_workspace / filename
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        return str(file_path)
    
    return _create_xml_file


@pytest.mark.unit
@pytest.mark.template_functions
class TestXMLTemplateFunctions:
    """Test XML template function functionality."""
    
    def test_xpath_value_extraction(self, template_functions, create_xml_file):
        """Test {{xpath_value:xpath:file}} function."""
        xml_file = create_xml_file("test.xml")
        
        # Extract user names
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:users/user[1]/name:{xml_file}}}}}")
        assert result == "John"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:users/user[2]/name:{xml_file}}}}}")
        assert result == "Alice"
        
        # Extract config values
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:config/debug:{xml_file}}}}}")
        assert result == "true"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:config/timeout:{xml_file}}}}}")
        assert result == "30"
        
        # Extract database info
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:database/host:{xml_file}}}}}")
        assert result == "localhost"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:database/port:{xml_file}}}}}")
        assert result == "5432"
    
    def test_xpath_attr_extraction(self, template_functions, create_xml_file):
        """Test {{xpath_attr:xpath@attribute:file}} function."""
        xml_file = create_xml_file("test.xml")
        
        # Extract user IDs
        result = template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user[1]@id:{xml_file}}}}}")
        assert result == "1"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user[2]@id:{xml_file}}}}}")
        assert result == "2"
        
        # Extract active status
        result = template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user[1]@active:{xml_file}}}}}")
        assert result == "true"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user[2]@active:{xml_file}}}}}")
        assert result == "false"
    
    def test_xpath_count_function(self, template_functions, create_xml_file):
        """Test {{xpath_count:xpath:file}} function."""
        xml_file = create_xml_file("test.xml")
        
        # Count users
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:users/user:{xml_file}}}}}")
        assert int(result) == 3
        
        # Count config elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:config/*:{xml_file}}}}}")
        assert int(result) == 3  # debug, timeout, max_users
        
        # Count database elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:database/*:{xml_file}}}}}")
        assert int(result) == 3  # host, port, name
        
        # Count with attribute filter
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:users/user[@active='true']:{xml_file}}}}}")
        assert int(result) == 2  # John and Bob
    
    def test_xpath_exists_function(self, template_functions, create_xml_file):
        """Test {{xpath_exists:xpath:file}} function."""
        xml_file = create_xml_file("test.xml")
        
        # Test existing elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:users/user:{xml_file}}}}}")
        assert result == "true"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:config/debug:{xml_file}}}}}")
        assert result == "true"
        
        # Test non-existing elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:users/admin:{xml_file}}}}}")
        assert result == "false"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:nonexistent:{xml_file}}}}}")
        assert result == "false"
        
        # Test with attribute conditions
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:users/user[@id='1']:{xml_file}}}}}")
        assert result == "true"
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_exists:users/user[@id='999']:{xml_file}}}}}")
        assert result == "false"
    
    def test_xpath_collect_function(self, template_functions, create_xml_file):
        """Test {{xpath_collect:xpath:file}} function."""
        xml_file = create_xml_file("test.xml")
        
        # Collect all user names
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:users/user/name:{xml_file}}}}}")
        names = result.split(',')
        assert set(names) == {'John', 'Alice', 'Bob'}
        
        # Collect all cities
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:users/user/city:{xml_file}}}}}")
        cities = result.split(',')
        assert len(cities) == 3
        assert 'New York' in cities
        assert 'Los Angeles' in cities
        assert 'Chicago' in cities
        
        # Collect database info
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:database/*:{xml_file}}}}}")
        db_values = result.split(',')
        assert 'localhost' in db_values
        assert '5432' in db_values
        assert 'testdb' in db_values
    
    def test_xpath_aggregation_functions(self, template_functions, create_xml_file):
        """Test XPath aggregation functions (sum, avg, max, min)."""
        xml_file = create_xml_file("test.xml")
        
        # Test sum of salaries
        result = template_functions.evaluate_all_functions(f"{{{{xpath_sum:users/user/salary:{xml_file}}}}}")
        assert float(result) == 220000.0  # 65000 + 75000 + 80000
        
        # Test average salary
        result = template_functions.evaluate_all_functions(f"{{{{xpath_avg:users/user/salary:{xml_file}}}}}")
        assert abs(float(result) - 73333.33333333333) < 0.1  # 220000 / 3
        
        # Test max salary
        result = template_functions.evaluate_all_functions(f"{{{{xpath_max:users/user/salary:{xml_file}}}}}")
        assert float(result) == 80000.0
        
        # Test min salary
        result = template_functions.evaluate_all_functions(f"{{{{xpath_min:users/user/salary:{xml_file}}}}}")
        assert float(result) == 65000.0
        
        # Test sum of ages
        result = template_functions.evaluate_all_functions(f"{{{{xpath_sum:users/user/age:{xml_file}}}}}")
        assert float(result) == 90.0  # 25 + 30 + 35
        
        # Test average age
        result = template_functions.evaluate_all_functions(f"{{{{xpath_avg:users/user/age:{xml_file}}}}}")
        assert float(result) == 30.0  # 90 / 3
    
    def test_xpath_function_errors(self, template_functions, create_xml_file):
        """Test error handling for XPath functions."""
        xml_file = create_xml_file("test.xml")
        
        # Test invalid XPath
        with pytest.raises(TemplateFunctionError, match="XPath .* not found"):
            template_functions.evaluate_all_functions(f"{{{{xpath_value:nonexistent/element:{xml_file}}}}}")
        
        # Test missing file
        with pytest.raises(TemplateFunctionError, match="XML file not found"):
            template_functions.evaluate_all_functions("{{xpath_value:users/user/name:/nonexistent/file.xml}}")
        
        # Test wrong argument count
        with pytest.raises(TemplateFunctionError, match="xpath_value requires exactly 2 arguments"):
            template_functions.evaluate_all_functions(f"{{{{xpath_value:users/user/name:{xml_file}:extra}}}}")
        
        # Test invalid attribute format
        with pytest.raises(TemplateFunctionError, match="xpath_attr requires format: xpath@attribute"):
            template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user/name:{xml_file}}}}}")
        
        # Test missing attribute
        with pytest.raises(TemplateFunctionError, match="Attribute .* not found"):
            template_functions.evaluate_all_functions(f"{{{{xpath_attr:users/user[1]@nonexistent:{xml_file}}}}}")
    
    def test_xpath_with_complex_data(self, template_functions, create_xml_file):
        """Test XPath functions with complex nested data."""
        # Create complex XML structure
        root = ET.Element('organization')
        
        departments = ET.SubElement(root, 'departments')
        
        # Engineering department
        eng_dept = ET.SubElement(departments, 'department')
        eng_dept.set('name', 'Engineering')
        eng_dept.set('budget', '1000000')
        
        eng_teams = ET.SubElement(eng_dept, 'teams')
        
        backend_team = ET.SubElement(eng_teams, 'team')
        backend_team.set('name', 'Backend')
        ET.SubElement(backend_team, 'size').text = '5'
        ET.SubElement(backend_team, 'budget').text = '500000'
        
        frontend_team = ET.SubElement(eng_teams, 'team')
        frontend_team.set('name', 'Frontend')
        ET.SubElement(frontend_team, 'size').text = '3'
        ET.SubElement(frontend_team, 'budget').text = '300000'
        
        # Marketing department
        mkt_dept = ET.SubElement(departments, 'department')
        mkt_dept.set('name', 'Marketing')
        mkt_dept.set('budget', '500000')
        
        mkt_teams = ET.SubElement(mkt_dept, 'teams')
        
        digital_team = ET.SubElement(mkt_teams, 'team')
        digital_team.set('name', 'Digital')
        ET.SubElement(digital_team, 'size').text = '4'
        ET.SubElement(digital_team, 'budget').text = '200000'
        
        xml_file = create_xml_file("complex.xml", root)
        
        # Test deep navigation
        result = template_functions.evaluate_all_functions(f"{{{{xpath_value:departments/department[@name='Engineering']/teams/team[@name='Backend']/size:{xml_file}}}}}")
        assert result == "5"
        
        # Test attribute extraction from deep paths
        result = template_functions.evaluate_all_functions(f"{{{{xpath_attr:departments/department[1]@name:{xml_file}}}}}")
        assert result == "Engineering"
        
        # Test counting nested elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:departments/department/teams/team:{xml_file}}}}}")
        assert int(result) == 3  # Backend, Frontend, Digital
        
        # Test sum across nested elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_sum:departments/department/teams/team/budget:{xml_file}}}}}")
        assert float(result) == 1000000.0  # 500000 + 300000 + 200000
        
        # Test collect across nested attributes
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:departments/department/teams/team/size:{xml_file}}}}}")
        sizes = [int(x) for x in result.split(',')]
        assert set(sizes) == {5, 3, 4}
    
    def test_xpath_with_empty_results(self, template_functions, create_xml_file):
        """Test XPath functions with queries that return no results."""
        xml_file = create_xml_file("test.xml")
        
        # Test aggregation functions with no matching elements
        result = template_functions.evaluate_all_functions(f"{{{{xpath_sum:nonexistent/element:{xml_file}}}}}")
        assert float(result) == 0.0
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_avg:nonexistent/element:{xml_file}}}}}")
        assert float(result) == 0.0
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_max:nonexistent/element:{xml_file}}}}}")
        assert float(result) == 0.0
        
        result = template_functions.evaluate_all_functions(f"{{{{xpath_min:nonexistent/element:{xml_file}}}}}")
        assert float(result) == 0.0
        
        # Test collect with no results
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:nonexistent/element:{xml_file}}}}}")
        assert result == ""
    
    def test_xpath_with_mixed_data_types(self, template_functions, create_xml_file):
        """Test XPath functions with mixed numeric and text data."""
        # Create XML with mixed content
        root = ET.Element('data')
        
        values = ET.SubElement(root, 'values')
        ET.SubElement(values, 'item').text = '10'
        ET.SubElement(values, 'item').text = '20.5'
        ET.SubElement(values, 'item').text = 'not_a_number'
        ET.SubElement(values, 'item').text = '30'
        
        strings = ET.SubElement(root, 'strings')
        ET.SubElement(strings, 'text').text = 'hello'
        ET.SubElement(strings, 'text').text = 'world'
        ET.SubElement(strings, 'text').text = 'test'
        
        xml_file = create_xml_file("mixed.xml", root)
        
        # Test sum skips non-numeric values
        result = template_functions.evaluate_all_functions(f"{{{{xpath_sum:values/item:{xml_file}}}}}")
        assert float(result) == 60.5  # 10 + 20.5 + 30 (skips 'not_a_number')
        
        # Test collect includes all text values
        result = template_functions.evaluate_all_functions(f"{{{{xpath_collect:strings/text:{xml_file}}}}}")
        texts = result.split(',')
        assert set(texts) == {'hello', 'world', 'test'}
        
        # Test count includes all elements regardless of content
        result = template_functions.evaluate_all_functions(f"{{{{xpath_count:values/item:{xml_file}}}}}")
        assert int(result) == 4  # All 4 items, including non-numeric one