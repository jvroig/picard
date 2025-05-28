"""
Integration test for Phase 1 components: EntityPool + TestDefinitionParser

Demonstrates how dynamic question generation works.
"""
from pathlib import Path
import sys

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from entity_pool import EntityPool
from test_definition_parser import TestDefinitionParser


def main():
    """Test Phase 1 integration: loading test definitions and generating dynamic questions."""
    print("=== QwenSense Phase 1 Integration Test ===\n")
    
    # Initialize components
    pool = EntityPool()
    parser = TestDefinitionParser()
    
    # Load test definitions
    current_dir = Path(__file__).parent.parent
    test_file = current_dir / "config" / "test_definitions.yaml"
    test_definitions = parser.parse_file(test_file)
    
    print(f"Loaded {pool.count_entities()} entities from entity pool")
    print(f"Loaded {len(test_definitions)} test definitions\n")
    
    # Generate sample questions for each test definition
    for test_def in test_definitions:
        print(f"--- Question {test_def.question_id} ({test_def.scoring_type}) ---")
        print(f"Template: {test_def.template}")
        print(f"Samples to generate: {test_def.samples}")
        
        # Generate 3 sample variations (or less if samples < 3)
        samples_to_show = min(3, test_def.samples)
        print(f"Showing {samples_to_show} sample variations:")
        
        for i in range(samples_to_show):
            result = pool.substitute_template(test_def.template, test_def.expected_structure)
            print(f"  Sample {i+1}: {result['substituted']}")
            print(f"    Entities: {result['entities']}")
        
        # Show what the precheck entry would look like for sample 1
        if samples_to_show > 0:
            result = pool.substitute_template(test_def.template, test_def.expected_structure)
            precheck_entry = {
                'scoring_type': test_def.scoring_type,
                'question_id': test_def.question_id,
                'sample_number': 1,
                'template': test_def.template,
                **result['entities']
            }
            
            # Add scoring-specific properties
            if test_def.file_to_read:
                substituted_file = pool.substitute_with_entities(test_def.file_to_read, result['entities'])
                precheck_entry['file_to_read'] = substituted_file
            
            if test_def.files_to_check:
                substituted_files = [
                    pool.substitute_with_entities(file_path, result['entities'])
                    for file_path in test_def.files_to_check
                ]
                precheck_entry['files_to_check'] = substituted_files
            
            if test_def.expected_structure:
                substituted_structure = [
                    pool.substitute_with_entities(path, result['entities'])
                    for path in test_def.expected_structure
                ]
                precheck_entry['expected_paths'] = substituted_structure
            
            if test_def.expected_response:
                substituted_response = pool.substitute_with_entities(test_def.expected_response, result['entities'])
                precheck_entry['expected_response'] = substituted_response
            
            print(f"  Precheck entry: {precheck_entry}")
        
        print()


if __name__ == "__main__":
    main()
