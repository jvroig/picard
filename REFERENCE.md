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
- [Template Functions](#template-functions)
  - [TARGET_FILE Keyword](#target_file-keyword)
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
- Template functions such as (`{{csv_count:COLUMN:TARGET_FILE}}`)
- Dynamic answer key generation

---

## Template Functions

Template functions enable dynamic answer key generation by extracting data from files created during test execution. They use the format `{{function_name:arg1:arg2:...}}` and are evaluated at runtime to create deterministic expected responses.

### TARGET_FILE Keyword

Most template functions accept `TARGET_FILE` as a file path argument, which gets replaced with the actual target file path from `sandbox_setup`:

```yaml
sandbox_setup:
  target_file: "{{artifacts}}/{{qs_id}}/data.csv"
expected_content: "{{csv_count:ID:TARGET_FILE}}"
# TARGET_FILE becomes: /sandbox/q301_s5/data.csv
```

---

### File Content Functions

Extract specific content from text files.

#### `file_line`
**Purpose**: Get a specific line number from a text file.
**Usage**: `{{file_line:line_number:file_path}}`
**Parameters**:
- `line_number`: Line number (1-based indexing)
- `file_path`: Path to text file (or `TARGET_FILE`)

**Example**:
```yaml
template: "What does line 34 say in {{artifacts}}/notes.txt?"
expected_response: "{{file_line:34:TARGET_FILE}}"
sandbox_setup:
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
expected_response: "{{file_word:35:TARGET_FILE}}"
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
expected_response: "{{csv_cell:1:1:TARGET_FILE}}"
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
expected_content: "{{csv_value:0:AGE:TARGET_FILE}}"
```

##### `csv_row`
**Purpose**: Get entire row as comma-separated string.
**Usage**: `{{csv_row:row_number:file_path}}`

##### `csv_column`
**Purpose**: Get entire column as comma-separated string.
**Usage**: `{{csv_column:header:file_path}}`

#### CSV Aggregation Functions

##### `csv_count`
**Purpose**: Count non-empty values in a column.
**Usage**: `{{csv_count:column:file_path}}`

**Example**:
```yaml
expected_content: '{"total_customers": {{csv_count:C_ID:TARGET_FILE}}}'
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
expected_content: '{"avg_age": {{csv_avg:AGE_YRS:TARGET_FILE}}}'
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
expected_content: "{{csv_count_where:EMP_ID:DEPT_CD:==:Engineering:TARGET_FILE}}"

# Count high earners
expected_content: "{{csv_count_where:EMP_ID:SALARY:>:50000:TARGET_FILE}}"
```

##### `csv_sum_where`
**Purpose**: Sum values in a column where filter condition is met.
**Usage**: `{{csv_sum_where:column:filter_column:operator:value:file_path}}`

**Example**:
```yaml
# Total salary for Engineering department
expected_content: "{{csv_sum_where:SAL_AMT:DEPT_CD:==:Engineering:TARGET_FILE}}"
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
expected_content: "{{sqlite_query:SELECT COUNT(*) FROM enterprise_orders o JOIN enterprise_customers c ON o.CUST_REF = c.CUST_ID WHERE c.DEPT_CD = 'Engineering' AND o.ORD_AMT > 50000:TARGET_FILE}}"
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

### Template Function Examples

#### Complex CSV Processing
```yaml
question_id: 301
template: "Create JSON summary with total customers and average age"
expected_content: |
  {
    "total_customers": {{csv_count:C_ID:TARGET_FILE}},
    "average_age": {{csv_avg:AGE_YRS:TARGET_FILE}},
    "engineering_count": {{csv_count_where:C_ID:DEPT_CD:==:Engineering:TARGET_FILE}},
    "high_earner_avg_age": {{csv_avg_where:AGE_YRS:SALARY:>:60000:TARGET_FILE}}
  }
```

#### Database Query with Business Logic
```yaml
question_id: 402
template: "How many high-value orders from Engineering customers?"
expected_content: "{{sqlite_query:SELECT COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.department = 'Engineering' AND o.amount > 50000:TARGET_FILE}}"
```

#### File Content Needle-in-Haystack
```yaml
question_id: 201
template: "Find the 35th word in the generated document"
expected_response: "{{file_word:35:TARGET_FILE}}"
sandbox_setup:
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

Sandbox setup operates through three main generator types:
- **`create_files`**: Text files with lorem ipsum content
- **`create_csv`**: CSV files with realistic business data
- **`create_sqlite`**: SQLite databases with tables and relationships

### Basic Configuration

```yaml
sandbox_setup:
  type: "create_csv"                           # Generator type
  target_file: "{{artifacts}}/{{qs_id}}/data.csv"   # Output file path
  content:                                     # Content specification
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
