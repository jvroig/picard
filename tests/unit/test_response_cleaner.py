"""
Unit tests for ResponseCleaner utility.

Tests the response cleaning functionality that strips thinking/reasoning content
from LLM responses before scoring.
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "scoring_types"))

from response_cleaner import ResponseCleaner


class TestThinkingTagStripping:
    """Test removal of thinking tags and their content."""
    
    def test_basic_think_tag_removal(self):
        """Test basic <think> tag removal - the failing case mentioned by user."""
        input_text = "<think> Hello I am thinking </think> Hello user!"
        expected_output = "Hello user!"
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_thinking_tag_removal(self):
        """Test <thinking> tag removal."""
        input_text = "<thinking>Let me analyze this...</thinking>The answer is 42."
        expected_output = "The answer is 42."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_reasoning_tag_removal(self):
        """Test <reasoning> tag removal."""
        input_text = "First, <reasoning>This requires careful consideration</reasoning> I conclude that X is true."
        expected_output = "First,  I conclude that X is true."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == "First, I conclude that X is true."
    
    def test_thought_tag_removal(self):
        """Test <thought> tag removal."""
        input_text = "<thought>Hmm, interesting question</thought>My response is here."
        expected_output = "My response is here."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_internal_tag_removal(self):
        """Test <internal> tag removal."""
        input_text = "Before answering: <internal>Need to be careful here</internal> The solution is X."
        expected_output = "Before answering:  The solution is X."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == "Before answering: The solution is X."
    
    def test_reflection_tag_removal(self):
        """Test <reflection> tag removal."""
        input_text = "<reflection>Let me double-check this logic</reflection>Yes, that's correct."
        expected_output = "Yes, that's correct."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_analysis_tag_removal(self):
        """Test <analysis> tag removal."""  
        input_text = "<analysis>Breaking down the problem step by step</analysis>The final answer is Y."
        expected_output = "The final answer is Y."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output


class TestMultilineContent:
    """Test thinking tag removal with multiline content."""
    
    def test_multiline_thinking_tag(self):
        """Test removal of thinking tags with newlines."""
        input_text = """<thinking>
This is a complex problem.
Let me think through it step by step:
1. First consideration
2. Second consideration  
3. Final conclusion
</thinking>My final answer is here."""
        
        expected_output = "My final answer is here."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_multiline_think_tag(self):
        """Test removal of <think> tags with newlines."""
        input_text = """<think>
