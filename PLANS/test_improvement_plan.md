# PICARD Test Improvement Plan

## Overview

This plan outlines the migration from ad-hoc testing (embedded `main()` functions) to a professional pytest-based testing framework for the PICARD project.

## Current State Analysis

### Existing Test Coverage
- **File Generators**: Tests embedded in `src/file_generators.py main()`
  - TextFileGenerator (lorem ipsum content)
  - CSVFileGenerator (data generation, field types)
  - SQLiteFileGenerator (database creation, foreign keys)
  - JSONFileGenerator (schema-driven generation) ✨ *New*
- **Template Functions**: Tests embedded in `src/template_functions.py main()`
  - File operations (line/word extraction)
  - CSV operations (cell access, aggregation)
  - SQLite operations (queries)
  - JSON operations (JSONPath extraction) ✨ *New*
- **Integration Tests**: None currently exist

### Problems with Current Approach
- Manual verification via print statements
- No assertions or automatic pass/fail
- Tests mixed with production code
- No test discovery or automation
- Difficult to run subset of tests
- No clear separation of test data
- Hard to debug failures

## Migration Strategy

### Phase 1: Foundation Setup
**Goal**: Establish pytest infrastructure and basic test structure

#### 1.1 Project Structure
```
picard/
├── src/                    # Production code (unchanged)
├── tests/                  # New test directory
│   ├── conftest.py        # Shared fixtures and configuration
│   ├── unit/              # Unit tests
│   │   ├── test_file_generators.py
│   │   ├── test_template_functions.py
│   │   ├── test_data_generator.py
│   │   └── test_entity_pool.py
│   ├── integration/       # Integration tests
│   │   ├── test_end_to_end.py
│   │   └── test_cross_format.py
│   ├── fixtures/          # Test data files
│   │   ├── sample_data.csv
│   │   ├── test_config.json
│   │   └── example.sqlite
│   └── utils/             # Test utilities
│       └── helpers.py
├── pytest.ini            # Pytest configuration
└── requirements-test.txt  # Testing dependencies
```

#### 1.2 Dependencies
Update `requirements.txt` or create `requirements-test.txt`:
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-parametrize>=1.0.0
```

#### 1.3 Configuration Files
**pytest.ini**:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests requiring external resources
```

### Phase 2: Core Unit Tests Migration
**Goal**: Migrate existing unit tests with proper assertions

#### 2.1 File Generator Tests (`tests/unit/test_file_generators.py`)
```python
import pytest
import tempfile
import json
from pathlib import Path
from src.file_generators import (
    TextFileGenerator, CSVFileGenerator, 
    SQLiteFileGenerator, JSONFileGenerator,
    FileGeneratorFactory
)

class TestTextFileGenerator:
    def test_lorem_lines_generation(self, tmp_path):
        # Migrate from existing main() function
        generator = TextFileGenerator(tmp_path)
        result = generator.generate(
            target_file="test.txt",
            content_spec={'type': 'lorem_lines', 'count': 5}
        )
        
        assert len(result['files_created']) == 1
        assert result['errors'] == []
        
        # Verify file exists and has content
        target_file = tmp_path / "test.txt"
        assert target_file.exists()
        content = target_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) == 5

class TestJSONFileGenerator:
    def test_simple_schema_generation(self, tmp_path):
        generator = JSONFileGenerator(tmp_path)
        schema = {
            'message': 'lorem_words',
            'count': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'active': {'type': 'boolean'}
        }
        
        result = generator.generate(
            target_file="test.json",
            content_spec={'schema': schema}
        )
        
        assert len(result['files_created']) == 1
        assert result['errors'] == []
        
        # Verify JSON structure
        json_data = result['json_data'][str(tmp_path / "test.json")]
        assert 'message' in json_data
        assert 'count' in json_data
        assert 'active' in json_data
        assert isinstance(json_data['count'], int)
        assert 1 <= json_data['count'] <= 100
        assert isinstance(json_data['active'], bool)
```

