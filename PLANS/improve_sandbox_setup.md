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

### Phase 3: Advanced Scenarios (Week 5-6)

#### 3.1 Component Dependencies
```yaml
# Example: JSON config depends on CSV data structure
sandbox_setup:
  components:
    - name: "source_data"  # Named component
      type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/employees.csv"
      content:
        headers: ["id", "name", "department", "salary"]
        rows: 50
    
    - name: "processing_config"
      type: "create_json"
      target_file: "{{artifacts}}/{{qs_id}}/pipeline_config.json"
      depends_on: ["source_data"]  # Dependency
      content:
        schema:
          type: "object"
          properties:
            source_file: {type: "string", value: "employees.csv"}
            total_records: {type: "number", value: "{{csv_count:id:employees.csv}}"}
```

#### 3.2 Cross-Component References
```yaml
# Template functions can reference multiple components
template: |
  Process data pipeline:
  - Source: {{csv_count:id:{{artifacts}}/{{qs_id}}/employees.csv}} employees
  - Config: {{json_value:processing.batch_size:{{artifacts}}/{{qs_id}}/pipeline_config.json}}
  - Output: Transform to {{yaml_path:$.output.format:{{artifacts}}/{{qs_id}}/transform_spec.yaml}}
```

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

### Phase 4: Container Support (Future)
```yaml
sandbox_setup:
  components:
    # Traditional file component
    - type: "create_csv"
      target_file: "{{artifacts}}/{{qs_id}}/init_data.csv"
      content: {...}
    
    # Infrastructure component (future)
    - type: "run_docker"
      name: "postgres_db"
      config:
        image: "postgres:13"
        environment:
          POSTGRES_DB: "testdb"
          POSTGRES_USER: "{{semantic1:person_name}}"
        ports:
          - "5432:5432"
        volumes:
          - "{{artifacts}}/{{qs_id}}/init_data.csv:/docker-entrypoint-initdb.d/data.csv"
    
    # Service component
    - type: "run_service"
      name: "api_server"
      depends_on: ["postgres_db"]
      config:
        command: "python app.py"
        environment:
          DATABASE_URL: "postgresql://{{semantic1:person_name}}@postgres_db:5432/testdb"
```

## 📋 Implementation Strategy

### Development Approach
1. **Incremental Implementation**: Start with file components only
2. **Backwards Compatibility**: Never break existing tests
3. **Comprehensive Testing**: Multi-component integration tests
4. **Documentation Updates**: REFERENCE.md examples for new syntax

### Testing Strategy
```python
# Comprehensive test suite for multi-component scenarios
class TestMultiComponentSandbox:
    def test_csv_json_yaml_combination(self):
        """Test all three file formats in one test."""
        
    def test_component_dependencies(self):
        """Test dependency resolution and ordering."""
        
    def test_cross_component_template_functions(self):
        """Test template functions across multiple files."""
        
    def test_backwards_compatibility(self):
        """Ensure legacy syntax still works."""
```

### Risk Mitigation
- **Parser Complexity**: Incremental implementation with extensive testing
- **Dependency Resolution**: Start simple, add complexity gradually
- **Performance Impact**: Profile multi-component generation
- **Memory Usage**: Monitor resource consumption with multiple files

## 📈 Success Metrics

### Functional Goals
- ✅ Support 2-5 components per test without performance degradation
- ✅ 100% backwards compatibility with existing tests
- ✅ Cross-component template function support
- ✅ Dependency resolution for component ordering

### Use Case Validation
- ✅ Data pipeline testing (CSV → JSON → XML)
- ✅ Configuration management (multiple config files)
- ✅ Enterprise microservices scenarios
- ✅ Cross-format validation workflows

### Technical Metrics
- **Performance**: < 10% overhead for multi-component vs single-component tests
- **Memory**: Linear scaling with component count
- **Reliability**: No test failures due to component ordering issues

## 🎉 Conclusion

This multi-component architecture will transform PICARD from supporting simple single-file scenarios to complex, realistic enterprise testing environments. The `components` array approach provides:

- **Flexibility**: Multiple resource types per test
- **Scalability**: Easy addition of new component types (files, containers, services)
- **Realism**: Enterprise-grade testing scenarios
- **Compatibility**: No disruption to existing tests

**Next Steps**: Begin with Phase 1 parser enhancement, maintaining strict backwards compatibility while enabling the foundation for advanced multi-component testing scenarios.