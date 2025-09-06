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


class TestRoundedNumbers:
    """Test rounded number functionality."""
    
    def test_round_hundreds_type(self):
        """Test round_hundreds generates numbers rounded to nearest 100."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Test multiple samples to verify consistency
        for _ in range(10):
            result = evs.substitute_all_variables("{{number1:1234:5678:round_hundreds}}")
            number = int(result['substituted'])
            assert number % 100 == 0, f"Should be rounded to hundreds: {number}"
            assert 1200 <= number <= 5700, f"Should be within rounded range: {number}"
            evs.clear_cache()  # Fresh generation each time

    def test_round_thousands_type(self):
        """Test round_thousands generates numbers rounded to nearest 1000."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        for _ in range(10):
            result = evs.substitute_all_variables("{{number1:40000:60000:round_thousands}}")
            number = int(result['substituted'])
            assert number % 1000 == 0, f"Should be rounded to thousands: {number}"
            assert 40000 <= number <= 60000, f"Should be within range: {number}"
            evs.clear_cache()

    def test_round_ten_thousands_type(self):
        """Test round_ten_thousands generates numbers rounded to nearest 10000."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        result = evs.substitute_all_variables("{{number1:85000:125000:round_ten_thousands}}")
        number = int(result['substituted'])
        assert number % 10000 == 0, f"Should be rounded to ten thousands: {number}"
        assert number in [90000, 100000, 110000, 120000], f"Should be valid rounded value: {number}"

    def test_custom_increment_rounding(self):
        """Test custom increment rounding (500, 250)."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Test 500 increments
        result = evs.substitute_all_variables("{{number1:1000:3000:round_500}}")
        number = int(result['substituted'])
        assert number % 500 == 0, f"Should be rounded to 500s: {number}"
        
        # Test 250 increments  
        result = evs.substitute_all_variables("{{number1:1000:2000:round_250}}")
        number = int(result['substituted'])
        assert number % 250 == 0, f"Should be rounded to 250s: {number}"
        
    def test_rounding_edge_cases(self):
        """Test rounding behavior at range boundaries."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Test small ranges
        result = evs.substitute_all_variables("{{number1:1:99:round_hundreds}}")
        number = int(result['substituted'])
        assert number == 0 or number == 100, f"Small range should round to 0 or 100: {number}"
        
        # Test single value ranges  
        result = evs.substitute_all_variables("{{number1:1500:1500:round_thousands}}")
        number = int(result['substituted'])
        assert number == 2000, f"1500 should round to 2000: {number}"
        
        # Test ranges that span rounding boundaries
        result = evs.substitute_all_variables("{{number1:49999:50001:round_thousands}}")
        number = int(result['substituted'])
        assert number == 50000, f"Range around 50000 should round to 50000: {number}"

    def test_rounding_range_validation(self):
        """Test that rounded values stay within logical bounds."""
        # Test with different seeds to get variety
        numbers = []
        for seed in range(10):  # Use different seeds instead of clearing cache
            evs = EnhancedVariableSubstitution(seed=seed)
            result = evs.substitute_all_variables("{{number1:45000:55000:round_thousands}}")
            number = int(result['substituted'])
            numbers.append(number)
        
        # All should be multiples of 1000
        assert all(n % 1000 == 0 for n in numbers), "All should be rounded to thousands"
        
        # Should have variety across different seeds
        unique_numbers = set(numbers)
        assert len(unique_numbers) > 1, f"Should generate varied numbers, got: {unique_numbers}"
        
        # All should be reasonable for the range
        assert all(45000 <= n <= 55000 for n in numbers), f"All should be in range, got: {min(numbers)} to {max(numbers)}"

    def test_rounded_variable_consistency(self):
        """Test that same rounded variable generates same value across template."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Budget {{number1:40000:60000:round_thousands}} vs actual {{number1:40000:60000:round_thousands}}"
        result = evs.substitute_all_variables(template)
        
        # Extract both numbers
        import re
        numbers = re.findall(r'\d+', result['substituted'])
        assert len(numbers) == 2, f"Should find exactly 2 numbers: {numbers}"
        assert numbers[0] == numbers[1], f"Same variable should have same value: {numbers}"
        
        # Verify both are properly rounded
        number = int(numbers[0])
        assert number % 1000 == 0, f"Should be rounded to thousands: {number}"

    def test_rounded_vs_regular_variable_independence(self):
        """Test that rounded and regular versions of same variable are independent."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "Regular: {{number1:40000:60000:integer}} Rounded: {{number2:40000:60000:round_thousands}}"
        result = evs.substitute_all_variables(template)
        
        import re
        numbers = re.findall(r'\d+', result['substituted'])
        regular = int(numbers[0])
        rounded = int(numbers[1])
        
        # Regular should potentially not be rounded
        # Rounded should definitely be rounded
        assert rounded % 1000 == 0, f"Rounded variable should be rounded: {rounded}"
        
        # They should be independent (different cache keys)
        assert regular != rounded or regular % 1000 == 0, "Variables should be independent"

    def test_rounded_variable_mappings(self):
        """Test that rounded variables are properly tracked in variable mappings."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        result = evs.substitute_all_variables("{{number1:1000:2000:round_hundreds}}")
        
        # Check variable mapping includes full type specification
        assert 'number1:1000:2000:round_hundreds' in result['variables'], \
            f"Should track full variable spec, got keys: {list(result['variables'].keys())}"
        
        # Check value is properly rounded
        value = int(result['variables']['number1:1000:2000:round_hundreds'])
        assert value % 100 == 0, f"Mapped value should be rounded: {value}"
        
        # Check substituted text matches mapped value
        substituted_number = int(result['substituted'])
        assert substituted_number == value, f"Substituted ({substituted_number}) should match mapped ({value})"

    def test_multiple_rounded_types_mapping(self):
        """Test variable mappings with multiple rounded types."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        template = "H:{{number1:1000:2000:round_hundreds}} T:{{number2:40000:60000:round_thousands}}"
        result = evs.substitute_all_variables(template)
        
        expected_keys = [
            'number1:1000:2000:round_hundreds',
            'number2:40000:60000:round_thousands'
        ]
        
        for key in expected_keys:
            assert key in result['variables'], f"Missing variable mapping: {key}"
            value = int(result['variables'][key])
            
            if 'round_hundreds' in key:
                assert value % 100 == 0, f"Hundreds value should be rounded: {value}"
            elif 'round_thousands' in key:
                assert value % 1000 == 0, f"Thousands value should be rounded: {value}"

    def test_existing_types_unchanged(self):
        """Test that existing number types continue working unchanged."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Test all existing types still work
        test_cases = [
            ("{{number1:1:100:integer}}", int, lambda x: isinstance(x, int)),
            ("{{number1:1:100:currency}}", int, lambda x: isinstance(x, int)),
        ]
        
        for template, expected_type, validator in test_cases:
            result = evs.substitute_all_variables(template)
            
            # Extract number from result
            number = int(result['substituted'])
            
            assert validator(number), f"Type validation failed for {template}: {number}"
            assert 1 <= number <= 100, f"Value out of range for {template}: {number}"

    def test_error_handling_for_unknown_types(self):
        """Test that unknown number types raise appropriate errors."""
        evs = EnhancedVariableSubstitution(seed=42)
        
        with pytest.raises(ValueError, match="Unknown number type: invalid_type"):
            evs._generate_number(1, 100, 'invalid_type')
        
        # Ensure new rounded types don't interfere with error detection
        with pytest.raises(ValueError, match="Unknown number type: round_invalid"):
            evs._generate_number(1, 100, 'round_invalid')

    def test_rounded_numbers_with_seed_consistency(self):
        """Test that rounded numbers are consistent with same seed."""
        template = "{{number1:40000:60000:round_thousands}}"
        
        # Generate with same seed twice
        evs1 = EnhancedVariableSubstitution(seed=12345)
        result1 = evs1.substitute_all_variables(template)
        
        evs2 = EnhancedVariableSubstitution(seed=12345)
        result2 = evs2.substitute_all_variables(template)
        
        assert result1['substituted'] == result2['substituted'], \
            f"Same seed should generate same result: {result1['substituted']} vs {result2['substituted']}"
        
        assert result1['variables'] == result2['variables'], \
            f"Same seed should generate same variables: {result1['variables']} vs {result2['variables']}"

    def test_realistic_enterprise_number_generation(self):
        """Test that rounded numbers model realistic enterprise scenarios."""
        # Generate rounded numbers with different seeds for variety
        rounded_numbers = []
        for seed in range(20):  # Use different seeds to get variety
            evs = EnhancedVariableSubstitution(seed=seed)
            result = evs.substitute_all_variables("{{number1:40000:60000:round_thousands}}")
            number = int(result['substituted'])
            rounded_numbers.append(number)
        
        # All should be properly rounded to thousands (realistic for enterprise thresholds)
        assert all(n % 1000 == 0 for n in rounded_numbers), \
            f"All should be rounded to thousands: {rounded_numbers}"
        
        # Should have good variety across different seeds (different enterprise scenarios)
        unique_numbers = set(rounded_numbers)
        assert len(unique_numbers) >= 5, f"Should have good variety for testing: {unique_numbers}"
        
        # All should be in valid range
        assert all(40000 <= n <= 60000 for n in rounded_numbers), \
            f"All should be in range: min={min(rounded_numbers)}, max={max(rounded_numbers)}"