#### 2.2 Template Function Tests (`tests/unit/test_template_functions.py`)
```python
import pytest
import json
import csv
from pathlib import Path
from src.template_functions import TemplateFunctions

class TestJSONTemplateFunctions:
    @pytest.fixture
    def sample_json_file(self, tmp_path):
        data = {
            "users": [
                {"id": 1, "name": "John", "age": 25},
                {"id": 2, "name": "Alice", "age": 30}
            ],
            "metadata": {"total": 2, "version": "1.0"}
        }
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data))
        return str(json_file)
    
    def test_json_path_extraction(self, sample_json_file):
        tf = TemplateFunctions()
        
        # Test array element access
        result = tf.evaluate_all_functions(f"{{{{json_path:$.users[0].name:{sample_json_file}}}}}")
        assert result == "John"
        
        # Test nested object access
        result = tf.evaluate_all_functions(f"{{{{json_path:$.metadata.total:{sample_json_file}}}}}")
        assert result == "2"
    
    @pytest.mark.parametrize("template,expected", [
        ("{{json_value:metadata.total:FILE}}", "2"),
        ("{{json_count:$.users:FILE}}", "2"),
        ("{{json_keys:$.metadata:FILE}}", "total,version"),
    ])
    def test_json_functions_parametrized(self, sample_json_file, template, expected):
        tf = TemplateFunctions()
        template_with_file = template.replace("FILE", sample_json_file)
        result = tf.evaluate_all_functions(template_with_file)
        assert result == expected
```

### Phase 3: Integration Tests
**Goal**: Test complete workflows and cross-format operations

#### 3.1 End-to-End Tests (`tests/integration/test_end_to_end.py`)
```python
class TestEndToEndWorkflows:
    def test_json_generation_and_extraction(self, tmp_path):
        """Test: Generate JSON → Extract with template functions → Verify correctness"""
        # Generate JSON file
        generator = JSONFileGenerator(tmp_path)
        schema = {
            'users': {
                'type': 'array',
                'count': 3,
                'items': {'id': 'id', 'name': 'person_name', 'age': 'age'}
            }
        }
        
        result = generator.generate(
            target_file="users.json",
            content_spec={'schema': schema}
        )
        
        # Extract data using template functions
        tf = TemplateFunctions(tmp_path)
        user_count = tf.evaluate_all_functions("{{json_count:$.users:users.json}}")
        first_user_name = tf.evaluate_all_functions("{{json_path:$.users[0].name:users.json}}")
        
        # Verify extraction matches generation
        assert int(user_count) == 3
        assert len(first_user_name) > 0  # Should have generated a name
        
        # Verify against original data
        original_data = result['json_data'][str(tmp_path / "users.json")]
        assert len(original_data['users']) == 3
        assert original_data['users'][0]['name'] == first_user_name

class TestCrossFormatOperations:
    def test_json_to_csv_workflow(self, tmp_path):
        """Test workflow: JSON → Process → CSV generation based on JSON data"""
        # This would test more complex scenarios where one format informs another
        pass
```

### Phase 4: Fixtures and Test Utilities
**Goal**: Create reusable test infrastructure

#### 4.1 Shared Fixtures (`tests/conftest.py`)
```python
import pytest
import tempfile
from pathlib import Path
from src.file_generators import FileGeneratorFactory

@pytest.fixture
def temp_workspace():
    """Provide a temporary directory for file operations"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_csv_data():
    """Standard CSV test data"""
    return {
        'headers': ['id', 'name', 'age', 'city'],
        'rows': [
            ['1', 'John Doe', '25', 'New York'],
            ['2', 'Jane Smith', '30', 'Los Angeles'],
            ['3', 'Bob Johnson', '35', 'Chicago']
        ]
    }

@pytest.fixture
def json_generator(temp_workspace):
    """Pre-configured JSON generator"""
    return FileGeneratorFactory.create_generator('create_json', temp_workspace)
```

#### 4.2 Test Utilities (`tests/utils/helpers.py`)
```python
def assert_file_exists_with_content(file_path, min_size=0):
    """Assert file exists and has minimum content size"""
    assert file_path.exists(), f"File {file_path} does not exist"
    assert file_path.stat().st_size >= min_size, f"File {file_path} is too small"

def validate_json_schema(data, expected_keys):
    """Validate JSON data has expected structure"""
    for key in expected_keys:
        assert key in data, f"Missing expected key: {key}"

def compare_template_function_result(tf, template, expected, file_path=None):
    """Helper to test template function with optional file substitution"""
    if file_path:
        template = template.replace("TARGET_FILE", str(file_path))
    result = tf.evaluate_all_functions(template)
    assert str(result) == str(expected), f"Template {template} returned {result}, expected {expected}"
```

