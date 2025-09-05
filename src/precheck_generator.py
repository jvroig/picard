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
                # Generate random entities for this sample using enhanced substitution
                result = self.entity_pool.substitute_template_enhanced(
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
                
                # Prepare ALL variables for both sandbox generation and scoring properties
                print(f"\n📋 DEBUG: Building variable dictionary for Q{test_def.question_id}.{sample_num}:")
                print(f"   Main template: {test_def.template}")
                print(f"   Enhanced substitution result: {result}")
                
                all_variables = {}
                if 'entities' in result:
                    all_variables.update(result['entities'])
                    print(f"   Added entities: {result['entities']}")
                if 'variables' in result:
                    all_variables.update(result['variables'])
                    print(f"   Added variables: {result['variables']}")
                    
                print(f"   Final all_variables: {all_variables}")
                
                # Handle sandbox setup and file generation if needed
                # This must happen BEFORE scoring properties because template functions need the files
                sandbox_result = self._handle_sandbox_generation(precheck_entry, test_def, all_variables)
                if sandbox_result:
                    precheck_entry.update(sandbox_result)
                
                # Add scoring-specific properties with template function evaluation
                self._add_scoring_properties(precheck_entry, test_def, all_variables)
                
                precheck_entries.append(precheck_entry)
        
        return precheck_entries
    
    def _handle_sandbox_generation(self, precheck_entry: Dict[str, Any], test_def, all_variables: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle sandbox file generation for questions that need it.
        
        Args:
            precheck_entry: The precheck entry being built
            test_def: Test definition object
            all_variables: All variables (entities + enhanced variables) for substitution
            
        Returns:
            Dictionary with sandbox-related fields to add to precheck entry
        """
        if not test_def.sandbox_components:
            return {}
        
        result = {
            'sandbox_components': [comp.to_dict() for comp in test_def.sandbox_components],
            'sandbox_generation': {}
        }
        
        try:
            question_id = precheck_entry['question_id']
            sample_number = precheck_entry['sample_number']
            
            # Use all variables (entities + enhanced variables) for consistent substitution
            entity_values = all_variables
            
            # Process each sandbox component
            all_files_created = []
            all_errors = []
            components_info = []
            
            for component in test_def.sandbox_components:
                # Process sandbox component templates
                target_file = component.target_file or ''
                target_file = self.parser.substitute_artifacts(target_file, None)  # Use config artifacts dir
                target_file = self._substitute_with_all_variables(target_file, entity_values)
                target_file = self.parser.substitute_qs_id(target_file, question_id, sample_number)
                
                content_spec = component.content or {}
                
                # Create file generator
                generator_type = component.type
                file_generator = FileGeneratorFactory.create_generator(generator_type, str(self.base_dir))
                
                # Generate files during precheck generation
                generation_result = file_generator.generate(
                    target_file=target_file,
                    content_spec=content_spec,
                    clutter_spec=None  # Components don't use clutter
                )
                
                # Collect results from this component
                all_files_created.extend(generation_result['files_created'])
                all_errors.extend(generation_result.get('errors', []))
                
                components_info.append({
                    'name': component.name,
                    'type': component.type,
                    'target_file_resolved': target_file,
                    'files_created': generation_result['files_created'],
                    'errors': generation_result.get('errors', [])
                })
            
            # Store generation results
            result['sandbox_generation'] = {
                'components': components_info,
                'all_files_created': all_files_created,
                'generation_successful': len(all_errors) == 0,
                'errors': all_errors,
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
        
        # Get sandbox components for template function resolution
        sandbox_components = test_def.sandbox_components
        
        if test_def.file_to_read:
            substituted_file = self._substitute_with_all_variables(
                test_def.file_to_read, entity_values
            )
            # Apply template substitutions  
            substituted_file = self.parser.substitute_artifacts(substituted_file, None)
            substituted_file = self.parser.substitute_qs_id(substituted_file, question_id, sample_number)
            precheck_entry['file_to_read'] = substituted_file
            
            # Handle expected_content substitution for readfile_stringmatch
            if test_def.scoring_type in ['readfile_stringmatch', 'readfile_jsonmatch'] and test_def.expected_content:
                # Use consistent variable substitution (both legacy entities and enhanced variables)
                substituted_expected_content = self._substitute_with_all_variables(
                    test_def.expected_content, entity_values
                )
                # Apply template substitutions and evaluate template functions
                substituted_expected_content = self._evaluate_template_functions(
                    substituted_expected_content, question_id, sample_number, sandbox_components, entity_values
                )
                precheck_entry['expected_content'] = substituted_expected_content
        
        if test_def.files_to_check:
            substituted_files = []
            for file_path in test_def.files_to_check:
                substituted_file = self._substitute_with_all_variables(file_path, entity_values)
                substituted_file = self.parser.substitute_artifacts(substituted_file, None)
                substituted_file = self.parser.substitute_qs_id(substituted_file, question_id, sample_number)
                substituted_files.append(substituted_file)
            precheck_entry['files_to_check'] = substituted_files
        
        if test_def.expected_structure:
            substituted_structure = []
            for path in test_def.expected_structure:
                substituted_path = self._substitute_with_all_variables(path, entity_values)
                substituted_path = self.parser.substitute_artifacts(substituted_path, None)
                substituted_path = self.parser.substitute_qs_id(substituted_path, question_id, sample_number)
                substituted_structure.append(substituted_path)
            precheck_entry['expected_paths'] = substituted_structure
        
        if test_def.expected_response:
            print(f"\n🔍 DEBUG expected_response processing for Q{question_id}.{sample_number}:")
            print(f"   Original: {test_def.expected_response}")
            print(f"   Available entity_values: {list(entity_values.keys())}")
            
            substituted_response = self._substitute_with_all_variables(
                test_def.expected_response, entity_values
            )
            print(f"   After variable substitution: {substituted_response}")
            
            # Apply template substitutions and evaluate template functions with TARGET_FILE support
            substituted_response = self._evaluate_template_functions(
                substituted_response, question_id, sample_number, sandbox_components, entity_values
            )
            print(f"   After template functions: {substituted_response}")
            precheck_entry['expected_response'] = substituted_response
    def _evaluate_template_functions(self, text: str, question_id: int, sample_number: int, 
                                    components=None, entity_values=None) -> str:
        """
        Evaluate template functions in text after applying template substitutions.
        
        Args:
            text: Text that may contain template functions like {{csv_count:col:TARGET_FILE[component_name]}}
            question_id: Question ID for {{qs_id}} substitution
            sample_number: Sample number for {{qs_id}} substitution
            components: List of ComponentSpec objects for TARGET_FILE[component_name] resolution
            
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
            
            # Finally evaluate any template functions with TARGET_FILE[component_name] support
            # Create resolved components with actual file paths (not template strings)
            resolved_components = []
            if components:
                for component in components:
                    # Resolve the target_file path using the same logic as sandbox generation
                    if component.target_file:
                        resolved_target_file = component.target_file
                        resolved_target_file = self.parser.substitute_artifacts(resolved_target_file, None)
                        resolved_target_file = self._substitute_with_all_variables(resolved_target_file, entity_values or {})
                        resolved_target_file = self.parser.substitute_qs_id(resolved_target_file, question_id, sample_number)
                        
                        # Create a new component with resolved path
                        from test_definition_parser import ComponentSpec
                        resolved_component = ComponentSpec(
                            type=component.type,
                            name=component.name,
                            target_file=resolved_target_file,
                            content=component.content,
                            config=component.config,
                            depends_on=component.depends_on
                        )
                        resolved_components.append(resolved_component)
                    else:
                        resolved_components.append(component)
            
            # Create a new TemplateFunctions instance with the resolved components
            from template_functions import TemplateFunctions
            template_functions = TemplateFunctions(base_dir=str(self.base_dir), components=resolved_components)
            
            result = template_functions.evaluate_all_functions(processed_text)
            
            return result
            
        except Exception as e:
            # If template function evaluation fails, log the error and return the text with basic substitutions
            # This allows the system to continue even if files don't exist yet
            print(f"WARNING: Template function evaluation failed: {e}")
            print(f"  Text: {text}")
            print(f"  Components: {components}")
            import traceback
            traceback.print_exc()
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
    
    def _substitute_with_all_variables(self, template: str, all_variables: Dict[str, str]) -> str:
        """
        Substitute template with all variables (both legacy entities and enhanced variables).
        
        Args:
            template: Template string containing variable placeholders
            all_variables: Dictionary of all variable mappings
            
        Returns:
            Template with all variables substituted
        """
        print(f"      🔧 _substitute_with_all_variables called:")
        print(f"         Input template: {template}")
        print(f"         Variable dictionary: {all_variables}")
        
        substituted = template
        
        # Substitute all variables in the template
        for var_name, var_value in all_variables.items():
            # Handle different variable formats
            if var_name.startswith('semantic'):
                # {{semantic1:city}} format
                if ':' in var_name:
                    placeholder = f"{{{{{var_name}}}}}"
                    print(f"         Trying semantic: {placeholder} -> {var_value}")
                    if placeholder in substituted:
                        substituted = substituted.replace(placeholder, var_value)
                        print(f"           ✅ Replaced! Now: {substituted}")
                    else:
                        print(f"           ❌ Not found in template")
            elif var_name.startswith('number'):
                # {{number1:15:35:integer}} format
                if ':' in var_name:
                    placeholder = f"{{{{{var_name}}}}}"
                    print(f"         Trying number: {placeholder} -> {var_value}")
                    if placeholder in substituted:
                        substituted = substituted.replace(placeholder, var_value)
                        print(f"           ✅ Replaced! Now: {substituted}")
                    else:
                        print(f"           ❌ Not found in template")
            elif var_name.startswith('entity'):
                # {{entity1}} format (legacy)
                placeholder = f"{{{{{var_name}}}}}"
                print(f"         Trying entity: {placeholder} -> {var_value}")
                if placeholder in substituted:
                    substituted = substituted.replace(placeholder, var_value)
                    print(f"           ✅ Replaced! Now: {substituted}")
                else:
                    print(f"           ❌ Not found in template")
        
        print(f"         Final result: {substituted}")
        return substituted


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
