"""
PICARD Test Runner - Execute LLM benchmark tests

Main command-line tool for running benchmark tests against LLMs.
Generates precheck files, executes questions, collects responses, and organizes results.
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add src and scripts to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent / "scripts"))

from precheck_generator import PrecheckGenerator
from sandbox_manager import SandboxManager
from file_generators import FileGeneratorFactory
from template_processor import TemplateProcessor


class TestRunner:
    """Main test runner for PICARD benchmarks."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize test runner.
        
        Args:
            base_dir: Base directory of PICARD project (optional)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.config_dir = self.base_dir / "config"
        
        # Initialize components
        self.sandbox_manager = SandboxManager(base_dir)
        self.template_processor = TemplateProcessor(base_dir=base_dir)
        self.precheck_generator = None
        
        # Test run info
        self.test_id = None
        self.test_dir = None
        
        # Progressive writing handles
        self.responses_file = None
        self.conversations_dir = None
    
    def sanitize_label(self, label: str) -> str:
        """
        Sanitize user-provided label for filesystem compatibility.
        
        Args:
            label: Raw user input label
            
        Returns:
            Sanitized label safe for folder names
            
        Rules:
            - Convert to lowercase
            - Replace spaces with underscores
            - Remove/replace special characters
            - Limit length to reasonable bounds
            - Ensure non-empty result
        """
        import re
        
        if not label or not label.strip():
            return "test"
        
        # Convert to lowercase and replace spaces, hyphens, and periods with underscores
        sanitized = label.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
        
        # Keep only alphanumeric and underscores 
        sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Trim underscores from start/end
        sanitized = sanitized.strip('_')
        
        # Length limits (reasonable for folder names)
        if len(sanitized) > 50:
            sanitized = sanitized[:50].rstrip('_')
        
        # Ensure non-empty
        if not sanitized:
            return "test"
        
        return sanitized
    
    def initialize_test_run(self, test_definitions_file: str = None, label: str = "test") -> str:
        """
        Initialize a new test run.
        
        Args:
            test_definitions_file: Path to test definitions YAML file
            label: Label for test run folder
            
        Returns:
            Test ID for this run
        """
        # Sanitize the label
        clean_label = self.sanitize_label(label)
        
        # Generate test ID with custom label
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_id = f"{clean_label}_{timestamp}"
        
        # Create test directory
        self.test_dir = self.results_dir / self.test_id
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize precheck generator
        if test_definitions_file is None:
            test_definitions_file = self.config_dir / "test_definitions.yaml"
        
        self.precheck_generator = PrecheckGenerator(
            test_definitions_file=str(test_definitions_file),
            base_dir=str(self.base_dir)
        )
        
        return self.test_id
    
    def run_benchmark(self, test_definitions_file: str = None, 
                     sandbox_template: str = "clean_sandbox",
                     max_retries: int = 3, max_llm_rounds: int = 20, retry_delay: float = 2.0,
                     use_mock_llm: bool = False, api_endpoint: str = None,
                     label: str = "test") -> Dict[str, str]:
        """
        Run complete benchmark test.
        
        Args:
            test_definitions_file: Path to test definitions YAML file
            sandbox_template: Sandbox template to use
            max_retries: Maximum retry attempts for failed LLM calls
            max_llm_rounds: Maximum rounds of inference an LLM can attempt for each test item
            retry_delay: Delay between retries in seconds
            use_mock_llm: Whether to use mock LLM API or not
            api_endpoint: Optional API endpoint for real LLM
            label: Label for test run folder
            
        Returns:
            Dictionary with file paths of generated results
        """
        # Import the appropriate LLM module based on parameter
        global execute_with_retry
        if use_mock_llm:
            print("🤖 Using MOCK LLM")
            from mock_llm import execute_with_retry
        else:
            print("🔗 Using REAL LLM API")
            from real_llm import execute_with_retry
        print("🚀 PICARD Test Runner")
        print("=" * 40)
        
        # Initialize test run
        test_id = self.initialize_test_run(test_definitions_file, label)
        print(f"🆔 Test ID: {test_id}")
        print(f"📁 Test directory: {self.test_dir}")
        print()
        
        # Reset sandbox
        print("🧹 Resetting sandbox...")
        success = self.sandbox_manager.reset_sandbox(sandbox_template, verbose=True)
        if not success:
            raise Exception(f"Failed to reset sandbox with template: {sandbox_template}")
        print()
        
        # Generate precheck entries
        print("📋 Generating precheck entries...")
        precheck_entries = self.precheck_generator.generate_precheck_entries()
        
        stats = self.precheck_generator.get_statistics()
        print(f"✅ Generated {len(precheck_entries)} precheck entries")
        print(f"   📊 Questions: {stats['total_questions']}")
        print(f"   📊 Total samples: {stats['total_samples']}")
        print(f"   📊 Entity pool: {stats['entity_pool_size']} words")
        print()
        
        # Save precheck file
        precheck_file = self.test_dir / "precheck.jsonl"
        self.precheck_generator.save_precheck_entries(precheck_entries, str(precheck_file))
        print(f"💾 Saved precheck file: {precheck_file}")
        print()
        
        # Initialize progressive writing
        print("📁 Setting up progressive result writing...")
        self._initialize_progressive_writers()
        print()
        
        # Execute questions against LLM with progressive writing
        print("🤖 Executing questions against LLM...")
        completed_count = self._execute_questions(precheck_entries, max_retries, max_llm_rounds, retry_delay, api_endpoint)
        
        # Finalize progressive writing and generate summary
        print(f"💾 Results written progressively - {completed_count} items completed")
        print()
        self._finalize_progressive_results()
        
        print("🎉 Test run completed successfully!")
        print(f"📁 Results saved in: {self.test_dir}")
        
        return {
            'test_id': test_id,
            'test_dir': str(self.test_dir),
            'precheck_file': str(precheck_file),
            'responses_file': str(self.test_dir / "responses.jsonl")
        }
    
    def _setup_question_sandbox(self, precheck_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up sandbox files for a question if it has sandbox_setup configuration.
        
        Args:
            precheck_entry: Precheck entry that may contain sandbox setup info
            
        Returns:
            Dictionary with sandbox setup results
        """
        sandbox_result = {
            'has_sandbox_setup': False,
            'files_created': [],
            'content_generated': {},
            'errors': []
        }
        
        # Check if this question has sandbox setup requirements
        if 'sandbox_setup' not in precheck_entry:
            return sandbox_result
        
        sandbox_setup = precheck_entry['sandbox_setup']
        sandbox_result['has_sandbox_setup'] = True
        
        try:
            # Get question context for qs_id substitution
            question_id = precheck_entry['question_id']
            sample_number = precheck_entry['sample_number']
            
            # Process sandbox setup templates with entity values
            setup_fields = {
                'target_file': sandbox_setup.get('target_file', ''),
                'content': str(sandbox_setup.get('content', {})),
                'clutter': str(sandbox_setup.get('clutter', {}))
            }
            
            # Get entity values from precheck entry
            entity_values = {}
            for key, value in precheck_entry.items():
                if key.startswith('entity'):
                    entity_values[key] = value
            
            # Process templates using the template processor
            processed_setup = self.template_processor.process_multiple_fields(
                setup_fields, question_id, sample_number
            )
            
            # Extract processed values
            target_file = processed_setup['target_file']['substituted']
            content_spec = eval(processed_setup['content']['substituted']) if processed_setup['content']['substituted'] != '{}' else {}
            clutter_spec = eval(processed_setup['clutter']['substituted']) if processed_setup['clutter']['substituted'] != '{}' else None
            
            # Create file generator
            generator_type = sandbox_setup.get('type', 'create_files')
            file_generator = FileGeneratorFactory.create_generator(generator_type, str(self.base_dir))
            
            # Generate files
            generation_result = file_generator.generate(
                target_file=target_file,
                content_spec=content_spec,
                clutter_spec=clutter_spec
            )
            
            sandbox_result.update({
                'files_created': generation_result['files_created'],
                'content_generated': generation_result['content_generated'],
                'errors': generation_result.get('errors', [])
            })
            
            # Store sandbox details in precheck entry for reference
            precheck_entry['sandbox_execution'] = {
                'target_file': target_file,
                'files_created': generation_result['files_created'],
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Sandbox setup failed for Q{question_id}S{sample_number}: {e}"
            sandbox_result['errors'].append(error_msg)
            print(f"\n   ⚠️  {error_msg}")
        
        return sandbox_result
    
    def _initialize_progressive_writers(self):
        """Set up files and directories for progressive result writing."""
        # Create and open responses.jsonl for writing
        responses_file_path = self.test_dir / "responses.jsonl"
        self.responses_file = responses_file_path.open('w', encoding='utf-8')
        
        # Create conversations directory
        self.conversations_dir = self.test_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)
    
    def _write_result_immediately(self, response_entry: Dict[str, Any], conversation_entry: Dict[str, Any]):
        """Write individual result immediately after question completion."""
        # Write to responses.jsonl immediately
        try:
            self.responses_file.write(json.dumps(response_entry) + '\n')
            self.responses_file.flush()  # Force write to disk
        except Exception as e:
            print(f"⚠️  Failed to write response to JSONL: {e}")
            # Continue execution - don't fail entire test
        
        # Write individual conversation file immediately
        try:
            question_id = conversation_entry['question_id']
            sample_number = conversation_entry['sample_number']
            filename = f"q{question_id}_s{sample_number}.json"
            conversation_file = self.conversations_dir / filename
            
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_entry, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to write conversation file: {e}")
            # Continue execution - don't fail entire test
    
    def _finalize_progressive_results(self):
        """Close file handles and finalize progressive writing."""
        # Close progressive file handles
        if self.responses_file:
            self.responses_file.close()
            self.responses_file = None
            
        # Generate final test summary (same as current implementation)
        self._generate_test_summary()
    
    def _execute_questions(self, precheck_entries: List[Dict[str, Any]], 
                          max_retries: int, max_llm_rounds: int, retry_delay: float, api_endpoint: str = None) -> int:
        """Execute all questions against the LLM with progressive result writing."""
        total_questions = len(precheck_entries)
        completed_count = 0
            
        for i, entry in enumerate(precheck_entries, 1):
            question_id = entry['question_id']
            sample_number = entry['sample_number']
            question = entry['substituted_question']
            
            print(f"Running: Question {question_id}, Sample {sample_number} ({i}/{total_questions})", end="")
            
            # Check if this entry had sandbox setup (informational only - files already generated during precheck)
            if 'sandbox_generation' in entry:
                sandbox_gen = entry['sandbox_generation']
                if sandbox_gen.get('generation_successful', False):
                    files_count = len(sandbox_gen.get('files_created', []))
                    print(f" [Using {files_count} pre-generated files]", end="")
                else:
                    print(f" [⚠️ Sandbox generation had errors]", end="")
            
            try:
                # Prepare execution parameters
                execution_params = {
                    'max_retries': max_retries,
                    'max_llm_rounds': max_llm_rounds,
                    'delay': retry_delay
                }
        
                
                # Add api_endpoint if provided
                if api_endpoint:
                    execution_params['api_endpoint'] = api_endpoint



                result = execute_with_retry(question, **execution_params)
                
                # Create response entry (for scoring)
                response_entry = {
                    'question_id': question_id,
                    'sample_number': sample_number,
                    'timestamp': result['timestamp'],
                    'response_text': result['response_text'],
                    'execution_successful': result['execution_successful'],
                    'error_message': result.get('error_message'),
                    'model_info': result.get('model_info')
                }
                
                # Create conversation entry (for analysis)
                conversation_entry = {
                    'question_id': question_id,
                    'sample_number': sample_number,
                    'timestamp': result['timestamp'],
                    'initial_question': question,
                    'conversation_history': result.get('conversation_history', []),
                    'statistics': result.get('statistics', {}),
                    'final_response': result['response_text'],
                    'execution_successful': result['execution_successful'],
                    'error_message': result.get('error_message'),
                    'model_info': result.get('model_info')
                }
                
                # Write results immediately instead of storing in memory
                self._write_result_immediately(response_entry, conversation_entry)
                completed_count += 1
                print(" ✅")
                
            except Exception as e:
                print(f" ❌")
                print(f"   💥 Fatal error: {e}")
                print(f"   🛑 Aborting test run (fail-fast strategy)")
                raise Exception(f"Test run aborted due to LLM execution failure: {e}")
        
        print(f"\n🎯 Executed {completed_count} questions successfully")
        return completed_count
    
    def _generate_test_summary(self):
        """Generate and save test run summary."""
        summary = {
            'test_id': self.test_id,
            'timestamp': datetime.now().isoformat(),
            'test_directory': str(self.test_dir),
            'sandbox_status': self.sandbox_manager.get_sandbox_status(),
            'statistics': self.precheck_generator.get_statistics() if self.precheck_generator else {},
            'files_generated': {
                'precheck': 'precheck.jsonl',
                'responses': 'responses.jsonl'
            }
        }
        
        summary_file = self.test_dir / 'test_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Generated test summary: {summary_file}")


def main():
    """Command-line interface for the test runner."""
    parser = argparse.ArgumentParser(
        description='PICARD Framework Benchmark Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python test_runner.py                                    # Run with defaults
  python test_runner.py --template clean_sandbox           # Specify sandbox template
  python test_runner.py --definitions custom_tests.yaml   # Use custom test definitions
  python test_runner.py --retries 5 --delay 3.0          # Custom retry settings
  python test_runner.py --real-llm                        # Use real LLM (localhost:5002)
  python test_runner.py --real-llm --api-endpoint http://example.com/api/chat  # Custom endpoint
'''
    )
    
    parser.add_argument(
        '--definitions', '-d',
        help='Path to test definitions YAML file (default: config/test_definitions.yaml)'
    )
    
    parser.add_argument(
        '--template', '-t',
        default='clean_sandbox',
        help='Sandbox template to use (default: clean_sandbox)'
    )

    parser.add_argument(
        '--max-llm-rounds',
        type=int,
        default=20,
        help='Maximum rounds of inference an LLM can attempt for each test item.'
    )

    parser.add_argument(
        '--retries', '-r',
        type=int,
        default=3,
        help='Maximum retry attempts for failed LLM calls (default: 3)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between retries in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--mock-llm',
        action='store_true',
        help='Use mock LLM API instead of real agentic server endpoint'
    )
    
    parser.add_argument(
        '--api-endpoint',
        help='API endpoint for agentic server (default: http://localhost:5002/api/chat)'
    )
    
    parser.add_argument(
        '--label', '-l',
        default='test',
        help='Label for test run folder (default: test). Creates folder: {label}_{timestamp}'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize and run test
        runner = TestRunner()
        result = runner.run_benchmark(
            test_definitions_file=args.definitions,
            sandbox_template=args.template,
            max_retries=args.retries,
            max_llm_rounds=args.max_llm_rounds,
            retry_delay=args.delay,
            use_mock_llm=args.mock_llm,
            api_endpoint=args.api_endpoint,
            label=args.label
        )
        
        print(f"\n🎊 Success! Test results available at: {result['test_dir']}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Test run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
