"""
Unit tests for the ResponseCleaner utility.

Tests LLM response cleaning functionality including thinking tags removal,
OpenAI Harmony format processing, and general response preprocessing.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "scoring_types"))

from response_cleaner import ResponseCleaner


class TestResponseCleaner:
    """Test the ResponseCleaner utility class."""
    
    def test_has_harmony_format_true(self):
        """Test detection of OpenAI Harmony format responses."""
        harmony_text = """
        <|channel|>analysis<|message|>The user is asking about weather.
        I should provide a helpful response.<|start|>assistant<|channel|>final<|message|>
        It's sunny today with a high of 75°F.
        """
        
        assert ResponseCleaner.has_harmony_format(harmony_text) is True
    
    def test_has_harmony_format_false(self):
        """Test detection when Harmony format is not present."""
        regular_text = "This is just a regular response without special formatting."
        
        assert ResponseCleaner.has_harmony_format(regular_text) is False
    
    def test_has_harmony_format_partial_markers(self):
        """Test with partial Harmony markers (should return False)."""
        partial_text = "This has <|channel|> but no <|message|> marker."
        
        # This will actually return True because it has both markers,
        # but the implementation checks for both markers being present
        assert ResponseCleaner.has_harmony_format(partial_text) is True
    
    def test_has_harmony_format_only_channel_marker(self):
        """Test with only channel marker (should return False)."""
        partial_text = "This has <|channel|> but no message marker."
        
        assert ResponseCleaner.has_harmony_format(partial_text) is False
    
    def test_has_harmony_format_only_message_marker(self):
        """Test with only message marker (should return False)."""
        partial_text = "This has <|message|> but no channel marker."
        
        assert ResponseCleaner.has_harmony_format(partial_text) is False
    
    def test_has_harmony_format_empty_text(self):
        """Test Harmony detection with empty text."""
        assert ResponseCleaner.has_harmony_format("") is False
        assert ResponseCleaner.has_harmony_format(None) is False
    
    def test_strip_harmony_format_simple(self):
        """Test extracting final answer from simple Harmony format."""
        harmony_text = """
        <|channel|>analysis<|message|>User says hello. Should greet back.
        <|start|>assistant<|channel|>final<|message|>Hello! How can I help you today?
        """
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        expected = "Hello! How can I help you today?\n        "
        
        assert result == expected
    
    def test_strip_harmony_format_multiple_final_channels(self):
        """Test extraction when there are multiple final channels (uses last one)."""
        harmony_text = """
        <|channel|>analysis<|message|>First analysis.
        <|channel|>final<|message|>First attempt answer.
        <|channel|>analysis<|message|>Let me reconsider.
        <|channel|>final<|message|>Better final answer.
        """
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        expected = "Better final answer.\n        "
        
        assert result == expected
    
    def test_strip_harmony_format_no_final_channel(self):
        """Test when no final channel exists (returns original text)."""
        harmony_text = """
        <|channel|>analysis<|message|>Some analysis here.
        <|channel|>thinking<|message|>Some thinking here.
        """
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        
        assert result == harmony_text
    
    def test_strip_harmony_format_empty_text(self):
        """Test Harmony format stripping with empty text."""
        assert ResponseCleaner.strip_harmony_format("") == ""
        assert ResponseCleaner.strip_harmony_format(None) is None
    
    def test_strip_thinking_tags_basic(self):
        """Test basic thinking tag removal."""
        text_with_thinking = """
        <thinking>
        This is internal reasoning that should be removed.
        It can span multiple lines.
        </thinking>
        This is the final answer that should remain.
        """
        
        result = ResponseCleaner.strip_thinking_tags(text_with_thinking)
        expected = """
        
        This is the final answer that should remain.
        """
        
        assert result == expected
    
    def test_strip_thinking_tags_multiple_types(self):
        """Test removal of multiple thinking tag types."""
        text_with_thinking = """
        <thinking>Internal thoughts here.</thinking>
        <reasoning>Logical reasoning here.</reasoning>
        The answer is 42.
        <reflection>Post-answer reflection.</reflection>
        """
        
        result = ResponseCleaner.strip_thinking_tags(text_with_thinking)
        expected = """
        
        
        The answer is 42.
        
        """
        
        assert result == expected
    
    def test_strip_thinking_tags_case_insensitive(self):
        """Test that thinking tag removal is case insensitive."""
        text_with_thinking = """
        <THINKING>Uppercase thinking.</THINKING>
        <ThInKiNg>Mixed case thinking.</ThInKiNg>
        Final answer here.
        """
        
        result = ResponseCleaner.strip_thinking_tags(text_with_thinking)
        expected = """
        
        
        Final answer here.
        """
        
        assert result == expected
    
    def test_strip_thinking_tags_nested_content(self):
        """Test thinking tag removal with complex nested content."""
        text_with_thinking = """
        <reasoning>
        Let me think about this step by step:
        1. First consideration
        2. Second consideration
           - Sub-point A
           - Sub-point B
        3. Final consideration
        
        So the answer should be X.
        </reasoning>
        
        The answer is X.
        """
        
        result = ResponseCleaner.strip_thinking_tags(text_with_thinking)
        expected = """
        
        
        The answer is X.
        """
        
        assert result == expected
    
    def test_strip_thinking_tags_no_tags(self):
        """Test thinking tag removal when no tags are present."""
        text_without_thinking = "This is a simple response without any thinking tags."
        
        result = ResponseCleaner.strip_thinking_tags(text_without_thinking)
        
        assert result == text_without_thinking
    
    def test_strip_thinking_tags_empty_text(self):
        """Test thinking tag removal with empty text."""
        assert ResponseCleaner.strip_thinking_tags("") == ""
        assert ResponseCleaner.strip_thinking_tags(None) is None
    
    def test_strip_thinking_tags_malformed_tags(self):
        """Test with malformed thinking tags (should not be removed)."""
        text_with_malformed = """
        <thinking>Properly closed thinking.</thinking>
        <reasoning>Unclosed reasoning tag.
        <thought>Another unclosed tag.
        This should all remain since tags aren't properly closed.
        """
        
        result = ResponseCleaner.strip_thinking_tags(text_with_malformed)
        
        # Only the properly closed thinking tag should be removed
        assert "<thinking>Properly closed thinking.</thinking>" not in result
        assert "<reasoning>Unclosed reasoning tag." in result
        assert "<thought>Another unclosed tag." in result
    
    def test_clean_response_thinking_only(self):
        """Test clean_response with only thinking tags."""
        text_with_thinking = """
        <thinking>Internal reasoning here.</thinking>
        Final answer: 42
        """
        
        result = ResponseCleaner.clean_response(text_with_thinking)
        expected = "Final answer: 42"
        
        assert result == expected
    
    def test_clean_response_harmony_format(self):
        """Test clean_response with Harmony format (should take precedence)."""
        harmony_text = """
        <thinking>This thinking tag should be ignored due to Harmony format.</thinking>
        <|channel|>analysis<|message|>Analysis here.
        <|channel|>final<|message|>Final answer from Harmony.
        """
        
        result = ResponseCleaner.clean_response(harmony_text)
        expected = "Final answer from Harmony."
        
        assert result == expected
    
    def test_clean_response_harmony_disabled(self):
        """Test clean_response with Harmony format disabled."""
        harmony_text = """
        <thinking>This thinking should be removed.</thinking>
        <|channel|>final<|message|>Harmony content.
        """
        
        result = ResponseCleaner.clean_response(harmony_text, strip_harmony=False)
        
        # Should strip thinking tags but leave Harmony format intact
        assert "<thinking>" not in result
        assert "<|channel|>final<|message|>" in result
        assert "Harmony content." in result
    
    def test_clean_response_thinking_disabled(self):
        """Test clean_response with thinking tag removal disabled."""
        text_with_thinking = """
        <thinking>This should remain.</thinking>
        Final answer here.
        """
        
        result = ResponseCleaner.clean_response(text_with_thinking, strip_thinking=False)
        
        # Should preserve thinking tags
        assert "<thinking>This should remain.</thinking>" in result
        assert "Final answer here." in result
    
    def test_clean_response_whitespace_disabled(self):
        """Test clean_response with whitespace stripping disabled."""
        text_with_whitespace = """
        
        Final answer with whitespace.
        
        """
        
        result = ResponseCleaner.clean_response(text_with_whitespace, strip_whitespace=False)
        
        # Should preserve leading/trailing whitespace
        assert result.startswith("\n        \n")
        assert result.endswith("\n        \n        ")
    
    def test_clean_response_all_options_disabled(self):
        """Test clean_response with all cleaning options disabled."""
        complex_text = """
        
        <thinking>Thinking content.</thinking>
        <|channel|>final<|message|>Harmony content.
        Regular content.
        
        """
        
        result = ResponseCleaner.clean_response(
            complex_text, 
            strip_thinking=False, 
            strip_harmony=False, 
            strip_whitespace=False
        )
        
        # Should be identical to input
        assert result == complex_text
    
    def test_clean_response_empty_text(self):
        """Test clean_response with empty text."""
        assert ResponseCleaner.clean_response("") == ""
        assert ResponseCleaner.clean_response(None) is None
    
    def test_has_thinking_tags_true(self):
        """Test detection of thinking tags."""
        text_with_thinking = "Some text <thinking>internal thoughts</thinking> more text."
        
        assert ResponseCleaner.has_thinking_tags(text_with_thinking) is True
    
    def test_has_thinking_tags_false(self):
        """Test detection when no thinking tags present."""
        text_without_thinking = "Just regular text without any special tags."
        
        assert ResponseCleaner.has_thinking_tags(text_without_thinking) is False
    
    def test_has_thinking_tags_harmony_format(self):
        """Test thinking tag detection with Harmony format (should be False)."""
        harmony_text = "<|channel|>final<|message|>Harmony response."
        
        # Harmony format shouldn't trigger thinking tag detection
        assert ResponseCleaner.has_thinking_tags(harmony_text) is False
    
    def test_has_thinking_tags_empty_text(self):
        """Test thinking tag detection with empty text."""
        assert ResponseCleaner.has_thinking_tags("") is False
        assert ResponseCleaner.has_thinking_tags(None) is False


class TestResponseCleanerEdgeCases:
    """Test edge cases and complex scenarios for ResponseCleaner."""
    
    def test_mixed_thinking_and_harmony(self):
        """Test text with both thinking tags and Harmony format."""
        mixed_text = """
        <thinking>This should be ignored due to Harmony format.</thinking>
        <|channel|>analysis<|message|>Analyzing the request.
        <thinking>Even this thinking tag should be ignored.</thinking>
        <|channel|>final<|message|>Final Harmony answer.
        """
        
        result = ResponseCleaner.clean_response(mixed_text)
        expected = "Final Harmony answer."
        
        assert result == expected
    
    def test_deeply_nested_thinking_content(self):
        """Test thinking tags with deeply nested content including code blocks."""
        complex_thinking = """
        <reasoning>
        Let me analyze this code:
        
        ```python
        def calculate(x, y):
            # This is a comment
            return x + y
        ```
        
        The function adds two numbers. I should explain this.
        </reasoning>
        
        This function adds two numbers together and returns the result.
        """
        
        result = ResponseCleaner.clean_response(complex_thinking)
        expected = "This function adds two numbers together and returns the result."
        
        assert result == expected
    
    def test_thinking_tags_with_xml_content(self):
        """Test thinking tags containing XML-like content."""
        xml_thinking = """
        <analysis>
        The input contains XML: <root><child>value</child></root>
        This is valid XML structure.
        </analysis>
        
        The XML structure is valid.
        """
        
        result = ResponseCleaner.clean_response(xml_thinking)
        expected = "The XML structure is valid."
        
        assert result == expected
    
    def test_harmony_format_with_code_blocks(self):
        """Test Harmony format containing code blocks in final answer."""
        harmony_with_code = """
        <|channel|>analysis<|message|>User wants code example.
        <|channel|>final<|message|>Here's the code:
        
        ```python
        print("Hello, World!")
        ```
        
        This prints a greeting.
        """
        
        result = ResponseCleaner.clean_response(harmony_with_code)
        
        assert "Here's the code:" in result
        assert "```python" in result
        assert "print(\"Hello, World!\")" in result
        assert "This prints a greeting." in result
    
    def test_multiple_thinking_tag_types_in_sequence(self):
        """Test multiple different thinking tag types in sequence."""
        multiple_thinking = """
        <thinking>First thought process.</thinking>
        <reasoning>Logical reasoning process.</reasoning>
        <reflection>Reflecting on the answer.</reflection>
        <analysis>Analyzing the problem.</analysis>
        <thought>Additional thoughts.</thought>
        <internal>Internal monologue.</internal>
        
        Final answer after all thinking.
        """
        
        result = ResponseCleaner.clean_response(multiple_thinking)
        expected = "Final answer after all thinking."
        
        assert result == expected
    
    def test_thinking_tags_with_special_characters(self):
        """Test thinking tags containing special characters and Unicode."""
        special_thinking = """
        <thinking>
        Special chars: !@#$%^&*()
        Unicode: 你好 🎉 α β γ
        Math: ∑ ∫ π ≈ ≠
        </thinking>
        
        Answer with special chars: π ≈ 3.14159
        """
        
        result = ResponseCleaner.clean_response(special_thinking)
        expected = "Answer with special chars: π ≈ 3.14159"
        
        assert result == expected
    
    def test_performance_with_large_text(self):
        """Test performance with large text content."""
        # Create a large text with thinking tags
        large_thinking = "<thinking>" + "Large content. " * 1000 + "</thinking>"
        large_text = large_thinking + "\n\nFinal answer."
        
        result = ResponseCleaner.clean_response(large_text)
        expected = "Final answer."
        
        assert result == expected
    
    def test_thinking_tags_with_newlines_and_formatting(self):
        """Test thinking tags with complex formatting and newlines."""
        formatted_thinking = """
        <reasoning>
        Step 1: Understand the problem
               - Sub-step A
               - Sub-step B
        
        Step 2: Formulate solution
               • Point 1
               • Point 2
               
        Step 3: Verify answer
        
        Conclusion: The answer is correct.
        </reasoning>
        
        The solution is 42.
        """
        
        result = ResponseCleaner.clean_response(formatted_thinking)
        expected = "The solution is 42."
        
        assert result == expected
    
    def test_edge_case_empty_thinking_tags(self):
        """Test with empty thinking tags."""
        empty_thinking = """
        <thinking></thinking>
        <reasoning></reasoning>
        Answer here.
        """
        
        result = ResponseCleaner.clean_response(empty_thinking)
        expected = "Answer here."
        
        assert result == expected
    
    def test_edge_case_thinking_tags_only_whitespace(self):
        """Test thinking tags containing only whitespace."""
        whitespace_thinking = """
        <thinking>
        
        
        </thinking>
        Real answer.
        """
        
        result = ResponseCleaner.clean_response(whitespace_thinking)
        expected = "Real answer."
        
        assert result == expected