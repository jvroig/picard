"""
Mock LLM Execution - Simple mock that returns "Okie dokie"

This will be replaced with real LLM API calls in the future.
"""
import time
from datetime import datetime
from typing import Dict, Any


def mock_llm_execute(question: str, **kwargs) -> Dict[str, Any]:
    """
    Mock LLM execution that always returns "Okie dokie".
    
    Args:
        question: The question to ask the LLM
        **kwargs: Additional parameters (ignored for mock)
        
    Returns:
        Dictionary with response data
    """
    # Simulate a tiny delay for realism
    time.sleep(0.01)
    
    return {
        "response_text": "Okie dokie",
        "execution_successful": True,
        "error_message": None,
        "timestamp": datetime.now().isoformat(),
        "model_info": "mock_llm_v1.0"
    }


def execute_with_retry(question: str, max_retries: int = 3, delay: float = 2.0, 
                      **kwargs) -> Dict[str, Any]:
    """
    Execute LLM call with retry logic.
    
    Args:
        question: The question to ask the LLM
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        **kwargs: Additional parameters passed to LLM function
        
    Returns:
        Dictionary with response data
        
    Raises:
        Exception: If all retry attempts fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # For now, just call the mock LLM
            # In the future, this will call real LLM APIs
            result = mock_llm_execute(question, **kwargs)
            
            # Check if execution was successful
            if result.get("execution_successful", False):
                return result
            else:
                # Treat unsuccessful execution as an error
                error_msg = result.get("error_message", "Unknown execution error")
                raise Exception(f"LLM execution failed: {error_msg}")
                
        except Exception as e:
            last_error = e
            
            if attempt < max_retries - 1:  # Not the last attempt
                print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
                print(f"   🔄 Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                # Last attempt failed
                raise Exception(f"Failed after {max_retries} attempts. Last error: {e}")
    
    # This shouldn't be reached, but just in case
    raise Exception(f"Unexpected error in retry logic. Last error: {last_error}")


def main():
    """Test the mock LLM execution."""
    print("🤖 Testing Mock LLM Execution")
    print("=" * 30)
    
    # Test basic execution
    test_question = "Write 'Hello world!' to test.txt"
    print(f"📝 Test question: {test_question}")
    
    result = mock_llm_execute(test_question)
    print(f"🔄 Response: {result}")
    print()
    
    # Test retry logic
    print("🔄 Testing retry logic...")
    try:
        result = execute_with_retry(test_question, max_retries=2, delay=0.5)
        print(f"✅ Retry test successful: {result['response_text']}")
    except Exception as e:
        print(f"❌ Retry test failed: {e}")
    
    print("\n✅ Mock LLM test completed!")


if __name__ == "__main__":
    main()
