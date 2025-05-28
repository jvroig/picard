"""
Entity Pool Management for QwenSense LLM Benchmarking Tool

Handles loading and random selection of entities for template substitution.
"""
import random
import re
from pathlib import Path
from typing import List, Dict, Any


class EntityPool:
    """Manages the pool of entities used for dynamic question generation."""
    
    def __init__(self, pool_file_path: str = None):
        """
        Initialize the entity pool.
        
        Args:
            pool_file_path: Path to the entity pool file. If None, uses default.
        """
        if pool_file_path is None:
            # Default to config/entity_pool.txt relative to this file
            current_dir = Path(__file__).parent.parent
            pool_file_path = current_dir / "config" / "entity_pool.txt"
        
        self.pool_file_path = Path(pool_file_path)
        self.entities = self._load_entities()
    
    def _load_entities(self) -> List[str]:
        """Load entities from the pool file."""
        if not self.pool_file_path.exists():
            raise FileNotFoundError(f"Entity pool file not found: {self.pool_file_path}")
        
        entities = []
        with open(self.pool_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    entities.append(line)
        
        if not entities:
            raise ValueError(f"No entities found in pool file: {self.pool_file_path}")
        
        return entities
    
    def get_random_entity(self) -> str:
        """Get a random entity from the pool."""
        return random.choice(self.entities)
    
    def get_random_entities(self, count: int) -> List[str]:
        """Get multiple random entities from the pool (with replacement)."""
        return [self.get_random_entity() for _ in range(count)]
    
    def substitute_template(self, template: str) -> Dict[str, Any]:
        """
        Substitute all {{entityN}} placeholders in a template with random entities.
        
        Args:
            template: String containing {{entity1}}, {{entity2}}, etc. placeholders
            
        Returns:
            Dictionary containing:
            - 'substituted': The template with placeholders replaced
            - 'entities': Dict mapping entity names to their values
        """
        # Find all entity placeholders
        entity_pattern = r'\{\{(entity\d+)\}\}'
        entity_matches = re.findall(entity_pattern, template)
        
        if not entity_matches:
            # No entities to substitute
            return {
                'substituted': template,
                'entities': {}
            }
        
        # Get unique entity names (in case same entity appears multiple times)
        unique_entities = list(set(entity_matches))
        
        # Generate random values for each unique entity
        entity_values = {}
        for entity_name in unique_entities:
            entity_values[entity_name] = self.get_random_entity()
        
        # Perform substitution
        substituted = template
        for entity_name, entity_value in entity_values.items():
            placeholder = f'{{{{{entity_name}}}}}'
            substituted = substituted.replace(placeholder, entity_value)
        
        return {
            'substituted': substituted,
            'entities': entity_values
        }
    
    def substitute_with_entities(self, template: str, entity_values: Dict[str, str]) -> str:
        """
        Substitute template using provided entity values.
        
        Args:
            template: String containing {{entityN}} placeholders
            entity_values: Dict mapping entity names to their values
            
        Returns:
            Template with placeholders replaced
        """
        substituted = template
        for entity_name, entity_value in entity_values.items():
            placeholder = f'{{{{{entity_name}}}}}'
            substituted = substituted.replace(placeholder, entity_value)
        
        return substituted
    
    def count_entities(self) -> int:
        """Return the number of entities in the pool."""
        return len(self.entities)
    
    def reload_entities(self):
        """Reload entities from the pool file."""
        self.entities = self._load_entities()


def main():
    """Test the EntityPool functionality."""
    pool = EntityPool()
    print(f"Loaded {pool.count_entities()} entities")
    
    # Test random entity selection
    print(f"Random entity: {pool.get_random_entity()}")
    print(f"5 random entities: {pool.get_random_entities(5)}")
    
    # Test template substitution
    template = "Create a {{entity1}} file in the {{entity2}} directory with {{entity3}} content"
    result = pool.substitute_template(template)
    print(f"\nOriginal template: {template}")
    print(f"Substituted: {result['substituted']}")
    print(f"Entity values: {result['entities']}")
    
    # Test substitution with provided values
    entity_values = {'entity1': 'config', 'entity2': 'logs', 'entity3': 'debug'}
    substituted = pool.substitute_with_entities(template, entity_values)
    print(f"\nUsing provided entities: {substituted}")


if __name__ == "__main__":
    main()
