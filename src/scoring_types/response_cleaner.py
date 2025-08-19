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
        <|channel|>analysis<|message|>User says "Hello". Probably just greet back.<|start|>assistant<|channel|>final<|message|>Hello! How can I assist you today?
        
        This function extracts everything after the last <|channel|>final<|message|> token.
        
        Args:
            text (str): Input text in Harmony format
            
        Returns:
            str: Final answer content, or original text if no final channel found
        """
        if not text:
            return text
        
        # Look for the final channel marker
        final_pattern = r'<\|channel\|>final<\|message\|>'
        
        # Find all matches to get the last one (in case there are multiple)
        matches = list(re.finditer(final_pattern, text))
        
        if not matches:
            # No final channel found, return original text
            return text
        
        # Get the position after the last final channel marker
        last_match = matches[-1]
        final_answer_start = last_match.end()
        
        # Extract everything after the final marker
        final_answer = text[final_answer_start:]
        
        return final_answer
    
    @staticmethod
    def strip_thinking_tags(text, preserve_whitespace=False):
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
        - Proper whitespace handling
        
        Args:
            text (str): Input text that may contain thinking tags
            preserve_whitespace (bool): If True, preserve original whitespace around tags
            
        Returns:
            str: Text with thinking tags and their content removed
        """
        if not text:
            return text
            
        if preserve_whitespace:
            # Think tags will be at the beginning, no spaces before them
            # Remove the think tag AND any spaces/newlines after the closing tag
            thinking_pattern = r'<(?:thinking|think|reasoning|thought|internal|reflection|analysis)>.*?</(?:thinking|think|reasoning|thought|internal|reflection|analysis)>\s*'
            
            # Remove thinking tags and trailing spaces, but preserve other whitespace
            cleaned_text = re.sub(thinking_pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        else:
            # Pattern to match thinking tags with surrounding whitespace
            # Replace tag and surrounding spaces with single space to maintain word separation
            thinking_pattern = r'\s*<(?:thinking|think|reasoning|thought|internal|reflection|analysis)>.*?</(?:thinking|think|reasoning|thought|internal|reflection|analysis)>\s*'
            
            # Remove thinking tags and replace with single space
            cleaned_text = re.sub(thinking_pattern, ' ', text, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned_text
    
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
            # Only apply thinking tag removal if not Harmony format
            # Preserve whitespace when strip_whitespace=False
            cleaned = ResponseCleaner.strip_thinking_tags(cleaned, preserve_whitespace=not strip_whitespace)
        
        # Handle whitespace normalization and stripping
        if strip_whitespace:
            # Only normalize internal whitespace if we actually processed something
            if cleaned != text:  # Something was changed (tags were removed)
                cleaned = re.sub(r'\s+', ' ', cleaned)
            # Always strip leading/trailing whitespace when strip_whitespace=True
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
        cleaned_length = len(ResponseCleaner.strip_thinking_tags(text, preserve_whitespace=False))
        
        return original_length != cleaned_length
