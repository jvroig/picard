# Improve Sandbox Setup: Multi-Component Architecture Plan

## 🎯 Executive Summary

This plan addresses a critical limitation in PICARD's sandbox setup: the current framework only supports creating **one resource per test question**. This significantly constrains realistic enterprise testing scenarios that require multiple file formats, configurations, and infrastructure components.

## 📊 Current State Analysis

### Current Limitation
```yaml
# Current syntax - SINGLE resource only
sandbox_setup:
  type: "create_csv"
  target_file: "{{artifacts}}/{{qs_id}}/data.csv"
  content: {...}
```

**Problems with Current Design:**
- ❌ Cannot create CSV + JSON + XML in same test
- ❌ Cannot simulate data pipelines (CSV → JSON transformation)
- ❌ Cannot test multi-format configurations  
- ❌ Cannot create realistic enterprise environments
- ❌ Limits testing of cross-format workflows

### Framework Impact
This limitation affects:
- **Data Pipeline Testing**: Cannot simulate ETL workflows
- **Configuration Management**: Cannot test systems with multiple config files
- **Enterprise Scenarios**: Cannot replicate real-world complexity
- **Cross-Format Validation**: Cannot test format transformation accuracy
- **Microservices**: Cannot simulate multi-component architectures

## 🚀 Proposed Solution: Multi-Component Architecture

### New Syntax Design
```yaml
sandbox_setup:
  components:  # Array of sandbox components
    - type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/source_data.csv"
      content:
        headers: ["id", "name", "amount"]
        rows: 100
    
    - type: "create_json"
      target_file: "{{artifacts}}/{{qs_id}}/config.json"
      content:
        schema:
          type: "object"
          properties:
            database_url: {type: "string", data_type: "entity_pool"}
    
    - type: "create_yaml"
      target_file: "{{artifacts}}/{{qs_id}}/app_config.yaml"
      content:
        schema:
          type: "object"
          properties:
            environment: {type: "string", data_type: "status"}
```

### Backwards Compatibility
Support both old and new syntax:

```yaml
# Legacy syntax (still supported)
sandbox_setup:
  type: "create_csv"
  target_file: "..."
  content: {...}

# New syntax (multi-component)
sandbox_setup:
  components:
    - type: "create_csv"
      target_file: "..."
      content: {...}
    - type: "create_json"
      target_file: "..."
      content: {...}
```

## 🏗️ Implementation Phases

### Phase 1: Parser Enhancement (Week 1-2)

#### 1.1 Schema Detection
```python
class SandboxSetupParser:
    def parse_sandbox_setup(self, sandbox_config: dict) -> List[ComponentSpec]:
        """Parse both legacy and new multi-component syntax."""
        
        # Detect legacy syntax
        if 'type' in sandbox_config:
            return [self._parse_legacy_component(sandbox_config)]
        
        # Detect new multi-component syntax  
        elif 'components' in sandbox_config:
            return [self._parse_component(comp) for comp in sandbox_config['components']]
        
        else:
            raise ValueError("Invalid sandbox_setup configuration")
    
    def _parse_legacy_component(self, config: dict) -> ComponentSpec:
        """Convert legacy syntax to component spec."""
        return ComponentSpec(
            type=config['type'],
            target_file=config['target_file'],
            content=config['content']
        )
```

#### 1.2 Component Specification
```python
@dataclass
class ComponentSpec:
    """Specification for a single sandbox component."""
    type: str  # "create_csv", "create_json", "run_docker", etc.
    target_file: Optional[str] = None  # File path (for file components)
    content: Optional[dict] = None     # Content specification
    config: Optional[dict] = None      # Component-specific configuration
    depends_on: Optional[List[str]] = None  # Dependencies on other components
```

#### 1.3 Backwards Compatibility Testing
```python
class TestSandboxCompatibility:
    def test_legacy_syntax_still_works(self):
        """Ensure existing tests don't break."""
        
    def test_new_multi_component_syntax(self):
        """Validate new multi-component functionality."""
        
    def test_mixed_component_types(self):
        """Test CSV + JSON + YAML combinations."""
```

### Phase 2: Multi-File Generation (Week 3-4)

#### 2.1 Component Orchestration
```python
class ComponentOrchestrator:
    """Manages creation of multiple sandbox components."""
    
    def create_components(self, components: List[ComponentSpec], 
                         question_id: int, sample_number: int) -> List[ComponentResult]:
        """Create all components in dependency order."""
        
        # Resolve dependencies
        ordered_components = self._resolve_dependencies(components)
        
        results = []
        for component in ordered_components:
            result = self._create_component(component, question_id, sample_number)
            results.append(result)
            
        return results
    
    def _resolve_dependencies(self, components: List[ComponentSpec]) -> List[ComponentSpec]:
        """Order components based on dependencies."""
        # Topological sort implementation
        pass
```

