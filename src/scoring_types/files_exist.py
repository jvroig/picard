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
            # Handle case where path already includes test_artifacts/
            if file_path_str.startswith('test_artifacts/'):
                relative_path = file_path_str[len('test_artifacts/'):]
                file_path = test_artifacts_dir / relative_path
            else:
                file_path = test_artifacts_dir / file_path_str
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
