"""
Read File String Match Scorer - Read file contents and check exact string match
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class ReadFileStringMatchScorer(BaseScoringType):
    """Scorer for readfile_stringmatch scoring type - read file and compare contents."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on reading file contents and exact string matching."""
        file_to_read = precheck_entry.get('file_to_read', '')
        expected_content = precheck_entry.get('expected_content', '').strip()
        
        if not file_to_read:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_stringmatch',
                correct=False,
                error_message="No file_to_read specified in precheck entry"
            )
        
        # Construct full file path
        # Handle case where file_to_read already includes test_artifacts/
        if file_to_read.startswith('test_artifacts/'):
            # Remove the test_artifacts/ prefix since we're already in test_artifacts_dir
            relative_path = file_to_read[len('test_artifacts/'):]
            file_path = test_artifacts_dir / relative_path
        else:
            file_path = test_artifacts_dir / file_to_read
        
        # Check if file exists
        if not file_path.exists():
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_stringmatch',
                correct=False,
                error_message=f"File does not exist: {file_path}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'file_exists': False
                }
            )
        
        # Read file contents
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                actual_content = f.read().strip()
        except Exception as e:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='readfile_stringmatch',
                correct=False,
                error_message=f"Error reading file {file_path}: {str(e)}",
                details={
                    'expected_file': str(file_path),
                    'expected_content': expected_content,
                    'file_exists': True,
                    'read_error': str(e)
                }
            )
        
        # Compare contents
        correct = expected_content == actual_content
        
        details = {
            'expected_file': str(file_path),
            'expected_content': expected_content,
            'actual_content': actual_content,
            'file_exists': True,
            'content_match': correct
        }
        
        error_message = None
        if not correct:
            error_message = f"File content mismatch. Expected '{expected_content}', got '{actual_content}'"
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='readfile_stringmatch',
            correct=correct,
            error_message=error_message,
            details=details
        )
