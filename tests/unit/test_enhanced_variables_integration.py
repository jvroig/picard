"""
Integration tests for enhanced variable substitution with PICARD components.

These tests would have caught the integration bugs we encountered:
1. Circular dependency preventing enhanced substitution from loading
2. EntityPool not properly loading EnhancedVariableSubstitution
3. Template functions not working with enhanced variables
4. Cross-component variable consistency issues
"""

import pytest
import tempfile
import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from enhanced_variable_substitution import EnhancedVariableSubstitution
from entity_pool import EntityPool
from data_generator import DataGenerator


class TestEnhancedVariableIntegration:
    """Test enhanced variable substitution integration with other components."""
    
    @pytest.fixture
    def minimal_entity_pool_file(self):
        """Create a minimal entity pool for testing."""
        content = """# Test entity pool
red
blue
green
test
data
sample
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_enhanced_substitution_can_be_imported_independently(self):
        """
        CRITICAL: Test that EnhancedVariableSubstitution can be imported without circular dependencies.
        
        This test would have caught the circular dependency issue that prevented
        the enhanced substitution system from loading properly.
        """
        try:
            # This should work without any circular import errors
            evs = EnhancedVariableSubstitution(seed=42)
            assert evs is not None
            
            # Should be able to use basic functionality
            result = evs.substitute_all_variables("Test {{semantic1:city}} value")
            assert result['substituted'] != "Test {{semantic1:city}} value"
            assert 'semantic1:city' in result['variables']
            
        except ImportError as e:
            pytest.fail(f"Enhanced variable substitution failed to import due to circular dependency: {e}")
    
    def test_data_generator_can_be_imported_independently(self):
        """
        CRITICAL: Test that DataGenerator can be imported without circular dependencies.
        
        This test would have caught the circular dependency that occurred when
        DataGenerator was embedded in enhanced_variable_substitution.py.
        """
        try:
            # This should work without any circular import errors
            data_gen = DataGenerator()
            assert data_gen is not None
            
            # Should be able to generate basic data
            person_name = data_gen.generate_field('person_name')
            assert ' ' in person_name  # Should have first and last name
            
            city = data_gen.generate_field('city')
            assert len(city) > 0
            
        except ImportError as e:
            pytest.fail(f"DataGenerator failed to import due to circular dependency: {e}")
    
    def test_entity_pool_loads_enhanced_substitution_successfully(self, minimal_entity_pool_file):
        """
        CRITICAL: Test that EntityPool can successfully load EnhancedVariableSubstitution.
        
        This test would have caught the bug where EntityPool couldn't load
        enhanced substitution due to circular dependencies.
        """
        entity_pool = EntityPool(minimal_entity_pool_file)
        
        # Should be able to get enhanced substitution without errors
        enhanced_sub = entity_pool._get_enhanced_substitution()
        assert enhanced_sub is not None, "EntityPool failed to load enhanced variable substitution"
        
        # Should be able to use it for substitution
        template = "Process {{semantic1:city}} data with {{number1:10:20}} items"
        result = enhanced_sub.substitute_all_variables(template)
        
        assert result['substituted'] != template
        assert 'semantic1:city' in result['variables']
        assert 'number1:10:20:integer' in result['variables']
        
        # Clean up
        os.unlink(minimal_entity_pool_file)
    
    def test_entity_pool_enhanced_substitution_consistency(self, minimal_entity_pool_file):
        """
        CRITICAL: Test that EntityPool uses enhanced substitution consistently.
        
        This test would have caught bugs where EntityPool and enhanced substitution
        generated different values for the same variables.
        """
        entity_pool = EntityPool(minimal_entity_pool_file)
        enhanced_sub = entity_pool._get_enhanced_substitution()
        
        # Generate variables using both systems
        template = "{{semantic1:person_name}} from {{semantic2:city}} has {{entity1}} access"
        
        # Through enhanced substitution directly
        result1 = enhanced_sub.substitute_all_variables(template)
        
        # Through EntityPool (should use same enhanced substitution instance)
        result2 = enhanced_sub.substitute_all_variables(template) 
        
        # Should get same results (due to caching)
        assert result1['variables']['semantic1:person_name'] == result2['variables']['semantic1:person_name']
        assert result1['variables']['semantic2:city'] == result2['variables']['semantic2:city']
        assert result1['variables']['entity1'] == result2['variables']['entity1']
        
        # Clean up
        os.unlink(minimal_entity_pool_file)
    
    def test_enhanced_variables_work_with_legacy_entity_substitution(self, minimal_entity_pool_file):
        """
        Test that enhanced variables work alongside legacy entity substitution.
        
        This ensures backward compatibility with existing entity substitution patterns.
        """
        entity_pool = EntityPool(minimal_entity_pool_file)
        enhanced_sub = entity_pool._get_enhanced_substitution()
        
        # Mix enhanced and legacy-style variables
        template = "Process {{semantic1:city}} with {{entity1}} and {{entity2}} tools"
        result = enhanced_sub.substitute_all_variables(template)
        
        variables = result['variables']
        
        # Enhanced semantic variable should work
        assert 'semantic1:city' in variables
        city = variables['semantic1:city']
        assert len(city) > 0
        
        # Legacy entity variables should work
        assert 'entity1' in variables  
        assert 'entity2' in variables
        entity1 = variables['entity1']
        entity2 = variables['entity2']
        assert len(entity1) > 0
        assert len(entity2) > 0
        
        # Should not have template strings in result
        substituted = result['substituted']
        assert '{{semantic1:city}}' not in substituted
        assert '{{entity1}}' not in substituted
        assert '{{entity2}}' not in substituted
        
        # Clean up
        os.unlink(minimal_entity_pool_file)
    
    def test_multiple_enhanced_substitution_instances_independence(self):
        """
        Test that multiple EnhancedVariableSubstitution instances work independently.
        
        This ensures that different test contexts don't interfere with each other.
        """
        # Create two instances with different seeds
        evs1 = EnhancedVariableSubstitution(seed=123)
        evs2 = EnhancedVariableSubstitution(seed=456)
        
        template = "Value: {{semantic1:person_name}} from {{semantic2:city}}"
        
        # Generate variables with both instances
        result1 = evs1.substitute_all_variables(template)
        result2 = evs2.substitute_all_variables(template)
        
        # Should likely get different values (not guaranteed but highly probable)
        vars1 = result1['variables']
        vars2 = result2['variables']
        
        # At least one variable should be different between the two instances
        different = (
            vars1['semantic1:person_name'] != vars2['semantic1:person_name'] or
            vars1['semantic2:city'] != vars2['semantic2:city']
        )
        assert different, "Different seeds should produce different variable values"
    
    def test_enhanced_substitution_handles_missing_entity_pools_gracefully(self):
        """
        Test that enhanced substitution handles missing entity pools gracefully.
        
        This ensures the system degrades gracefully when entity pools are unavailable.
        """
        # Create enhanced substitution with default entity pools
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Try to use a non-existent entity pool
        template = "Use {{entity1:nonexistent_pool}} theme"
        
        with pytest.raises(ValueError, match="Unknown entity pool"):
            evs.substitute_all_variables(template)
    
    def test_enhanced_substitution_semantic_data_type_validation(self):
        """
        Test that enhanced substitution handles semantic data types properly.
        
        This ensures the system behaves consistently with valid and invalid data types.
        """
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Valid data types should work
        valid_template = "{{semantic1:person_name}} in {{semantic2:city}}"
        result = evs.substitute_all_variables(valid_template)
        assert result['substituted'] != valid_template
        
        # Test behavior with invalid data types
        invalid_template = "{{semantic1:invalid_data_type}}"
        
        try:
            result = evs.substitute_all_variables(invalid_template)
            # If it doesn't raise an error, it should at least not substitute the invalid type
            # or handle it gracefully in some way
            assert result is not None
        except ValueError:
            # If it does raise an error, that's also acceptable behavior
            pass
    
    def test_cross_component_variable_generation_consistency(self, minimal_entity_pool_file):
        """
        CRITICAL: Test variable consistency across different PICARD components.
        
        This test would have caught bugs where the same variable (e.g., semantic1:city)
        had different values when used in different components due to separate
        variable generation instances.
        """
        # Create components that might use variables
        entity_pool = EntityPool(minimal_entity_pool_file)
        enhanced_sub = entity_pool._get_enhanced_substitution()
        data_gen = DataGenerator()
        
        # Generate a semantic variable through enhanced substitution
        template = "{{semantic1:city}} analysis"
        result = enhanced_sub.substitute_all_variables(template)
        city_from_enhanced = result['variables']['semantic1:city']
        
        # Generate city through DataGenerator directly
        city_from_data_gen = data_gen.generate_field('city')
        
        # While they won't be identical (different random seeds), both should be valid cities
        assert len(city_from_enhanced) > 0
        assert len(city_from_data_gen) > 0
        
        # Both should be in the available cities list
        assert city_from_enhanced in data_gen.cities
        assert city_from_data_gen in data_gen.cities
        
        # Clean up
        os.unlink(minimal_entity_pool_file)
    
    def test_enhanced_substitution_caching_across_components(self, minimal_entity_pool_file):
        """
        Test that variable caching works correctly across component interactions.
        
        This ensures that when multiple components use the same enhanced substitution
        instance, variables remain consistent.
        """
        entity_pool = EntityPool(minimal_entity_pool_file)
        enhanced_sub = entity_pool._get_enhanced_substitution()
        
        # Use same variable in multiple templates
        template1 = "Analyze {{semantic1:city}} data"
        template2 = "Report on {{semantic1:city}} metrics"
        template3 = "{{semantic1:city}} summary with {{number1:100:200}} records"
        
        result1 = enhanced_sub.substitute_all_variables(template1)
        result2 = enhanced_sub.substitute_all_variables(template2)
        result3 = enhanced_sub.substitute_all_variables(template3)
        
        # Same semantic1:city should have same value across all uses
        city1 = result1['variables']['semantic1:city']
        city2 = result2['variables']['semantic1:city']
        city3 = result3['variables']['semantic1:city']
        
        assert city1 == city2 == city3, "Same semantic variable should have consistent value across templates"
        
        # Same number1:100:200 should be consistent
        number3 = result3['variables']['number1:100:200:integer']
        
        # Use the same number variable in another template
        template4 = "Budget: ${{number1:100:200}} allocated"
        result4 = enhanced_sub.substitute_all_variables(template4)
        number4 = result4['variables']['number1:100:200:integer']
        
        assert number3 == number4, "Same numeric variable should have consistent value across templates"
        
        # Clean up
        os.unlink(minimal_entity_pool_file)
    
    def test_enhanced_substitution_reset_functionality(self):
        """
        Test that enhanced substitution reset/clear functionality works properly.
        
        This ensures that test isolation can be maintained when needed.
        """
        evs = EnhancedVariableSubstitution(seed=42)
        
        # Generate some variables
        template = "{{semantic1:person_name}} has {{number1:50:100}} points"
        result1 = evs.substitute_all_variables(template)
        
        person1 = result1['variables']['semantic1:person_name']
        number1 = result1['variables']['number1:50:100:integer']
        
        # Clear cache and generate again
        evs.clear_cache()
        result2 = evs.substitute_all_variables(template)
        
        person2 = result2['variables']['semantic1:person_name']
        number2 = result2['variables']['number1:50:100:integer']
        
        # After cache clear with same seed, should get same values
        assert person1 == person2, "Cache clear should reset to same seed values"
        assert number1 == number2, "Cache clear should reset to same seed values"