"""
CRITICAL Randomization Tests for PICARD Variable Substitution

These tests ensure that PICARD's core randomization actually works.
The bug we just fixed (deterministic entity selection) would have been
caught immediately by these tests.

Tests verify that:
1. Entity variables produce different values across multiple uses
2. Semantic variables show proper randomization 
3. Numeric variables generate diverse values within ranges
4. Cross-sample independence works correctly

This prevents the critical bug where all test samples were identical.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from enhanced_variable_substitution import EnhancedVariableSubstitution


class TestVariableRandomization:
    """Critical tests to ensure PICARD variables are actually random."""
    
    def test_entity_variables_are_actually_random(self):
        """
        CRITICAL: Entity variables must produce different values across uses.
        
        This test would have immediately caught the deterministic bug where
        {{entity1}} always had the same value, defeating PICARD's purpose.
        """
        # Production behavior - no seed!
        evs = EnhancedVariableSubstitution()
        
        values = []
        for _ in range(100):
            evs.clear_cache()  # Fresh randomization each iteration
            result = evs.substitute_all_variables("Test {{entity1}} value")
            values.append(result['variables']['entity1'])
        
        unique_values = set(values)
        
        # CRITICAL: Must have more than 1 unique value!
        assert len(unique_values) > 1, f"Entity1 not random - only got: {unique_values}"
        
        # With 173 entity pool options, expect high diversity (>40% unique minimum)
        uniqueness_ratio = len(unique_values) / len(values)
        assert uniqueness_ratio > 0.4, f"Poor randomization: {uniqueness_ratio:.1%} unique values out of {len(values)} samples"
        
        print(f"✅ Entity1 randomization: {len(unique_values)} unique values ({uniqueness_ratio:.1%} unique)")
    
    def test_enhanced_entity_pools_are_random(self):
        """
        Test that enhanced entity pools ({{entity1:colors}}) are properly randomized.
        
        This tests the enhanced entity functionality specifically.
        """
        evs = EnhancedVariableSubstitution()
        
        # Test colors pool (14 options)
        colors = []
        for _ in range(50):
            evs.clear_cache()
            result = evs.substitute_all_variables("Color: {{entity1:colors}}")
            colors.append(result['variables']['entity1:colors'])
        
        unique_colors = set(colors)
        assert len(unique_colors) > 1, f"entity1:colors not random - only: {unique_colors}"
        
        # With 12 color options and 50 samples, expect some repeats but good diversity
        uniqueness_ratio = len(unique_colors) / len(colors)
        assert uniqueness_ratio > 0.2, f"Poor color randomization: {uniqueness_ratio:.1%} unique (expected >20% with 12 colors)"
        
        print(f"✅ Color entity randomization: {len(unique_colors)} unique colors ({uniqueness_ratio:.1%} unique)")
    
    def test_semantic_variables_are_random(self):
        """
        Test that semantic variables produce different values.
        
        Semantic variables should show diversity in generated data.
        """
        evs = EnhancedVariableSubstitution()
        
        # Test person names
        names = []
        for _ in range(50):
            evs.clear_cache()
            result = evs.substitute_all_variables("Name: {{semantic1:person_name}}")
            names.append(result['variables']['semantic1:person_name'])
        
        unique_names = set(names)
        assert len(unique_names) > 1, f"semantic1:person_name not random - only: {unique_names}"
        
        # Test cities
        cities = []
        for _ in range(50):
            evs.clear_cache()
            result = evs.substitute_all_variables("City: {{semantic2:city}}")
            cities.append(result['variables']['semantic2:city'])
        
        unique_cities = set(cities)
        assert len(unique_cities) > 1, f"semantic2:city not random - only: {unique_cities}"
        
        print(f"✅ Semantic randomization: {len(unique_names)} unique names, {len(unique_cities)} unique cities")
    
    def test_numeric_variables_are_random(self):
        """
        Test that numeric variables produce different values within ranges.
        
        Numeric variables should generate diverse values in the specified range.
        """
        evs = EnhancedVariableSubstitution()
        
        numbers = []
        for _ in range(100):
            evs.clear_cache()
            result = evs.substitute_all_variables("Value: {{number1:1:100}}")
            numbers.append(int(result['variables']['number1:1:100:integer']))
        
        unique_numbers = set(numbers)
        assert len(unique_numbers) > 1, f"number1 not random - only: {unique_numbers}"
        
        # All should be in valid range
        assert all(1 <= n <= 100 for n in numbers), f"Numbers outside range 1-100: {[n for n in numbers if not (1 <= n <= 100)]}"
        
        # Should have reasonable spread
        uniqueness_ratio = len(unique_numbers) / len(numbers)
        assert uniqueness_ratio > 0.1, f"Poor numeric randomization: {uniqueness_ratio:.1%} unique"
        
        print(f"✅ Numeric randomization: {len(unique_numbers)} unique values in range 1-100 ({uniqueness_ratio:.1%} unique)")
    
    def test_multiple_variables_independence(self):
        """
        Test that different variable indices produce independent randomization.
        
        {{entity1}} and {{entity2}} should be independently random, not correlated.
        """
        evs = EnhancedVariableSubstitution()
        
        pairs = []
        for _ in range(50):
            evs.clear_cache()
            result = evs.substitute_all_variables("{{entity1}} and {{entity2}}")
            entity1 = result['variables']['entity1']
            entity2 = result['variables']['entity2']
            pairs.append((entity1, entity2))
        
        # Extract individual values
        entity1_values = [pair[0] for pair in pairs]
        entity2_values = [pair[1] for pair in pairs]
        
        # Both should show randomization
        unique_entity1 = set(entity1_values)
        unique_entity2 = set(entity2_values)
        
        assert len(unique_entity1) > 1, f"entity1 not random: {unique_entity1}"
        assert len(unique_entity2) > 1, f"entity2 not random: {unique_entity2}"
        
        # Should not be identical sequences (independence)
        identical_count = sum(1 for e1, e2 in pairs if e1 == e2)
        identical_ratio = identical_count / len(pairs)
        
        # With 173 options, identical pairs should be rare (<30%)
        assert identical_ratio < 0.3, f"entity1 and entity2 too correlated: {identical_ratio:.1%} identical pairs"
        
        print(f"✅ Variable independence: entity1={len(unique_entity1)} unique, entity2={len(unique_entity2)} unique, {identical_ratio:.1%} identical pairs")
    
    def test_cross_sample_randomization(self):
        """
        Test that the same variable produces different values across samples.
        
        This simulates real PICARD usage where the same template is used
        across multiple samples/questions.
        """
        # Simulate multiple samples
        sample_values = []
        
        for sample in range(20):  # 20 different samples
            evs = EnhancedVariableSubstitution()  # Fresh instance per sample
            result = evs.substitute_all_variables("Process {{entity1}} data")
            sample_values.append(result['variables']['entity1'])
        
        unique_across_samples = set(sample_values)
        
        # Should have diversity across samples
        assert len(unique_across_samples) > 1, f"Cross-sample not random: {unique_across_samples}"
        
        uniqueness_ratio = len(unique_across_samples) / len(sample_values)
        assert uniqueness_ratio > 0.4, f"Poor cross-sample randomization: {uniqueness_ratio:.1%} unique"
        
        print(f"✅ Cross-sample randomization: {len(unique_across_samples)} unique values across {len(sample_values)} samples ({uniqueness_ratio:.1%} unique)")
    
    def test_cache_clearing_produces_fresh_randomization(self):
        """
        Test that cache clearing allows for fresh randomization.
        
        This ensures that clear_cache() actually works for new randomization.
        """
        evs = EnhancedVariableSubstitution()
        
        # Generate same variable multiple times with cache clearing
        values_with_clearing = []
        for _ in range(30):
            evs.clear_cache()  # Should produce fresh values
            result = evs.substitute_all_variables("{{entity1}}")
            values_with_clearing.append(result['variables']['entity1'])
        
        # Generate same variable multiple times WITHOUT cache clearing
        evs.clear_cache()  # Start fresh
        values_without_clearing = []
        for _ in range(30):
            # Don't clear cache - should reuse cached values
            result = evs.substitute_all_variables("{{entity1}}")
            values_without_clearing.append(result['variables']['entity1'])
        
        unique_with_clearing = set(values_with_clearing)
        unique_without_clearing = set(values_without_clearing)
        
        # With cache clearing: should have diversity
        assert len(unique_with_clearing) > 1, f"Cache clearing not working: {unique_with_clearing}"
        
        # Without cache clearing: should have only 1 value (cached)
        assert len(unique_without_clearing) == 1, f"Caching not working: {unique_without_clearing}"
        
        print(f"✅ Cache behavior: {len(unique_with_clearing)} unique with clearing, {len(unique_without_clearing)} unique without clearing")
    
    def test_deterministic_vs_random_behavior(self):
        """
        Test that seeded instances show internal consistency, unseeded are random.
        
        This verifies the seed functionality works for repeatability within an instance.
        """
        # Single seeded instance should be internally consistent after cache clearing
        evs1 = EnhancedVariableSubstitution(seed=12345)
        
        # Get first result
        result1 = evs1.substitute_all_variables("{{entity1}} {{semantic1:city}}")
        entity1_first = result1['variables']['entity1']
        city1_first = result1['variables']['semantic1:city']
        
        # Clear cache and get second result - should be same due to seed reset
        evs1.clear_cache()
        result2 = evs1.substitute_all_variables("{{entity1}} {{semantic1:city}}")
        entity1_second = result2['variables']['entity1']
        city1_second = result2['variables']['semantic1:city']
        
        # Should be identical due to seed reset in clear_cache()
        assert entity1_first == entity1_second, f"Seeded instance not deterministic: {entity1_first} != {entity1_second}"
        assert city1_first == city1_second, f"Seeded instance not deterministic: {city1_first} != {city1_second}"
        
        # Unseeded instances should be random across cache clears
        evs2 = EnhancedVariableSubstitution()  # No seed
        
        values = []
        for _ in range(10):
            evs2.clear_cache()
            result = evs2.substitute_all_variables("{{entity1}}")
            values.append(result['variables']['entity1'])
        
        unique_values = set(values)
        assert len(unique_values) > 1, f"Unseeded instance should be random, got: {unique_values}"
        
        print(f"✅ Seed behavior: seeded instance consistent ({entity1_first}, {city1_first}), unseeded random ({len(unique_values)} unique values)")


if __name__ == "__main__":
    # Run the tests manually for quick verification
    test = TestVariableRandomization()
    
    print("🔍 Running CRITICAL randomization tests...")
    print()
    
    test.test_entity_variables_are_actually_random()
    test.test_enhanced_entity_pools_are_random()
    test.test_semantic_variables_are_random()
    test.test_numeric_variables_are_random()
    test.test_multiple_variables_independence()
    test.test_cross_sample_randomization()
    test.test_cache_clearing_produces_fresh_randomization()
    test.test_deterministic_vs_random_behavior()
    
    print()
    print("🎉 All randomization tests passed! PICARD variables are properly randomized.")