#### 2.2 Enhanced File Factory
```python
class EnhancedFileGeneratorFactory:
    """Extended factory supporting multi-component scenarios."""
    
    def create_component(self, component_spec: ComponentSpec) -> ComponentGenerator:
        """Create appropriate generator for component type."""
        
        if component_spec.type.startswith('create_'):
            # File generation component
            return self._create_file_generator(component_spec)
        elif component_spec.type.startswith('run_'):
            # Infrastructure component (future)
            return self._create_infrastructure_component(component_spec)
        else:
            raise ValueError(f"Unknown component type: {component_spec.type}")
```

### Phase 3: Breaking Change Migration & TARGET_FILE Enhancement (Week 5-6)

#### 3.1 Architecture Simplification

**Decision: Break Backwards Compatibility for Cleaner Architecture**

Since PICARD has no production users yet, we're making a breaking change to eliminate complexity and technical debt from maintaining dual syntax support.

**Remove Backwards Compatibility Infrastructure:**
```python
# DELETE entirely:
- SandboxSetup class (~50 lines)
- Legacy parsing logic in SandboxSetupParser (~100 lines)
- Dual field support in TestDefinition (~30 lines)  
- test_sandbox_parser_compatibility.py (~240 lines)
- Backwards compatibility tests in other files

# SIMPLIFY:
- TestDefinitionParser to single syntax path
- ComponentOrchestrator integration
- Template function resolution logic
```

**Enforce New Syntax Requirements:**
```python
@dataclass
class ComponentSpec:
    type: str
    name: str  # Now REQUIRED (validated with naming standards)
    target_file: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    depends_on: Optional[List[str]] = None

@dataclass  
class TestDefinition:
    # ... existing fields ...
    # SINGLE field for sandbox components:
    sandbox_components: Optional[List[ComponentSpec]] = None
    # Remove: sandbox_setup field (legacy support)
```

**Component Naming Standards:**
```python
# Validation: ^[a-zA-Z][a-zA-Z0-9_-]*$ (1-50 chars)
# Valid: "employees", "config_data", "hr-reports", "finalReport2024"
# Invalid: "employee data", "_private", "config@prod", "123-data"

COMPONENT_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')

def validate_component_name(name: str) -> bool:
    return 1 <= len(name) <= 50 and COMPONENT_NAME_PATTERN.match(name)
```

#### 3.2 TARGET_FILE Enhancement

**Only Supported Syntax:**
```yaml
# MANDATORY: All sandbox_setup must use components array
sandbox_setup:
  components:
    - name: "employee_data"  # Mandatory named components
      type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/employees.csv"
      content:
        headers: ["id", "name", "department", "salary"]
        rows: 100
    
    - name: "config_data"
      type: "create_json"
      target_file: "{{artifacts}}/{{qs_id}}/config.json"
      depends_on: ["employee_data"]
      content:
        schema:
          type: "object"
          properties:
            max_employees: {type: "integer", value: 50}

# MANDATORY: All TARGET_FILE references must specify component name
template: |
  Employee analysis:
  - Total employees: {{csv_count:id:TARGET_FILE[employee_data]}}
  - Config limit: {{json_value:max_employees:TARGET_FILE[config_data]}}
  - Reference data: {{csv_count:id:reference_data.csv}}  # Literal paths still supported
```

**TARGET_FILE Resolution Implementation:**
```python
def resolve_target_file(expression: str, components: List[ComponentSpec]) -> str:
    """
    Resolve TARGET_FILE expressions for multi-component setups.
    
    Args:
        expression: TARGET_FILE[component_name] or literal path
        components: List of available components
    
    Returns:
        Resolved file path
    """
    if expression.startswith("TARGET_FILE[") and expression.endswith("]"):
        # Multi-component targeting: TARGET_FILE[component_name]
        component_name = expression[12:-1]  # Extract component name
        
        if not validate_component_name(component_name):
            raise ValueError(f"Invalid component name in TARGET_FILE[{component_name}]")
        
        for component in components:
            if component.name == component_name:
                return component.target_file
        
        raise ValueError(f"Component '{component_name}' not found in sandbox components")
    
    elif expression == "TARGET_FILE":
        # Legacy bare TARGET_FILE no longer supported
        raise ValueError("TARGET_FILE requires component name: TARGET_FILE[component_name]")
    
    else:
        # Literal file path - pass through unchanged
        return expression
```

