"""
Directory Structure Scorer - Check if expected directory structure exists
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class DirectoryStructureScorer(BaseScoringType):
    """Scorer for directory_structure scoring type - check if directory structure matches expected paths."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on directory structure - all expected paths must exist."""
        expected_paths = precheck_entry.get('expected_paths', [])
        
        if not expected_paths:
            return ScoringResult(
                question_id=precheck_entry['question_id'],
                sample_number=precheck_entry['sample_number'],
                scoring_type='directory_structure',
                correct=False,
                error_message="No expected_paths specified in precheck entry"
            )
        
        # Check each expected path
        path_status = {}
        all_exist = True
        missing_paths = []
        wrong_type_paths = []
        
        for expected_path in expected_paths:
            # Smart path resolution - handle both relative and absolute paths
            full_path = self._resolve_file_path(expected_path, test_artifacts_dir)
            exists = full_path.exists()
            
            # Determine expected type based on trailing slash
            expected_is_dir = expected_path.endswith('/')
            
            path_info = {
                'expected_path': expected_path,
                'full_path': str(full_path),
                'exists': exists,
                'expected_type': 'directory' if expected_is_dir else 'file'
            }
            
            if exists:
                actual_is_dir = full_path.is_dir()
                path_info['actual_type'] = 'directory' if actual_is_dir else 'file'
                path_info['type_matches'] = (expected_is_dir == actual_is_dir)
                
                if not path_info['type_matches']:
                    all_exist = False
                    wrong_type_paths.append(expected_path)
            else:
                all_exist = False
                missing_paths.append(expected_path)
                path_info['actual_type'] = None
                path_info['type_matches'] = False
            
            path_status[expected_path] = path_info
        
        details = {
            'expected_paths': expected_paths,
            'path_status': path_status,
            'all_paths_correct': all_exist,
            'missing_paths': missing_paths,
            'wrong_type_paths': wrong_type_paths
        }
        
        error_message = None
        if not all_exist:
            errors = []
            if missing_paths:
                errors.append(f"Missing paths: {missing_paths}")
            if wrong_type_paths:
                errors.append(f"Wrong type paths: {wrong_type_paths}")
            error_message = "; ".join(errors)
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='directory_structure',
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
