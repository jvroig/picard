# Fix Variable Expansion Bugs in Sandbox Components

## Problem Statement

PICARD's variable expansion system has gaps in certain sandbox components and contexts. While the system works correctly for most cases (create_sqlite, expected_content, main templates), there are specific bugs preventing numeric and entity variables from being properly expanded in:

1. **create_files count property** - Numeric variables in content count specifications not expanded
2. **Template functions in expected_response** - Numeric variables in template function arguments not expanded (specifically file_line/file_word)

## Current Working Cases ✅

### **Confirmed Working Variable Expansion:**
- **Main template text**: `template: "How many orders above {{number1:50000:100000}} are there?"`
- **expected_content**: Uses `_substitute_with_all_variables()` + `_evaluate_template_functions()`
- **create_sqlite rows**: Uses `_process_content_spec_variables()` 
- **sandbox target_file**: Processed via `template_processor.process_multiple_fields()`

### **Working Example:**
```yaml
- question_id: 402
  template: "How many orders above {{number1:40000:60000:currency}} are there?"
  expected_content: "{\"num_big_orders\": {{sqlite_query:SELECT COUNT(*) WHERE ORD_AMT > {{number1:40000:60000:currency}}:TARGET_FILE[db]}}}"
  sandbox_setup:
    components:
      - type: "create_sqlite"
        content:
          tables:
            - name: "enterprise_orders"
              rows: "{{number99:250:300}}"  # ✅ Works - gets expanded
```

**Why this works:**
1. `expected_content` uses two-step processing:
   - Step 1: `_substitute_with_all_variables()` expands `{{number1:40000:60000:currency}}` to actual value
   - Step 2: `_evaluate_template_functions()` processes `sqlite_query` with expanded arguments
2. `create_sqlite` uses `_process_content_spec_variables()` to expand `rows` property

## Identified Bugs ❌

### **Bug #1: create_files Count Property**

**Problem Location:** `TextFileGenerator.generate()` in `src/file_generators.py`

**Failing Example:**
```yaml
- type: "create_files"
  content:
    type: "lorem_lines"
    count: {{number9:30:50}}  # ❌ Stays as string "{{number9:30:50}}"
```

**Root Cause:** 
- `TextFileGenerator` is missing the `_process_content_spec_variables()` call that other generators have
- All other generators (SQLite, CSV, JSON, YAML, XML) include this line:
  ```python
  processed_content_spec = self._process_content_spec_variables(content_spec)
  ```
- `TextFileGenerator` calls `_generate_text_content(content_spec)` directly with unprocessed spec

**Current Code Flow:**
```python
class TextFileGenerator(BaseFileGenerator):
    def generate(self, target_file, content_spec, clutter_spec=None):
        # ❌ MISSING: processed_content_spec = self._process_content_spec_variables(content_spec)
        content = self._generate_text_content(content_spec)  # Uses raw content_spec
        
    def _generate_text_content(self, content_spec):
        count = content_spec.get('count', 10)  # Gets "{{number9:30:50}}" instead of 42
        return self.lorem_generator.generate_lines(count)  # ❌ Fails with non-integer
```

**Impact:** Any numeric variable in create_files content count property fails to expand.

### **Bug #2: Template Function Arguments in expected_response**

**Problem Location:** Template function argument parsing in expected_response processing

**Failing Example:**
```yaml
- question_id: 201
  template: "What is line {{number1:10:15}} in file notes.txt?"
  expected_response: "{{file_line:{{number1:10:15}}:TARGET_FILE[notes_file]}}"
  # ❌ file_line fails because {{number1:10:15}} not expanded before function call
```

**Root Cause Analysis:**

**Expected Processing Flow:**
1. `_substitute_with_all_variables()` should expand: `{{file_line:{{number1:10:15}}:TARGET_FILE[notes_file]}}` → `{{file_line:12:TARGET_FILE[notes_file]}}`
2. `_evaluate_template_functions()` should process: `{{file_line:12:TARGET_FILE[notes_file]}}` → `"Line 12 content"`

**Suspected Issue:** Variable expansion within template function arguments may not be working correctly in the `expected_response` context, even though it works in `expected_content`.

**Need Investigation:** 
- Exact error message from file_line failure
- Whether the issue is in argument parsing or function execution
- Difference between expected_content and expected_response processing (if any)

## Technical Details

### **Variable Processing Methods:**

#### **Method 1: _process_content_spec_variables()** 
Used by: SQLite, CSV, JSON, YAML, XML generators
```python
def _process_content_spec_variables(self, content_spec: Dict[str, Any]) -> Dict[str, Any]:
    spec_json = json.dumps(content_spec)
    result = self.entity_pool.substitute_template_enhanced(spec_json)
    return json.loads(result['substituted'])
```