#### 3.3 Migration & Testing

**Limited Migration Scope:**
- ✅ **Only `picard_abridged_standard`** test cases need migration (~10-15 files)
- ✅ **Extensive documentation updates required:**
  - `REFERENCE.md` - All sandbox_setup examples
  - `DATA_GENERATION.md` - Template function examples  
  - `improve_sandbox_setup.md` - This plan document
  - Any other documentation with syntax examples

**Template Function Updates:**
- Update all 60+ template functions to use `resolve_target_file()`
- Maintain existing function signatures and behavior
- Add component list parameter to resolution chain

**Migration Script Example:**
```bash
# Before migration:
sandbox_setup:
  type: "create_csv"
  target_file: "{{artifacts}}/{{qs_id}}/data.csv"
  content:
    headers: ["id", "name"]
    rows: 10

template: "Count: {{csv_count:id:TARGET_FILE}}"

# After migration:
sandbox_setup:
  components:
    - name: "data"
      type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/data.csv"
      content:
        headers: ["id", "name"]
        rows: 10

template: "Count: {{csv_count:id:TARGET_FILE[data]}}"
```

#### 3.4 Code Reduction Benefits

**Estimated Lines Removed:**
- SandboxSetup class: ~50 lines
- Legacy parser logic: ~100 lines  
- Backwards compatibility tests: ~240 lines
- Dual TestDefinition support: ~30 lines
- **Total reduction: ~420 lines**

**Complexity Reduction:**
- 60% simpler parser logic
- Single syntax mental model
- No dual data structure maintenance
- Cleaner template function resolution
- Easier future enhancements without legacy burden

## 🌟 Advanced Use Cases

### Enterprise Data Pipeline
```yaml
question_id: 501
template: "Implement ETL pipeline: CSV → JSON → YAML transformation"
sandbox_setup:
  components:
    # Raw data source
    - type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/raw_sales.csv"
      content:
        headers: ["transaction_id", "customer", "product", "amount", "date"]
        rows: 200
    
    # Processing configuration
    - type: "create_json"
      target_file: "{{artifacts}}/{{qs_id}}/etl_config.json"
      content:
        schema:
          type: "object"
          properties:
            source_file: {type: "string", value: "raw_sales.csv"}
            filters: 
              type: "object"
              properties:
                min_amount: {type: "number", data_type: "currency"}
                date_range: {type: "string", data_type: "semester"}
    
    # Output specification
    - type: "create_yaml"
      target_file: "{{artifacts}}/{{qs_id}}/output_spec.yaml"
      content:
        schema:
          type: "object"
          properties:
            format: {type: "string", value: "summary_report"}
            aggregations:
              type: "array"
              count: 3
              item_schema:
                type: "object"
                properties:
                  metric: {type: "string", data_type: "category"}
                  function: {type: "string", value: "sum"}

scoring_type: "readfile_jsonmatch"
file_to_read: "{{artifacts}}/{{qs_id}}/pipeline_result.json"
expected_content: |
  {
    "pipeline_status": "completed",
    "source_records": {{csv_count:transaction_id:{{artifacts}}/{{qs_id}}/raw_sales.csv}},
    "total_amount": {{csv_sum:amount:{{artifacts}}/{{qs_id}}/raw_sales.csv}},
    "config_filters": {{json_value:filters:{{artifacts}}/{{qs_id}}/etl_config.json}},
    "output_format": "{{yaml_path:$.format:{{artifacts}}/{{qs_id}}/output_spec.yaml}}"
  }
```

### Microservices Configuration
```yaml
question_id: 502
template: "Configure microservices environment with database, API, and monitoring"
sandbox_setup:
  components:
    # Database configuration
    - type: "create_yaml"
      target_file: "{{artifacts}}/{{qs_id}}/database.yaml"
      content:
        schema:
          type: "object"
          properties:
            host: {type: "string", data_type: "entity_pool"}
            port: {type: "integer", value: 5432}
            database: {type: "string", data_type: "company"}
    
    # API configuration
    - type: "create_json"
      target_file: "{{artifacts}}/{{qs_id}}/api_config.json"
      content:
        schema:
          type: "object"
          properties:
            endpoints:
              type: "array"
              count: 5
              item_schema:
                type: "object"
                properties:
                  path: {type: "string", data_type: "entity_pool"}
                  method: {type: "string", data_type: "status"}
    
    # User data
    - type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/users.csv"
      content:
        headers: ["id", "username", "email", "role"]
        header_types: ["id", "person_name", "email", "department"]
        rows: 25
```

