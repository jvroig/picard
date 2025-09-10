"""
Scorer module for the PICARD framework
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

class ScoringResult:
    """Represents the result of scoring a single question."""
    
    def __init__(self, question_id: int, sample_number: int, scoring_type: str, 
                 correct: bool, error_message: str = None, details: Dict[str, Any] = None):
        self.question_id = question_id
        self.sample_number = sample_number
        self.scoring_type = scoring_type
        self.correct = correct
        self.error_message = error_message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'question_id': self.question_id,
            'sample_number': self.sample_number,
            'scoring_type': self.scoring_type,
            'correct': self.correct,
            'error_message': self.error_message,
            'details': self.details,
            'timestamp': self.timestamp
        }


class BaseScoringType(ABC):
    """Abstract base class for all scoring type implementations."""
    
    @abstractmethod
    def score(self, precheck_entry: Dict[str, Any], response_entry: Dict[str, Any], 
              test_artifacts_dir: Path) -> ScoringResult:
        """Score a single question based on precheck data and LLM response."""
        pass


class PicardScorer:
    """Main scorer that coordinates all scoring operations."""
    
    def __init__(self, base_dir: str = None):
        """Initialize the scorer."""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = base_dir
        self.results_dir = base_dir / "results"
        
        # Load artifacts directory from config instead of hardcoding
        try:
            import sys
            if str(base_dir) not in sys.path:
                sys.path.insert(0, str(base_dir))
            
            import picard_config
            self.test_artifacts_dir = Path(picard_config.get_artifacts_dir())
        except Exception:
            # Fallback to default if config can't be loaded
            self.test_artifacts_dir = base_dir / "test_artifacts"
            print(f"Warning: Could not load config, using default artifacts dir: {self.test_artifacts_dir}")
        
        self.scoring_types = {}
        self._register_scoring_types()
    
    def _register_scoring_types(self):
        """Register all available scoring type implementations."""
        try:
            from scoring_types.stringmatch import StringMatchScorer
            from scoring_types.readfile_stringmatch import ReadFileStringMatchScorer
            from scoring_types.files_exist import FilesExistScorer
            from scoring_types.directory_structure import DirectoryStructureScorer
            from scoring_types.jsonmatch import JsonMatchScorer
            from scoring_types.readfile_jsonmatch import ReadFileJsonMatchScorer
            from scoring_types.json_targeted_edit import JsonTargetedEditScorer
            
            self.scoring_types = {
                'stringmatch': StringMatchScorer(),
                'readfile_stringmatch': ReadFileStringMatchScorer(),
                'files_exist': FilesExistScorer(),
                'directory_structure': DirectoryStructureScorer(),
                'jsonmatch': JsonMatchScorer(),
                'readfile_jsonmatch': ReadFileJsonMatchScorer(),
                'json_targeted_edit': JsonTargetedEditScorer()
            }
        except ImportError as e:
            print(f"Warning: Could not import scoring types: {e}")
            self.scoring_types = {}
    
    def find_test_directories(self) -> List[Path]:
        """Find all test directories in results folder."""
        if not self.results_dir.exists():
            return []
        
        test_dirs = []
        for item in self.results_dir.iterdir():
            if item.is_dir() and item.name.startswith('test_'):
                test_dirs.append(item)
        
        return sorted(test_dirs, key=lambda x: x.name)
    
    def find_latest_test_directory(self) -> Optional[Path]:
        """Find the most recent test directory."""
        test_dirs = self.find_test_directories()
        return test_dirs[-1] if test_dirs else None
    
    def validate_test_directory(self, test_dir: Path) -> bool:
        """Check if test directory has required files."""
        required_files = ['precheck.jsonl', 'responses.jsonl']
        
        for filename in required_files:
            if not (test_dir / filename).exists():
                return False
        
        return True
    
    def load_precheck_file(self, precheck_file: str) -> List[Dict[str, Any]]:
        """Load precheck entries from JSONL file."""
        precheck_entries = []
        with open(precheck_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    precheck_entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Error parsing precheck line {line_num}: {e}")
        
        return precheck_entries
    
    def load_responses_file(self, responses_file: str) -> List[Dict[str, Any]]:
        """Load response entries from JSONL file."""
        response_entries = []
        with open(responses_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    response_entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Error parsing response line {line_num}: {e}")
        
        return response_entries
    
    def match_entries(self, precheck_entries: List[Dict[str, Any]], 
                     response_entries: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Match precheck entries with corresponding response entries."""
        # Create lookup for responses
        response_lookup = {}
        for response in response_entries:
            key = (response['question_id'], response['sample_number'])
            response_lookup[key] = response
        
        # Match with precheck entries
        matched_pairs = []
        for precheck in precheck_entries:
            key = (precheck['question_id'], precheck['sample_number'])
            if key in response_lookup:
                matched_pairs.append((precheck, response_lookup[key]))
            else:
                print(f"Warning: No response found for Question {key[0]}, Sample {key[1]}")
        
        return matched_pairs
    
    def score_single_entry(self, precheck_entry: Dict[str, Any], 
                          response_entry: Dict[str, Any]) -> ScoringResult:
        """Score a single precheck/response pair."""
        scoring_type = precheck_entry['scoring_type']
        
        if scoring_type not in self.scoring_types:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type=scoring_type,
                correct=False,
                error_message=f"Unknown scoring type: {scoring_type}"
            )
        
        scorer = self.scoring_types[scoring_type]
        try:
            return scorer.score(precheck_entry, response_entry, self.test_artifacts_dir)
        except Exception as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type=scoring_type,
                correct=False,
                error_message=f"Scoring error: {str(e)}"
            )
    
    def score_test_directory(self, test_dir: Path) -> List[ScoringResult]:
        """Score a specific test directory."""
        print(f"🎯 Scoring test directory: {test_dir}")
        print("=" * 50)
        
        # Validate directory
        if not self.validate_test_directory(test_dir):
            raise ValueError(f"Invalid test directory: {test_dir}. Missing required files.")
        
        # Load files
        precheck_file = test_dir / "precheck.jsonl"
        responses_file = test_dir / "responses.jsonl"
        
        print(f"📄 Loading precheck file: {precheck_file}")
        precheck_entries = self.load_precheck_file(str(precheck_file))
        print(f"📝 Loaded {len(precheck_entries)} precheck entries")
        
        print(f"📄 Loading responses file: {responses_file}")
        response_entries = self.load_responses_file(str(responses_file))
        print(f"🤖 Loaded {len(response_entries)} response entries")
        
        # Match entries
        matched_pairs = self.match_entries(precheck_entries, response_entries)
        print(f"🔗 Matched {len(matched_pairs)} precheck/response pairs")
        print()
        
        # Score each pair
        results = []
        correct_count = 0
        
        for precheck, response in matched_pairs:
            result = self.score_single_entry(precheck, response)
            results.append(result)
            
            if result.correct:
                correct_count += 1
                status = "✅ CORRECT"
            else:
                status = "❌ INCORRECT"
            
            print(f"Q{result.question_id}.{result.sample_number} ({result.scoring_type}): {status}")
            if result.error_message:
                print(f"   Error: {result.error_message}")
        
        # Summary
        total_count = len(results)
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        
        print()
        print("📊 SCORING SUMMARY")
        print("=" * 20)
        print(f"Total questions: {total_count}")
        print(f"Correct answers: {correct_count}")
        print(f"Incorrect answers: {total_count - correct_count}")
        print(f"Accuracy: {accuracy:.2f}%")
        
        return results
    
    def score_all_tests(self) -> Dict[str, List[ScoringResult]]:
        """Score all test directories."""
        test_dirs = self.find_test_directories()
        
        if not test_dirs:
            print("❌ No test directories found in results folder")
            return {}
        
        print(f"📊 Found {len(test_dirs)} test directories to score")
        print()
        
        all_results = {}
        
        for test_dir in test_dirs:
            try:
                results = self.score_test_directory(test_dir)
                all_results[test_dir.name] = results
                print(f"✅ Completed scoring for {test_dir.name}")
                print()
            except Exception as e:
                print(f"❌ Failed to score {test_dir.name}: {e}")
                print()
        
        return all_results
    
    def save_results_to_test_directory(self, results: List[ScoringResult], test_dir: Path):
        """Save scoring results to the test directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Summary data
        total_count = len(results)
        correct_count = sum(1 for r in results if r.correct)
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Group by question and scoring type
        by_question = {}
        by_scoring_type = {}
        
        for result in results:
            # By question
            qid = result.question_id
            if qid not in by_question:
                by_question[qid] = {'correct': 0, 'total': 0, 'scoring_type': result.scoring_type}
            by_question[qid]['total'] += 1
            if result.correct:
                by_question[qid]['correct'] += 1
            
            # By scoring type
            stype = result.scoring_type
            if stype not in by_scoring_type:
                by_scoring_type[stype] = {'correct': 0, 'total': 0}
            by_scoring_type[stype]['total'] += 1
            if result.correct:
                by_scoring_type[stype]['correct'] += 1
        
        # Create final output
        output_data = {
            'metadata': {
                'test_id': test_dir.name,
                'timestamp': timestamp,
                'total_questions': total_count,
                'correct_answers': correct_count,
                'accuracy_percentage': round(accuracy, 2)
            },
            'by_question': by_question,
            'by_scoring_type': by_scoring_type,
            'detailed_results': [result.to_dict() for result in results]
        }
        
        scores_file = test_dir / "scores.json"
        with open(scores_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"💾 Saved scores to: {scores_file}")
        return scores_file


def main():
    """Command-line interface for the scorer."""
    parser = argparse.ArgumentParser(
        description='PICARD Framework Scorer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scorer.py                                    # Score latest test
  python scorer.py --test-dir results/test_20250529   # Score specific test
  python scorer.py --all                             # Score all tests
  python scorer.py --list                            # List available tests
'''
    )
    
    parser.add_argument(
        '--test-dir', '-t',
        help='Path to specific test directory to score'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Score all test directories'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available test directories'
    )
    
    args = parser.parse_args()
    
    try:
        scorer = PicardScorer()
        
        if args.list:
            # List available tests
            test_dirs = scorer.find_test_directories()
            if test_dirs:
                print("📁 Available test directories:")
                for test_dir in test_dirs:
                    print(f"   {test_dir.name}")
            else:
                print("❌ No test directories found")
            return
        
        if args.all:
            # Score all tests
            all_results = scorer.score_all_tests()
            
            # Save results for each test
            for test_name, results in all_results.items():
                test_dir = scorer.results_dir / test_name
                scorer.save_results_to_test_directory(results, test_dir)
            
            print(f"🎊 Scored {len(all_results)} test directories!")
            
        elif args.test_dir:
            # Score specific test
            test_dir = Path(args.test_dir)
            if not test_dir.is_absolute():
                test_dir = scorer.base_dir / test_dir
            
            results = scorer.score_test_directory(test_dir)
            scorer.save_results_to_test_directory(results, test_dir)
            
            print(f"🎊 Scoring completed for {test_dir.name}!")
            
        else:
            # Score latest test (default)
            latest_test = scorer.find_latest_test_directory()
            
            if not latest_test:
                print("❌ No test directories found. Run test_runner.py first.")
                return
            
            print(f"🎯 Scoring latest test: {latest_test.name}")
            print()
            
            results = scorer.score_test_directory(latest_test)
            scorer.save_results_to_test_directory(results, latest_test)
            
            print(f"🎊 Scoring completed for {latest_test.name}!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scoring interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Scoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
