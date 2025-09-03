"""
Response Cleaner Utility - Shared preprocessing for LLM responses

Provides common cleaning functions for LLM responses that can be used
across different scoring types (stringmatch, jsonmatch, etc.).

Supports multiple response formats:
- Standard thinking tags (<thinking>, <reasoning>, etc.)
- OpenAI Harmony format (<|channel|>analysis/final<|message|>)
"""
import re


class ResponseCleaner:
    """Utility class for cleaning LLM responses before scoring."""
    
    @staticmethod
    def has_harmony_format(text):
        """
        Check if text contains OpenAI Harmony format markers.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if Harmony format markers are found
        """
        if not text:
            return False
            
        # Look for the characteristic Harmony format tokens
        return '<|channel|>' in text and '<|message|>' in text
    
    @staticmethod
    def strip_harmony_format(text):
        """
        Extract the final answer from OpenAI Harmony format response.
        
        The Harmony format looks like:
        <|channel|>analysis<|message|>reasoning...<|end|><|start|>assistant<|channel|>final<|message|>Hello! How can I assist you today?
        
        This function extracts everything after the last <|message|> token, regardless of channel type.
        This handles cases where the answer might be in 'final', 'commentary', or other channels.
        
        Args:
            text (str): Input text in Harmony format
            
        Returns:
            str: Final answer content, or original text if no message tags found
        """
        if not text:
            return text
        
        # Look for any message marker (regardless of channel)
        message_pattern = r'<\|message\|>'
        
        # Find all matches to get the last one
        matches = list(re.finditer(message_pattern, text))
        
        if not matches:
            # No message tags found, return original text
            return text
        
        # Get the position after the last message marker
        last_match = matches[-1]
        final_answer_start = last_match.end()
        
        # Extract everything after the last message marker
        final_answer = text[final_answer_start:]
        
        return final_answer
    
    @staticmethod
    def strip_thinking_tags(text):
        """
        Remove thinking/reasoning tags and their content from text.
        
        Handles various thinking tag formats:
        - <thinking>...</thinking>
        - <think>...</think>
        - <reasoning>...</reasoning>
        - <thought>...</thought>
        - <internal>...</internal>
        - Case insensitive matching
        - Multiline content support
        
        Args:
            text (str): Input text that may contain thinking tags
            
        Returns:
            str: Text with thinking tags and their content removed
        """
        if not text:
            return text
            
        # Define patterns for common thinking tag formats
        thinking_patterns = [
            r'<thinking>.*?</thinking>',
            r'<think>.*?</think>', 
            r'<reasoning>.*?</reasoning>',
            r'<thought>.*?</thought>',
            r'<internal>.*?</internal>',
            r'<reflection>.*?</reflection>',
            r'<analysis>.*?</analysis>'
        ]
        
        # Apply each pattern with case-insensitive matching and DOTALL flag
        # DOTALL makes . match newlines too
        cleaned_text = text
        for pattern in thinking_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned_text
    
    @staticmethod
    def strip_orphaned_think_closing(text):
        """
        Handle orphaned closing think tags by returning everything after the last </think>.
        
        Some models (e.g., newer Qwen reasoning models) emit closing </think> tags
        without proper opening <think> tags. This function finds the last </think>
        and returns everything after it.
        
        Args:
            text (str): Input text that may contain orphaned </think> tags
            
        Returns:
            str: Text after the last </think> tag, or original text if no </think> found
        """
        if not text:
            return text
            
        # Find the last occurrence of </think> (case insensitive)
        think_close_pattern = r'</think>'
        matches = list(re.finditer(think_close_pattern, text, flags=re.IGNORECASE))
        
        if not matches:
            # No </think> tags found, return original text
            return text
        
        # Get position after the last </think> tag
        last_match = matches[-1]
        after_think_start = last_match.end()
        
        # Return everything after the last </think> tag
        result = text[after_think_start:]
        
        return result
    
    @staticmethod
    def clean_response(text, strip_thinking=True, strip_harmony=True, strip_whitespace=True):
        """
        Apply standard cleaning operations to an LLM response.
        
        Automatically detects and handles different response formats:
        - OpenAI Harmony format (<|channel|>final<|message|>content)
        - Standard thinking tags (<thinking>, <reasoning>, etc.)
        
        Args:
            text (str): Raw LLM response text
            strip_thinking (bool): Whether to remove thinking tags (for non-Harmony responses)
            strip_harmony (bool): Whether to process Harmony format responses
            strip_whitespace (bool): Whether to strip leading/trailing whitespace
            
        Returns:
            str: Cleaned response text
        """
        if not text:
            return text
            
        cleaned = text
        
        # Check for Harmony format first (takes precedence)
        if strip_harmony and ResponseCleaner.has_harmony_format(cleaned):
            cleaned = ResponseCleaner.strip_harmony_format(cleaned)
        elif strip_thinking:
            # Apply standard thinking tag removal first
            cleaned = ResponseCleaner.strip_thinking_tags(cleaned)
            # Then handle any orphaned </think> tags that weren't caught
            cleaned = ResponseCleaner.strip_orphaned_think_closing(cleaned)
        
        # Strip whitespace last
        if strip_whitespace:
            cleaned = cleaned.strip()
            
        return cleaned
    
    @staticmethod
    def has_thinking_tags(text):
        """
        Check if text contains thinking tags.
        
        Note: This only checks for traditional thinking tags, not Harmony format.
        Use has_harmony_format() to check for Harmony format responses.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if thinking tags are found
        """
        if not text:
            return False
            
        original_length = len(text)
        cleaned_length = len(ResponseCleaner.strip_thinking_tags(text))
        
        return original_length != cleaned_length
