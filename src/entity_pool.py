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
    
    def substitute_template(self, template: str, expected_structure: List[str] = None) -> Dict[str, Any]:
        """
        Substitute all {{entityN}} placeholders in a template with random entities.
        Also handles special {{expected_structure}} placeholder if expected_structure is provided.
        
        Args:
            template: String containing {{entity1}}, {{entity2}}, etc. placeholders
            expected_structure: List of paths for directory structure (optional)
            
        Returns:
            Dictionary containing:
            - 'substituted': The template with placeholders replaced
            - 'entities': Dict mapping entity names to their values
        """
        # Find all entity placeholders
        entity_pattern = r'\{\{(entity\d+)\}\}'
        entity_matches = re.findall(entity_pattern, template)
        
        # Check if we have expected_structure placeholder
        has_expected_structure = '{{expected_structure}}' in template
        
        if not entity_matches and not has_expected_structure:
            # No entities to substitute
            return {
                'substituted': template,
                'entities': {}
            }
        
        # Get unique entity names (in case same entity appears multiple times)
        unique_entities = list(set(entity_matches))
        
        # If we have expected_structure, we need to find entities in it too
        if has_expected_structure and expected_structure:
            for path in expected_structure:
                path_entities = re.findall(entity_pattern, path)
                unique_entities.extend(path_entities)
            unique_entities = list(set(unique_entities))
        
        # Generate random values for each unique entity
        entity_values = {}
        for entity_name in unique_entities:
            entity_values[entity_name] = self.get_random_entity()
        
        # Perform basic entity substitution
        substituted = template
        for entity_name, entity_value in entity_values.items():
            placeholder = f'{{{{{entity_name}}}}}'
            substituted = substituted.replace(placeholder, entity_value)
        
        # Handle expected_structure substitution
        if has_expected_structure and expected_structure:
            # Substitute entities in the expected_structure paths
            substituted_paths = []
            for path in expected_structure:
                substituted_path = path
                for entity_name, entity_value in entity_values.items():
                    placeholder = f'{{{{{entity_name}}}}}'
                    substituted_path = substituted_path.replace(placeholder, entity_value)
                substituted_paths.append(substituted_path)
            
            # Format as tree structure
            tree_structure = self._format_directory_tree(substituted_paths)
            
            # Replace {{expected_structure}} with the formatted tree
            substituted = substituted.replace('{{expected_structure}}', f'\n```\n{tree_structure}\n```')
        
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
    
    def _format_directory_tree(self, paths: List[str]) -> str:
        """
        Format a list of file/directory paths into a tree structure.
        
        Args:
            paths: List of paths like ["dir1/", "dir1/subdir/", "dir1/file.txt"]
            
        Returns:
            Formatted tree structure as string
        """
        if not paths:
            return ""
        
        # Sort paths to ensure proper tree structure
        sorted_paths = sorted(paths)
        tree_lines = []
        
        for i, path in enumerate(sorted_paths):
            # Count depth based on slashes
            depth = path.count('/') - (1 if path.endswith('/') else 0)
            
            # Get the name (last part of path)
            if path.endswith('/'):
                name = path.rstrip('/').split('/')[-1] + "/"
            else:
                name = path.split('/')[-1]
            
            # Determine if this is the last item at this depth level
            is_last = True
            current_prefix = '/'.join(path.rstrip('/').split('/')[:-1])
            
            for j in range(i + 1, len(sorted_paths)):
                next_path = sorted_paths[j]
                next_prefix = '/'.join(next_path.rstrip('/').split('/')[:-1])
                next_depth = next_path.count('/') - (1 if next_path.endswith('/') else 0)
                
                if next_depth == depth and next_prefix == current_prefix:
                    is_last = False
                    break
                elif next_depth < depth:
                    break
            
            # Build the tree prefix
            prefix = ""
            for d in range(depth):
                # Check if there are more items at parent levels
                parent_parts = path.rstrip('/').split('/')[:d+1]
                parent_path = '/'.join(parent_parts)
                
                has_siblings_below = False
                for j in range(i + 1, len(sorted_paths)):
                    check_path = sorted_paths[j]
                    check_parts = check_path.rstrip('/').split('/')
                    if len(check_parts) > d:
                        check_parent = '/'.join(check_parts[:d+1])
                        if check_parent != parent_path and '/'.join(check_parts[:d]) == '/'.join(parent_parts[:d]):
                            has_siblings_below = True
                            break
                
                if has_siblings_below:
                    prefix += "│   "
                else:
                    prefix += "    "
            
            # Add the final connector
            if is_last:
                connector = "└── "
            else:
                connector = "├── "
            
            tree_lines.append(f"{prefix}{connector}{name}")
        
        return '\n'.join(tree_lines)

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