## 🔮 Future Infrastructure Components

### Future Phase: Container Support
*Note: Infrastructure components (Docker, services) are planned for future development but are not part of the current Phase 3 scope.*

```yaml
# Future capability example:
sandbox_setup:
  components:
    # File component (Phase 3)
    - name: "init_data"
      type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/init_data.csv"
      content: {...}
    
    # Infrastructure component (future)
    - name: "postgres_db"
      type: "run_docker"
      config:
        image: "postgres:13"
        environment:
          POSTGRES_DB: "testdb"
          POSTGRES_USER: "{{semantic1:person_name}}"
        volumes:
          - "{{artifacts}}/{{qs_id}}/init_data.csv:/docker-entrypoint-initdb.d/data.csv"
    
    # Service component (future)
    - name: "api_server"
      type: "run_service"
      depends_on: ["postgres_db"]
      config:
        command: "python app.py"
        environment:
          DATABASE_URL: "postgresql://{{semantic1:person_name}}@postgres_db:5432/testdb"
```

## 📋 Implementation Strategy

### Development Approach
1. **Breaking Change Strategy**: Clean architecture over backwards compatibility
2. **Single Syntax Focus**: Mandatory named components with TARGET_FILE[component_name]
3. **Comprehensive Testing**: Multi-component integration tests with new syntax only
4. **Extensive Documentation Updates**: All examples updated to new syntax

### Testing Strategy
```python
# Comprehensive test suite for multi-component scenarios with new syntax
class TestMultiComponentSandbox:
    def test_csv_json_yaml_combination(self):
        """Test all file formats with TARGET_FILE[component_name]."""
        
    def test_component_dependencies(self):
        """Test dependency resolution and ordering."""
        
    def test_target_file_resolution(self):
        """Test TARGET_FILE[component_name] resolution."""
        
    def test_component_naming_validation(self):
        """Test component naming standards enforcement."""
        
    def test_template_function_integration(self):
        """Test all 60+ template functions with new resolution."""
```

### Risk Mitigation
- **Breaking Change Impact**: Limited scope (only picard_abridged_standard needs migration)
- **Documentation Debt**: Comprehensive documentation update required across multiple files
- **Template Function Updates**: All 60+ functions need TARGET_FILE resolution integration
- **Testing Coverage**: Ensure new syntax is thoroughly tested before removing old code

## 📈 Success Metrics

### Phase 3 Goals
- ✅ **Single syntax**: All tests use mandatory `components` array with named components
- ✅ **TARGET_FILE enhancement**: `TARGET_FILE[component_name]` works for all 60+ template functions
- ✅ **Component naming**: Enforced validation standards for component names
- ✅ **Migration complete**: `picard_abridged_standard` updated to new syntax
- ✅ **Documentation updated**: All examples use new syntax across all documentation
- ✅ **Code simplified**: Backwards compatibility infrastructure removed (~420 lines)
- ✅ **Testing coverage**: New syntax comprehensively tested

### Use Case Validation
- ✅ **Multi-format testing**: CSV + JSON + YAML + XML in single tests
- ✅ **Data pipeline validation**: Template functions across multiple components
- ✅ **Configuration management**: Named component references
- ✅ **Complex dependencies**: Multi-level component dependency chains

### Technical Metrics
- **Code Reduction**: ~420 lines of backwards compatibility code removed
- **Complexity**: 60% reduction in parser logic complexity
- **Performance**: Support 2-10 components per test without degradation
- **Reliability**: No test failures due to component resolution issues

## 🎉 Conclusion

This breaking change approach will transform PICARD from a backwards-compatibility-burdened framework to a clean, powerful multi-component testing platform. The mandatory `components` array with `TARGET_FILE[component_name]` provides:

- **Simplicity**: Single, consistent syntax across all use cases
- **Power**: Multi-format testing with cross-component template functions
- **Clarity**: Named components with enforced naming standards
- **Maintainability**: 60% reduction in parser complexity
- **Extensibility**: Clean foundation for future infrastructure components

**Phase 3 Deliverables:**
1. **Week 5**: Remove backwards compatibility infrastructure, implement TARGET_FILE[component_name] resolution
2. **Week 6**: Migrate picard_abridged_standard, update all documentation, comprehensive testing

This approach prioritizes **clean architecture and developer experience** over maintaining legacy compatibility, resulting in a more powerful and maintainable framework for complex enterprise testing scenarios.