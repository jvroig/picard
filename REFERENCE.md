# PICARD Framework Reference

This document provides detailed reference information for PICARD's core components: scoring types, template functions, and sandbox setup options.

## Table of Contents

- [Scoring Types](#scoring-types)
- [Template Functions](#template-functions) *(Coming Soon)*
- [Sandbox Setup](#sandbox-setup) *(Coming Soon)*

---

## Scoring Types

PICARD provides multiple scoring mechanisms to evaluate different types of agentic AI tasks. All scoring types support deterministic evaluation without "LLM-as-judge" uncertainty.

### Response Preprocessing

All scoring types automatically clean LLM responses before evaluation:
- **Thinking tag removal**: Strips `<thinking>`, `<reasoning>`, `<internal>` tags and their content
- **Whitespace normalization**: Trims leading/trailing whitespace
- **Case-insensitive tag matching**: Handles various tag formats

### Special Placeholders

PICARD provides built-in placeholders that are automatically substituted during test execution:

#### `{{artifacts}}`
**Purpose**: Points to the configured sandbox directory where test files are created.

**Substitution**: Replaced with the actual path from `picard_config.py` (e.g., `/path/to/your/sandbox`)

**Usage Examples**:
```yaml
template: "Create a file at {{artifacts}}/data.txt"
# Becomes: "Create a file at /path/to/your/sandbox/data.txt"

file_to_read: "{{artifacts}}/{{entity1}}/output.csv"
# Becomes: "/path/to/your/sandbox/crimson/output.csv"
```

#### `{{qs_id}}`
**Purpose**: Provides a unique identifier for each question-sample combination to prevent file conflicts.

**Substitution**: Replaced with `q{question_id}_s{sample_number}` format

**Usage Examples**:
```yaml
# Question 301, Sample 5
target_file: "{{artifacts}}/{{qs_id}}/data.csv"
# Becomes: "/path/to/your/sandbox/q301_s5/data.csv"

template: "Process the database {{artifacts}}/{{qs_id}}/{{entity1}}.db"
# Becomes: "Process the database /path/to/your/sandbox/q301_s5/harbor.db"
```

**Benefits**:
- **Isolation**: Each test sample gets its own subdirectory
- **No conflicts**: Multiple samples can run simultaneously
- **Debugging**: Easy to identify which files belong to which test
- **Cleanup**: Simple to clean up per-question artifacts

**Combined Usage**:
```yaml
sandbox_setup:
  target_file: "{{artifacts}}/{{qs_id}}/{{entity1}}/customers.csv"
  # Creates: /sandbox/q301_s5/crimson/customers.csv

scoring_type: "readfile_stringmatch"
file_to_read: "{{artifacts}}/{{qs_id}}/result.txt"
expected_content: "{{csv_count:ID:TARGET_FILE}}"
```

---

### `stringmatch`

**Purpose**: Direct text comparison for simple question-answer scenarios.

**Use Cases**:
- Single word/phrase responses
- Exact text output validation
- Simple factual questions

**Configuration**:
```yaml
scoring_type: "stringmatch"
expected_response: "{{entity1}}"
```

**Example**:
```yaml
- question_id: 102
  template: "Respond only with this word: {{entity1}}"
  scoring_type: "stringmatch"
  expected_response: "{{entity1}}"
```

**Scoring Logic**:
- Compares expected response exactly with cleaned actual response
- Whitespace trimmed, thinking tags removed
- Case-sensitive matching

**Success Criteria**: `expected_response == cleaned_actual_response`

---

### `jsonmatch`

**Purpose**: Semantic JSON comparison for structured data responses.

**Use Cases**:
- API-like JSON responses
- Structured data output
- Complex multi-field answers

**Configuration**:
```yaml
scoring_type: "jsonmatch"
expected_response: '{"total": {{csv_count:ID:TARGET_FILE}}, "avg": {{csv_avg:AGE:TARGET_FILE}}}'
```

**Example**:
```yaml
- question_id: 303
  template: "Return customer statistics as JSON with 'total_customers' and 'average_age' keys"
  scoring_type: "jsonmatch"
  expected_response: '{"total_customers": {{csv_count:C_ID:TARGET_FILE}}, "average_age": {{csv_avg:AGE_YRS:TARGET_FILE}}}'
```

**Scoring Logic**:
- Parses both expected and actual responses as JSON
- Performs deep semantic comparison
- Key order independent
- Handles nested objects and arrays
- Type-sensitive (string vs number)

**Success Criteria**: JSON structures match semantically

**Error Details**: Provides specific path-based difference analysis for debugging

---

### `files_exist`

**Purpose**: Verify that specified files have been created by the LLM.

**Use Cases**:
- File creation tasks
- Batch file operations
- Directory population verification

**Configuration**:
```yaml
scoring_type: "files_exist"
files_to_check:
  - "{{artifacts}}/{{entity1}}/data.txt"
  - "{{artifacts}}/logs/{{entity2}}.log"
```

**Example**:
```yaml
- question_id: 101
  template: "Create these files: {{entity1}}.log and {{entity2}}.config in {{artifacts}}/{{entity3}}/"
  scoring_type: "files_exist"
  files_to_check:
    - "{{artifacts}}/{{entity3}}/{{entity1}}.log"
    - "{{artifacts}}/{{entity3}}/{{entity2}}.config"
```

**Scoring Logic**:
- Checks existence of each specified file
- Handles both absolute and relative paths
- Smart path resolution (strips `test_artifacts/` prefix if present)

**Success Criteria**: All specified files must exist

**Path Resolution**:
- Absolute paths: Used directly
- Relative paths: Resolved relative to artifacts directory
- `test_artifacts/` prefix: Automatically stripped

---

### `directory_structure`

**Purpose**: Validate complete directory hierarchies and file structures.

**Use Cases**:
- Complex directory creation
- Project scaffolding verification
- Hierarchical file organization

**Configuration**:
```yaml
scoring_type: "directory_structure"
expected_structure:
  - "{{artifacts}}/{{entity1}}/"
  - "{{artifacts}}/{{entity1}}/logs/"
  - "{{artifacts}}/{{entity1}}/logs/{{entity2}}.log"
  - "{{artifacts}}/{{entity3}}/README.md"
```

**Example**:
```yaml
- question_id: 104
  template: "Create this directory structure: {{expected_structure}}"
  scoring_type: "directory_structure"
  expected_structure:
    - "{{artifacts}}/{{entity1}}/"
    - "{{artifacts}}/{{entity1}}/{{entity2}}/"
    - "{{artifacts}}/{{entity1}}/logs/"
    - "{{artifacts}}/{{entity1}}/logs/{{entity3}}.log"
```

**Scoring Logic**:
- Validates each path in expected_structure list
- Distinguishes files from directories using trailing slash
- Checks both existence and correct type (file vs directory)

**Path Conventions**:
- Directories: Must end with `/`
- Files: No trailing slash
- Both relative and absolute paths supported

**Success Criteria**: All paths exist with correct types

---

### `readfile_stringmatch`

**Purpose**: Read file contents and verify exact text match.

**Use Cases**:
- File content validation
- Text file generation verification
- Specific content requirements

**Configuration**:
```yaml
scoring_type: "readfile_stringmatch"
file_to_read: "{{artifacts}}/{{entity1}}/output.txt"
expected_content: "Hello {{entity2}}!"
```

**Example**:
```yaml
- question_id: 201
  template: "Read {{artifacts}}/notes.txt and tell me line 34. Save to {{artifacts}}/result.txt"
  scoring_type: "readfile_stringmatch"
  file_to_read: "{{artifacts}}/result.txt"
  expected_content: "{{file_line:34:TARGET_FILE}}"
```

**Scoring Logic**:
- Reads specified file contents
- Compares with expected content exactly
- Handles file reading errors gracefully
- Content is whitespace-trimmed

**Success Criteria**: `expected_content == actual_file_content.strip()`

**Error Handling**:
- File not found
- File read permissions
- Encoding issues

---

### `readfile_jsonmatch`

**Purpose**: Read JSON file and perform semantic comparison.

**Use Cases**:
- JSON file generation validation
- Structured data file verification
- Configuration file validation

**Configuration**:
```yaml
scoring_type: "readfile_jsonmatch"
file_to_read: "{{artifacts}}/summary.json"
expected_content: '{"count": {{csv_count:ID:TARGET_FILE}}, "stats": {"avg": {{csv_avg:VALUE:TARGET_FILE}}}}'
```

**Example**:
```yaml
- question_id: 301
  template: "Process {{artifacts}}/data.csv and create JSON summary at {{artifacts}}/summary.json"
  scoring_type: "readfile_jsonmatch"
  file_to_read: "{{artifacts}}/summary.json"
  expected_content: '{"total_customers": {{csv_count:C_ID:TARGET_FILE}}, "average_age": {{csv_avg:AGE_YRS:TARGET_FILE}}}'
```

**Scoring Logic**:
- Reads file as text, then parses as JSON
- Performs semantic JSON comparison (same as `jsonmatch`)
- Handles both file I/O and JSON parsing errors

**Success Criteria**: JSON structures match semantically

**Error Handling**:
- File not found or unreadable
- Invalid JSON in file
- Invalid expected JSON format

---

## Scoring Type Selection Guide

| Task Type | Recommended Scorer | Why |
|-----------|-------------------|-----|
| Simple text response | `stringmatch` | Direct, fast comparison |
| Structured data response | `jsonmatch` | Handles formatting variations |
| File creation | `files_exist` | Verifies basic file operations |
| Directory setup | `directory_structure` | Validates complex hierarchies |
| File content validation | `readfile_stringmatch` | Checks exact file contents |
| JSON file validation | `readfile_jsonmatch` | Semantic JSON file comparison |

## Advanced Features

### Path Resolution
All file-based scorers use intelligent path resolution:
- Absolute paths used directly
- Relative paths resolved from artifacts directory  
- `test_artifacts/` prefix automatically stripped for portability

### Error Reporting
All scorers provide detailed error information:
- Specific failure reasons
- Expected vs actual values
- File system status details
- JSON parsing error locations

### Template Integration
All `expected_content` and `expected_response` fields support:
- Entity substitution (`{{entity1}}`)
- Template functions (`{{csv_count:COLUMN:TARGET_FILE}}`)
- Dynamic answer key generation

---

*Next sections: [Template Functions](#template-functions) and [Sandbox Setup](#sandbox-setup) coming soon...*
