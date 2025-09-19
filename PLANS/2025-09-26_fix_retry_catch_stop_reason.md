# Catch and Use Stop Reason for Intelligent Retry Logic

## Problem Statement

Currently, PICARD's retry logic treats all "response ended prematurely" scenarios as failures requiring retry. However, the agentic server will be updated to provide stop reasons, which should inform whether a retry is actually beneficial or necessary.

## Current Implementation Issues

### **How retry logic works now:**

**In `real_llm.py`:**
```python
def execute_with_retry(question: str, max_retries: int = 5, delay: float = 30.0, 
                      api_endpoint: str = None, **kwargs) -> Dict[str, Any]:
    """
    Execute LLM call with retry logic optimized for rate-limited APIs.
    Uses escalating delays: 30s, 60s, 90s, 120s, 150s
    """
    for attempt in range(total_attempts):
        try:
            result = real_llm_execute(question, api_endpoint=api_endpoint, **kwargs)
            
            # Check if execution was successful
            if result.get("execution_successful", False):
                return result
            else:
                # Treat unsuccessful execution as an error - ALWAYS RETRIES
                error_msg = result.get("error_message", "Unknown execution error")
                raise Exception(f"LLM execution failed: {error_msg}")
```

**In `test_runner.py`:**
```python
def _execute_questions(self, precheck_entries: List[Dict[str, Any]], 
                      max_retries: int, max_llm_rounds: int, retry_delay: float, api_endpoint: str = None) -> int:
    # ...
    result = execute_with_retry(question, **execution_params)  # Always retries on any failure
```

### **Problems with current approach:**

1. **Blind retries**: Any response ending triggers retry, regardless of cause
2. **Wasted resources**: Retrying when max_tokens limit reached doesn't help
3. **Poor user experience**: Unnecessary delays when response is actually complete
4. **Rate limit inefficiency**: Retrying legitimate completions wastes API calls

## Stop Reason Analysis

### **Expected Stop Reasons from Agentic Server:**

Based on common LLM completion reasons, we expect:

1. **`stop`** - Natural completion (finished thinking, found answer)
2. **`length`** - Hit max_tokens limit 
3. **`tool_limit`** - Maximum tool calls reached
4. **`time_limit`** - Conversation timeout reached
5. **`error`** - Network, API, or processing error
6. **`interrupted`** - User or system interruption
7. **`insufficient_context`** - Context window exceeded

### **Retry Decision Matrix:**

| Stop Reason | Should Retry? | Why / Strategy |
|-------------|---------------|----------------|
| `stop` | ❌ **No** | Natural completion - response is likely complete |
| `length` | ❌ **No** | Hit token limit - need different approach, not retry |
| `tool_limit` | ❌ **No** | Reached tool execution limit - retry won't help |
| `time_limit` | ❌ **No** | Conversation too long - architectural issue |
| `error` | ✅ **Yes** | Network/API issues - retry may succeed |
| `interrupted` | ❌ **No** | Intentional interruption - shouldn't retry |
| `insufficient_context` | ❌ **No** | Context size issue - retry won't fix |
| *Unknown/Missing* | ✅ **Yes** | Backwards compatibility - assume network issue |

## Proposed Solution: Intelligent Stop Reason Handling

### **Enhanced Response Format from Agentic Server:**

```json
{
  "response_text": "The final assistant response...",
  "execution_successful": true,
  "stop_reason": "length",  // ← NEW: Why the response ended
  "error_message": null,
  "timestamp": "2025-01-09T10:30:00Z",
  "conversation_history": [...],
  "statistics": {
    "total_tokens": 4000,
    "max_tokens": 4000,  // ← Shows if we hit the limit
    "inference_rounds": 3,
    "tool_calls": 5,
    "execution_time_seconds": 45.2
  }
}
```

### **Updated Retry Logic:**

```python
def should_retry_based_on_stop_reason(result: Dict[str, Any]) -> bool:
    """
    Determine if a response should be retried based on stop reason.
    
    Args:
        result: LLM execution result with stop_reason field
        
    Returns:
        True if retry is beneficial, False otherwise
    """
    stop_reason = result.get("stop_reason")
    execution_successful = result.get("execution_successful", False)
    
    # If execution was successful, check stop reason for retry decision
    if execution_successful:
        # These stop reasons indicate natural/expected completion - no retry needed
        no_retry_reasons = {
            "stop",                    # Natural completion
            "length",                  # Hit max_tokens limit  
            "tool_limit",              # Maximum tool calls reached
            "time_limit",              # Conversation timeout
            "interrupted",             # Intentional interruption
            "insufficient_context"     # Context window exceeded
        }
        
        if stop_reason in no_retry_reasons:
            return False
        
        # Unknown stop reason or "error" - retry may help
        return True
    
    # If execution failed entirely, check if it's worth retrying
    else:
        # Network/API errors - retry beneficial
        error_message = result.get("error_message", "").lower()
        
        # Rate limit, network, timeout errors - should retry
        retryable_errors = [
            "rate limit", "timeout", "connection", "network", 
            "502", "503", "504", "429"
        ]
        
        if any(error in error_message for error in retryable_errors):
            return True
            
        # Other execution failures - likely code/logic issues, retry unlikely to help
        return False


def execute_with_retry(question: str, max_retries: int = 5, delay: float = 30.0, 
                      api_endpoint: str = None, **kwargs) -> Dict[str, Any]:
    """Enhanced retry logic with stop reason awareness."""
    
    for attempt in range(total_attempts):
        try:
            result = real_llm_execute(question, api_endpoint=api_endpoint, **kwargs)
            
            # NEW: Check if we should retry based on stop reason
            if not should_retry_based_on_stop_reason(result):
                # Don't retry - return result as-is (may be successful or not)
                return result
            
            # Only retry if stop reason indicates it may help
            error_msg = result.get("error_message") or f"Stop reason: {result.get('stop_reason', 'unknown')}"
            raise Exception(f"Retryable condition: {error_msg}")
                
        except Exception as e:
            # ... existing retry delay logic ...
```

