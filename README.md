# QwenSense: LLM Benchmarking Tool Implementation Plan

## Overview
A dynamic LLM benchmarking tool designed to test multi-step workflows with tool usage while preventing memorization through randomized entity substitution.

## Core Concepts

### 1. Dynamic Questions
- Template-based questions with placeholders: `{{entity1}}`, `{{entity2}}`, etc.
- Runtime substitution from entity pool (100-200 words: adjectives, nouns)
- Prevents memorization through combinatorial explosion of possibilities

### 2. Dynamic Handling
- Precheck file records actual entity values used for each test run
- JSONL format for easy streaming/appending
- Enables deterministic scoring despite randomization

### 3. Scoring Types
- **readfile_stringmatch**: Read file, exact string match (whitespace trimmed)
- **files_exist**: Check if specified files exist (all must exist)
- **stringmatch**: Traditional Q&A exact string matching
- **directory_structure**: Verify folder hierarchy using path lists
- **tool_call_sequence**: (v2) Capture and validate tool call sequences

### 4. Test Set Definition
- Human-readable YAML/JSON format
- `samples` property: number of randomized runs per question
- Scoring-specific properties (e.g., `file_to_read`, `files_to_check`)

## Project Structure
```
/Users/jvroig/Dev/QwenSense/
├── src/
│   ├── benchmark.py          # Main orchestrator
│   ├── entity_pool.py        # Entity word management
│   ├── test_runner.py        # Execute tests against LLM
│   ├── scorer.py             # Score results using precheck
│   └── scoring_types/        # Individual scoring implementations
│       ├── __init__.py
│       ├── readfile_stringmatch.py
│       ├── files_exist.py
│       ├── stringmatch.py
│       └── directory_structure.py
├── config/
│   ├── entity_pool.txt       # Word list for substitution
│   └── test_definitions.yaml # Human-readable test suite
├── test_artifacts/           # Working directory for LLM file operations
├── results/                  # Output folder
│   ├── precheck_TIMESTAMP.jsonl
│   ├── responses_TIMESTAMP.jsonl
│   └── scores_TIMESTAMP.json
├── requirements.txt
└── README.md
```

## Example Data Formats

### Test Definition (YAML)
```yaml
question_id: 1
samples: 20
template: "Write \"Hey {{entity1}}\" inside of this file (fullpath): test_artifacts/{{entity2}}.txt"
scoring_type: "readfile_stringmatch"
file_to_read: "test_artifacts/{{entity2}}.txt"
```

### Precheck Entry (JSONL)
```json
{"scoring_type": "readfile_stringmatch", "question_id": 1, "sample_number": 1, "template": "Write \"Hey {{entity1}}\" inside of this file (fullpath): test_artifacts/{{entity2}}.txt", "entity1": "rosebud", "entity2": "withered", "file_to_read": "test_artifacts/withered.txt"}
```

### Directory Structure Example
```yaml
scoring_type: "directory_structure"
expected_structure:
  - "{{entity1}}/"
  - "{{entity1}}/{{entity2}}/"
  - "{{entity1}}/logs/{{entity3}}.log"
```

## Design Decisions

### LLM Integration
- Use OpenAI API standard for compatibility
- Delegate actual LLM calling to external engines/APIs
- Focus on testing different tool-calling implementations
- Revisit integration approach during Phase 3

### Anti-Memorization Strategy
- Large entity pool (100-200+ words)
- Multiple samples per question template
- Dynamic substitution at runtime
- Combinatorial explosion makes memorization infeasible

### Scoring Philosophy
- Deterministic and reproducible
- Exact matching (with reasonable whitespace handling)
- Extensible scoring type system
- Clear pass/fail criteria
