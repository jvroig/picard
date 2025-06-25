"""
Response Cleaner Utility - Shared preprocessing for LLM responses

Provides common cleaning functions for LLM responses that can be used
across different scoring types (stringmatch, jsonmatch, etc.).
"""
import re


class ResponseCleaner:
    """Utility class for cleaning LLM responses before scoring."""
    
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
    def clean_response(text, strip_thinking=True, strip_whitespace=True):
        """
        Apply standard cleaning operations to an LLM response.
        
        Args:
            text (str): Raw LLM response text
            strip_thinking (bool): Whether to remove thinking tags
            strip_whitespace (bool): Whether to strip leading/trailing whitespace
            
        Returns:
            str: Cleaned response text
        """
        if not text:
            return text
            
        cleaned = text
        
        # Remove thinking tags first
        if strip_thinking:
            cleaned = ResponseCleaner.strip_thinking_tags(cleaned)
        
        # Strip whitespace last
        if strip_whitespace:
            cleaned = cleaned.strip()
            
        return cleaned
    
    @staticmethod
    def has_thinking_tags(text):
        """
        Check if text contains thinking tags.
        
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
