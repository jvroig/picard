# Progressive Result Writing Enhancement Plan

## Problem Statement

Currently, PICARD writes all result files (except precheck) only **after the entire test run is completed**. This creates poor user experience during long-running tests because:

### Current Behavior (Problematic)
- **In-memory accumulation**: Results accumulate in Python lists during test execution
- **Batch writing after completion**: All files written only when entire test finishes
- **Files affected**:
  - `responses.jsonl` - All response entries written at once  
  - `conversations/q{X}_s{Y}.json` - All 200 conversation files written at once
  - `test_summary.json` - Written at the very end

### Pain Points for Users
1. **No incremental feedback**: Users can't monitor progress by checking result files
2. **Risk of total loss**: If test crashes mid-run, all progress lost (except precheck)
3. **Long wait times**: For 200 test items, users must wait for complete run before seeing any individual results
4. **Poor debugging experience**: Can't examine individual completed items during long runs

## Root Cause Analysis

**Location**: `src/test_runner.py` in `TestRunner` class

### Current Flow (Batch Writing)
```python
def run_benchmark(self, ...):
    # 1. Generate precheck entries (✅ already written)
    precheck_entries = self.precheck_generator.generate_precheck_entries()
    precheck_file = self.test_dir / "precheck.jsonl"
    self.precheck_generator.save_precheck_entries(precheck_entries, str(precheck_file))
    
    # 2. Execute questions (❌ results stored in memory)
    responses, conversations = self._execute_questions(...)
    
    # 3. Write results ONLY after all questions complete (❌ batch writing)
    responses_file = self.test_dir / "responses.jsonl"
    self._save_responses(responses, str(responses_file))  # ALL AT ONCE
    
    conversations_dir = self.test_dir / "conversations" 
    self._save_conversations(conversations, conversations_dir)  # ALL AT ONCE
```

### Critical Methods Analysis

**`_execute_questions()` (lines 302-378)**
- Creates empty `responses = []` and `conversations = []` lists
- Accumulates results with `responses.append()` and `conversations.append()`
- Returns complete lists only after all questions processed

**`_save_responses()` (lines 380-384)**
- Takes complete list and writes entire JSONL file at once
- Uses single file handle for entire batch

**`_save_conversations()` (lines 386-397)**  
- Takes complete list and creates all individual JSON files at once
- Single loop writes all 200 files consecutively

## Proposed Solution: Progressive Writing

### Design Goals
1. **Write immediately**: Save results as soon as each question completes
2. **Maintain compatibility**: Keep existing file formats and structures
3. **No streaming complexity**: Simple file writes, not real-time streaming
4. **Preserve error handling**: Current error handling should remain intact
5. **Maintain test integrity**: Failed questions should not break progressive writing

### Implementation Strategy

#### 1. Modify `TestRunner` Class Structure

**Add new instance variables for progressive writing**:
```python
class TestRunner:
    def __init__(self, ...):
        # ... existing initialization ...
        self.responses_file = None  # File handle for responses.jsonl
        self.conversations_dir = None  # Directory for conversation files
```

#### 2. Initialize Progressive Writers Early

**In `run_benchmark()` method, set up files before question execution**:
```python
def run_benchmark(self, ...):
    # ... existing precheck generation ...
    
    # 🆕 Initialize progressive writing BEFORE executing questions
    self._initialize_progressive_writers()
    
    # Execute questions with progressive writing enabled
    self._execute_questions_progressively(precheck_entries, ...)
    
    # 🆕 Only finalize, don't batch-write
    self._finalize_progressive_results()
```

#### 3. Create Progressive Writer Methods

**New method: `_initialize_progressive_writers()`**
```python
def _initialize_progressive_writers(self):
    """Set up files and directories for progressive result writing."""
    # Create responses.jsonl file handle (kept open during test)
    self.responses_file = (self.test_dir / "responses.jsonl").open('w', encoding='utf-8')
    
    # Create conversations directory
    self.conversations_dir = self.test_dir / "conversations"
    self.conversations_dir.mkdir(exist_ok=True)
```

**New method: `_write_result_immediately()`**
```python
def _write_result_immediately(self, response_entry, conversation_entry):
    """Write individual result immediately after question completion."""
    # Write to responses.jsonl immediately
    self.responses_file.write(json.dumps(response_entry) + '\n')
    self.responses_file.flush()  # Force write to disk
    
    # Write individual conversation file immediately
    question_id = conversation_entry['question_id'] 
    sample_number = conversation_entry['sample_number']
    filename = f"q{question_id}_s{sample_number}.json"
    conversation_file = self.conversations_dir / filename
    
    with open(conversation_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_entry, f, indent=2)
```

#### 4. Modify Question Execution Loop

**Transform `_execute_questions()` to write progressively**:
```python
def _execute_questions_progressively(self, precheck_entries, ...):
    """Execute questions with immediate result writing."""
    total_questions = len(precheck_entries)
        
    for i, entry in enumerate(precheck_entries, 1):
        # ... existing question setup ...
        
        try:
            result = execute_with_retry(question, **execution_params)
            
            # Create entries (same as before)
            response_entry = { ... }
            conversation_entry = { ... }
            
            # 🆕 Write immediately instead of appending to lists
            self._write_result_immediately(response_entry, conversation_entry)
            
            print(" ✅")
            
        except Exception as e:
            # ... existing error handling ...
            # 🆕 Could optionally write failed entries with error status
```

