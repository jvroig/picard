"""
Precheck Generator - Shared logic for generating precheck entries

Extracted from system_test.py for reuse in test_runner.py and other components.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from entity_pool import EntityPool
from test_definition_parser import TestDefinitionParser


class PrecheckGenerator:
    """Generates precheck entries from test definitions and entity pool."""
    
    def __init__(self, entity_pool_file: str = None, test_definitions_file: str = None):
        """
        Initialize the precheck generator.
        
        Args:
            entity_pool_file: Path to entity pool file (optional)
            test_definitions_file: Path to test definitions file (optional)
        """
        self.entity_pool = EntityPool(entity_pool_file)
        self.parser = TestDefinitionParser()
        
        if test_definitions_file:
            self.test_definitions = self.parser.parse_file(test_definitions_file)
        else:
            self.test_definitions = []
    
    def load_test_definitions(self, test_definitions_file: str):
        """Load test definitions from file."""
        self.test_definitions = self.parser.parse_file(test_definitions_file)
    
    def generate_precheck_entries(self) -> List[Dict[str, Any]]:
        """
        Generate precheck entries for all test definitions.
        
        Returns:
            List of precheck entry dictionaries
        """
        precheck_entries = []
        
        for test_def in self.test_definitions:
            for sample_num in range(1, test_def.samples + 1):
                # Generate random entities for this sample
                result = self.entity_pool.substitute_template(
                    test_def.template, 
                    test_def.expected_structure
                )
                
                # Build precheck entry
                precheck_entry = {
                    'scoring_type': test_def.scoring_type,
                    'question_id': test_def.question_id,
                    'sample_number': sample_num,
                    'template': test_def.template,
                    'substituted_question': result['substituted'],
                    **result['entities']  # Add all entity mappings
                }
                
                # Add scoring-specific properties
                self._add_scoring_properties(precheck_entry, test_def, result['entities'])
                
                precheck_entries.append(precheck_entry)
        
        return precheck_entries
    
    def _add_scoring_properties(self, precheck_entry: Dict[str, Any], 
                               test_def, entity_values: Dict[str, str]):
        """Add scoring-specific properties to precheck entry."""
        
        if test_def.file_to_read:
            substituted_file = self.entity_pool.substitute_with_entities(
                test_def.file_to_read, entity_values
            )
            precheck_entry['file_to_read'] = substituted_file
            
            # Generate expected content for readfile_stringmatch
            if test_def.scoring_type == 'readfile_stringmatch':
                # Extract expected content from template
                if 'Hello {{entity1}}' in test_def.template:
                    expected_content = f"Hello {entity_values.get('entity1', '')}"
                    precheck_entry['expected_content'] = expected_content
        
        if test_def.files_to_check:
            substituted_files = [
                self.entity_pool.substitute_with_entities(file_path, entity_values)
                for file_path in test_def.files_to_check
            ]
            precheck_entry['files_to_check'] = substituted_files
        
        if test_def.expected_structure:
            substituted_structure = [
                self.entity_pool.substitute_with_entities(path, entity_values)
                for path in test_def.expected_structure
            ]
            precheck_entry['expected_paths'] = substituted_structure
        
        if test_def.expected_response:
            substituted_response = self.entity_pool.substitute_with_entities(
                test_def.expected_response, entity_values
            )
            precheck_entry['expected_response'] = substituted_response
    
    def save_precheck_entries(self, precheck_entries: List[Dict[str, Any]], 
                             output_file: str):
        """Save precheck entries to JSONL file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in precheck_entries:
                f.write(json.dumps(entry) + '\n')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded test definitions."""
        if not self.test_definitions:
            return {'error': 'No test definitions loaded'}
        
        total_samples = sum(test_def.samples for test_def in self.test_definitions)
        by_scoring_type = {}
        
        for test_def in self.test_definitions:
            scoring_type = test_def.scoring_type
            if scoring_type not in by_scoring_type:
                by_scoring_type[scoring_type] = {'questions': 0, 'samples': 0}
            by_scoring_type[scoring_type]['questions'] += 1
            by_scoring_type[scoring_type]['samples'] += test_def.samples
        
        return {
            'total_questions': len(self.test_definitions),
            'total_samples': total_samples,
            'entity_pool_size': self.entity_pool.count_entities(),
            'by_scoring_type': by_scoring_type
        }


def main():
    """Test the precheck generator."""
    print("🧪 Testing Precheck Generator")
    print("=" * 30)
    
    # Initialize generator
    current_dir = Path(__file__).parent.parent
    test_file = current_dir / "config" / "test_definitions.yaml"
    
    generator = PrecheckGenerator(test_definitions_file=str(test_file))
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"📊 Statistics:")
    print(f"   Questions: {stats['total_questions']}")
    print(f"   Total samples: {stats['total_samples']}")
    print(f"   Entity pool: {stats['entity_pool_size']} words")
    print(f"   By scoring type: {stats['by_scoring_type']}")
    print()
    
    # Generate precheck entries
    print("🔄 Generating precheck entries...")
    precheck_entries = generator.generate_precheck_entries()
    print(f"✅ Generated {len(precheck_entries)} precheck entries")
    
    # Show first few entries
    print("\n📄 Sample entries:")
    for i, entry in enumerate(precheck_entries[:3]):
        print(f"   Entry {i+1}: Q{entry['question_id']}.{entry['sample_number']} ({entry['scoring_type']})")
        print(f"      Question: {entry['substituted_question'][:60]}{'...' if len(entry['substituted_question']) > 60 else ''}")
    
    print("\n✅ Precheck generator test completed!")


if __name__ == "__main__":
    main()
