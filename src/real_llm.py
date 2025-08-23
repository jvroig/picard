"""
Real LLM Integration for PICARD - Connects to qwen-agentic-server API

Replaces mock_llm.py with actual LLM API calls to the qwen-agentic-server engine.
Handles streaming responses, tool execution loops, and conversation storage.
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path


class LLMEngineClient:
    """Client for communicating with qwen-agentic-server API."""
    
    def __init__(self, api_endpoint: str = "http://localhost:5002/api/chat", timeout: int = 300):
        """
        Initialize the LLM client.
        
        Args:
            api_endpoint: Full API endpoint URL (e.g., "http://example.com/api/chat")
            timeout: Request timeout in seconds
        """
        self.api_endpoint = api_endpoint
        self.timeout = timeout
    
    def execute_question(self, question: str, temperature: float = 0.4, 
                        max_tokens: int = 4000, max_llm_rounds: int = 20) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute a question against the LLM and return final response + full conversation.
        
        Args:
            question: The question to ask the LLM
            temperature: LLM temperature parameter
            max_tokens: Maximum tokens for response (default: 4000 for reasoning models)
            
        Returns:
            Tuple of:
            - final_response: The LLM's final response text
            - conversation_history: Full conversation including tool calls
            - statistics: Execution statistics
        """
        start_time = time.time()
        
        # Prepare request payload
        payload = {
            "messages": [{"role": "user", "content": question}],
            "temperature": temperature,
            "max_output_tokens": max_tokens
        }
        
        print(f"   🔗 Calling LLM API: {self.api_endpoint}")
        
        # Make streaming request to LLM API
        response = requests.post(
            self.api_endpoint,
            json=payload,
            stream=True,
            timeout=self.timeout
        )
        
        if not response.ok:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")
        
        # Parse streaming response
        conversation_history = [{"role": "user", "content": question}]
        final_response = ""
        current_assistant_message = ""
        tool_calls = []
        inference_rounds = 0
        tools_used = set()
        
        for line in response.iter_lines():
            if not line:
                continue
                
            try:
                data = json.loads(line.decode('utf-8'))
                
                if data['role'] == 'assistant':
                    if data.get('type') == 'chunk':
                        # Accumulate assistant message chunks
                        current_assistant_message += data['content']
                    elif data.get('type') == 'done':
                        # Assistant message complete
                        if current_assistant_message.strip():
                            conversation_history.append({
                                "role": "assistant", 
                                "content": current_assistant_message
                            })
                            final_response = current_assistant_message  # Track latest assistant response
                            inference_rounds += 1
                            if inference_rounds >= max_llm_rounds:
                                break  # Exit the streaming loop

                        current_assistant_message = ""
                
                elif data['role'] == 'tool_call':
                    # Tool execution result
                    tool_result = data['content']
                    conversation_history.append({
                        "role": "user",  # Tool results appear as user messages
                        "content": tool_result
                    })
                    tool_calls.append(tool_result)
                    
                    #FIXME: Extract tool name from result (basic parsing)
                    if "Tool result:" in tool_result:
                        # This is a bit hacky but works for basic analysis
                        tools_used.add("tool_executed")  # Generic for now
                
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Warning: Could not parse streaming response: {line}")
                continue
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Generate statistics
        statistics = {
            "total_messages": len(conversation_history),
            "inference_rounds": inference_rounds,  
            "tool_calls": len(tool_calls),
            "tools_used": list(tools_used),
            "execution_time_seconds": round(execution_time, 2),
            "total_tokens_estimated": len(final_response) * 1.3  # Rough estimate
        }
        
        print(f"   📊 Completed: {inference_rounds} rounds, {len(tool_calls)} tools, {execution_time:.1f}s")
        
        return final_response, conversation_history, statistics


