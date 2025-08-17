"""
Unit tests for enhanced variable substitution system.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from enhanced_variable_substitution import EnhancedVariableSubstitution


class TestEnhancedVariableSubstitution:
    """Test the enhanced variable substitution system."""
    
    def test_semantic_variables(self):
        """Test semantic variable substitution."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Employee {{semantic1:person_name}} in {{semantic2:department}}"
        result = evs.substitute_all_variables(template)
        
        assert result['substituted'] != template
        assert 'semantic1:person_name' in result['variables']
        assert 'semantic2:department' in result['variables']
        
        # Check that person name looks valid
        person_name = result['variables']['semantic1:person_name']
        assert ' ' in person_name  # Should have first and last name
        
        # Check that department is valid
        department = result['variables']['semantic2:department']
        assert len(department) > 0
    
    def test_semantic_variable_consistency(self):
        """Test that semantic variables are consistent within a test."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template1 = "Employee {{semantic1:person_name}} works in {{semantic2:department}}"
        template2 = "{{semantic1:person_name}} from {{semantic2:department}} earns salary"
        
        result1 = evs.substitute_all_variables(template1)
        result2 = evs.substitute_all_variables(template2)
        
        # Same semantic variables should produce same values
        assert result1['variables']['semantic1:person_name'] == result2['variables']['semantic1:person_name']
        assert result1['variables']['semantic2:department'] == result2['variables']['semantic2:department']
    
    def test_numeric_variables(self):
        """Test numeric variable substitution."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Score: {{number1:60:100}} and budget: {{number2:1000:5000:currency}}"
        result = evs.substitute_all_variables(template)
        
        assert result['substituted'] != template
        assert 'number1:60:100:integer' in result['variables']
        assert 'number2:1000:5000:currency' in result['variables']
        
        # Check numeric ranges
        score = int(result['variables']['number1:60:100:integer'])
        budget = int(result['variables']['number2:1000:5000:currency'])
        
        assert 60 <= score <= 100
        assert 1000 <= budget <= 5000
    
    def test_numeric_variable_consistency(self):
        """Test that numeric variables are consistent within a test."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template1 = "Budget is ${{number1:1000:5000}}"
        template2 = "Allocated ${{number1:1000:5000}} for project"
        
        result1 = evs.substitute_all_variables(template1)
        result2 = evs.substitute_all_variables(template2)
        
        # Same numeric variables should produce same values
        assert result1['variables']['number1:1000:5000:integer'] == result2['variables']['number1:1000:5000:integer']
    
    def test_numeric_types(self):
        """Test different numeric types."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Integer: {{number1:10:20}}, Decimal: {{number2:10:20:decimal}}, Currency: {{number3:1000:2000:currency}}, Percentage: {{number4:0:100:percentage}}"
        result = evs.substitute_all_variables(template)
        
        # Check each type
        integer_val = result['variables']['number1:10:20:integer']
        decimal_val = result['variables']['number2:10:20:decimal']
        currency_val = result['variables']['number3:1000:2000:currency']
        percentage_val = result['variables']['number4:0:100:percentage']
        
        # Integer should be whole number
        assert integer_val == str(int(integer_val))
        
        # Decimal should have decimal point
        assert '.' in decimal_val
        
        # Currency should be integer
        assert currency_val == str(int(currency_val))
        
        # Percentage should have decimal point
        assert '.' in percentage_val
    
    def test_entity_pool_variables(self):
        """Test enhanced entity pool variables."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Use {{entity1:colors}} theme with {{entity2:metals}} accents"
        result = evs.substitute_all_variables(template)
        
        assert result['substituted'] != template
        assert 'entity1:colors' in result['variables']
        assert 'entity2:metals' in result['variables']
        
        # Check that values come from correct pools
        color = result['variables']['entity1:colors']
        metal = result['variables']['entity2:metals']
        
        assert color in evs.entity_pools['colors']
        assert metal in evs.entity_pools['metals']
    
    def test_entity_pool_consistency(self):
        """Test that entity pool variables are consistent within a test."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template1 = "Process {{entity1:colors}} data"
        template2 = "Archive {{entity1:colors}} results"
        
        result1 = evs.substitute_all_variables(template1)
        result2 = evs.substitute_all_variables(template2)
        
        # Same entity variables should produce same values
        assert result1['variables']['entity1:colors'] == result2['variables']['entity1:colors']
    
    def test_entity_variables(self):
        """Test entity variables from default pool."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Process {{entity1}} file and {{entity2}} backup"
        result = evs.substitute_all_variables(template)
        
        assert result['substituted'] != template
        assert 'entity1' in result['variables']
        assert 'entity2' in result['variables']
        
        # Check that values come from default pool
        entity1 = result['variables']['entity1']
        entity2 = result['variables']['entity2']
        
        assert entity1 in evs.entity_pools['default']
        assert entity2 in evs.entity_pools['default']
    
    def test_entity_consistency(self):
        """Test that entity variables are consistent within a test."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template1 = "Process {{entity1}} file"
        template2 = "Archive {{entity1}} data"
        
        result1 = evs.substitute_all_variables(template1)
        result2 = evs.substitute_all_variables(template2)
        
        # Same entity variables should produce same values
        assert result1['variables']['entity1'] == result2['variables']['entity1']
    
    def test_mixed_variable_types(self):
        """Test mixing different variable types in same template."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Employee {{semantic1:person_name}} in {{semantic2:department}} earns ${{number1:30000:80000:currency}} working on {{entity1:colors}} project with {{entity2}} tools"
        result = evs.substitute_all_variables(template)
        
        variables = result['variables']
        
        # Should have all variable types
        assert 'semantic1:person_name' in variables
        assert 'semantic2:department' in variables
        assert 'number1:30000:80000:currency' in variables
        assert 'entity1:colors' in variables
        assert 'entity2' in variables
        
        # Check substituted text doesn't contain original placeholders
        substituted = result['substituted']
        assert '{{semantic1:person_name}}' not in substituted
        assert '{{semantic2:department}}' not in substituted
        assert '{{number1:30000:80000:currency}}' not in substituted
        assert '{{entity1:colors}}' not in substituted
        assert '{{entity2}}' not in substituted
    
    def test_deterministic_generation(self):
        """Test that cached variables are consistent within same instance."""
        # Test that variables are consistent within the same instance
        evs = EnhancedVariableSubstitution(seed=123)
        
        template1 = "Score: {{number1:60:100}} on {{entity1:colors}} project"
        template2 = "Budget {{number1:60:100}} for {{entity1:colors}} theme"
        
        result1 = evs.substitute_all_variables(template1)
        result2 = evs.substitute_all_variables(template2)
        
        # Same variables should be consistent within same instance
        assert result1['variables']['number1:60:100:integer'] == result2['variables']['number1:60:100:integer']
        assert result1['variables']['entity1:colors'] == result2['variables']['entity1:colors']
    
    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        template = "Employee {{semantic1:person_name}} earns ${{number1:30000:80000:currency}}"
        
        evs1 = EnhancedVariableSubstitution(seed=123)
        evs2 = EnhancedVariableSubstitution(seed=456)
        
        result1 = evs1.substitute_all_variables(template)
        result2 = evs2.substitute_all_variables(template)
        
        # Different seeds should likely produce different results
        # (Not guaranteed but highly likely with different seeds)
        assert result1['variables'] != result2['variables']
    
    def test_cache_clearing(self):
        """Test that cache clearing resets random sequence."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Value: {{number1:1:1000}}"
        
        # Generate first value
        result1 = evs.substitute_all_variables(template)
        value1 = result1['variables']['number1:1:1000:integer']
        
        # Generate second value (should use cache, so same value)
        result2 = evs.substitute_all_variables(template)
        value2 = result2['variables']['number1:1:1000:integer']
        
        # Should be same due to caching
        assert value1 == value2
        
        # Clear cache and generate again (should reset random sequence)
        evs.clear_cache()
        result3 = evs.substitute_all_variables(template)
        value3 = result3['variables']['number1:1:1000:integer']
        
        # Should get same value as first because we reset the random seed
        assert value1 == value3
    
    def test_invalid_number_type(self):
        """Test error handling for invalid number types."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Value: {{number1:10:20:invalid_type}}"
        
        with pytest.raises(ValueError, match="Unknown number type"):
            evs.substitute_all_variables(template)
    
    def test_invalid_entity_pool(self):
        """Test error handling for invalid entity pools."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Value: {{entity1:invalid_pool}}"
        
        with pytest.raises(ValueError, match="Unknown entity pool"):
            evs.substitute_all_variables(template)
    
    def test_semantic_data_types(self):
        """Test various semantic data types."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Test various data types that should work
        data_types = [
            'person_name', 'first_name', 'last_name', 'email', 'age', 'city',
            'company', 'product', 'currency', 'salary', 'price', 'phone',
            'date', 'status', 'department', 'region', 'id', 'experience',
            'score', 'course', 'semester', 'category', 'boolean', 'lorem_word'
        ]
        
        for data_type in data_types:
            template = f"Value: {{{{semantic1:{data_type}}}}}"
            result = evs.substitute_all_variables(template)
            
            # Should have the variable and a non-empty value
            var_key = f'semantic1:{data_type}'
            assert var_key in result['variables']
            assert len(result['variables'][var_key]) > 0
            
            # Clear cache for next test
            evs.clear_cache()
    
    def test_no_variables(self):
        """Test template with no variables."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "This is a plain text template"
        result = evs.substitute_all_variables(template)
        
        assert result['substituted'] == template
        assert result['variables'] == {}
    
    def test_malformed_variables(self):
        """Test handling of malformed variable syntax."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # These should not be substituted (malformed syntax)
        template = "Values: {{semantic1}} {{number1:}} {{entity1:}} {{invalid}}"
        result = evs.substitute_all_variables(template)
        
        # Should remain unchanged (no valid variables found)
        assert '{{semantic1}}' in result['substituted']
        assert '{{number1:}}' in result['substituted']
        assert '{{entity1:}}' in result['substituted']
        assert '{{invalid}}' in result['substituted']