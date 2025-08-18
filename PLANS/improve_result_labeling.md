# Improve Result Labeling: Meaningful Test Run Folder Names

## 🎯 Problem Statement

Currently, all PICARD test runs create folders with generic timestamp-based names like `test_20250118_143052`. When running multiple tests against different models or configurations, it becomes impossible to identify which folder corresponds to which model without manually checking the contents.

**Current Naming**: `test_[timestamp]`
**Desired Naming**: `[user_label]_[timestamp]`

## 📊 Current State Analysis

### Current Test Runner Flow
```python
# In test_runner.py line 62:
self.test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
# Results in: test_20250118_143052
```

### Problems with Current Approach
- ❌ **Indistinguishable folders**: All results look identical in file explorer
- ❌ **Manual identification required**: Must open files to determine model/config used  
- ❌ **Poor organization**: Hard to compare results across different models
- ❌ **Time-consuming analysis**: Researchers waste time identifying test runs
- ❌ **Error-prone workflows**: Easy to mix up results from different models

### Impact on Workflows
- **Model Comparison**: Researchers running A/B tests across multiple models
- **Configuration Testing**: Testing different hyperparameters or setups
- **Batch Processing**: Running tests against multiple model endpoints
- **Result Analysis**: Post-processing and visualization of results
- **Team Collaboration**: Sharing specific test results with colleagues

## 🚀 Proposed Solution: User-Defined Labels

### New Command-Line Interface
```bash
# Enhanced test runner with --label parameter
python src/test_runner.py --label "openai_gpt4"
# Results in: openai_gpt4_20250118_143052

python src/test_runner.py --label "claude_sonnet" --api-endpoint http://claude-proxy:8080
# Results in: claude_sonnet_20250118_143052

python src/test_runner.py -l "llama_70b_quantized" --definitions custom_tests.yaml
# Results in: llama_70b_quantized_20250118_143052
```

### Design Principles
1. **Backwards Compatible**: Default to "test" if no label provided
2. **User-Friendly**: Short `-l` alias for frequent use
3. **Robust**: Handle edge cases (spaces, special characters, length limits)
4. **Informative**: Clear help text with practical examples
5. **Consistent**: Maintain timestamp format for uniqueness

## 🏗️ Implementation Plan

### Phase 1: Core Implementation (30 minutes)

#### 1.1 Add Command-Line Parameter
```python
# In main() function argument parsing section
parser.add_argument(
    '--label', '-l',
    default='test',
    help='Label for test run folder (default: test). Creates folder: {label}_{timestamp}'
)
```

#### 1.2 Update Method Signatures
```python
# Modify initialize_test_run() to accept label parameter
def initialize_test_run(self, test_definitions_file: str = None, label: str = "test") -> str:
```

#### 1.3 Implement Label Sanitization
```python
def sanitize_label(self, label: str) -> str:
    """
    Sanitize user-provided label for filesystem compatibility.
    
    Args:
        label: Raw user input label
        
    Returns:
        Sanitized label safe for folder names
        
    Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Remove/replace special characters
        - Limit length to reasonable bounds
        - Ensure non-empty result
    """
    if not label or not label.strip():
        return "test"
    
    # Convert to lowercase and replace spaces
    sanitized = label.lower().replace(' ', '_')
    
    # Keep only alphanumeric, underscores, and hyphens
    import re
    sanitized = re.sub(r'[^a-z0-9_-]', '', sanitized)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim underscores from start/end
    sanitized = sanitized.strip('_')
    
    # Length limits (reasonable for folder names)
    if len(sanitized) > 50:
        sanitized = sanitized[:50].rstrip('_')
    
    # Ensure non-empty
    if not sanitized:
        return "test"
    
    return sanitized
```

#### 1.4 Update Folder Creation Logic
```python
# In initialize_test_run() method
def initialize_test_run(self, test_definitions_file: str = None, label: str = "test") -> str:
    # Sanitize the label
    clean_label = self.sanitize_label(label)
    
    # Generate test ID with custom label
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    self.test_id = f"{clean_label}_{timestamp}"
    
    # Rest of method unchanged...
```

#### 1.5 Update Call Chain
```python
# In run_benchmark() method - pass label through
def run_benchmark(self, test_definitions_file: str = None, 
                 sandbox_template: str = "clean_sandbox",
                 max_retries: int = 3, max_llm_rounds: int = 20, 
                 retry_delay: float = 2.0,
                 use_mock_llm: bool = False, api_endpoint: str = None,
                 label: str = "test") -> Dict[str, str]:
    
    # Initialize test run with custom label
    test_id = self.initialize_test_run(
        test_definitions_file=test_definitions_file,
        label=label
    )
    # Rest of method unchanged...
```