#### **Method 2: _substitute_with_all_variables()** 
Used by: expected_content, expected_response processing
```python
# In precheck_generator.py
substituted_content = self._substitute_with_all_variables(test_def.expected_content, entity_values)
```

#### **Method 3: entity_pool.substitute_template_enhanced()**
Used by: Main template processing
```python
# In precheck_generator.py  
result = self.entity_pool.substitute_template_enhanced(test_def.template, test_def.expected_structure)
```

### **Processing Pipelines:**

#### **Working Pipeline (create_sqlite):**
```
content_spec (with {{number1:50:100}}) 
  ↓ 
_process_content_spec_variables() 
  ↓ 
processed_content_spec (with actual numbers)
  ↓
_generate_sqlite_content()
```

#### **Broken Pipeline (create_files):**
```
content_spec (with {{number9:30:50}})
  ↓ 
_generate_text_content() [NO VARIABLE PROCESSING]
  ↓
count = "{{number9:30:50}}" ❌
  ↓
lorem_generator.generate_lines("{{number9:30:50}}") ❌ FAILS
```

#### **Expected Working Pipeline (expected_response):**
```
"{{file_line:{{number1:10:15}}:TARGET_FILE[notes]}}"
  ↓
_substitute_with_all_variables()
  ↓  
"{{file_line:12:TARGET_FILE[notes]}}"
  ↓
_evaluate_template_functions()
  ↓
"Line 12 content" ✅
```

## Implementation Plan

### **Phase 1: Fix create_files Count Property**

**File to modify:** `src/file_generators.py`

**Change needed in TextFileGenerator.generate():**
```python
def generate(self, target_file: str, content_spec: Dict[str, Any], clutter_spec: Dict[str, Any] = None):
    # ... existing setup ...
    
    try:
        # ADD THIS LINE - Process {{numeric}} variables in content_spec
        processed_content_spec = self._process_content_spec_variables(content_spec)
        
        # Generate main file content using processed spec
        content = self._generate_text_content(processed_content_spec)  # ← Use processed_content_spec
        
        # ... rest of method unchanged ...
```

**Testing:**
- Create test with `count: {{number1:10:20}}`
- Verify count gets expanded to actual number
- Verify file generation works with expanded count

### **Phase 2: Investigate expected_response Template Function Bug**

**Steps:**
1. **Reproduce the failure** - Run the failing test case and capture exact error
2. **Debug variable expansion** - Check if `_substitute_with_all_variables()` is properly expanding nested variables
3. **Debug template function parsing** - Verify if function arguments are correctly parsed after expansion
4. **Compare with working case** - Analyze why sqlite_query works but file_line doesn't

**Potential Fixes:**
- Fix variable expansion in template function arguments if broken
- Ensure consistent processing between expected_content and expected_response
- Fix argument parsing in template function evaluation

### **Phase 3: Comprehensive Testing**

**Test Cases:**
1. **create_files with numeric count**
   ```yaml
   content:
     type: "lorem_lines" 
     count: {{number1:15:25}}
   ```

2. **file_line with numeric argument in expected_response**
   ```yaml
   expected_response: "{{file_line:{{number1:5:10}}:TARGET_FILE[file]}}"
   ```

3. **Regression testing** - Ensure existing working cases still work
   - create_sqlite with numeric rows
   - expected_content with sqlite_query and numeric variables
   - Main template with numeric variables

4. **Edge cases**
   - Multiple numeric variables in same template function
   - Nested template functions with numeric arguments
   - Different template functions (file_word, csv_cell, etc.)

## Success Criteria

### **Phase 1 Success:**
- ✅ create_files count property accepts and expands numeric variables
- ✅ Generated files have correct number of lines based on expanded variable
- ✅ No regression in existing create_files functionality

### **Phase 2 Success:**  
- ✅ file_line works with numeric variables in expected_response
- ✅ file_word and other template functions work with numeric variables
- ✅ Consistent behavior between expected_content and expected_response

### **Overall Success:**
- ✅ All sandbox components support numeric variables consistently
- ✅ All template functions support numeric variables in arguments
- ✅ Variable expansion works uniformly across all contexts
- ✅ Comprehensive test coverage for variable expansion edge cases

## Risk Assessment

### **Low Risk Changes:**
- **create_files fix**: Simple addition of existing method call, follows established pattern

### **Medium Risk Changes:**  
- **Template function argument processing**: May affect multiple template functions, requires careful testing

### **Mitigation:**
- Comprehensive regression testing on existing working cases
- Incremental implementation with validation at each step
- Rollback plan if changes break existing functionality

---

**Priority:** High - Breaks expected functionality in common use cases  
**Complexity:** Low-Medium - Well-understood patterns, targeted fixes  
**Timeline:** Phase 1 can be implemented immediately, Phase 2 requires investigation  
**Dependencies:** None - self-contained bug fixes in variable expansion system