**New method: `_finalize_progressive_results()`**
```python
def _finalize_progressive_results(self):
    """Close file handles and finalize progressive writing."""
    if self.responses_file:
        self.responses_file.close()
        
    # Generate summary (same as before)
    self._generate_test_summary()
```

### Error Handling Strategy

#### File I/O Error Resilience
- **Individual failures**: If one conversation file fails to write, continue with others
- **Response log failures**: If responses.jsonl write fails, log error but continue test
- **Recovery mechanisms**: Keep partial results even if some writes fail

#### Implementation
```python
def _write_result_immediately(self, response_entry, conversation_entry):
    """Write with error handling for individual failures."""
    try:
        # Write to responses.jsonl
        self.responses_file.write(json.dumps(response_entry) + '\n')
        self.responses_file.flush()
    except Exception as e:
        print(f"⚠️  Failed to write response to JSONL: {e}")
        # Continue execution - don't fail entire test
    
    try:
        # Write conversation file
        # ... conversation file writing ...
    except Exception as e:
        print(f"⚠️  Failed to write conversation file: {e}")
        # Continue execution - don't fail entire test
```

### Compatibility Considerations

#### Maintain Existing Interfaces
- **File formats remain identical**: JSONL and JSON formats unchanged
- **File structures unchanged**: Same directory layout and naming conventions
- **Scorer compatibility**: No changes needed to scorer.py or other consumers

#### Backward Compatibility Testing
- **Verify scorer works**: Ensure scorer.py can read progressively-written files
- **Check visualization tools**: Ensure visualize_cli_score.py works correctly
- **Test result processing**: Ensure process_results.py handles progressive files

### Implementation Phases

#### Phase 1: Core Progressive Writing (Essential)
1. Modify `TestRunner` to initialize file handles early
2. Transform `_execute_questions()` to write immediately  
3. Add error handling for individual write failures
4. Update file handle management and cleanup

**Success Criteria**: 
- Results written immediately after each question completes
- Test continues if individual writes fail
- Same file formats as before

#### Phase 2: Enhanced Error Recovery (Optional)
1. Add retry logic for failed individual writes
2. Implement partial result recovery on test crash
3. Add progress indicators showing successful writes

#### Phase 3: Performance Optimization (Future)
1. Investigate if frequent file flushes impact performance
2. Consider buffered writes for responses.jsonl  
3. Add optional progress reporting

### Risk Assessment

#### Minimal Risk Changes
- ✅ **File format compatibility**: No changes to JSON/JSONL structures
- ✅ **Error handling**: Individual failures don't break entire test  
- ✅ **Existing workflows**: Scorer and visualization tools unaffected

#### Potential Risks & Mitigations
- **File handle management**: Ensure proper cleanup → Use try/finally blocks
- **Disk space during run**: Progressive writes use same total space → No additional risk
- **Performance impact**: File flushing overhead → Minimal, only after each question

### Testing Strategy

#### Unit Tests
- **Progressive writing logic**: Test `_write_result_immediately()` method
- **Error handling**: Test behavior when individual writes fail
- **File handle management**: Test proper cleanup

#### Integration Tests  
- **End-to-end compatibility**: Run complete test and verify scorer works
- **Crash recovery**: Simulate test interruption, verify partial results readable
- **Large test scenarios**: Test with 200+ questions to verify performance

#### Test Cases
```python
def test_progressive_writing_individual_files():
    """Test that individual conversation files written immediately."""
    
def test_progressive_responses_jsonl():
    """Test that responses.jsonl accumulates progressively."""
    
def test_error_handling_individual_write_failure():
    """Test that test continues if individual write fails."""
    
def test_compatibility_with_existing_tools():
    """Test that scorer and visualizer work with progressive files."""
```

### Implementation Estimate

#### Effort Breakdown
- **Core implementation**: ~4-6 hours
  - Modify TestRunner class structure  
  - Transform execution loop
  - Add progressive writing methods
  - Error handling
- **Testing**: ~2-3 hours  
  - Unit tests for new methods
  - Integration testing
- **Documentation updates**: ~1 hour
  - Update README if needed
  - Code comments

#### Total Estimate: 1 development day (7-10 hours)

### Success Metrics

#### Functional Success
- ✅ Result files written immediately after each question completes
- ✅ Users can monitor progress by watching result files during execution  
- ✅ Partial results preserved if test interrupted
- ✅ No regression in existing functionality

#### Performance Success
- ✅ No significant performance degradation
- ✅ Test execution time remains similar
- ✅ File I/O overhead negligible

#### Compatibility Success  
- ✅ Existing scorer, visualizer, and process_results tools work unchanged
- ✅ File formats and structures identical to current implementation
- ✅ Error handling as robust as current system

---

## Implementation Priority: HIGH

This enhancement significantly improves user experience for long-running tests with minimal risk and high compatibility. The implementation is straightforward and maintains all existing functionality while providing immediate feedback to users.