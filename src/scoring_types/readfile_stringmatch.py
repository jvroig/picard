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
        
        # Smart path resolution - handle both relative and absolute paths
        file_path = self._resolve_file_path(file_to_read, test_artifacts_dir)
        
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
    
    def _resolve_file_path(self, file_path_str: str, test_artifacts_dir: Path) -> Path:
        """
        Resolve file path intelligently - handle both relative and absolute paths.
        
        Args:
            file_path_str: File path from precheck entry (may be relative or absolute)
            test_artifacts_dir: Test artifacts directory from scorer
            
        Returns:
            Resolved Path object
        """
        file_path = Path(file_path_str)
        
        # If it's already an absolute path, use it directly
        if file_path.is_absolute():
            return file_path
        
        # If it starts with test_artifacts/, remove that prefix and use test_artifacts_dir
        if file_path_str.startswith('test_artifacts/'):
            relative_path = file_path_str[len('test_artifacts/'):]
            return test_artifacts_dir / relative_path
        
        # Otherwise, treat it as relative to test_artifacts_dir
        return test_artifacts_dir / file_path_str
