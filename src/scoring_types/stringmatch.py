"""
String Match Scorer - Traditional Q&A exact string matching
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from scorer import BaseScoringType, ScoringResult
from response_cleaner import ResponseCleaner


class StringMatchScorer(BaseScoringType):
    """Scorer for stringmatch scoring type - exact string comparison."""
    
    def score(self, precheck_entry, response_entry, test_artifacts_dir):
        """Score based on exact string matching (whitespace trimmed, thinking tags removed)."""
        expected_response = precheck_entry.get('expected_response', '').strip()
        raw_actual_response = response_entry.get('response_text', '')
        
        # Clean the response using shared utility
        cleaned_actual_response = ResponseCleaner.clean_response(raw_actual_response)
        
        correct = expected_response == cleaned_actual_response
        
        details = {
            'expected': expected_response,
            'actual_raw': raw_actual_response,
            'actual_cleaned': cleaned_actual_response,
            'comparison_method': 'exact_match_trimmed_cleaned',
            'thinking_tags_found': ResponseCleaner.has_thinking_tags(raw_actual_response),
            'harmony_format_found': ResponseCleaner.has_harmony_format(raw_actual_response)
        }
        
        error_message = None
        if not correct:
            error_message = f"Expected '{expected_response}', got '{cleaned_actual_response}'"
        
        return ScoringResult(
            question_id=precheck_entry['question_id'],
            sample_number=precheck_entry['sample_number'],
            scoring_type='stringmatch',
            correct=correct,
            error_message=error_message,
            details=details
        )
