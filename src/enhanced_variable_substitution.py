"""
Enhanced Variable Substitution for the PICARD framework.

Supports semantic variables, numeric ranges, and enhanced entity pools
while maintaining backwards compatibility with the existing entity system.
"""

import re
import random
from typing import Dict, Any, List
from pathlib import Path
from file_generators import DataGenerator
from entity_pool import EntityPool


class EnhancedVariableSubstitution:
    """
    Enhanced variable substitution supporting semantic, numeric, and entity pool variables.
    
    Supports:
    - Semantic variables: {{semantic1:person_name}}, {{semantic2:company}}, etc.
    - Numeric variables: {{number1:10:100}}, {{number2:1000:5000:currency}}, etc.
    - Enhanced entity pools: {{entity1:colors}}, {{entity2:metals}}, etc.
    - Backwards compatibility: {{entity1}} = {{entity1:default}}
    """
    
    def __init__(self, seed: int = None):
        """
        Initialize the enhanced variable substitution system.
        
        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            
        self.data_generator = DataGenerator()
        self.entity_pool = EntityPool()  # Load existing entity pool
        
        # Caches for consistent variable referencing within a test
        self.semantic_cache = {}  # {(index, data_type): value}
        self.numeric_cache = {}   # {(index, min, max, type): value}
        self.entity_cache = {}    # {(index, pool): value}
        
        # Enhanced entity pools
        self.entity_pools = {
            'default': self.entity_pool.entities,  # Use actual loaded entity pool
            'colors': [
                'crimson', 'azure', 'amber', 'emerald', 'golden', 'silver',
                'red', 'blue', 'green', 'yellow', 'orange', 'purple'
            ],
            'nature': [
                'mountain', 'forest', 'river', 'canyon', 'valley', 'meadow',
                'ocean', 'desert', 'prairie', 'creek', 'lake', 'beach'
            ],
            'metals': [
                'silver', 'golden', 'copper', 'platinum', 'iron', 'bronze',
                'steel', 'titanium', 'chrome', 'aluminum', 'zinc', 'nickel'
            ],
            'gems': [
                'emerald', 'crystal', 'diamond', 'pearl', 'sapphire', 'ruby',
                'amber', 'opal', 'topaz', 'amethyst', 'garnet', 'onyx'
            ]
        }
    
    def substitute_all_variables(self, text: str) -> Dict[str, Any]:
        """
        Substitute all enhanced variable types in text.
        
        Args:
            text: Text containing variable placeholders
            
        Returns:
            Dict with 'substituted' text and variable mappings
        """
        substituted = text
        all_variables = {}
        
        # Process semantic variables: {{semantic1:data_type}}
        substituted, semantic_vars = self._substitute_semantic_variables(substituted)
        all_variables.update(semantic_vars)
        
        # Process numeric variables: {{number1:min:max:type}}
        substituted, numeric_vars = self._substitute_numeric_variables(substituted)
        all_variables.update(numeric_vars)
        
        # Process enhanced entity variables: {{entity1:pool}}
        substituted, entity_vars = self._substitute_entity_variables(substituted)
        all_variables.update(entity_vars)
        
        # Process legacy entity variables for backwards compatibility: {{entity1}}
        substituted, legacy_vars = self._substitute_legacy_entities(substituted)
        all_variables.update(legacy_vars)
        
        return {
            'substituted': substituted,
            'variables': all_variables
        }
    
    def _substitute_semantic_variables(self, text: str) -> tuple[str, Dict[str, str]]:
        """
        Substitute semantic variables like {{semantic1:person_name}}.
        
        Returns:
            Tuple of (substituted_text, variable_mappings)
        """
        pattern = r'\{\{semantic(\d+):([a-zA-Z_]+)\}\}'
        variables = {}
        
        def replace_semantic(match):
            index = int(match.group(1))
            data_type = match.group(2)
            cache_key = (index, data_type)
            
            # Return cached value if already generated
            if cache_key in self.semantic_cache:
                value = self.semantic_cache[cache_key]
            else:
                # Generate and cache new value
                value = self.data_generator.generate_field(data_type)
                self.semantic_cache[cache_key] = value
            
            # Track in variables mapping
            var_name = f"semantic{index}:{data_type}"
            variables[var_name] = value
            
            return value
        
        substituted = re.sub(pattern, replace_semantic, text)
        return substituted, variables
    
    def _substitute_numeric_variables(self, text: str) -> tuple[str, Dict[str, str]]:
        """
        Substitute numeric variables like {{number1:10:100:currency}}.
        
        Returns:
            Tuple of (substituted_text, variable_mappings)
        """
        pattern = r'\{\{number(\d+):(\d+):(\d+)(?::([a-zA-Z_]+))?\}\}'
        variables = {}
        
        def replace_numeric(match):
            index = int(match.group(1))
            min_val = int(match.group(2))
            max_val = int(match.group(3))
            num_type = match.group(4) or 'integer'
            cache_key = (index, min_val, max_val, num_type)
            
            # Return cached value if already generated
            if cache_key in self.numeric_cache:
                value = self.numeric_cache[cache_key]
            else:
                # Generate and cache new value
                value = self._generate_number(min_val, max_val, num_type)
                self.numeric_cache[cache_key] = value
            
            # Track in variables mapping
            var_name = f"number{index}:{min_val}:{max_val}:{num_type}"
            variables[var_name] = str(value)
            
            return str(value)
        
        substituted = re.sub(pattern, replace_numeric, text)
        return substituted, variables
    
    def _substitute_entity_variables(self, text: str) -> tuple[str, Dict[str, str]]:
        """
        Substitute enhanced entity variables like {{entity1:colors}}.
        
        Returns:
            Tuple of (substituted_text, variable_mappings)
        """
        pattern = r'\{\{entity(\d+):([a-zA-Z_]+)\}\}'
        variables = {}
        
        def replace_entity(match):
            index = int(match.group(1))
            pool_name = match.group(2)
            cache_key = (index, pool_name)
            
            # Return cached value if already generated
            if cache_key in self.entity_cache:
                value = self.entity_cache[cache_key]
            else:
                # Generate and cache new value
                if pool_name not in self.entity_pools:
                    raise ValueError(f"Unknown entity pool: {pool_name}")
                
                # Use index for deterministic selection within the pool
                pool = self.entity_pools[pool_name]
                value = pool[index % len(pool)]
                self.entity_cache[cache_key] = value
            
            # Track in variables mapping
            var_name = f"entity{index}:{pool_name}"
            variables[var_name] = value
            
            return value
        
        substituted = re.sub(pattern, replace_entity, text)
        return substituted, variables
    
    def _substitute_legacy_entities(self, text: str) -> tuple[str, Dict[str, str]]:
        """
        Substitute legacy entity variables like {{entity1}} for backwards compatibility.
        
        Returns:
            Tuple of (substituted_text, variable_mappings)
        """
        pattern = r'\{\{entity(\d+)\}\}'
        variables = {}
        
        def replace_legacy(match):
            index = int(match.group(1))
            # Legacy entities use the default pool
            cache_key = (index, 'default')
            
            # Return cached value if already generated
            if cache_key in self.entity_cache:
                value = self.entity_cache[cache_key]
            else:
                # Generate and cache new value using default pool
                pool = self.entity_pools['default']
                value = pool[index % len(pool)]
                self.entity_cache[cache_key] = value
            
            # Track in variables mapping
            var_name = f"entity{index}"
            variables[var_name] = value
            
            return value
        
        substituted = re.sub(pattern, replace_legacy, text)
        return substituted, variables
    
    def _generate_number(self, min_val: int, max_val: int, num_type: str) -> Any:
        """
        Generate a number based on type and range.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            num_type: Type of number (integer, decimal, currency, percentage)
            
        Returns:
            Generated number of appropriate type
        """
        if num_type == 'integer':
            return random.randint(min_val, max_val)
        elif num_type == 'decimal':
            return round(random.uniform(min_val, max_val), 2)
        elif num_type == 'currency':
            return random.randint(min_val, max_val)
        elif num_type == 'percentage':
            return round(random.uniform(min_val, max_val), 1)
        else:
            raise ValueError(f"Unknown number type: {num_type}")
    
    def clear_cache(self):
        """Clear all variable caches (for new test)."""
        self.semantic_cache.clear()
        self.numeric_cache.clear()
        self.entity_cache.clear()
        
        # Reset random seed if one was provided
        if self.seed is not None:
            random.seed(self.seed)


def main():
    """Test the enhanced variable substitution."""
    evs = EnhancedVariableSubstitution(seed=42)
    
    # Test semantic variables
    template1 = "Employee {{semantic1:person_name}} works in {{semantic2:department}} with salary ${{number1:30000:150000:currency}}"
    result1 = evs.substitute_all_variables(template1)
    print("Semantic + Numeric test:")
    print(f"Template: {template1}")
    print(f"Result: {result1['substituted']}")
    print(f"Variables: {result1['variables']}")
    print()
    
    # Test consistency
    template2 = "{{semantic1:person_name}} from {{semantic2:department}} earns ${{number1:30000:150000:currency}}"
    result2 = evs.substitute_all_variables(template2)
    print("Consistency test (should have same values):")
    print(f"Template: {template2}")
    print(f"Result: {result2['substituted']}")
    print()
    
    # Test entity pools
    template3 = "Process {{entity1:colors}}_data.csv in {{entity2:metals}}_server using {{entity3:gems}}_backup"
    result3 = evs.substitute_all_variables(template3)
    print("Entity pools test:")
    print(f"Template: {template3}")
    print(f"Result: {result3['substituted']}")
    print(f"Variables: {result3['variables']}")
    print()
    
    # Test backwards compatibility
    template4 = "Legacy: {{entity1}} and {{entity2}} files"
    result4 = evs.substitute_all_variables(template4)
    print("Backwards compatibility test:")
    print(f"Template: {template4}")
    print(f"Result: {result4['substituted']}")
    print(f"Variables: {result4['variables']}")


if __name__ == "__main__":
    main()