#### 1.6 Update Main Function
```python
# In main() function - pass parsed label to runner
def main():
    # ... existing argument parsing ...
    
    try:
        runner = TestRunner()
        result = runner.run_benchmark(
            test_definitions_file=args.definitions,
            sandbox_template=args.template,
            max_retries=args.retries,
            max_llm_rounds=args.max_llm_rounds,
            retry_delay=args.delay,
            use_mock_llm=args.mock_llm,
            api_endpoint=args.api_endpoint,
            label=args.label  # New parameter
        )
        # Rest unchanged...
```

### Phase 2: Documentation and Examples (15 minutes)

#### 2.1 Update Help Text
```python
parser.add_argument(
    '--label', '-l',
    default='test',
    help='Label for test run folder (default: test). Examples: "openai_gpt4", "claude_sonnet", "llama_70b"'
)
```

#### 2.2 Update CLI Examples in Docstring
```python
# Update the epilog examples in argument parser
epilog='''
Examples:
  python test_runner.py                                     # Default: test_20250118_143052
  python test_runner.py --label "openai_gpt4"             # Result: openai_gpt4_20250118_143052
  python test_runner.py -l "claude_sonnet" --real-llm     # Result: claude_sonnet_20250118_143052
  python test_runner.py --label "llama 70B quantized"     # Result: llama_70b_quantized_20250118_143052
  python test_runner.py --definitions custom.yaml -l "experiment_1"  # Result: experiment_1_20250118_143052
'''
```

#### 2.3 Update README.md Examples
```markdown
# Update README examples to show new labeling capability
```bash
# Run with meaningful labels for different models
python src/test_runner.py --label "openai_gpt4" --api-endpoint "http://localhost:5002/api/chat"
python src/test_runner.py --label "claude_sonnet" --api-endpoint "http://localhost:5003/api/chat" 
python src/test_runner.py --label "llama_70b" --api-endpoint "http://localhost:5004/api/chat"

# Results will be organized as:
# results/openai_gpt4_20250118_143052/
# results/claude_sonnet_20250118_143115/
# results/llama_70b_20250118_143200/
```

### Phase 3: Edge Cases and Validation (10 minutes)

#### 3.1 Test Label Sanitization
```python
# Test cases for sanitization function
test_cases = {
    "OpenAI GPT-4": "openai_gpt4",
    "Claude 3.5 Sonnet": "claude_35_sonnet", 
    "LLaMA-2 70B (Quantized)": "llama2_70b_quantized",
    "  spaces  ": "spaces",
    "special!@#$%chars": "specialchars",
    "": "test",  # Empty fallback
    "very_long_label_that_exceeds_reasonable_limits_for_folder_names": "very_long_label_that_exceeds_reasonable_limits_fo",  # Truncated
}
```

#### 3.2 Backward Compatibility Testing
```bash
# Ensure existing workflows still work
python src/test_runner.py  # Should still create test_[timestamp]
```

#### 3.3 Integration Testing
```bash
# Test full workflow with new labels
python src/test_runner.py --label "integration_test" --mock-llm
# Verify folder creation and proper naming
```

## 📋 Implementation Checklist

### Core Functionality ✓
- [ ] Add `--label` command-line parameter with `-l` short alias
- [ ] Implement `sanitize_label()` function with robust edge case handling
- [ ] Update `initialize_test_run()` method signature to accept label parameter
- [ ] Modify test ID generation from `test_[timestamp]` to `[label]_[timestamp]`
- [ ] Update `run_benchmark()` method to pass label through call chain
- [ ] Update `main()` function to pass parsed label to runner methods

### Input Validation ✓
- [ ] Handle empty/null labels (fallback to "test")
- [ ] Convert spaces to underscores for filesystem compatibility  
- [ ] Remove special characters that could cause filesystem issues
- [ ] Implement reasonable length limits (50 characters)
- [ ] Convert to lowercase for consistency
- [ ] Remove consecutive underscores and trim edge underscores

### Documentation ✓
- [ ] Update command-line help text with clear examples
- [ ] Update argument parser epilog with practical usage examples
- [ ] Update README.md examples to demonstrate new labeling capability
- [ ] Add usage examples for common model comparison scenarios

### Testing & Validation ✓
- [ ] Test sanitization function with edge cases
- [ ] Verify backward compatibility (no --label should default to "test")
- [ ] Test full integration with mock LLM
- [ ] Verify folder creation with custom labels
- [ ] Test label sanitization with real-world model names

### Error Handling ✓
- [ ] Handle filesystem permission issues gracefully
- [ ] Validate sanitized labels are valid folder names
- [ ] Provide clear error messages for invalid inputs

## 🌟 Benefits After Implementation

### For Researchers
- **Immediate Model Identification**: Folder names clearly indicate which model was tested
- **Efficient Result Organization**: Results naturally grouped by model/configuration
- **Faster Analysis Workflows**: No need to dig into files to identify test runs
- **Better Experiment Tracking**: Easy to correlate folders with experimental conditions

### For Team Collaboration  
- **Clear Communication**: "Check the claude_sonnet_20250118_143052 results" 
- **Shared Understanding**: Team members immediately know what each folder contains
- **Reduced Confusion**: No more "which test_20250118_143052 folder was that again?"

### For Automation & Scripting
- **Predictable Naming**: Scripts can generate folder names programmatically
- **Batch Processing**: Easy to iterate over results from specific models
- **Integration Friendly**: Other tools can parse folder names for metadata

## 🚦 Usage Examples

### Model Comparison Workflow
```bash
# Compare multiple models on same test suite
python src/test_runner.py --label "gpt4" --api-endpoint http://openai-proxy:8080
python src/test_runner.py --label "claude35" --api-endpoint http://claude-proxy:8080  
python src/test_runner.py --label "llama70b" --api-endpoint http://llama-proxy:8080

