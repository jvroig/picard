"""
Unit tests for the StringMatch scoring type.

Tests exact string matching functionality including response cleaning,
thinking tag removal, and Harmony format processing.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "scoring_types"))

from scoring_types.stringmatch import StringMatchScorer
from scorer import ScoringResult


class TestStringMatchScorer:
    """Test the StringMatchScorer implementation."""
    
    @pytest.fixture
    def scorer(self):
        """Create StringMatchScorer instance for testing."""
        return StringMatchScorer()
    
    @pytest.fixture
    def test_artifacts_dir(self, tmp_path):
        """Create temporary test artifacts directory."""
        return tmp_path / "test_artifacts"
    
    def test_exact_match_success(self, scorer, test_artifacts_dir):
        """Test successful exact string match."""
        precheck_entry = {
            'question_id': 101,
            'sample_number': 1,
            'expected_response': 'Hello World'
        }
        
        response_entry = {
            'question_id': 101,
            'sample_number': 1,
            'response_text': 'Hello World'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert isinstance(result, ScoringResult)
        assert result.question_id == 101
        assert result.sample_number == 1
        assert result.scoring_type == 'stringmatch'
        assert result.correct is True
        assert result.error_message is None
        
        # Check details
        assert result.details['expected'] == 'Hello World'
        assert result.details['actual_cleaned'] == 'Hello World'
        assert result.details['comparison_method'] == 'exact_match_trimmed_cleaned'
    
    def test_exact_match_failure(self, scorer, test_artifacts_dir):
        """Test failed exact string match."""
        precheck_entry = {
            'question_id': 102,
            'sample_number': 1,
            'expected_response': 'Expected Answer'
        }
        
        response_entry = {
            'question_id': 102,
            'sample_number': 1,
            'response_text': 'Different Answer'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "Expected 'Expected Answer', got 'Different Answer'"
        
        # Check details
        assert result.details['expected'] == 'Expected Answer'
        assert result.details['actual_cleaned'] == 'Different Answer'
        assert result.details['actual_raw'] == 'Different Answer'
    
    def test_whitespace_trimming(self, scorer, test_artifacts_dir):
        """Test that whitespace is properly trimmed for matching."""
        precheck_entry = {
            'question_id': 103,
            'sample_number': 1,
            'expected_response': '  Trimmed Answer  '
        }
        
        response_entry = {
            'question_id': 103,
            'sample_number': 1,
            'response_text': '   Trimmed Answer   '
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['expected'] == 'Trimmed Answer'  # Should be trimmed
        assert result.details['actual_cleaned'] == 'Trimmed Answer'  # Should be trimmed
    
    def test_thinking_tags_removal(self, scorer, test_artifacts_dir):
        """Test that thinking tags are properly removed from responses."""
        precheck_entry = {
            'question_id': 104,
            'sample_number': 1,
            'expected_response': 'The answer is 42'
        }
        
        response_entry = {
            'question_id': 104,
            'sample_number': 1,
            'response_text': '''
            <thinking>
            Let me think about this problem.
            The user is asking for a specific answer.
            I should respond with 42.
            </thinking>
            The answer is 42
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == 'The answer is 42'
        assert '<thinking>' not in result.details['actual_cleaned']
    
    def test_harmony_format_processing(self, scorer, test_artifacts_dir):
        """Test that OpenAI Harmony format is properly processed."""
        precheck_entry = {
            'question_id': 105,
            'sample_number': 1,
            'expected_response': 'Final answer here'
        }
        
        response_entry = {
            'question_id': 105,
            'sample_number': 1,
            'response_text': '''
            <|channel|>analysis<|message|>Let me analyze this question.
            The user wants a specific response.
            <|channel|>final<|message|>Final answer here
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['harmony_format_found'] is True
        assert result.details['actual_cleaned'] == 'Final answer here'
    
    def test_multiple_thinking_tag_types(self, scorer, test_artifacts_dir):
        """Test removal of various thinking tag types."""
        precheck_entry = {
            'question_id': 106,
            'sample_number': 1,
            'expected_response': 'Clean answer'
        }
        
        response_entry = {
            'question_id': 106,
            'sample_number': 1,
            'response_text': '''
            <thinking>First thought process.</thinking>
            <reasoning>Logical reasoning here.</reasoning>
            Clean answer
            <reflection>Post-answer reflection.</reflection>
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == 'Clean answer'
    
    def test_case_sensitive_matching(self, scorer, test_artifacts_dir):
        """Test that string matching is case-sensitive."""
        precheck_entry = {
            'question_id': 107,
            'sample_number': 1,
            'expected_response': 'Hello World'
        }
        
        response_entry = {
            'question_id': 107,
            'sample_number': 1,
            'response_text': 'hello world'  # Different case
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.error_message == "Expected 'Hello World', got 'hello world'"
    
    def test_empty_expected_response(self, scorer, test_artifacts_dir):
        """Test handling of empty expected response."""
        precheck_entry = {
            'question_id': 108,
            'sample_number': 1,
            'expected_response': ''
        }
        
        response_entry = {
            'question_id': 108,
            'sample_number': 1,
            'response_text': ''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['expected'] == ''
        assert result.details['actual_cleaned'] == ''
    
    def test_missing_expected_response_field(self, scorer, test_artifacts_dir):
        """Test handling when expected_response field is missing."""
        precheck_entry = {
            'question_id': 109,
            'sample_number': 1
            # missing expected_response field
        }
        
        response_entry = {
            'question_id': 109,
            'sample_number': 1,
            'response_text': 'Some response'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.details['expected'] == ''  # Should default to empty string
        assert result.details['actual_cleaned'] == 'Some response'
    
    def test_missing_response_text_field(self, scorer, test_artifacts_dir):
        """Test handling when response_text field is missing."""
        precheck_entry = {
            'question_id': 110,
            'sample_number': 1,
            'expected_response': 'Expected'
        }
        
        response_entry = {
            'question_id': 110,
            'sample_number': 1
            # missing response_text field
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is False
        assert result.details['expected'] == 'Expected'
        assert result.details['actual_raw'] == ''  # Should default to empty string
        assert result.details['actual_cleaned'] == ''
    
    def test_complex_multiline_content(self, scorer, test_artifacts_dir):
        """Test matching of complex multiline content."""
        expected_multiline = """Line 1
