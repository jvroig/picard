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
from file_generators import FileGeneratorFactory
from template_processor import TemplateProcessor


class PrecheckGenerator:
    """Generates precheck entries from test definitions and entity pool."""
    
    def __init__(self, entity_pool_file: str = None, test_definitions_file: str = None, base_dir: str = None):
        """
        Initialize the precheck generator.
        
        Args:
            entity_pool_file: Path to entity pool file (optional)
            test_definitions_file: Path to test definitions file (optional)
            base_dir: Base directory for file operations (optional)
        """
        self.entity_pool = EntityPool(entity_pool_file)
        self.parser = TestDefinitionParser()
        
        # Initialize template processor for function evaluation
        self.template_processor = TemplateProcessor(
            entity_pool_file=entity_pool_file,
            base_dir=base_dir
        )
        
        # Set base directory for file generation
        if base_dir is None:
            base_dir = Path.cwd()
        self.base_dir = Path(base_dir)
        
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
        Handles sandbox file generation and template function evaluation.
        
        Returns:
            List of precheck entry dictionaries with resolved template functions
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
                
                # Apply {{artifacts}} and {{qs_id}} substitutions to the question
                # This ensures the LLM sees the fully resolved question
                # Use the same artifacts directory resolution as sandbox generation
                artifacts_dir = None  # Let it load from config for consistency
                fully_substituted_question = self.parser.substitute_artifacts(precheck_entry['substituted_question'], artifacts_dir)
                fully_substituted_question = self.parser.substitute_qs_id(fully_substituted_question, test_def.question_id, sample_num)
                precheck_entry['substituted_question'] = fully_substituted_question
                
                # Handle sandbox setup and file generation if needed
                # This must happen BEFORE scoring properties because template functions need the files
                sandbox_result = self._handle_sandbox_generation(precheck_entry, test_def)
                if sandbox_result:
                    precheck_entry.update(sandbox_result)
                
                # Add scoring-specific properties with template function evaluation
                # Pass the entity values from the initial substitution to ensure consistency
                self._add_scoring_properties(precheck_entry, test_def, result['entities'])
                
                precheck_entries.append(precheck_entry)
        
        return precheck_entries
    
    def _handle_sandbox_generation(self, precheck_entry: Dict[str, Any], test_def) -> Dict[str, Any]:
        """
        Handle sandbox file generation for questions that need it.
        
        Args:
            precheck_entry: The precheck entry being built
            test_def: Test definition object
            
        Returns:
            Dictionary with sandbox-related fields to add to precheck entry
        """
        if not test_def.sandbox_setup:
            return {}
        
        result = {
            'sandbox_setup': test_def.sandbox_setup.to_dict(),
            'sandbox_generation': {}
        }
        
        try:
            question_id = precheck_entry['question_id']
            sample_number = precheck_entry['sample_number']
            
            # Get entity values from precheck entry
            entity_values = {k: v for k, v in precheck_entry.items() if k.startswith('entity')}
            
            # Process sandbox setup templates
            setup_fields = {
                'target_file': test_def.sandbox_setup.target_file or '',
                'content': str(test_def.sandbox_setup.content or {}),
                'clutter': str(test_def.sandbox_setup.clutter or {})
            }
            
            # Use manual entity substitution and template substitutions for consistency
            target_file = setup_fields['target_file']
            target_file = self.parser.substitute_artifacts(target_file, None)  # Use config artifacts dir
            target_file = self.entity_pool.substitute_with_entities(target_file, entity_values)
            target_file = self.parser.substitute_qs_id(target_file, question_id, sample_number)
            
            content_spec = eval(setup_fields['content']) if setup_fields['content'] != '{}' else {}
            clutter_spec = eval(setup_fields['clutter']) if setup_fields['clutter'] != '{}' else None
            
            # Create file generator
            generator_type = test_def.sandbox_setup.type
            file_generator = FileGeneratorFactory.create_generator(generator_type, str(self.base_dir))
            
            # Generate files during precheck generation
            generation_result = file_generator.generate(
                target_file=target_file,
                content_spec=content_spec,
                clutter_spec=clutter_spec
            )
            
            # Store generation results
            result['sandbox_generation'] = {
                'target_file_resolved': target_file,
                'files_created': generation_result['files_created'],
                'generation_successful': len(generation_result.get('errors', [])) == 0,
                'errors': generation_result.get('errors', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['sandbox_generation'] = {
                'generation_successful': False,
                'errors': [f"Sandbox generation failed: {e}"],
                'timestamp': datetime.now().isoformat()
            }
        
        return result
    
    def _add_scoring_properties(self, precheck_entry: Dict[str, Any], 
                               test_def, entity_values: Dict[str, str]):
        """Add scoring-specific properties to precheck entry with template function evaluation."""
        
        question_id = precheck_entry['question_id']
        sample_number = precheck_entry['sample_number']
        
        # Get the resolved target file path if sandbox setup exists
        target_file_path = None
        if 'sandbox_generation' in precheck_entry:
            target_file_path = precheck_entry['sandbox_generation'].get('target_file_resolved')
        
        if test_def.file_to_read:
            substituted_file = self.entity_pool.substitute_with_entities(
                test_def.file_to_read, entity_values
            )
            # Apply template substitutions  
            substituted_file = self.parser.substitute_artifacts(substituted_file, None)
            substituted_file = self.parser.substitute_qs_id(substituted_file, question_id, sample_number)
            precheck_entry['file_to_read'] = substituted_file
            
            # Handle expected_content substitution for readfile_stringmatch
            if test_def.scoring_type in ['readfile_stringmatch', 'readfile_jsonmatch'] and test_def.expected_content:
                substituted_expected_content = self.entity_pool.substitute_with_entities(
                    test_def.expected_content, entity_values
                )
                # Apply template substitutions and evaluate template functions
                substituted_expected_content = self._evaluate_template_functions(
                    substituted_expected_content, question_id, sample_number, target_file_path
                )
                precheck_entry['expected_content'] = substituted_expected_content
        
        if test_def.files_to_check:
            substituted_files = []
            for file_path in test_def.files_to_check:
                substituted_file = self.entity_pool.substitute_with_entities(file_path, entity_values)
                substituted_file = self.parser.substitute_artifacts(substituted_file, None)
                substituted_file = self.parser.substitute_qs_id(substituted_file, question_id, sample_number)
                substituted_files.append(substituted_file)
            precheck_entry['files_to_check'] = substituted_files
        
        if test_def.expected_structure:
            substituted_structure = []
            for path in test_def.expected_structure:
                substituted_path = self.entity_pool.substitute_with_entities(path, entity_values)
                substituted_path = self.parser.substitute_artifacts(substituted_path, None)
                substituted_path = self.parser.substitute_qs_id(substituted_path, question_id, sample_number)
                substituted_structure.append(substituted_path)
            precheck_entry['expected_paths'] = substituted_structure
        
        if test_def.expected_response:
            substituted_response = self.entity_pool.substitute_with_entities(
                test_def.expected_response, entity_values
            )
            # Apply template substitutions and evaluate template functions with TARGET_FILE support
            substituted_response = self._evaluate_template_functions(
                substituted_response, question_id, sample_number, target_file_path
            )
            precheck_entry['expected_response'] = substituted_response
    def _evaluate_template_functions(self, text: str, question_id: int, sample_number: int, 
                                    target_file_path: str = None) -> str:
        """
        Evaluate template functions in text after applying template substitutions.
        
        Args:
            text: Text that may contain template functions like {{file_line:3:path}}
            question_id: Question ID for {{qs_id}} substitution
            sample_number: Sample number for {{qs_id}} substitution
            target_file_path: Path to substitute for TARGET_FILE keyword (optional)
            
        Returns:
            Text with template functions evaluated to their actual values
        """
        if not text:
            return text
        
        try:
            # First apply {{artifacts}} substitution
            processed_text = self.parser.substitute_artifacts(text)
            
            # Then apply {{qs_id}} substitution
            processed_text = self.parser.substitute_qs_id(processed_text, question_id, sample_number)
            
            # Finally evaluate any template functions with TARGET_FILE support
            result = self.template_processor.template_functions.evaluate_all_functions(
                processed_text, target_file_path
            )
            
            return result
            
        except Exception as e:
            # If template function evaluation fails, return the text with basic substitutions
            # This allows the system to continue even if files don't exist yet
            processed_text = self.parser.substitute_artifacts(text)
            return self.parser.substitute_qs_id(processed_text, question_id, sample_number)
    
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