# Results organized clearly:
# results/gpt4_20250118_143000/
# results/claude35_20250118_143100/  
# results/llama70b_20250118_143200/

# Analyze results with clear model identification
python src/scorer.py --test-dir results/gpt4_20250118_143000
python src/scorer.py --test-dir results/claude35_20250118_143100
```

### Configuration Testing Workflow
```bash
# Test different configurations of same model
python src/test_runner.py --label "llama_default" --api-endpoint http://llama:8080
python src/test_runner.py --label "llama_quantized" --api-endpoint http://llama-q:8080
python src/test_runner.py --label "llama_finetuned" --api-endpoint http://llama-ft:8080

# Clear configuration differentiation in results
# results/llama_default_20250118_143000/
# results/llama_quantized_20250118_143100/
# results/llama_finetuned_20250118_143200/
```

### Research Experiment Workflow  
```bash
# Systematic experimental runs
python src/test_runner.py --label "baseline_experiment" --definitions baseline_tests.yaml
python src/test_runner.py --label "treatment_a" --definitions treatment_a_tests.yaml
python src/test_runner.py --label "treatment_b" --definitions treatment_b_tests.yaml

# Results clearly linked to experimental conditions
# results/baseline_experiment_20250118_143000/
# results/treatment_a_20250118_143100/
# results/treatment_b_20250118_143200/
```

## 🔒 Risk Assessment

### Low Risk Changes
- **Backward Compatibility**: Default "test" maintains existing behavior
- **Filesystem Safety**: Robust sanitization prevents invalid folder names
- **Parameter Addition**: New optional parameter doesn't break existing scripts

### Mitigation Strategies
- **Extensive Testing**: Test sanitization with diverse inputs
- **Fallback Behavior**: Always fallback to "test" for invalid inputs
- **Clear Documentation**: Comprehensive examples prevent user confusion

## 📈 Success Metrics

### Immediate Benefits
- ✅ **Folder Creation**: Custom labels successfully create appropriately named folders
- ✅ **Sanitization**: Edge cases handled gracefully without errors
- ✅ **Backward Compatibility**: Existing workflows continue to work unchanged

### User Experience Improvements
- ✅ **Time Savings**: Researchers can identify test runs 5-10x faster
- ✅ **Reduced Errors**: Fewer mistakes when selecting result folders for analysis
- ✅ **Better Organization**: Natural grouping of related test runs

### Long-term Workflow Benefits
- ✅ **Scalable Organization**: System supports hundreds of labeled test runs
- ✅ **Team Productivity**: Improved collaboration through clear naming conventions
- ✅ **Automation Ready**: Predictable naming enables automated processing

## 🎉 Conclusion

This enhancement transforms PICARD's test result organization from a generic timestamp-based system to a user-controlled, meaningful labeling system. The implementation is straightforward, low-risk, and provides immediate value for researchers conducting model comparisons and experimental work.

**Key Value Proposition**: Transform cryptic `test_20250118_143052` folders into meaningful `openai_gpt4_20250118_143052` folders that immediately convey the model/configuration tested.

**Implementation Time**: ~1 hour total (30 min core + 15 min docs + 15 min testing)  
**Risk Level**: Low (backward compatible, well-tested sanitization)  
**User Impact**: High (immediate workflow improvement for all researchers)