def real_llm_execute(question: str, api_endpoint: str = None, **kwargs) -> Dict[str, Any]:
    """
    Execute question against real LLM (compatible with mock_llm interface).
    
    Args:
        question: The question to ask the LLM
        api_endpoint: Optional API endpoint URL override
        **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
    Returns:
        Dictionary with response data (compatible with mock_llm format)
    """
    if api_endpoint:
        client = LLMEngineClient(api_endpoint=api_endpoint)
    else:
        client = LLMEngineClient()
    
    try:
        final_response, conversation_history, statistics = client.execute_question(
            question=question,
            temperature=kwargs.get("temperature", 0.4),
            max_tokens=kwargs.get("max_tokens", 4000),
            max_llm_rounds=kwargs.get("max_llm_rounds", 20),
        )
        
        return {
            "response_text": final_response,
            "execution_successful": True,
            "error_message": None,
            "timestamp": datetime.now().isoformat(),
            "model_info": "Unknown [BUG: need to retrieve from server]",
            "conversation_history": conversation_history,
            "statistics": statistics
        }
        
    except Exception as e:
        return {
            "response_text": "",
            "execution_successful": False,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat(),
            "model_info": "Unknown [BUG: need to retrieve from server]",
            "conversation_history": [{"role": "user", "content": question}],
            "statistics": {
                "total_messages": 1,
                "inference_rounds": 0,
                "tool_calls": 0,
                "tools_used": [],
                "execution_time_seconds": 0,
                "total_tokens_estimated": 0
            }
        }


def execute_with_retry(question: str, max_retries: int = 5, delay: float = 30.0, 
                      api_endpoint: str = None, **kwargs) -> Dict[str, Any]:
    """
    Execute LLM call with retry logic optimized for rate-limited APIs.
    
    Uses escalating delays: 30s, 60s, 90s, 120s, 150s (30s * retry_number)
    Total attempts: 6 (1 initial + 5 retries)
    
    Args:
        question: The question to ask the LLM
        max_retries: Maximum number of retry attempts (default: 5 for rate limits)
        delay: Base delay multiplier in seconds (default: 30.0)
        api_endpoint: Optional API endpoint URL override
        **kwargs: Additional parameters passed to LLM function
        
    Returns:
        Dictionary with response data
        
    Raises:
        Exception: If all retry attempts fail
    """
    last_error = None
    total_attempts = max_retries + 1  # Include initial attempt
    
    for attempt in range(total_attempts):
        try:
            result = real_llm_execute(question, api_endpoint=api_endpoint, **kwargs)
            
            # Check if execution was successful
            if result.get("execution_successful", False):
                return result
            else:
                # Treat unsuccessful execution as an error
                error_msg = result.get("error_message", "Unknown execution error")
                raise Exception(f"LLM execution failed: {error_msg}")
                
        except Exception as e:
            last_error = e
            
            if attempt < total_attempts - 1:  # Not the last attempt
                retry_number = attempt + 1
                # Escalating delays: 30s, 60s, 90s, 120s, 150s
                wait_time = delay * retry_number
                
                print(f"   ⚠️  Attempt {attempt + 1}/{total_attempts} failed: {e}")
                print(f"   🔄 Retrying in {wait_time:.0f} seconds (retry #{retry_number})...")
                time.sleep(wait_time)
            else:
                # Last attempt failed
                raise Exception(f"Failed after {total_attempts} attempts. Last error: {e}")
    
    # This shouldn't be reached, but just in case
    raise Exception(f"Unexpected error in retry logic. Last error: {last_error}")


def main():
    """Test the real LLM integration."""
    print("🤖 Testing Real LLM Integration")
    print("=" * 40)
    
    # Test basic execution
    test_question = "Write 'Hello Jean-Luc!' to test.txt"
    print(f"📝 Test question: {test_question}")
    
    try:
        result = real_llm_execute(test_question)
        print(f"✅ Success: {result['response_text'][:100]}...")
        print(f"📊 Stats: {result['statistics']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test retry logic
    print("🔄 Testing retry logic...")
    try:
        result = execute_with_retry(test_question, max_retries=2, delay=0.5)
        print(f"✅ Retry test successful")
        
    except Exception as e:
        print(f"❌ Retry test failed: {e}")
    
    print("\n✅ Real LLM integration test completed!")


if __name__ == "__main__":
    main()
