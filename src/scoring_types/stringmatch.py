"""
String Match Scorer - Traditional Q&A exact string matching
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scorer import BaseScoringType, ScoringResult


class StringMatchScorer(BaseScoringType):
    """Scorer for stringmatch scoring type - exact string comparison."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on exact string matching (whitespace trimmed)."""
        expected_response = precheck_entry.get('expected_response', '').strip()
        actual_response = response_entry.get('response_text', '').strip()
        
        correct = expected_response == actual_response
        
        details = {
            'expected': expected_response,
            'actual': actual_response,
            'comparison_method': 'exact_match_trimmed'
        }
        
        error_message = None
        if not correct:
            error_message = f"Expected '{expected_response}', got '{actual_response}'"
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='stringmatch',
            correct=correct,
            error_message=error_message,
            details=details
        )