### Phase 5: Legacy Code Cleanup
**Goal**: Remove old test code from production files

#### 5.1 Remove `main()` Functions
- Remove `main()` from `src/file_generators.py`
- Remove `main()` from `src/template_functions.py`
- Update `if __name__ == "__main__"` blocks

#### 5.2 Production Code Focus
- Ensure src/ directory contains only production code
- Move any test-specific utilities to tests/utils/

### Phase 6: Continuous Integration
**Goal**: Automate testing in development workflow

#### 6.1 GitHub Actions (if applicable)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    - name: Run tests
      run: pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### 6.2 Pre-commit Hooks (optional)
```yaml
# .pre-commit-config.yaml
repos:
- repo: local
  hooks:
  - id: pytest
    name: pytest
    entry: pytest
    language: system
    pass_filenames: false
    always_run: true
```

## Migration Timeline

### Week 1: Foundation
- [ ] Create directory structure
- [ ] Add pytest dependencies
- [ ] Configure pytest.ini
- [ ] Create basic conftest.py

### Week 2: Core Unit Tests
- [ ] Migrate file generator tests
- [ ] Migrate template function tests
- [ ] Add parametrized tests for comprehensive coverage

### Week 3: Integration & Utilities
- [ ] Create end-to-end tests
- [ ] Build test fixtures and utilities
- [ ] Add cross-format operation tests

### Week 4: Cleanup & Polish
- [ ] Remove old test code from src/
- [ ] Add GitHub Actions (if applicable)
- [ ] Documentation updates
- [ ] Performance benchmarks

## Success Criteria

### Functionality
- [ ] All existing test scenarios converted to pytest
- [ ] New tests have proper assertions (no print statements)
- [ ] Tests can be run individually or as suites
- [ ] Coverage reports show comprehensive testing

### Quality
- [ ] Tests follow pytest best practices
- [ ] Clear separation of unit vs integration tests
- [ ] Reusable fixtures reduce code duplication
- [ ] Error cases are explicitly tested

### Automation
- [ ] `pytest` command runs all tests
- [ ] Tests can be filtered by markers (`pytest -m unit`)
- [ ] Coverage reporting works correctly
- [ ] Tests pass consistently on different environments

### Maintainability
- [ ] Test code is as clean as production code
- [ ] New features can easily add corresponding tests
- [ ] Test failures provide clear diagnostic information
- [ ] Documentation explains how to run and extend tests

## Benefits After Migration

### For Development
- **Faster feedback**: Quick test execution with clear pass/fail
- **Better debugging**: Detailed failure reports with stack traces
- **Confidence**: Automated verification prevents regressions
- **Coverage insights**: Know exactly what code is tested

### For Collaboration
- **Onboarding**: New contributors can run tests to verify setup
- **Code reviews**: Tests serve as executable specifications
- **Documentation**: Tests demonstrate expected usage patterns
- **Quality assurance**: Automated checks prevent broken code

### For PICARD's Mission
- **Reliability**: Testing framework that's thoroughly tested itself
- **Extensibility**: Easy to add tests for new file formats (YAML, XML)
- **Credibility**: Professional testing practices enhance project reputation
- **Research quality**: Robust testing enables confident research conclusions

## Risks and Mitigation

### Risk: Migration Breaks Existing Functionality
**Mitigation**: 
- Keep existing `main()` functions during migration
- Run both old and new tests in parallel initially
- Only remove old tests after new tests prove comprehensive

### Risk: Tests Become Too Slow
**Mitigation**:
- Use pytest markers to separate fast/slow tests
- Optimize fixture setup/teardown
- Run subset of tests during development

### Risk: Test Maintenance Overhead
**Mitigation**:
- Invest in good fixtures and utilities upfront
- Follow DRY principles in test code
- Regular refactoring of test code alongside production code

## Next Steps

1. **Review and approve this plan**
2. **Start with Phase 1: Foundation Setup**
3. **Create initial test structure with one simple test**
4. **Validate pytest setup works correctly**
5. **Begin systematic migration of existing tests**

---

This plan provides a comprehensive roadmap for professionalizing PICARD's testing infrastructure while maintaining development velocity and code quality.