Line 2
Line 3"""
        
        response_multiline = """<thinking>Processing multiline response.</thinking>
Line 1
Line 2
Line 3"""
        
        precheck_entry = {
            'question_id': 111,
            'sample_number': 1,
            'expected_response': expected_multiline
        }
        
        response_entry = {
            'question_id': 111,
            'sample_number': 1,
            'response_text': response_multiline
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == expected_multiline
    
    def test_unicode_and_special_characters(self, scorer, test_artifacts_dir):
        """Test matching with Unicode and special characters."""
        unicode_text = "Special chars: α β γ 🎉 你好"
        
        precheck_entry = {
            'question_id': 112,
            'sample_number': 1,
            'expected_response': unicode_text
        }
        
        response_entry = {
            'question_id': 112,
            'sample_number': 1,
            'response_text': unicode_text
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['actual_cleaned'] == unicode_text
    
    def test_thinking_tags_without_content_change(self, scorer, test_artifacts_dir):
        """Test that thinking tag detection works even when content doesn't change."""
        precheck_entry = {
            'question_id': 113,
            'sample_number': 1,
            'expected_response': 'Answer'
        }
        
        response_entry = {
            'question_id': 113,
            'sample_number': 1,
            'response_text': 'Answer'  # No thinking tags
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is False
        assert result.details['harmony_format_found'] is False
    
    def test_harmony_format_detection(self, scorer, test_artifacts_dir):
        """Test proper detection of Harmony format vs regular responses."""
        # Test with Harmony format
        precheck_entry = {
            'question_id': 114,
            'sample_number': 1,
            'expected_response': 'Answer'
        }
        
        harmony_response = {
            'question_id': 114,
            'sample_number': 1,
            'response_text': '<|channel|>final<|message|>Answer'
        }
        
        result = scorer.score(precheck_entry, harmony_response, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['harmony_format_found'] is True
        assert result.details['thinking_tags_found'] is False  # Should be False for Harmony
    
    def test_edge_case_exact_match_with_only_whitespace(self, scorer, test_artifacts_dir):
        """Test edge case where response is only whitespace."""
        precheck_entry = {
            'question_id': 115,
            'sample_number': 1,
            'expected_response': ''
        }
        
        response_entry = {
            'question_id': 115,
            'sample_number': 1,
            'response_text': '   \n\t  '  # Only whitespace
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True  # Whitespace should be trimmed to empty string
        assert result.details['actual_cleaned'] == ''
    
    def test_details_structure_completeness(self, scorer, test_artifacts_dir):
        """Test that all expected details are included in the result."""
        precheck_entry = {
            'question_id': 116,
            'sample_number': 1,
            'expected_response': 'Test'
        }
        
        response_entry = {
            'question_id': 116,
            'sample_number': 1,
            'response_text': '<thinking>Thoughts</thinking>Test'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        # Verify all expected details keys are present
        expected_keys = [
            'expected',
            'actual_raw', 
            'actual_cleaned',
            'comparison_method',
            'thinking_tags_found',
            'harmony_format_found'
        ]
        
        for key in expected_keys:
            assert key in result.details, f"Missing details key: {key}"
        
        assert result.details['comparison_method'] == 'exact_match_trimmed_cleaned'


class TestStringMatchScorerIntegration:
    """Integration tests for StringMatchScorer with various response formats."""
    
    @pytest.fixture
    def scorer(self):
        """Create StringMatchScorer instance for testing."""
        return StringMatchScorer()
    
    @pytest.fixture
    def test_artifacts_dir(self, tmp_path):
        """Create temporary test artifacts directory."""
        return tmp_path / "test_artifacts"
    
    def test_real_world_chatbot_response(self, scorer, test_artifacts_dir):
        """Test with realistic chatbot response including thinking tags."""
        precheck_entry = {
            'question_id': 201,
            'sample_number': 1,
            'expected_response': 'The capital of France is Paris.'
        }
        
        response_entry = {
            'question_id': 201,
            'sample_number': 1,
            'response_text': '''
            <thinking>
            The user is asking about the capital of France. This is a straightforward 
            geography question. The capital of France is Paris, which is well-known.
            I should provide a clear, direct answer.
            </thinking>
            
            The capital of France is Paris.
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == 'The capital of France is Paris.'
    
    def test_real_world_harmony_response(self, scorer, test_artifacts_dir):
        """Test with realistic OpenAI Harmony format response."""
        precheck_entry = {
            'question_id': 202,
            'sample_number': 1,
            'expected_response': 'I can help you with that task.'
        }
        
        response_entry = {
            'question_id': 202,
            'sample_number': 1,
            'response_text': '''
            <|channel|>analysis<|message|>The user is asking for help with a task.
            This seems like a reasonable request that I can assist with.
            I should provide a helpful and positive response.
            <|start|>assistant<|channel|>final<|message|>I can help you with that task.
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['harmony_format_found'] is True
        assert result.details['actual_cleaned'] == 'I can help you with that task.'
    
    def test_mixed_format_edge_case(self, scorer, test_artifacts_dir):
        """Test edge case with both thinking tags and Harmony markers (Harmony should win)."""
        precheck_entry = {
            'question_id': 203,
            'sample_number': 1,
            'expected_response': 'Harmony wins'
        }
        
        response_entry = {
            'question_id': 203,
            'sample_number': 1,
            'response_text': '''
            <thinking>This thinking should be ignored due to Harmony format.</thinking>
            <|channel|>analysis<|message|>Analyzing the request.
            <thinking>Even this thinking should be ignored.</thinking>
            <|channel|>final<|message|>Harmony wins
            '''
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['harmony_format_found'] is True
        # Note: thinking_tags_found might still be True as it checks the raw text
        assert result.details['actual_cleaned'] == 'Harmony wins'
    
    def test_performance_with_large_response(self, scorer, test_artifacts_dir):
        """Test performance with large response text."""
        # Create large thinking content
        large_thinking = "<thinking>" + "Large content. " * 1000 + "</thinking>"
        large_response_text = large_thinking + "\nSimple answer."
        
        precheck_entry = {
            'question_id': 204,
            'sample_number': 1,
            'expected_response': 'Simple answer.'
        }
        
        response_entry = {
            'question_id': 204,
            'sample_number': 1,
            'response_text': large_response_text
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == 'Simple answer.'
    
    def test_code_output_matching(self, scorer, test_artifacts_dir):
        """Test matching of code output responses."""
        code_output = '''```python
def hello():
    print("Hello, World!")

hello()
```

Output: Hello, World!'''
        
        precheck_entry = {
            'question_id': 205,
            'sample_number': 1,
            'expected_response': code_output
        }
        
        response_entry = {
            'question_id': 205,
            'sample_number': 1,
            'response_text': f'<reasoning>User wants code example.</reasoning>\n{code_output}'
        }
        
        result = scorer.score(precheck_entry, response_entry, test_artifacts_dir)
        
        assert result.correct is True
        assert result.details['thinking_tags_found'] is True
        assert result.details['actual_cleaned'] == code_output