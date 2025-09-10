# PICARD Framework Reference

This document provides detailed reference information for PICARD's core components: scoring types, template functions, and sandbox setup options.

For the list of all supported semantic data types for data generation, see [Data Generation Reference](DATA_GENERATION.md).

## Table of Contents

- [Scoring Types](#scoring-types)
  - [Response Preprocessing](#response-preprocessing)
  - [Special Placeholders](#special-placeholders)
    - [`{{artifacts}}`](#artifacts)
    - [`{{qs_id}}`](#qs_id)
  - [Scoring Type Reference](#scoring-type-reference)
    - [`stringmatch`](#stringmatch) - Direct text comparison
    - [`jsonmatch`](#jsonmatch) - Semantic JSON comparison
    - [`files_exist`](#files_exist) - File existence verification
    - [`directory_structure`](#directory_structure) - Directory hierarchy validation
    - [`readfile_stringmatch`](#readfile_stringmatch) - File content text verification
    - [`readfile_jsonmatch`](#readfile_jsonmatch) - File content JSON verification
  - [Scoring Type Selection Guide](#scoring-type-selection-guide)
  - [Advanced Features](#advanced-features)
- [Enhanced Variable Substitution](#enhanced-variable-substitution)
  - [Overview](#overview-1)
  - [Semantic Variables](#semantic-variables)
  - [Numeric Range Variables](#numeric-range-variables)
  - [Enhanced Entity Pool Variables](#enhanced-entity-pool-variables)
  - [Entity Variables](#entity-variables)
  - [Variable Consistency](#variable-consistency)
  - [Usage Examples](#usage-examples-1)
- [Template Functions](#template-functions)
  - [TARGET_FILE[component_name] Keyword](#target_filecomponent_name-keyword)
  - [File Content Functions](#file-content-functions)
    - [`file_line`](#file_line) - Get specific line number
    - [`file_word`](#file_word) - Get Nth word from file
    - [`file_line_count`](#file_line_count) - Count total lines
    - [`file_word_count`](#file_word_count) - Count total words
  - [CSV Functions](#csv-functions)
    - [Basic CSV Access](#basic-csv-access)
      - [`csv_cell`](#csv_cell) - Get cell by row/column indices
      - [`csv_value`](#csv_value) - Get cell by row/header name
      - [`csv_row`](#csv_row) - Get entire row
      - [`csv_column`](#csv_column) - Get entire column
    - [CSV Aggregation Functions](#csv-aggregation-functions)
      - [`csv_count`](#csv_count) - Count non-empty values
      - [`csv_sum`](#csv_sum) - Sum numeric values
      - [`csv_avg`](#csv_avg) - Average numeric values
    - [CSV Filtered Aggregation](#csv-filtered-aggregation)
      - [`csv_count_where`](#csv_count_where) - Count with filter
      - [`csv_sum_where`](#csv_sum_where) - Sum with filter
      - [`csv_avg_where`](#csv_avg_where) - Average with filter
  - [SQLite Functions](#sqlite-functions)
    - [`sqlite_query`](#sqlite_query) - Execute arbitrary SQL
    - [`sqlite_value`](#sqlite_value) - Get specific value by row/column
  - [JSON Functions](#json-functions)
    - [Basic JSON Access](#basic-json-access)
      - [`json_path`](#json_path) - JSONPath-like extraction
      - [`json_value`](#json_value) - Dot notation navigation
      - [`json_count`](#json_count) - Count array/object elements
      - [`json_keys`](#json_keys) - Extract object keys
    - [JSON Aggregation Functions](#json-aggregation-functions)
      - [`json_sum`](#json_sum) - Sum numeric values with wildcards
      - [`json_avg`](#json_avg) - Average numeric values
      - [`json_max`](#json_max) - Maximum value in array
      - [`json_min`](#json_min) - Minimum value in array
    - [JSON Collection and Filtering](#json-collection-and-filtering)
      - [`json_collect`](#json_collect) - Collect values as comma-separated
      - [`json_count_where`](#json_count_where) - Count with filter conditions
      - [`json_filter`](#json_filter) - Filter and extract values
  - [YAML Functions](#yaml-functions)
    - [Basic YAML Access](#basic-yaml-access)
      - [`yaml_path`](#yaml_path) - JSONPath-like extraction on YAML
      - [`yaml_value`](#yaml_value) - Dot notation navigation
      - [`yaml_count`](#yaml_count) - Count array/object elements
      - [`yaml_keys`](#yaml_keys) - Extract object keys
    - [YAML Aggregation Functions](#yaml-aggregation-functions)
      - [`yaml_sum`](#yaml_sum) - Sum numeric values with wildcards
      - [`yaml_avg`](#yaml_avg) - Average numeric values
      - [`yaml_max`](#yaml_max) - Maximum value in array
      - [`yaml_min`](#yaml_min) - Minimum value in array
    - [YAML Collection and Filtering](#yaml-collection-and-filtering)
      - [`yaml_collect`](#yaml_collect) - Collect values as comma-separated
      - [`yaml_count_where`](#yaml_count_where) - Count with filter conditions
      - [`yaml_filter`](#yaml_filter) - Filter and extract values
  - [XML Functions](#xml-functions)
    - [Basic XML Access](#basic-xml-access)
      - [`xpath_value`](#xpath_value) - Extract text content using XPath
      - [`xpath_attr`](#xpath_attr) - Extract attribute values using XPath
      - [`xpath_count`](#xpath_count) - Count elements matching XPath
      - [`xpath_exists`](#xpath_exists) - Check if XPath matches any elements
    - [XML Collection and Aggregation](#xml-collection-and-aggregation)
      - [`xpath_collect`](#xpath_collect) - Collect all matching text values
      - [`xpath_sum`](#xpath_sum) - Sum numeric values from XPath results
      - [`xpath_avg`](#xpath_avg) - Average numeric values from XPath results
      - [`xpath_max`](#xpath_max) - Maximum value from XPath results
      - [`xpath_min`](#xpath_min) - Minimum value from XPath results
  - [Template Function Examples](#template-function-examples)
  - [Error Handling](#error-handling)
  - [Performance Notes](#performance-notes)
- [Sandbox Setup](#sandbox-setup)
  - [Overview](#overview)
  - [Basic Configuration](#basic-configuration)
  - [Text File Generation (`create_files`)](#text-file-generation-create_files)
    - [Content Types](#content-types)
    - [Clutter Files](#clutter-files)
  - [CSV File Generation (`create_csv`)](#csv-file-generation-create_csv)
    - [Basic CSV Structure](#basic-csv-structure)
    - [Automatic Field Type Detection](#automatic-field-type-detection)
    - [Explicit Field Types](#explicit-field-types)
    - [Advanced CSV Examples](#advanced-csv-examples)
    - [CSV Clutter](#csv-clutter)
  - [SQLite Database Generation (`create_sqlite`)](#sqlite-database-generation-create_sqlite)
    - [Single Table Database](#single-table-database)
    - [Multi-Table Database with Relationships](#multi-table-database-with-relationships)
    - [SQLite Column Specifications](#sqlite-column-specifications)
  - [JSON File Generation (`create_json`)](#json-file-generation-create_json)
    - [Schema-Driven Generation](#schema-driven-generation)
    - [Semantic Data Types](#semantic-data-types)
    - [Complex Nested Structures](#complex-nested-structures)
    - [Array Generation](#array-generation)
    - [Type Constraints](#type-constraints)
  - [YAML File Generation (`create_yaml`)](#yaml-file-generation-create_yaml)
    - [Schema-Driven Generation](#schema-driven-generation-1)
    - [Complex Nested Structures](#complex-nested-structures-1)
    - [Type Constraints and Arrays](#type-constraints-and-arrays)
    - [Semantic Data Types](#semantic-data-types-1)
    - [YAML Formatting Standards](#yaml-formatting-standards)
  - [XML File Generation (`create_xml`)](#xml-file-generation-create_xml)
    - [Schema-Driven Generation](#schema-driven-generation-2)
    - [Element Structure and Attributes](#element-structure-and-attributes)
    - [Complex Nested XML](#complex-nested-xml)
    - [XML Arrays and Collections](#xml-arrays-and-collections)
    - [Semantic Data Types in XML](#semantic-data-types-in-xml)
  - [Advanced Sandbox Features](#advanced-sandbox-features)
  - [Sandbox Best Practices](#sandbox-best-practices)
  - [Error Handling](#error-handling-1)
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
expected_content: "{{csv_count:ID:TARGET_FILE[data_component]}}"
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
expected_response: '{"total": {{csv_count:ID:TARGET_FILE[customer_data]}}, "avg": {{csv_avg:AGE:TARGET_FILE[customer_data]}}}'
```

**Example**:
```yaml
- question_id: 303
  template: "Return customer statistics as JSON with 'total_customers' and 'average_age' keys"
  scoring_type: "jsonmatch"
  expected_response: '{"total_customers": {{csv_count:C_ID:TARGET_FILE[customer_data]}}, "average_age": {{csv_avg:AGE_YRS:TARGET_FILE[customer_data]}}}'
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
  expected_content: "{{file_line:34:TARGET_FILE[notes_file]}}"
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
expected_content: '{"count": {{csv_count:ID:TARGET_FILE[data_file]}}, "stats": {"avg": {{csv_avg:VALUE:TARGET_FILE[data_file]}}}}'
```

**Example**:
```yaml
- question_id: 301
  template: "Process {{artifacts}}/data.csv and create JSON summary at {{artifacts}}/summary.json"
  scoring_type: "readfile_jsonmatch"
  file_to_read: "{{artifacts}}/summary.json"
  expected_content: '{"total_customers": {{csv_count:C_ID:TARGET_FILE[customer_data]}}, "average_age": {{csv_avg:AGE_YRS:TARGET_FILE[customer_data]}}}'
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
- Template functions such as (`{{csv_count:COLUMN:TARGET_FILE[component_name]}}`)
- Dynamic answer key generation with multi-component support

---

## Enhanced Variable Substitution

PICARD's enhanced variable substitution system provides powerful templating capabilities beyond simple entity replacement. It supports semantic data types, numeric ranges, and thematic entity pools while maintaining complete backwards compatibility with existing `{{entity1}}` syntax.

### Overview

The enhanced system supports four types of variables:

- **Semantic Variables**: `{{semantic1:person_name}}`, `{{semantic2:company}}` - Use PICARD's 42 data types
- **Numeric Range Variables**: `{{number1:10:100}}`, `{{number2:1000:5000:currency}}` - Configurable numeric ranges
- **Enhanced Entity Pools**: `{{entity1:colors}}`, `{{entity2:metals}}` - Thematic word groups
- **Entity Variables**: `{{entity1}}`, `{{entity2}}` - Default entity pool words

All variables maintain **consistent referencing** - the same variable produces the same value throughout a test.

### Semantic Variables

Use any of PICARD's 42 semantic data types for realistic, contextual data generation.

**Syntax**: `{{semantic[INDEX]:[DATA_TYPE]}}`

**Examples**:
```yaml
template: "Employee {{semantic1:person_name}} in {{semantic2:department}} earns ${{semantic3:salary}}"
# Result: "Employee Sarah Johnson in Engineering earns $75000"

template: "Contact {{semantic1:person_name}} at {{semantic4:email}} regarding {{semantic2:department}} project"  
# Result: "Contact Sarah Johnson at sarah.johnson@company.com regarding Engineering project"
```

**Available Data Types** (same as CSV/SQLite):
- **People**: `person_name`, `first_name`, `last_name`, `email`
- **Business**: `company`, `department`, `salary`, `product`
- **Location**: `city`, `region`, `phone`
- **Time**: `date`, `age`, `experience`
- **Other**: `status`, `category`, `boolean`, `id`, `price`, `currency`, `course`, `semester`, `score`, `version`, `lorem_word`

See [Data Generation Reference](DATA_GENERATION.md) for the complete list of 42 semantic data types.

### Numeric Range Variables

Generate numbers within specified ranges with different formatting types.

**Syntax**: `{{number[INDEX]:[MIN]:[MAX]:[TYPE]}}`

**Parameters**:
- `INDEX`: Variable index for consistent referencing (1, 2, 3, etc.)
- `MIN`: Minimum value (inclusive)
- `MAX`: Maximum value (inclusive)  
- `TYPE`: Optional formatting type (default: `integer`)

**Number Types**:
- `integer`: Whole numbers (e.g., "42")
- `decimal`: Two decimal places (e.g., "42.75")
- `currency`: Whole numbers for money (e.g., "1500")
- `percentage`: One decimal place (e.g., "87.3")
- `round_hundreds`: Round to nearest 100 (e.g., "47927" → "47900")
- `round_thousands`: Round to nearest 1000 (e.g., "47927" → "48000")
- `round_ten_thousands`: Round to nearest 10,000 (e.g., "47927" → "50000")
- `round_500`: Round to nearest 500 (e.g., "47927" → "48000")
- `round_250`: Round to nearest 250 (e.g., "47927" → "48000")

**Examples**:
```yaml
# Basic numeric variables
template: "Score: {{number1:60:100}}% with budget ${{number2:1000:5000:currency}}"
# Result: "Score: 87% with budget $3250"

template: "Success rate: {{number1:85:99:percentage}}% over {{number2:30:180}} days"
# Result: "Success rate: 92.4% over 127 days"

template: "Price: ${{number1:25:500:decimal}} with {{number2:5:15}} day shipping"
# Result: "Price: $127.85 with 8 day shipping"

# Rounded number examples for enterprise scenarios
template: "Employee {{semantic1:person_name}} earns ${{number1:40000:80000:round_thousands}} annually"
# Result: "Employee John Smith earns $67000 annually"

template: "Budget {{number1:150000:300000:round_ten_thousands}} with {{number2:1000:5000:round_500}} contingency"
# Result: "Budget 250000 with 3500 contingency"

template: "Quarterly target ${{number1:25000:75000:round_hundreds}} vs actual ${{number2:20000:80000:round_250}}"
# Result: "Quarterly target $47900 vs actual $48000"
```

**Rounded Number Use Cases**:
- **Enterprise modeling**: Budgets, thresholds, and limits often use round numbers in real business contexts
- **SQL testing**: Expose pattern-matching weaknesses where LLMs confuse rounded amounts with ID fields
- **Realistic scenarios**: Model genuine business scenarios that naturally use round numbers
- **PICARD validation**: Test both round and non-round scenarios to identify model failure modes

### Enhanced Entity Pool Variables

Use thematic word groups for more contextual and realistic scenarios.

**Syntax**: `{{entity[INDEX]:[POOL]}}`

**Available Pools**:
- `colors`: crimson, azure, amber, emerald, golden, silver, red, blue, green, yellow, orange, purple
- `metals`: silver, golden, copper, platinum, iron, bronze, steel, titanium, chrome, aluminum, zinc, nickel  
- `gems`: emerald, crystal, diamond, pearl, sapphire, ruby, amber, opal, topaz, amethyst, garnet, onyx
- `nature`: mountain, forest, river, canyon, valley, meadow, ocean, desert, prairie, creek, lake, beach

**Examples**:
```yaml
template: "Deploy {{entity1:colors}} server with {{entity2:metals}} backup"
# Result: "Deploy crimson server with platinum backup"

template: "Process {{entity1:gems}}_data.csv using {{entity2:nature}}_algorithm"  
# Result: "Process emerald_data.csv using mountain_algorithm"

template: "Create {{entity1:colors}} theme with {{entity2:metals}} accents"
# Result: "Create azure theme with bronze accents"
```

### Entity Variables

Use words from PICARD's default entity pool.

**Syntax**: `{{entity[INDEX]}}`

**Examples**:
```yaml
template: "Process {{entity1}} file and backup {{entity2}} data"
# Result: "Process harbor file and backup crystal data"

template: "Archive {{entity1}} logs to {{entity2}}_backup"
# Result: "Archive summit logs to canyon_backup"
```

### Variable Consistency

**Critical Feature**: The same variable produces the same value throughout a test, enabling consistent referencing across templates, expected values, and sandbox files.

**Example Test**:
```yaml
question_id: 501
template: "Create summary for {{semantic1:person_name}} in {{semantic2:department}} with budget ${{number1:50000:100000:round_thousands}}"
scoring_type: "readfile_jsonmatch"
file_to_read: "{{artifacts}}/summary.json"
expected_content: |
  {
    "employee": "{{semantic1:person_name}}",
    "department": "{{semantic2:department}}",
    "budget": {{number1:50000:100000:round_thousands}},
    "status": "active"
  }
```

**Consistency Rules**:
- `{{semantic1:person_name}}` produces the same name in template and expected_content
- `{{number1:50000:100000:round_thousands}}` produces the same rounded amount in both places
- Different indexes produce different values: `{{semantic1:person_name}}` ≠ `{{semantic2:person_name}}`
- Same index with different types: `{{entity1:colors}}` ≠ `{{entity1:metals}}`
- Same index with different number types: `{{number1:50000:100000:currency}}` ≠ `{{number1:50000:100000:round_thousands}}`

### Usage Examples

**Mixed Variable Types**:
```yaml
template: "Employee {{semantic1:person_name}} in {{semantic2:department}} earns ${{number1:30000:80000:round_thousands}} working on {{entity1:colors}} project with {{entity2}} tools"
# Result: "Employee John Smith in Engineering earns $65000 working on crimson project with harbor tools"
```

**Business Scenario**:
```yaml
template: "Assign {{semantic1:person_name}} to {{entity1:colors}} project with budget ${{number1:10000:50000:round_thousands}} due in {{number2:30:180}} days"
# Result: "Assign Alice Chen to azure project with budget $32000 due in 127 days"
```

**System Configuration**:
```yaml
template: "Deploy {{entity1:metals}} server for {{semantic1:company}} with {{number1:8:64}} GB RAM and timeout {{number2:30:300}} seconds"
# Result: "Deploy platinum server for TechCorp with 32 GB RAM and timeout 120 seconds"
```

**Mixed Variable Types**:
```yaml
# Different variable types can be used together
template: "Migrate {{entity1}} database to {{entity2:gems}} cluster using {{semantic1:person_name}} credentials"
# Result: "Migrate harbor database to emerald cluster using Sarah Johnson credentials"
```

**Enterprise Rounded Number Scenarios**:
```yaml
# Budget planning with multiple rounding types
template: "Department {{semantic1:department}} budget: ${{number1:100000:500000:round_ten_thousands}} total, ${{number2:5000:25000:round_thousands}} monthly, ${{number3:500:2500:round_250}} discretionary"
# Result: "Department Engineering budget: $400000 total, $18000 monthly, $1750 discretionary"

# SQL testing scenario - rounded amounts vs ID confusion  
template: "Find orders above ${{number1:40000:80000:round_thousands}} threshold for customer {{number2:100:999}} in Q{{number3:1:4}}"
# Result: "Find orders above $67000 threshold for customer 445 in Q2"
# Tests LLM's ability to distinguish rounded amounts from customer IDs

# Variable consistency with rounded numbers
template: "Budget approval: ${{number1:200000:600000:round_hundreds}} allocated, ${{number1:200000:600000:round_hundreds}} confirmed"
# Result: "Budget approval: $347900 allocated, $347900 confirmed" (same rounded value)
```

---

## Template Functions

Template functions enable dynamic answer key generation by extracting data from files created during test execution. They use the format `{{function_name:arg1:arg2:...}}` and are evaluated at runtime to create deterministic expected responses.

### TARGET_FILE[component_name] Keyword

Template functions use `TARGET_FILE[component_name]` syntax to reference files from specific sandbox components. This enables multi-component scenarios and precise file targeting:

```yaml
sandbox_setup:
  components:
    - type: "create_csv"
      name: "customer_data"
      target_file: "{{artifacts}}/{{qs_id}}/customers.csv"
      content:
        headers: ["ID", "NAME", "AGE"]
        rows: 50
    - type: "create_json" 
      name: "config_data"
      target_file: "{{artifacts}}/{{qs_id}}/config.json"
      content:
        schema:
          total_customers: "{{csv_count:ID:TARGET_FILE[customer_data]}}"
          settings:
            debug: "boolean"

expected_content: "{{json_value:total_customers:TARGET_FILE[config_data]}}"
```

**Component Requirements**:
- All components **must** have a unique `name` field
- Use `TARGET_FILE[component_name]` to reference specific component files
- Component names must match regex `^[a-zA-Z][a-zA-Z0-9_-]*$` (max 50 chars)

---

### File Content Functions

Extract specific content from text files.

#### `file_line`
**Purpose**: Get a specific line number from a text file.
**Usage**: `{{file_line:line_number:file_path}}`
**Parameters**:
- `line_number`: Line number (1-based indexing)
- `file_path`: Path to text file (or `TARGET_FILE[component_name]`)

**Example**:
```yaml
template: "What does line 34 say in {{artifacts}}/notes.txt?"
expected_response: "{{file_line:34:TARGET_FILE[notes_file]}}"
sandbox_setup:
  components:
    - type: "create_files"
      name: "notes_file"
      target_file: "{{artifacts}}/notes.txt"
      content:
        type: "lorem_lines"
        count: 100
```

#### `file_word`
**Purpose**: Get the Nth word from entire file content.
**Usage**: `{{file_word:word_number:file_path}}`
**Parameters**:
- `word_number`: Word number (1-based indexing)
- `file_path`: Path to text file

**Example**:
```yaml
expected_response: "{{file_word:35:TARGET_FILE[document]}}"
# Returns the 35th word in the file
```

#### `file_line_count`
**Purpose**: Count total lines in a text file.
**Usage**: `{{file_line_count:file_path}}`

#### `file_word_count`
**Purpose**: Count total words in a text file.
**Usage**: `{{file_word_count:file_path}}`

---

### CSV Functions

Extract and process data from CSV files with headers.

#### Basic CSV Access

##### `csv_cell`
**Purpose**: Get specific cell by row and column indices.
**Usage**: `{{csv_cell:row:column:file_path}}`
**Parameters**:
- `row`: Row number (0-based, 0 = header row)
- `column`: Column number (0-based)

**Example**:
```yaml
# Get first data row, second column
expected_response: "{{csv_cell:1:1:TARGET_FILE[csv_data]}}"
```

##### `csv_value`
**Purpose**: Get cell by row number and column header name.
**Usage**: `{{csv_value:row:header:file_path}}`
**Parameters**:
- `row`: Data row number (0-based, excludes header)
- `header`: Column header name

**Example**:
```yaml
# Get age of first customer (row 0, "AGE" column)
expected_content: "{{csv_value:0:AGE:TARGET_FILE[customers]}}"
```

##### `csv_row`

**Description**: Extract an entire row from CSV as comma-separated values  
**Usage**: `{{csv_row:row_number:file_path}}`

Returns the complete row at the specified index (0-based) as a comma-separated string. Useful for getting all data associated with a specific record.

**Examples**:
```yaml
# Get first data row (row 0, after headers)
template: "First employee: {{csv_row:0:TARGET_FILE[data_file]}}"
expected_response: "First employee: {{csv_row:0:TARGET_FILE[data_file]}}"

# Get last row using dynamic count
template: "Row contents: {{csv_row:{{csv_count:NAME:TARGET_FILE[data_file]}}-1:TARGET_FILE[data_file]}}"
expected_response: "Row contents: {{csv_row:{{csv_count:NAME:TARGET_FILE[data_file]}}-1:TARGET_FILE[data_file]}}"
```

##### `csv_column`

**Description**: Extract an entire column from CSV as comma-separated values  
**Usage**: `{{csv_column:header:file_path}}`

Returns all values from the specified column as a comma-separated string. Column order matches the original CSV row order.

**Examples**:
```yaml
# Get all employee names
template: "All employees: {{csv_column:NAME:TARGET_FILE[data_file]}}"
expected_response: "All employees: {{csv_column:NAME:TARGET_FILE[data_file]}}"

# Get all salaries for analysis
template: "Salary data: {{csv_column:SALARY:TARGET_FILE[data_file]}}"
expected_response: "Salary data: {{csv_column:SALARY:TARGET_FILE[data_file]}}"
```

**Note**: Both functions preserve data order and formatting from the original CSV file.

#### CSV Aggregation Functions

##### `csv_count`
**Purpose**: Count non-empty values in a column.
**Usage**: `{{csv_count:column:file_path}}`

**Example**:
```yaml
expected_content: '{"total_customers": {{csv_count:C_ID:TARGET_FILE[data_file]}}}'
# Counts non-empty values in C_ID column
```

##### `csv_sum`
**Purpose**: Sum all numeric values in a column.
**Usage**: `{{csv_sum:column:file_path}}`

##### `csv_avg`
**Purpose**: Average all numeric values in a column.
**Usage**: `{{csv_avg:column:file_path}}`

**Example**:
```yaml
expected_content: '{"avg_age": {{csv_avg:AGE_YRS:TARGET_FILE[data_file]}}}'
```

#### CSV Filtered Aggregation

Advanced functions that apply filters before aggregation.

##### `csv_count_where`
**Purpose**: Count rows matching a filter condition.
**Usage**: `{{csv_count_where:column:filter_column:operator:value:file_path}}`

**Parameters**:
- `column`: Column to count (usually same as filter_column)
- `filter_column`: Column to apply filter on
- `operator`: Comparison operator (`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `startswith`, `endswith`)
- `value`: Value to compare against

**Example**:
```yaml
# Count Engineering department employees
expected_content: "{{csv_count_where:EMP_ID:DEPT_CD:==:Engineering:TARGET_FILE[data_file]}}"

# Count high earners
expected_content: "{{csv_count_where:EMP_ID:SALARY:>:50000:TARGET_FILE[data_file]}}"
```

##### `csv_sum_where`
**Purpose**: Sum values in a column where filter condition is met.
**Usage**: `{{csv_sum_where:column:filter_column:operator:value:file_path}}`

**Example**:
```yaml
# Total salary for Engineering department
expected_content: "{{csv_sum_where:SAL_AMT:DEPT_CD:==:Engineering:TARGET_FILE[data_file]}}"
```

##### `csv_avg_where`
**Purpose**: Average values in a column where filter condition is met.
**Usage**: `{{csv_avg_where:column:filter_column:operator:value:file_path}}`

**Supported Operators**:
- **Equality**: `==`, `!=`
- **Numeric comparison**: `>`, `<`, `>=`, `<=` (tries numeric first, falls back to string)
- **String operations**: `contains`, `startswith`, `endswith`

---

### SQLite Functions

Execute SQL queries against SQLite databases.

#### `sqlite_query`
**Purpose**: Execute arbitrary SQL query and return first result.
**Usage**: `{{sqlite_query:sql_statement:file_path}}`

**Parameters**:
- `sql_statement`: Complete SQL query
- `file_path`: Path to SQLite database file

**Example**:
```yaml
expected_content: "{{sqlite_query:SELECT COUNT(*) FROM enterprise_orders o JOIN enterprise_customers c ON o.CUST_REF = c.CUST_ID WHERE c.DEPT_CD = 'Engineering' AND o.ORD_AMT > 50000:TARGET_FILE[data_file]}}"
```

**Return Value**: First column of first result row as string

#### `sqlite_value`
**Purpose**: Get specific value by row and column from a table.
**Usage**: `{{sqlite_value:row:column:file_path}}` or `{{sqlite_value:row:column:table:file_path}}`

**Parameters**:
- `row`: Row number (0-based)
- `column`: Column name or index
- `table`: Table name (optional, uses first table if omitted)
- `file_path`: Path to SQLite database

---

### JSON Functions

Extract and process data from JSON files with powerful querying, aggregation, and filtering capabilities.

#### Basic JSON Access

##### `json_path`
**Purpose**: Extract values using JSONPath-like syntax.
**Usage**: `{{json_path:$.path.to.value:file_path}}`

**Parameters**:
- `path_expression`: JSONPath-like expression (e.g., `$.users[0].name`)
- `file_path`: Path to JSON file

**Examples**:
```yaml
# Get employee name
expected_response: "{{json_path:$.employee.name:TARGET_FILE[data_file]}}"

# Get first project budget
expected_response: "{{json_path:$.employee.projects[0].budget:TARGET_FILE[data_file]}}"

# Get nested contact info
expected_response: "{{json_path:$.employee.manager.contact.phone:TARGET_FILE[data_file]}}"
```

##### `json_value`
**Purpose**: Navigate JSON using simple dot notation.
**Usage**: `{{json_value:key1.key2[0]:file_path}}`

**Parameters**:
- `key_path`: Dot notation path (e.g., `employee.manager.email`)
- `file_path`: Path to JSON file

**Example**:
```yaml
expected_response: "{{json_value:employee.manager.email:TARGET_FILE[data_file]}}"
```

##### `json_count`
**Purpose**: Count elements in JSON arrays or object keys.
**Usage**: `{{json_count:$.path.to.array:file_path}}`

**Example**:
```yaml
# Count total projects
expected_response: "{{json_count:$.employee.projects:TARGET_FILE[data_file]}}"
```

##### `json_keys`
**Purpose**: Extract object keys as comma-separated string.
**Usage**: `{{json_keys:$.path.to.object:file_path}}`

**Example**:
```yaml
# Get all employee object keys
expected_response: "{{json_keys:$.employee:TARGET_FILE[data_file]}}"
# Result: "name,email,department,manager,projects"
```

#### JSON Aggregation Functions

Perform mathematical operations on arrays using wildcard notation.

##### `json_sum`
**Purpose**: Sum all numeric values in an array.
**Usage**: `{{json_sum:$.array[*].field:file_path}}`

**Example**:
```yaml
# Total project budgets
expected_response: "{{json_sum:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
```

##### `json_avg`
**Purpose**: Calculate average of numeric values.
**Usage**: `{{json_avg:$.array[*].field:file_path}}`

**Example**:
```yaml
# Average project budget
expected_response: "{{json_avg:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
```

##### `json_max`
**Purpose**: Find maximum value in array.
**Usage**: `{{json_max:$.array[*].field:file_path}}`

##### `json_min`
**Purpose**: Find minimum value in array.
**Usage**: `{{json_min:$.array[*].field:file_path}}`

#### JSON Collection and Filtering

Advanced functions for gathering and filtering data.

##### `json_collect`
**Purpose**: Collect values into comma-separated string.
**Usage**: `{{json_collect:$.array[*].field:file_path}}`

**Examples**:
```yaml
# Get all project names
expected_response: "{{json_collect:$.employee.projects[*].name:TARGET_FILE[data_file]}}"
# Result: "Widget Pro,Super Gadget"

# Get all team members across projects  
expected_response: "{{json_collect:$.employee.projects[*].team[*]:TARGET_FILE[data_file]}}"
# Result: "Alice,Bob,Charlie,Diana,Eve"
```

##### `json_count_where`
**Purpose**: Count array elements matching filter condition.
**Usage**: `{{json_count_where:$.array[?field>value]:file_path}}`

**Filter Operators**:
- **Numeric**: `>`, `<`, `>=`, `<=`, `==`, `!=`
- **String**: `contains`, `startswith`, `endswith`

**Examples**:
```yaml
# Count high-budget projects
expected_response: "{{json_count_where:$.employee.projects[?budget>60000]:TARGET_FILE[data_file]}}"

# Count Engineering employees
expected_response: "{{json_count_where:$.employees[?department==Engineering]:TARGET_FILE[data_file]}}"
```

##### `json_filter`
**Purpose**: Filter array and extract values from matching elements.
**Usage**: `{{json_filter:$.array[?condition].field:file_path}}`

**Examples**:
```yaml
# Get names of high-budget projects
expected_response: "{{json_filter:$.employee.projects[?budget>60000].name:TARGET_FILE[data_file]}}"

# Get emails of senior developers
expected_response: "{{json_filter:$.employees[?level==senior].email:TARGET_FILE[data_file]}}"
```

#### Advanced JSON Examples

**Complex Enterprise Analysis**:
```yaml
question_id: 501
template: "What's the total budget for Engineering department projects?"
expected_response: "{{json_sum:$.departments[?name==Engineering].projects[*].budget:TARGET_FILE[data_file]}}"

question_id: 502
template: "List all senior team members across high-priority projects"
expected_response: "{{json_collect:$.projects[?priority==high].team[?role==senior].name:TARGET_FILE[data_file]}}"
```

**Multi-Level Aggregation**:
```yaml
question_id: 503
template: "What's the average team size for projects over $50k?"
# Note: Uses nested aggregation - sum team sizes, then average
expected_response: "{{json_avg:$.projects[?budget>50000].team_size:TARGET_FILE[data_file]}}"
```

**Wildcard Support**:
- **Single level**: `$.projects[*].budget`
- **Multi-level**: `$.departments[*].teams[*].members[*].name`
- **With filtering**: `$.projects[?active==true][*].budget`

---

## XML Functions

XML template functions use XPath expressions to navigate and extract data from XML files. All functions support TARGET_FILE keyword substitution.

### Basic XML Access

#### `xpath_value`
**Usage**: `{{xpath_value:xpath:file.xml}}`  
**Purpose**: Extract text content from XML using XPath

```xml
<!-- example.xml -->
<config>
  <database>
    <host>localhost</host>
    <port>5432</port>
  </database>
  <users>
    <user id="1">John</user>
    <user id="2">Alice</user>
  </users>
</config>
```

Examples:
- `{{xpath_value:database/host:example.xml}}` → `"localhost"`
- `{{xpath_value:database/port:example.xml}}` → `"5432"`
- `{{xpath_value:users/user[1]:example.xml}}` → `"John"`

#### `xpath_attr`
**Usage**: `{{xpath_attr:xpath@attribute:file.xml}}`  
**Purpose**: Extract attribute values from XML elements

Examples using the XML above:
- `{{xpath_attr:users/user[1]@id:example.xml}}` → `"1"`
- `{{xpath_attr:users/user[2]@id:example.xml}}` → `"2"`

#### `xpath_count`
**Usage**: `{{xpath_count:xpath:file.xml}}`  
**Purpose**: Count elements matching XPath expression

Examples:
- `{{xpath_count:users/user:example.xml}}` → `"2"`
- `{{xpath_count:database/*:example.xml}}` → `"2"` (host and port)

#### `xpath_exists`
**Usage**: `{{xpath_exists:xpath:file.xml}}`  
**Purpose**: Check if XPath matches any elements (returns "true" or "false")

Examples:
- `{{xpath_exists:database/host:example.xml}}` → `"true"`
- `{{xpath_exists:database/password:example.xml}}` → `"false"`
- `{{xpath_exists:users/user[@id='1']:example.xml}}` → `"true"`

### XML Collection and Aggregation

#### `xpath_collect`
**Usage**: `{{xpath_collect:xpath:file.xml}}`  
**Purpose**: Collect all text values from matching elements as comma-separated string

```xml
<!-- products.xml -->
<catalog>
  <product>
    <name>Widget A</name>
    <price>29.99</price>
    <category>Tools</category>
  </product>
  <product>
    <name>Widget B</name>
    <price>49.99</price>
    <category>Electronics</category>
  </product>
</catalog>
```

Examples:
- `{{xpath_collect:product/name:products.xml}}` → `"Widget A,Widget B"`
- `{{xpath_collect:product/category:products.xml}}` → `"Tools,Electronics"`

#### Numeric Aggregation Functions

**Usage**: 
- `{{xpath_sum:xpath:file.xml}}` - Sum numeric values
- `{{xpath_avg:xpath:file.xml}}` - Average numeric values  
- `{{xpath_max:xpath:file.xml}}` - Maximum value
- `{{xpath_min:xpath:file.xml}}` - Minimum value

Examples using products.xml:
- `{{xpath_sum:product/price:products.xml}}` → `"79.98"`
- `{{xpath_avg:product/price:products.xml}}` → `"39.99"`
- `{{xpath_max:product/price:products.xml}}` → `"49.99"`
- `{{xpath_min:product/price:products.xml}}` → `"29.99"`

#### Advanced XPath Expressions

XML functions support standard XPath syntax including:

**Element navigation**:
- `database/host` - Direct child access
- `//user` - Descendant search anywhere in document
- `users/user[1]` - First user element
- `users/user[last()]` - Last user element

**Attribute filtering**:
- `user[@id='1']` - User with specific ID
- `product[@category='Electronics']` - Products in Electronics category
- `item[@active='true']` - Active items only

**Complex expressions**:
- `departments/department[budget>100000]/name` - High-budget department names
- `employees/employee[salary>50000 and department='Engineering']` - Well-paid engineers
- `projects/project[status='active']/team/member` - Active project team members

#### Error Handling

XML functions provide clear error messages for common issues:
- **File not found**: `XML file not found: /path/to/file.xml`
- **Invalid XPath**: `XPath 'invalid/path' not found in XML`
- **Missing attributes**: `Attribute 'missing_attr' not found on element`
- **Malformed XML**: `Invalid XML file: syntax error at line X`

---

## YAML Functions

YAML functions enable extraction and analysis of data from YAML files using JSONPath-like syntax. These functions work seamlessly with YAML's hierarchical structure and support all data types and operations available in JSON functions.

### Basic YAML Access

#### `yaml_path`

**Description**: Extract values from YAML using JSONPath-like expressions  
**Usage**: `{{yaml_path:$.path.to.value:file_path}}`

**Examples**:
```yaml
template: "Database host is {{yaml_path:$.database.host:TARGET_FILE[data_file]}}"
expected_response: "Database host is {{yaml_path:$.database.host:TARGET_FILE[data_file]}}"

template: "First user is {{yaml_path:$.users[0].name:TARGET_FILE[data_file]}}"
expected_response: "First user is {{yaml_path:$.users[0].name:TARGET_FILE[data_file]}}"

template: "Manager email is {{yaml_path:$.employee.manager.contact.email:TARGET_FILE[data_file]}}"
expected_response: "Manager email is {{yaml_path:$.employee.manager.contact.email:TARGET_FILE[data_file]}}"
```

#### `yaml_value`

**Description**: Navigate YAML structure using dot notation  
**Usage**: `{{yaml_value:key1.key2[0]:file_path}}`

Simple navigation for nested YAML structures:

```yaml
template: "Manager email: {{yaml_value:employee.manager.email:TARGET_FILE[data_file]}}"
expected_response: "Manager email: {{yaml_value:employee.manager.email:TARGET_FILE[data_file]}}"
```

#### `yaml_count`

**Description**: Count elements in YAML arrays or objects  
**Usage**: `{{yaml_count:$.path.to.array:file_path}}`

```yaml
template: "Total projects: {{yaml_count:$.employee.projects:TARGET_FILE[data_file]}}"
expected_response: "Total projects: {{yaml_count:$.employee.projects:TARGET_FILE[data_file]}}"
```

#### `yaml_keys`

**Description**: Extract keys from YAML objects  
**Usage**: `{{yaml_keys:$.path.to.object:file_path}}`

```yaml
template: "Available fields: {{yaml_keys:$.employee:TARGET_FILE[data_file]}}"
expected_response: "Available fields: {{yaml_keys:$.employee:TARGET_FILE[data_file]}}"
```

### YAML Aggregation Functions

#### `yaml_sum`

**Description**: Sum numeric values from YAML arrays using wildcards  
**Usage**: `{{yaml_sum:$.array[*].field:file_path}}`

```yaml
template: "Total budget: ${{yaml_sum:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
expected_response: "Total budget: ${{yaml_sum:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
```

#### `yaml_avg`

**Description**: Calculate average of numeric values  
**Usage**: `{{yaml_avg:$.array[*].field:file_path}}`

```yaml
template: "Average budget: ${{yaml_avg:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
expected_response: "Average budget: ${{yaml_avg:$.employee.projects[*].budget:TARGET_FILE[data_file]}}"
```

#### `yaml_max`

**Description**: Find maximum value in YAML array  
**Usage**: `{{yaml_max:$.array[*].field:file_path}}`

#### `yaml_min`

**Description**: Find minimum value in YAML array  
**Usage**: `{{yaml_min:$.array[*].field:file_path}}`

**Examples**:
```yaml
# Using employees.yaml with salary data
template: "Salary range: ${{yaml_min:$.employees[*].salary:TARGET_FILE[data_file]}} - ${{yaml_max:$.employees[*].salary:TARGET_FILE[data_file]}}"
expected_response: "Salary range: ${{yaml_min:$.employees[*].salary:TARGET_FILE[data_file]}} - ${{yaml_max:$.employees[*].salary:TARGET_FILE[data_file]}}"
```

### YAML Collection and Filtering

#### `yaml_collect`

**Description**: Collect values as comma-separated list  
**Usage**: `{{yaml_collect:$.array[*].field:file_path}}`

```yaml
template: "Project names: {{yaml_collect:$.employee.projects[*].name:TARGET_FILE[data_file]}}"
expected_response: "Project names: {{yaml_collect:$.employee.projects[*].name:TARGET_FILE[data_file]}}"

template: "All team members: {{yaml_collect:$.employee.projects[*].team[*]:TARGET_FILE[data_file]}}"
expected_response: "All team members: {{yaml_collect:$.employee.projects[*].team[*]:TARGET_FILE[data_file]}}"
```

#### `yaml_count_where`

**Description**: Count elements matching filter conditions  
**Usage**: `{{yaml_count_where:$.array[?field>value]:file_path}}`

**Filter Operators**: `>`, `<`, `>=`, `<=`, `==`, `!=`

```yaml
template: "High-budget projects: {{yaml_count_where:$.employee.projects[?budget>60000]:TARGET_FILE[data_file]}}"
expected_response: "High-budget projects: {{yaml_count_where:$.employee.projects[?budget>60000]:TARGET_FILE[data_file]}}"

template: "Engineering staff: {{yaml_count_where:$.employees[?department==Engineering]:TARGET_FILE[data_file]}}"
expected_response: "Engineering staff: {{yaml_count_where:$.employees[?department==Engineering]:TARGET_FILE[data_file]}}"
```

#### `yaml_filter`

**Description**: Filter and extract specific values based on conditions  
**Usage**: `{{yaml_filter:$.array[?condition].field:file_path}}`

```yaml
template: "High-value projects: {{yaml_filter:$.employee.projects[?budget>60000].name:TARGET_FILE[data_file]}}"
expected_response: "High-value projects: {{yaml_filter:$.employee.projects[?budget>60000].name:TARGET_FILE[data_file]}}"

template: "Senior emails: {{yaml_filter:$.employees[?level==senior].email:TARGET_FILE[data_file]}}"
expected_response: "Senior emails: {{yaml_filter:$.employees[?level==senior].email:TARGET_FILE[data_file]}}"
```

### Advanced YAML Processing

#### Complex Filtering and Aggregation

```yaml
# Complex department budget analysis
template: "Engineering budget total: ${{yaml_sum:$.departments[?name==Engineering].projects[*].budget:TARGET_FILE[data_file]}}"
expected_response: "Engineering budget total: ${{yaml_sum:$.departments[?name==Engineering].projects[*].budget:TARGET_FILE[data_file]}}"

template: "Senior team leads: {{yaml_collect:$.projects[?priority==high].team[?role==senior].name:TARGET_FILE[data_file]}}"
expected_response: "Senior team leads: {{yaml_collect:$.projects[?priority==high].team[?role==senior].name:TARGET_FILE[data_file]}}"
```

#### Multi-Level Aggregation

```yaml
# Calculate average budget for high-value projects
template: "Average high-value budget: ${{yaml_avg:$.projects[?budget>50000].team_size:TARGET_FILE[data_file]}}"
expected_response: "Average high-value budget: ${{yaml_avg:$.projects[?budget>50000].team_size:TARGET_FILE[data_file]}}"
```

### YAML Path Expressions

YAML functions support advanced path expressions including:

**Array navigation**:
- `employees[0]` - First employee
- `employees[*]` - All employees
- `employees[-1]` - Last employee

**Nested access**:
- `department.teams[*].lead` - All team leads in department
- `projects[*].members[?role==developer]` - All developers across projects

**Filtering**:
- `employees[?salary>75000]` - High-paid employees
- `projects[?status==active and priority==high]` - Active high-priority projects
- `teams[?size>=5].members[*]` - Members of large teams

#### Error Handling

YAML functions provide clear error messages for common issues:
- **File not found**: `YAML file not found: /path/to/file.yaml`
- **Invalid path**: `YAML path '$.invalid.path' not found`
- **Parse errors**: `Invalid YAML file: syntax error at line X`
- **Type errors**: `Cannot perform numeric operation on non-numeric value`

---

### Template Function Examples

#### Complex CSV Processing
```yaml
question_id: 301
template: "Create JSON summary with total customers and average age"
expected_content: |
  {
    "total_customers": {{csv_count:C_ID:TARGET_FILE[customer_data]}},
    "average_age": {{csv_avg:AGE_YRS:TARGET_FILE[customer_data]}},
    "engineering_count": {{csv_count_where:C_ID:DEPT_CD:==:Engineering:TARGET_FILE[customer_data]}},
    "high_earner_avg_age": {{csv_avg_where:AGE_YRS:SALARY:>:60000:TARGET_FILE[customer_data]}}
  }
sandbox_setup:
  components:
    - type: "create_csv"
      name: "customer_data"
      target_file: "{{artifacts}}/{{qs_id}}/customers.csv"
      content:
        headers: ["C_ID", "AGE_YRS", "DEPT_CD", "SALARY"]
        rows: 100
```

#### Database Query with Business Logic
```yaml
question_id: 402
template: "How many high-value orders from Engineering customers?"
expected_content: "{{sqlite_query:SELECT COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.department = 'Engineering' AND o.amount > 50000:TARGET_FILE[data_file]}}"
```

#### File Content Needle-in-Haystack
```yaml
question_id: 201
template: "Find the 35th word in the generated document"
expected_response: "{{file_word:35:TARGET_FILE[document]}}"
sandbox_setup:
  components:
    - type: "create_files"
      name: "document"
      target_file: "{{artifacts}}/{{qs_id}}/document.txt"
      content:
        type: "lorem_lines"
        count: 100
```

### Error Handling

Template functions provide detailed error messages:
- **File not found**: Clear path information
- **Invalid parameters**: Parameter validation with suggestions
- **CSV/SQL errors**: Column/table not found with available options
- **Type errors**: Numeric conversion failures in aggregation functions

### Performance Notes

- **CSV functions**: Load entire file into memory (suitable for test-sized data)
- **SQLite functions**: Use database connections (better for larger datasets)
- **File functions**: Stream-read for better memory efficiency
- **Caching**: Functions re-read files on each call (acceptable for test scenarios)

---

## Sandbox Setup

The sandbox setup system creates realistic test environments by generating files, databases, and directory structures dynamically. Each test gets isolated data that prevents memorization while testing genuine agentic capabilities.

### Overview

Sandbox setup operates through four main generator types:
- **`create_files`**: Text files with lorem ipsum content
- **`create_csv`**: CSV files with realistic business data
- **`create_sqlite`**: SQLite databases with tables and relationships
- **`create_json`**: JSON files with schema-driven structured data
- **`create_yaml`**: YAML files with consistent block-style formatting

### Basic Configuration

**Multi-Component Setup**:
```yaml
sandbox_setup:
  components:
    - type: "create_csv"                        # Generator type
      name: "main_data"                        # Required: component name
      target_file: "{{artifacts}}/{{qs_id}}/data.csv"  # Output file path
      content:                                 # Content specification
        headers: ["ID", "NAME", "AGE", "CITY"]
        rows: 50
    - type: "create_json"
      name: "config_file"
      target_file: "{{artifacts}}/{{qs_id}}/config.json"
      content:
        schema:
          total_records: "{{csv_count:ID:TARGET_FILE[main_data]}}"
```

**Single Component Setup**:
```yaml
sandbox_setup:
  type: "create_csv" 
  name: "data_component"                       # Required: component name
  target_file: "{{artifacts}}/{{qs_id}}/data.csv"
  content:
    headers: ["ID", "NAME", "AGE", "CITY"]
    rows: 50
```

---

### Text File Generation (`create_files`)

Creates text files with lorem ipsum content for reading and processing tasks.

#### Content Types

##### `lorem_lines`
```yaml
sandbox_setup:
  type: "create_files"
  target_file: "{{artifacts}}/{{qs_id}}/notes.txt"
  content:
    type: "lorem_lines"
    count: 100                    # Generate 100 lines of text
```

##### `lorem_sentences`
```yaml
content:
  type: "lorem_sentences"
  count: 20                       # Generate 20 sentences
```

##### `lorem_paragraphs`
```yaml
content:
  type: "lorem_paragraphs"
  count: 5                        # Generate 5 paragraphs
```

##### `lorem_words`
```yaml
content:
  type: "lorem_words"
  count: 500                      # Generate 500 words
```

##### `custom` with Placeholders
```yaml
content:
  type: "custom"
  content: |
    Document Header
    {{lorem:10l}}                 # 10 lines
    
    Section 2
    {{lorem:5s}}                  # 5 sentences
    
    Footer
    {{lorem:3p}}                  # 3 paragraphs
```

**Placeholder Formats**:
- `{{lorem:Nl}}` - N lines
- `{{lorem:Ns}}` - N sentences  
- `{{lorem:Np}}` - N paragraphs

#### Clutter Files

Add realistic "noise" files to simulate authentic environments:

```yaml
sandbox_setup:
  type: "create_files"
  target_file: "{{artifacts}}/{{qs_id}}/main.txt"
  content:
    type: "lorem_lines"
    count: 50
  config:
    clutter:
      count: 5                      # Generate 5 random clutter files
      pattern: "**/*.txt"           # File pattern (future feature)
```

**Clutter Generation**:
- Creates random subdirectories (`dir_1`, `dir_42`, etc.)
- Generates files with random names (`file_123.txt`, `clutter_45.log`)
- Adds realistic content to distract from target files
- Tests LLM's ability to focus on correct files

---

### CSV File Generation (`create_csv`)

Creates realistic business data in CSV format with intelligent field type detection.

#### Basic CSV Structure

```yaml
sandbox_setup:
  type: "create_csv"
  target_file: "{{artifacts}}/{{qs_id}}/customers.csv"
  content:
    headers: ["C_ID", "C_NAME", "AGE_YRS", "LOC_CD", "REG_DT"]
    rows: 75
```

#### Automatic Field Type Detection

PICARD automatically detects appropriate data types from header names:

| Header Pattern | Generated Data | Example |
|----------------|---------------|---------|
| `name`, `customer_name` | Person names | "John Smith" |
| `email`, `email_address` | Email addresses | "john.smith@company.com" |
| `age`, `age_yrs` | Ages 18-70 | "34" |
| `city`, `location` | City names | "New York" |
| `salary`, `income` | Salary ranges | "65000" |
| `price`, `cost`, `amount` | Prices | "123.45" |
| `phone`, `telephone` | Phone numbers | "(555) 123-4567" |
| `date`, `reg_dt` | Dates | "2024-03-15" |
| `status`, `state` | Status values | "active", "inactive" |
| `department`, `dept` | Departments | "Engineering", "Sales" |
| `region`, `area` | Regions | "North", "Southeast" |
| `*_id`, `id` | ID numbers | "1247" |

#### Explicit Field Types

Override automatic detection with explicit `header_types`:

```yaml
content:
  headers: ["CUST_ID", "CUST_NM", "ORD_AMT", "STAT_CD"]
  header_types: ["id", "person_name", "currency", "status"]
  rows: 100
```

**Available Data Types**:
- **People**: `person_name`, `first_name`, `last_name`, `email`
- **Business**: `company`, `department`, `salary`, `currency`, `price`
- **Location**: `city`, `region`, `phone`
- **Time**: `date`, `age`, `experience`
- **Status**: `status`, `boolean`, `category`
- **IDs**: `id` (numbers), `auto_id` (auto-increment)
- **Content**: `lorem_word`, `lorem_words`

#### Advanced CSV Examples

**Enterprise Employee Data**:
```yaml
content:
  headers: ["EMP_ID", "EMP_NM", "DEPT_CD", "SAL_AMT", "YRS_EXP", "STATUS"]
  header_types: ["id", "person_name", "department", "salary", "experience", "status"]  
  rows: 150
```

**E-commerce Orders**:
```yaml
content:
  headers: ["ORDER_ID", "CUSTOMER", "PRODUCT", "PRICE", "CATEGORY", "ORDER_DATE"]
  header_types: ["id", "person_name", "product", "price", "category", "date"]
  rows: 200
```

#### CSV Clutter

```yaml
config:
  clutter:
    count: 3                        # Creates 3 additional CSV/text files
    # Generates: clutter_42.csv, random_data.txt, etc.
```

---

### SQLite Database Generation (`create_sqlite`)

Creates relational databases with tables, data, and foreign key relationships.

#### Single Table Database

```yaml
sandbox_setup:
  type: "create_sqlite"
  target_file: "{{artifacts}}/{{qs_id}}/employees.db"
  content:
    table_name: "enterprise_employees"
    columns:
      - {name: "EMP_ID", type: "auto_id"}
      - {name: "EMP_NM", type: "TEXT", data_type: "person_name"}
      - {name: "DEPT_CD", type: "TEXT", data_type: "department"}
      - {name: "SAL_AMT", type: "INTEGER", data_type: "salary"}
      - {name: "STAT_FLG", type: "TEXT", data_type: "status"}
    rows: 50
```

#### Multi-Table Database with Relationships

```yaml
sandbox_setup:
  type: "create_sqlite"
  target_file: "{{artifacts}}/{{qs_id}}/business.db"
  content:
    tables:
      - name: "enterprise_customers"
        columns:
          - {name: "CUST_ID", type: "auto_id"}
          - {name: "CUST_NM", type: "TEXT", data_type: "person_name"}
          - {name: "DEPT_CD", type: "TEXT", data_type: "department"}
          - {name: "LOC_CD", type: "TEXT", data_type: "region"}
        rows: 20
      
      - name: "enterprise_orders"
        columns:
          - {name: "ORD_ID", type: "auto_id"}
          - {name: "CUST_REF", type: "INTEGER", foreign_key: "enterprise_customers.CUST_ID"}
          - {name: "ORD_AMT", type: "INTEGER", data_type: "currency"}
          - {name: "STAT_CD", type: "TEXT", data_type: "status"}
        rows: 75
```

#### SQLite Column Specifications

**Column Definition**:
```yaml
columns:
  - name: "COLUMN_NAME"           # Column name
    type: "SQL_TYPE"              # SQLite data type
    data_type: "DATA_GENERATOR"   # PICARD data generator type (optional)
    foreign_key: "table.column"   # Foreign key reference (optional)
```

**SQLite Data Types**:
- `INTEGER` - Numeric values
- `TEXT` - String values  
- `REAL` - Floating-point numbers
- `auto_id` - Auto-incrementing primary key

**Foreign Key Relationships**:
```yaml
foreign_key: "enterprise_customers.CUST_ID"  # References parent table
```

Foreign keys automatically reference existing parent table IDs, creating realistic relational data.

---

### JSON File Generation (`create_json`)

Creates structured JSON files with schema-driven generation, supporting complex nested objects, arrays, and type constraints.

#### Schema-Driven Generation

```yaml
sandbox_setup:
  type: "create_json"
  target_file: "{{artifacts}}/{{qs_id}}/data.json"
  content:
    schema:
      name: "person_name"
      email: "email"
      age: "age"
      active: "boolean"
```

**Generated JSON**:
```json
{
  "name": "John Smith",
  "email": "john.smith@gmail.com",
  "age": "34",
  "active": "true"
}
```

#### Semantic Data Types

JSON generation supports all existing semantic data types from CSV and SQLite:

```yaml
content:
  schema:
    employee:
      name: "person_name"           # Same as CSV
      department: "department"      # Same as CSV  
      salary: "salary"             # Same as CSV
      city: "city"                 # Same as CSV
```

#### Complex Nested Structures

**Object Nesting**:
```yaml
content:
  schema:
    employee:
      name: "person_name"
      contact:
        email: "email"
        phone: "phone"
        address:
          city: "city"
          region: "region"
```

**Array Generation**:
```yaml
content:
  schema:
    projects:
      type: "array"
      count: "{{number1:2:5}}"     # Random count between 2-5 using {{numeric}} variables
      items:
        name: "product"
        budget: "currency"
        team:
          type: "array"
          count: 3
          items: "person_name"
```

#### Type Constraints

Unlike CSV/SQLite, JSON supports configurable constraints:

```yaml
content:
  schema:
    metrics:
      score:
        type: "integer"
        minimum: 1
        maximum: 100
      rating:
        type: "number"  
        minimum: 1.0
        maximum: 5.0
      description:
        type: "string"
        min_length: 10
        max_length: 100
```

#### Advanced JSON Examples

**Enterprise Employee Data**:
```yaml
sandbox_setup:
  type: "create_json"
  target_file: "{{artifacts}}/{{qs_id}}/company.json"
  content:
    schema:
      company: "company"
      departments:
        type: "array"
        count: "{{number2:2:4}}"
        items:
          name: "department"
          manager:
            name: "person_name"
            email: "email"
          employees:
            type: "array"
            count: "{{number3:5:15}}"
            items:
              name: "person_name"
              salary: "salary"
              experience: "experience"
              projects:
                type: "array"
                count: "{{number4:1:3}}"
                items:
                  name: "product"
                  budget:
                    type: "integer"
                    minimum: 10000
                    maximum: 100000
```

**API Response Simulation**:
```yaml
content:
  schema:
    status: "status"
    data:
      users:
        type: "array"
        count: 10
        items:
          id: "id"
          profile:
            name: "person_name"
            preferences:
              theme: "category"
              notifications: "boolean"
    metadata:
      page: "id"
      total: "id"
      generated: "date"
```

### YAML File Generation (`create_yaml`)

Creates structured YAML files with schema-driven generation, supporting complex nested objects, arrays, and type constraints. Uses consistent block-style formatting for predictable parsing.

#### Schema-Driven Generation

```yaml
sandbox_setup:
  type: "create_yaml"
  target_file: "{{artifacts}}/{{qs_id}}/config.yaml"
  content:
    schema:
      database:
        host: "city"
        port: "id" 
        name: "company"
      services:
        type: "array"
        count: "{{number5:2:4}}"
        items:
          name: "product"
          enabled: "boolean"
```

**Generated YAML**:
```yaml
database:
  host: chicago-db-01
  port: 5432
  name: TechCorp
services:
  - name: ProductAPI
    enabled: true
  - name: UserService
    enabled: false
  - name: Analytics
    enabled: true
```

#### Complex Nested Structures

YAML generation supports deep nesting with consistent 2-space indentation:

```yaml
sandbox_setup:
  type: "create_yaml"
  target_file: "{{artifacts}}/{{qs_id}}/app.yaml"
  content:
    schema:
      application:
        environments:
          type: "array"
          count: 3
          items:
            name: "category"
            database:
              host: "city"
              config:
                pool_size: 
                  type: "integer"
                  minimum: 5
                  maximum: 20
                timeout:
                  type: "integer" 
                  minimum: 30
                  maximum: 120
            features:
              type: "array"
              count: "{{number6:1:3}}"
              items: "product"
```

#### Type Constraints and Arrays

Same type system as JSON with YAML-specific formatting:

```yaml
sandbox_setup:
  type: "create_yaml"
  target_file: "{{artifacts}}/{{qs_id}}/teams.yaml"
  content:
    schema:
      teams:
        type: "array"
        count: 5
        items:
          name: "product"
          budget:
            type: "integer"
            minimum: 50000
            maximum: 200000
          members:
            type: "array"
            count: "{{number7:2:8}}"
            items:
              name: "person_name"
              role: "category"
              active: "boolean"
      metadata:
        created: "date"
        version: "version"
```

#### Semantic Data Types

YAML generation supports all 42 semantic data types from DATA_GENERATION.md:

```yaml
sandbox_setup:
  type: "create_yaml"
  target_file: "{{artifacts}}/{{qs_id}}/enterprise.yaml"
  content:
    schema:
      company: "company"
      departments:
        type: "array"
        count: "{{number8:3:5}}"
        items:
          name: "department"
          manager:
            name: "person_name"
            email: "email"
            phone: "phone"
          budget: "currency"
          location:
            city: "city"
            region: "region"
```

#### YAML Formatting Standards

PICARD generates YAML with consistent formatting:
- **Block style only** (no flow style `{key: value}`)
- **2-space indentation**
- **No quotes unless necessary**
- **Array items with dashes**
- **Predictable structure for parsing**

---

### XML File Generation (`create_xml`)

PICARD can generate realistic XML files using schema-driven generation with proper XML structure, element hierarchies, and data validation.

#### Schema-Driven Generation

XML generation uses schema definitions similar to JSON/YAML but produces properly formatted XML with configurable root elements:

```yaml
files:
  - type: create_xml
    target_file: "{{artifacts}}/config.xml"
    content_spec:
      schema:
        database:
          host: "city"
          port: {"type": "integer", "minimum": 1000, "maximum": 9999}
          name: "company"
        settings:
          debug: {"type": "boolean"}
          timeout: {"type": "integer", "minimum": 30, "maximum": 300}
      root_element: "configuration"
```

Generated XML:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <database>
    <host>Chicago</host>
    <port>5432</port>
    <name>Tech Solutions</name>
  </database>
  <settings>
    <debug>True</debug>
    <timeout>120</timeout>
  </settings>
</configuration>
```

#### Element Structure and Attributes

XML generation creates hierarchical element structures with proper nesting and formatting:

**Basic structure**:
- Schema keys become XML element names
- String values become element text content
- Nested objects become child elements
- Pretty-printed with proper indentation

**Root element configuration**:
```yaml
content_spec:
  root_element: "enterprise"  # Optional, defaults to "root"
  schema:
    # ... schema definition
```

#### Complex Nested XML

XML supports deeply nested structures with multiple levels:

```yaml
content_spec:
  schema:
    company:
      name: "company"
      departments:
        type: "array"
        count: 3
        items:
          name: "department" 
          budget: {"type": "integer", "minimum": 100000, "maximum": 500000}
          employees:
            type: "array"
            count: "{{number9:2:5}}"
            items:
              name: "person_name"
              role: "category"
              salary: "salary"
  root_element: "organization"
```

Generated structure:
```xml
<organization>
  <company>
    <name>Global Industries</name>
    <departments>
      <item>
        <name>Engineering</name>
        <budget>350000</budget>
        <employees>
          <item>
            <name>John Smith</name>
            <role>Electronics</role>
            <salary>75000</salary>
          </item>
          <!-- More employee items... -->
        </employees>
      </item>
      <!-- More department items... -->
    </departments>
  </company>
</organization>
```

#### XML Arrays and Collections

Arrays in XML are represented as container elements with `<item>` children:

**Array configuration**:
```yaml
schema:
  products:
    type: "array"
    count: "{{number10:2:4}}"  # Random count between 2-4 using {{numeric}} variables
    items:
      name: "product"
      price: "price"
      category: "category"
```

**Generated XML**:
```xml
<products>
  <item>
    <name>Widget Pro</name>
    <price>29.99</price>
    <category>Tools</category>
  </item>
  <item>
    <name>Smart Device</name>
    <price>149.99</price>
    <category>Electronics</category>
  </item>
</products>
```

#### Semantic Data Types in XML

XML generation supports all PICARD semantic data types with proper XML formatting:

```yaml
schema:
  user_profile:
    personal_info:
      name: "person_name"           # → <name>John Smith</name>
      email: "email"                # → <email>john.smith@company.com</email>
      age: "age"                    # → <age>35</age>
      city: "city"                  # → <city>New York</city>
    employment:
      company: "company"            # → <company>Tech Solutions</company>
      department: "department"      # → <department>Engineering</department>
      salary: "salary"              # → <salary>85000</salary>
      start_date: "date"            # → <start_date>2023-06-15</start_date>
    preferences:
      active: {"type": "boolean"}   # → <active>True</active>
      score: "score"                # → <score>92</score>
```

**Type constraints work identically to JSON/YAML**:
```yaml
schema:
  metrics:
    revenue: {"type": "number", "minimum": 1000.0, "maximum": 50000.0}
    user_count: {"type": "integer", "minimum": 100, "maximum": 10000}
    version: {"type": "string", "pattern": "lorem_word"}
```

**XML output**:
```xml
<metrics>
  <revenue>25750.85</revenue>
  <user_count>3247</user_count>
  <version>tempor</version>
</metrics>
```

---

### Advanced Sandbox Features

#### File Path Templating

All file paths support full templating:

```yaml
target_file: "{{artifacts}}/{{qs_id}}/{{entity1}}/data.csv"
# Becomes: /sandbox/q301_s5/crimson/data.csv
```

#### Realistic Directory Structures

Create complex enterprise-like environments:

```yaml
- question_id: 501
  template: "Process all customer data files in the corporate directory structure"
  sandbox_setup:
    type: "create_csv"
    target_file: "{{artifacts}}/{{qs_id}}/corporate/{{entity1}}/customers/master_data.csv"
    content:
      headers: ["CUST_ID", "COMPANY", "REVENUE", "INDUSTRY"] 
      header_types: ["id", "company", "currency", "category"]
      rows: 100
    config:
      clutter:
        count: 8                    # Creates realistic corporate file chaos
```

#### Complex Business Scenarios

**Multi-Department Analysis**:
```yaml
sandbox_setup:
  type: "create_sqlite" 
  target_file: "{{artifacts}}/{{qs_id}}/{{entity1}}_analytics.db"
  content:
    tables:
      - name: "departments"
        columns:
          - {name: "dept_id", type: "auto_id"}
          - {name: "dept_name", type: "TEXT", data_type: "department"}
          - {name: "budget", type: "INTEGER", data_type: "currency"}
        rows: 5
      
      - name: "employees"  
        columns:
          - {name: "emp_id", type: "auto_id"}
          - {name: "name", type: "TEXT", data_type: "person_name"}
          - {name: "dept_ref", type: "INTEGER", foreign_key: "departments.dept_id"}
          - {name: "salary", type: "INTEGER", data_type: "salary"}
          - {name: "years_exp", type: "INTEGER", data_type: "experience"}
        rows: 200
        
      - name: "projects"
        columns:
          - {name: "proj_id", type: "auto_id"}
          - {name: "proj_name", type: "TEXT", data_type: "product"}
          - {name: "dept_ref", type: "INTEGER", foreign_key: "departments.dept_id"}
          - {name: "budget", type: "INTEGER", data_type: "currency"}
          - {name: "status", type: "TEXT", data_type: "status"}
        rows: 50
```

### Sandbox Best Practices

#### For File Processing Tasks
- Use meaningful nested directories (`{{entity1}}/data/{{entity2}}.csv`)
- Add clutter files to test focus and filtering
- Mix file types (CSV, TXT, LOG) for realism

#### For Database Tasks  
- Create realistic table relationships
- Use business-appropriate column names (`CUST_ID`, `ORD_AMT`)
- Include enough rows for meaningful aggregation (50-200)

#### For Multi-Step Workflows
- Generate multiple related files
- Create dependencies between data sources
- Test both reading and writing capabilities

#### Sample Size Considerations
- **Simple tasks**: 10-50 rows adequate
- **Aggregation tasks**: 50-200 rows for stable statistics  
- **Complex queries**: 100+ rows to test query optimization
- **Performance tests**: 500+ rows to stress test algorithms

### Error Handling

Sandbox generation provides detailed error reporting:
- **File creation failures**: Permission and disk space issues
- **Data generation errors**: Invalid field type specifications
- **Foreign key violations**: Broken table relationships
- **Template substitution errors**: Invalid placeholder usage

All errors are captured in precheck entries for debugging while allowing tests to continue.

---

*This completes the comprehensive PICARD Framework Reference covering all scoring types, template functions, and sandbox capabilities.*
