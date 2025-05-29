"""
QwenSense Test Runner - Execute LLM benchmark tests

Main command-line tool for running benchmark tests against LLMs.
Generates precheck files, executes questions, collects responses, and organizes results.
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src and scripts to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent / "scripts"))

from precheck_generator import PrecheckGenerator
from mock_llm import execute_with_retry
from sandbox_manager import SandboxManager


class TestRunner:
    """Main test runner for QwenSense benchmarks."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize test runner.
        
        Args:
            base_dir: Base directory of QwenSense project (optional)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.config_dir = self.base_dir / "config"
        
        # Initialize components
        self.sandbox_manager = SandboxManager(base_dir)
        self.precheck_generator = None
        
        # Test run info
        self.test_id = None
        self.test_dir = None
    
    def initialize_test_run(self, test_definitions_file: str = None) -> str:
        """
        Initialize a new test run.
        
        Args:
            test_definitions_file: Path to test definitions YAML file
            
        Returns:
            Test ID for this run
        """
        # Generate test ID
        self.test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create test directory
        self.test_dir = self.results_dir / self.test_id
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize precheck generator
        if test_definitions_file is None:
            test_definitions_file = self.config_dir / "test_definitions.yaml"
        
        self.precheck_generator = PrecheckGenerator(
            test_definitions_file=str(test_definitions_file)
        )
        
        return self.test_id
    
    def run_benchmark(self, test_definitions_file: str = None, 
                     sandbox_template: str = "clean_sandbox",
                     max_retries: int = 3, retry_delay: float = 2.0) -> Dict[str, str]:
        """
        Run complete benchmark test.
        
        Args:
            test_definitions_file: Path to test definitions YAML file
            sandbox_template: Sandbox template to use
            max_retries: Maximum retry attempts for failed LLM calls
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary with file paths of generated results
        """
        print("🚀 QwenSense Test Runner")
        print("=" * 40)
        
        # Initialize test run
        test_id = self.initialize_test_run(test_definitions_file)
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
        
        # Execute questions against LLM
        print("🤖 Executing questions against LLM...")
        responses = self._execute_questions(precheck_entries, max_retries, retry_delay)
        
        # Save responses file
        responses_file = self.test_dir / "responses.jsonl"
        self._save_responses(responses, str(responses_file))
        print(f"💾 Saved responses file: {responses_file}")
        print()
        
        # Generate summary
        self._generate_test_summary()
        
        print("🎉 Test run completed successfully!")
        print(f"📁 Results saved in: {self.test_dir}")
        
        return {
            'test_id': test_id,
            'test_dir': str(self.test_dir),
            'precheck_file': str(precheck_file),
            'responses_file': str(responses_file)
        }
    
    def _execute_questions(self, precheck_entries: List[Dict[str, Any]], 
                          max_retries: int, retry_delay: float) -> List[Dict[str, Any]]:
        """Execute all questions against the LLM."""
        responses = []
        total_questions = len(precheck_entries)
        
        for i, entry in enumerate(precheck_entries, 1):
            question_id = entry['question_id']
            sample_number = entry['sample_number']
            question = entry['substituted_question']
            
            print(f"Running: Question {question_id}, Sample {sample_number} ({i}/{total_questions})", end="")
            
            try:
                # Execute with retry logic
                result = execute_with_retry(
                    question, 
                    max_retries=max_retries, 
                    delay=retry_delay
                )
                
                # Create response entry
                response_entry = {
                    'question_id': question_id,
                    'sample_number': sample_number,
                    'timestamp': result['timestamp'],
                    'response_text': result['response_text'],
                    'execution_successful': result['execution_successful'],
                    'error_message': result.get('error_message'),
                    'model_info': result.get('model_info')
                }
                
                responses.append(response_entry)
                print(" ✅")
                
            except Exception as e:
                print(f" ❌")
                print(f"   💥 Fatal error: {e}")
                print(f"   🛑 Aborting test run (fail-fast strategy)")
                raise Exception(f"Test run aborted due to LLM execution failure: {e}")
        
        print(f"\n🎯 Executed {len(responses)} questions successfully")
        return responses
    
    def _save_responses(self, responses: List[Dict[str, Any]], output_file: str):
        """Save responses to JSONL file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            for response in responses:
                f.write(json.dumps(response) + '\n')
    
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
        description='QwenSense LLM Benchmark Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python test_runner.py                                    # Run with defaults
  python test_runner.py --template clean_sandbox           # Specify sandbox template
  python test_runner.py --definitions custom_tests.yaml   # Use custom test definitions
  python test_runner.py --retries 5 --delay 3.0          # Custom retry settings
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
    
    args = parser.parse_args()
    
    try:
        # Initialize and run test
        runner = TestRunner()
        result = runner.run_benchmark(
            test_definitions_file=args.definitions,
            sandbox_template=args.template,
            max_retries=args.retries,
            retry_delay=args.delay
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
