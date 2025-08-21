"""
Enhanced Template Processor for the PICARD framework

Combines entity substitution with template function evaluation.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from entity_pool import EntityPool
from template_functions import TemplateFunctions, TemplateFunctionError
from test_definition_parser import TestDefinitionParser


class TemplateProcessor:
    """Enhanced template processor that handles both entity and function substitution."""
    
    def __init__(self, entity_pool_file: str = None, base_dir: str = None):
        """
        Initialize the template processor.
        
        Args:
            entity_pool_file: Path to entity pool file (optional)
            base_dir: Base directory for resolving file paths (optional)
        """
        self.entity_pool = EntityPool(entity_pool_file)
        self.template_functions = TemplateFunctions(base_dir)
    
    def process_template(self, template: str, question_id: int, sample_number: int, 
                        expected_structure: List[str] = None) -> Dict[str, Any]:
        """
        Process a template with full entity and function substitution.
        
        Args:
            template: Template string with {{entity1}}, {{qs_id}}, {{file_line:3:path}} etc.
            question_id: Question ID for {{qs_id}} substitution
            sample_number: Sample number for {{qs_id}} substitution
            expected_structure: List of paths for directory structure (optional)
        
        Returns:
            Dictionary containing:
            - 'original_template': The original template
            - 'substituted': Fully processed template
            - 'entities': Dict of legacy entity substitutions (for compatibility)
            - 'variables': Dict of all variable substitutions (enhanced)
            - 'template_function_results': Dict of template function results (if any)
            - 'has_template_functions': Boolean indicating if template functions were used
        """
        result = {
            'original_template': template,
            'entities': {},
            'template_function_results': {},
            'has_template_functions': False
        }
        
        # Step 1: {{qs_id}} substitution
        current_template = TestDefinitionParser.substitute_qs_id(template, question_id, sample_number)
        
        # Step 2: Enhanced entity substitution (with fallback to legacy)
        entity_result = self.entity_pool.substitute_template_enhanced(current_template, expected_structure)
        current_template = entity_result['substituted']
        result['entities'] = entity_result['entities']  # Legacy compatibility
        result['variables'] = entity_result.get('variables', {})
        
        # Step 3: Template function evaluation (if any)
        try:
            # Check if there are any template functions to process
            import re
            function_pattern = r'\{\{([^:]+):([^}]+)\}\}'
            if re.search(function_pattern, current_template):
                result['has_template_functions'] = True
                
                # Store function calls before evaluation for debugging
                function_matches = re.findall(function_pattern, current_template)
                for func_name, args_str in function_matches:
                    function_call = f"{{{{{func_name}:{args_str}}}}}"
                    result['template_function_results'][function_call] = None  # Will be filled during evaluation
                
                # Evaluate template functions
                final_template = self.template_functions.evaluate_all_functions(current_template)
                
                # Record what each function resolved to
                if function_matches:
                    # Re-evaluate individual functions to capture results
                    for func_name, args_str in function_matches:
                        function_call = f"{{{{{func_name}:{args_str}}}}}"
                        args = [arg.strip() for arg in args_str.split(':')]
                        try:
                            func_result = self.template_functions.evaluate_function(func_name, args)
                            result['template_function_results'][function_call] = str(func_result)
                        except Exception as e:
                            result['template_function_results'][function_call] = f"ERROR: {e}"
                
                current_template = final_template
            
        except TemplateFunctionError as e:
            # Template function evaluation failed, but we continue with what we have
            result['template_function_error'] = str(e)
        except Exception as e:
            # Unexpected error during template function processing
            result['template_function_error'] = f"Unexpected error: {e}"
        
        result['substituted'] = current_template
        return result
    
    def process_multiple_fields(self, fields: Dict[str, str], question_id: int, sample_number: int,
                               expected_structure: List[str] = None) -> Dict[str, Any]:
        """
        Process multiple template fields using consistent enhanced variable substitution.
        
        Uses the enhanced substitution system to support semantic, numeric, and entity variables
        while maintaining consistency across all fields (same variable produces same value).
        
        Args:
            fields: Dict mapping field names to template strings
            question_id: Question ID for {{qs_id}} substitution  
            sample_number: Sample number for {{qs_id}} substitution
            expected_structure: List of paths for directory structure (optional)
        
        Returns:
            Dictionary containing processed results for all fields
        """
        # Use enhanced substitution for all fields with shared variable state
        # This ensures consistent values across all fields (same {{number1:10:50}} produces same value)
        
        # Step 1: {{qs_id}} substitution for all fields
        qs_id_substituted = {}
        for field_name, template in fields.items():
            qs_id_substituted[field_name] = TestDefinitionParser.substitute_qs_id(template, question_id, sample_number)
        
        # Step 2: Enhanced variable substitution with shared state
        # Process all templates with the same enhanced substitution instance to maintain consistency
        enhanced_result = self.entity_pool.substitute_template_enhanced(
            '\n'.join(qs_id_substituted.values()), expected_structure
        )
        
        # Split the results back to individual fields
        substituted_lines = enhanced_result['substituted'].split('\n')
        field_names = list(qs_id_substituted.keys())
        
        # Step 3: Template function evaluation for each field
        results = {}
        all_variables = enhanced_result.get('variables', {})
        legacy_entities = enhanced_result.get('entities', {})
        
        for i, field_name in enumerate(field_names):
            current_template = substituted_lines[i] if i < len(substituted_lines) else qs_id_substituted[field_name]
            
            # Handle template functions
            template_function_results = {}
            has_template_functions = False
            
            try:
                import re
                function_pattern = r'\{\{([^:]+):([^}]+)\}\}'
                if re.search(function_pattern, current_template):
                    has_template_functions = True
                    function_matches = re.findall(function_pattern, current_template)
                    
                    for func_name, args_str in function_matches:
                        function_call = f"{{{{{func_name}:{args_str}}}}}"
                        args = [arg.strip() for arg in args_str.split(':')]
                        try:
                            func_result = self.template_functions.evaluate_function(func_name, args)
                            template_function_results[function_call] = str(func_result)
                        except Exception as e:
                            template_function_results[function_call] = f"ERROR: {e}"
                    
                    current_template = self.template_functions.evaluate_all_functions(current_template)
            
            except Exception as e:
                template_function_results['error'] = str(e)
            
            results[field_name] = {
                'original_template': fields[field_name],
                'substituted': current_template,
                'has_template_functions': has_template_functions,
                'template_function_results': template_function_results
            }
        
        # Add shared variable information (enhanced)
        results['_shared'] = {
            'entities': legacy_entities,  # For backwards compatibility
            'variables': all_variables,   # All enhanced variables
            'question_id': question_id,
            'sample_number': sample_number,
            'qs_id': f"q{question_id}_s{sample_number}"
        }
        
        return results


def main():
    """Test the TemplateProcessor functionality."""
    import tempfile
    import os
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files for template functions
        test_file = temp_path / "q1_s1" / "test_data.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("First line\nSecond line\nThird line content\nFourth line")
        
        csv_file = temp_path / "q1_s1" / "data.csv"
        csv_file.write_text("name,age,salary\nJohn,25,50000\nAlice,30,60000")
        
        # Initialize processor
        processor = TemplateProcessor(base_dir=temp_dir)
        
        # Test cases
        test_cases = [
            # Basic entity substitution
            {
                'template': 'Hello {{entity1}} from {{entity2}}',
                'description': 'Basic entity substitution'
            },
            # {{qs_id}} substitution
            {
                'template': 'File: test_artifacts/{{qs_id}}/{{entity1}}.txt',
                'description': 'qs_id and entity substitution'
            },
            # Template functions
            {
                'template': 'Line 3 says: {{file_line:3:{{qs_id}}/test_data.txt}}',
                'description': 'Template function with qs_id'
            },
            # CSV template functions
            {
                'template': 'Name in row 1: {{csv_value:1:name:{{qs_id}}/data.csv}}',
                'description': 'CSV template function'
            },
            # Combined everything
            {
                'template': 'User {{entity1}} ({{csv_value:0:name:{{qs_id}}/data.csv}}) has salary {{csv_value:0:salary:{{qs_id}}/data.csv}}',
                'description': 'Entity + CSV functions'
            },
            # Enhanced variables
            {
                'template': 'Employee {{semantic1:person_name}} in {{semantic2:department}} earns ${{number1:30000:80000:currency}}',
                'description': 'Enhanced semantic and numeric variables'
            },
            # Enhanced entity pools
            {
                'template': 'Process {{entity1:colors}} data on {{entity2:metals}} server',
                'description': 'Enhanced entity pools'
            },
            # Mixed enhanced and legacy
            {
                'template': 'Archive {{entity1}} and {{semantic1:person_name}} files to {{entity2:gems}} backup',
                'description': 'Mixed enhanced and legacy variables'
            }
        ]
        
        print("Testing TemplateProcessor:")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"   Template: {test_case['template']}")
            
            try:
                result = processor.process_template(test_case['template'], question_id=1, sample_number=1)
                print(f"   Result: {result['substituted']}")
                if result['entities']:
                    print(f"   Legacy Entities: {result['entities']}")
                if result.get('variables'):
                    print(f"   All Variables: {result['variables']}")
                if result['has_template_functions']:
                    print(f"   Functions: {result['template_function_results']}")
            except Exception as e:
                print(f"   ERROR: {e}")


if __name__ == "__main__":
    main()