## Implementation Plan

### **Phase 1: Update Response Parsing**

**Modify `real_llm.py` to capture stop reason:**

```python
def execute_question(self, question: str, temperature: float = 0.4, 
                    max_tokens: int = 4000, max_llm_rounds: int = 20) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Execute question and capture stop reason from agentic server."""
    
    # ... existing streaming logic ...
    
    stop_reason = "unknown"  # Default
    
    for line in response.iter_lines():
        data = json.loads(line.decode('utf-8'))
        
        # NEW: Capture stop reason from server response
        if 'stop_reason' in data:
            stop_reason = data['stop_reason']
        
        # ... existing parsing logic ...
    
    # Include stop reason in result
    statistics["stop_reason"] = stop_reason
    
    return final_response, conversation_history, statistics
```

### **Phase 2: Implement Intelligent Retry Logic**

**Add stop reason evaluation functions:**

1. `should_retry_based_on_stop_reason()` - Core decision logic
2. Update `execute_with_retry()` to use stop reason
3. Add logging for retry decisions

### **Phase 3: Enhanced User Feedback**

**Update test runner output:**

```python
# In test_runner.py
def _execute_questions(...):
    for entry in precheck_entries:
        try:
            result = execute_with_retry(question, **execution_params)
            
            # NEW: Enhanced status reporting
            stop_reason = result.get("statistics", {}).get("stop_reason", "unknown")
            
            if result.get("execution_successful"):
                if stop_reason == "length":
                    print(f"   ⚠️  Response hit max_tokens limit ({max_tokens})")
                elif stop_reason == "tool_limit":
                    print(f"   ⚠️  Response hit tool execution limit")
                else:
                    print(f"   ✅ Response completed normally (stop: {stop_reason})")
            else:
                print(f"   ❌ Execution failed (stop: {stop_reason})")
```

### **Phase 4: Backwards Compatibility**

**Ensure graceful handling of old server responses:**

```python
def should_retry_based_on_stop_reason(result: Dict[str, Any]) -> bool:
    """Handle both new stop_reason field and legacy responses."""
    
    stop_reason = result.get("stop_reason") or result.get("statistics", {}).get("stop_reason")
    
    # If no stop_reason available, fall back to legacy behavior
    if not stop_reason:
        execution_successful = result.get("execution_successful", False)
        # Old logic: retry if execution failed
        return not execution_successful
    
    # New logic: intelligent retry based on stop reason
    # ... rest of implementation ...
```

## Enhanced Logging and Debugging

### **Stop Reason Visibility:**

```python
# Enhanced logging throughout PICARD
print(f"   📊 LLM completed: stop_reason='{stop_reason}', tokens={token_count}/{max_tokens}")

if stop_reason == "length":
    print(f"   💡 Suggestion: Consider increasing max_tokens (current: {max_tokens})")
elif stop_reason == "tool_limit":
    print(f"   💡 Suggestion: Review tool usage strategy")
```

### **Results Analysis:**

```python
# In results summary
stop_reason_counts = {
    "stop": 12,
    "length": 3,      # ← Shows token limit issues
    "error": 1,       # ← Shows API problems  
    "tool_limit": 0
}

print(f"   📈 Stop reasons: {stop_reason_counts}")
if stop_reason_counts.get("length", 0) > 0:
    print(f"   💡 {stop_reason_counts['length']} responses hit token limits - consider increasing max_tokens")
```

## Benefits

### **Immediate Benefits**
- **Faster execution**: No unnecessary retries for natural completions
- **Better resource usage**: Fewer wasted API calls on legitimate responses
- **Clearer feedback**: Users understand why responses ended

### **Diagnostic Benefits**
- **Token limit detection**: Clear visibility when responses are truncated
- **Tool usage insights**: Understanding when tool limits are reached
- **API health monitoring**: Distinguish network issues from completion reasons

### **Future Benefits**
- **Adaptive strategies**: Different handling for different stop reasons
- **Performance optimization**: Response length prediction based on stop patterns
- **Quality assessment**: Better understanding of response completeness

## Risk Assessment

**Low Risk**:
- Backwards compatible - defaults to current behavior if stop_reason unavailable
- Opt-in enhancement - existing retry logic preserved as fallback
- Server-side change only affects response parsing

**Mitigation**:
- Comprehensive testing with both old and new server responses
- Gradual rollout with feature flag if needed
- Clear logging to debug retry decision logic

## Success Criteria

- ✅ Stop reason properly captured from agentic server responses
- ✅ Intelligent retry decisions based on stop reason type
- ✅ Backwards compatibility with servers not providing stop_reason
- ✅ Enhanced user feedback showing why responses ended
- ✅ Reduced unnecessary retries for natural completions
- ✅ Improved diagnostic capabilities for token limits and tool usage

---

*Plan created: January 9, 2025*  
*Priority: Medium-High (improves user experience, reduces resource waste)*  
*Complexity: Low-Medium (primarily response parsing and decision logic)*  
*Dependencies: Agentic server update to provide stop_reason field*