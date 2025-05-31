"""
Files Exist Scorer - Check if specified files exist
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class FilesExistScorer(BaseScoringType):
    """Scorer for files_exist scoring type - check if all specified files exist."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on file existence - all files must exist for correct score."""
        files_to_check = precheck_entry.get('files_to_check', [])
        
        if not files_to_check:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='files_exist',
                correct=False,
                error_message="No files_to_check specified in precheck entry"
            )
        
        # Check each file
        file_status = {}
        all_exist = True
        missing_files = []
        
        for file_path_str in files_to_check:
            # Smart path resolution - handle both relative and absolute paths
            file_path = self._resolve_file_path(file_path_str, test_artifacts_dir)
            
            exists = file_path.exists()
            file_status[file_path_str] = {
                'expected_path': str(file_path),
                'exists': exists,
                'is_file': file_path.is_file() if exists else False
            }
            
            if not exists:
                all_exist = False
                missing_files.append(file_path_str)
        
        details = {
            'files_to_check': files_to_check,
            'file_status': file_status,
            'all_files_exist': all_exist,
            'missing_files': missing_files
        }
        
        error_message = None
        if not all_exist:
            error_message = f"Missing files: {missing_files}"
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='files_exist',
            correct=all_exist,
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