Line 1 of thinking
Line 2 of thinking
More complex reasoning here
</think>
This is my actual response."""
        
        expected_output = "This is my actual response."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output


class TestCaseInsensitive:
    """Test case-insensitive tag matching."""
    
    def test_uppercase_think_tag(self):
        """Test that uppercase <THINK> tags are removed."""
        input_text = "<THINK>Internal reasoning</THINK>Final response."
        expected_output = "Final response."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output
    
    def test_mixed_case_thinking_tag(self):
        """Test that mixed case <ThInKiNg> tags are removed."""
        input_text = "<ThInKiNg>Mixed case reasoning</ThInKiNg>Response here."
        expected_output = "Response here."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == expected_output


class TestMultipleTags:
    """Test handling of multiple thinking tags."""
    
    def test_multiple_think_tags(self):
        """Test removal of multiple <think> tags."""
        input_text = "<think>First thought</think>Some text<think>Second thought</think>Final answer."
        expected_output = "Some textFinal answer."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == "Some text Final answer."
    
    def test_mixed_thinking_tags(self):
        """Test removal of different types of thinking tags."""
        input_text = "<think>Thinking</think>Text<reasoning>Reasoning</reasoning>More text<internal>Internal</internal>Final."
        expected_output = "TextMore textFinal."
        
        result = ResponseCleaner.strip_thinking_tags(input_text)
        assert result.strip() == "Text More text Final."


class TestHarmonyFormat:
    """Test OpenAI Harmony format processing."""
    
    def test_harmony_format_detection(self):
        """Test detection of Harmony format markers."""
        harmony_text = "<|channel|>analysis<|message|>Thinking...<|channel|>final<|message|>Answer here"
        non_harmony_text = "<thinking>Regular thinking</thinking>Answer"
        
        assert ResponseCleaner.has_harmony_format(harmony_text) == True
        assert ResponseCleaner.has_harmony_format(non_harmony_text) == False
    
    def test_harmony_format_extraction(self):
        """Test extraction of final answer from Harmony format."""
        harmony_text = "<|channel|>analysis<|message|>Let me analyze this problem carefully.<|channel|>final<|message|>The answer is 42."
        expected_output = "The answer is 42."
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        assert result == expected_output
    
    def test_harmony_format_multiple_final_channels(self):
        """Test handling of multiple final channels (should use last one)."""
        harmony_text = "<|channel|>analysis<|message|>Analysis<|channel|>final<|message|>Wrong answer<|channel|>final<|message|>Correct answer"
        expected_output = "Correct answer"
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        assert result == expected_output
    
    def test_harmony_format_no_final_channel(self):
        """Test Harmony format without final channel (should return original)."""
        harmony_text = "<|channel|>analysis<|message|>Only analysis here"
        
        result = ResponseCleaner.strip_harmony_format(harmony_text)
        assert result == harmony_text


class TestCleanResponse:
    """Test the main clean_response method with auto-detection."""
    
    def test_auto_detect_thinking_tags(self):
        """Test that clean_response automatically processes thinking tags."""
        input_text = "<think>Internal thoughts</think>Final response here."
        expected_output = "Final response here."
        
        result = ResponseCleaner.clean_response(input_text)
        assert result == expected_output
    
    def test_auto_detect_harmony_format(self):
        """Test that clean_response automatically processes Harmony format."""
        input_text = "<|channel|>analysis<|message|>Analysis here<|channel|>final<|message|>Final answer"
        expected_output = "Final answer"
        
        result = ResponseCleaner.clean_response(input_text)
        assert result == expected_output
    
    def test_harmony_takes_precedence(self):
        """Test that Harmony format processing takes precedence over thinking tags."""
        # This text has both formats - Harmony should be processed first
        input_text = "<thinking>Should not be processed</thinking><|channel|>analysis<|message|>Analysis<|channel|>final<|message|>Harmony answer"
        expected_output = "Harmony answer"
        
        result = ResponseCleaner.clean_response(input_text)  
        assert result == expected_output
    
    def test_clean_response_with_options(self):
        """Test clean_response with different option combinations."""
        input_text = "  <think>Thinking</think>  Answer here  "
        
        # Default behavior
        result1 = ResponseCleaner.clean_response(input_text)
        assert result1 == "Answer here"
        
        # Don't strip thinking
        result2 = ResponseCleaner.clean_response(input_text, strip_thinking=False)
        assert result2 == "<think>Thinking</think>  Answer here"
        
        # Don't strip whitespace  
        result3 = ResponseCleaner.clean_response(input_text, strip_whitespace=False)
        assert result3 == "  Answer here  "


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_string(self):
        """Test handling of empty strings."""
        assert ResponseCleaner.strip_thinking_tags("") == ""
        assert ResponseCleaner.strip_harmony_format("") == ""
        assert ResponseCleaner.clean_response("") == ""
    
    def test_none_input(self):
        """Test handling of None input."""
        assert ResponseCleaner.strip_thinking_tags(None) == None
        assert ResponseCleaner.strip_harmony_format(None) == None  
        assert ResponseCleaner.clean_response(None) == None
    
    def test_no_tags_present(self):
        """Test text with no thinking tags or Harmony format."""
        plain_text = "This is just a plain response with no special formatting."
        
        assert ResponseCleaner.strip_thinking_tags(plain_text) == plain_text
        assert ResponseCleaner.strip_harmony_format(plain_text) == plain_text
        assert ResponseCleaner.clean_response(plain_text) == plain_text
    
    def test_malformed_tags(self):
        """Test handling of malformed or incomplete tags."""
        malformed1 = "<think>Unclosed thinking tag"
        malformed2 = "Unopened thinking tag</think>"
        
        # Should not crash and should return input (unclosed tags not matched)
        result1 = ResponseCleaner.strip_thinking_tags(malformed1)
        assert result1 == malformed1
        
        result2 = ResponseCleaner.strip_thinking_tags(malformed2) 
        assert result2 == malformed2


class TestUtilityMethods:
    """Test utility methods for detection."""
    
    def test_has_thinking_tags(self):
        """Test detection of thinking tags."""
        assert ResponseCleaner.has_thinking_tags("<think>content</think>") == True
        assert ResponseCleaner.has_thinking_tags("<thinking>content</thinking>") == True
        assert ResponseCleaner.has_thinking_tags("No tags here") == False
        assert ResponseCleaner.has_thinking_tags("") == False
        assert ResponseCleaner.has_thinking_tags(None) == False
    
    def test_has_harmony_format(self):
        """Test detection of Harmony format."""
        harmony_text = "<|channel|>test<|message|>content"
        non_harmony_text = "Regular text"
        
        assert ResponseCleaner.has_harmony_format(harmony_text) == True
        assert ResponseCleaner.has_harmony_format(non_harmony_text) == False
        assert ResponseCleaner.has_harmony_format("") == False
        assert ResponseCleaner.has_harmony_format(None) == False


class TestRealWorldExamples:
    """Test with realistic LLM response examples."""
    
    def test_claude_style_thinking(self):
        """Test Claude-style thinking tag usage."""
        claude_response = """<thinking>
The user is asking about response cleaning. I need to:
1. Explain what response cleaning does
2. Give a clear example
3. Be helpful and accurate

Let me structure my response clearly.
</thinking>

Response cleaning is a process that removes internal reasoning from LLM outputs. For example, if an LLM generates thinking tags around its reasoning process, those should be stripped before presenting the final answer to users."""
        
        expected = "Response cleaning is a process that removes internal reasoning from LLM outputs. For example, if an LLM generates thinking tags around its reasoning process, those should be stripped before presenting the final answer to users."
        
        result = ResponseCleaner.clean_response(claude_response)
        assert result == expected
    
    def test_mixed_content_with_thinking(self):
        """Test realistic mixed content with thinking interspersed."""
        mixed_response = """I'll help you with that problem. <think>Let me make sure I understand the requirements correctly...</think>

Based on your requirements, here's my recommendation:

<thinking>
Actually, let me reconsider this approach. The user might benefit from a different solution.
</thinking>

The best approach would be to use method X because it provides better performance and maintainability."""
        
        expected = """I'll help you with that problem. 

Based on your requirements, here's my recommendation:



The best approach would be to use method X because it provides better performance and maintainability."""
        
        result = ResponseCleaner.clean_response(mixed_response)
        # Clean up extra whitespace for comparison
        result_cleaned = ' '.join(result.split())
        expected_cleaned = ' '.join(expected.split())
        assert result_cleaned == expected_cleaned