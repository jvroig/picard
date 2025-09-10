# Fix Clutter Configuration Naming and Structure

## Problem Statement

PICARD's component `config` property has a design inconsistency where the entire config object is passed as `clutter_spec` to file generators. This prevents using `config` for its intended broader purpose of component-specific configuration.

## Current Misimplementation

### **How it works now:**
```yaml
# Test definition
sandbox_setup:
  components:
    - type: "create_csv"
      name: "data"
      config:           # ← Entire config becomes clutter_spec
        count: 5
        pattern: "**/*.csv"
```

```python
# In component_orchestrator.py
result_info = generator.generate(component.target_file, component.content, 
                               component.config)  # ← Passes entire config as clutter_spec
```

```python  
# In file generators
def generate(self, target_file, content_spec, clutter_spec=None):
    if clutter_spec:  # ← Treats entire config as clutter config
        clutter_result = self._generate_clutter_files(target_file, clutter_spec)
```

### **Problems with current approach:**
1. **Semantic confusion**: `config` suggests broad component configuration, not just clutter
2. **Prevents expansion**: Can't add other config properties (performance, validation, etc.)
3. **Misnamed parameters**: `clutter_spec` parameter suggests clutter-only, but receives entire config
4. **Future limitations**: Infrastructure components need real config for Docker settings, database connections, etc.

## Proposed Solution: Hierarchical Configuration

### **Target Structure:**
```yaml
sandbox_setup:
  components:
    - type: "create_csv"
      name: "data"
      config:
        clutter:        # ← Clutter as sub-property
          count: {{number1:3:8}}
          pattern: "**/*.csv"
        performance:    # ← Other config categories possible
          timeout: 30
        validation:
          strict_mode: true
          
    # Future infrastructure example:
    - type: "run_docker"
      name: "postgres_db"
      config:
        clutter:        # ← Same clutter structure for all components
          count: 2
        docker:         # ← Component-specific config
          image: "postgres:13"
          environment:
            POSTGRES_DB: "testdb"
            POSTGRES_USER: "{{semantic1:person_name}}"
          ports:
            - "5432:5432"
```

## Implementation Plan

### **Phase 1: Update File Generators (Backwards Compatible)**

**Modify all 6 file generators to support hierarchical config:**

```python
# In BaseFileGenerator and all subclasses
def generate(self, target_file: str, content_spec: Dict[str, Any], 
             config: Dict[str, Any] = None) -> Dict[str, Any]:  # ← Rename parameter
    """
    Generate files according to specifications.
    
    Args:
        target_file: Path to the main target file
        content_spec: Content specification dictionary
        config: Component configuration (replaces clutter_spec)
        
    Returns:
        Dictionary with generation results and metadata
    """
    # ... existing content generation logic ...
    
    # Handle clutter generation with backwards compatibility
    clutter_config = self._extract_clutter_config(config)
    if clutter_config:
        clutter_result = self._generate_clutter_files(target_file, clutter_config)
        # ... merge results ...

def _extract_clutter_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract clutter configuration with backwards compatibility."""
    if not config:
        return None
    
    # New hierarchical format: config.clutter
    if 'clutter' in config:
        return config['clutter']
    
    # Old flat format: entire config is clutter (backwards compatibility)
    # Check if config looks like clutter config (has count/pattern)
    if 'count' in config or 'pattern' in config:
        return config
    
    return None
```

### **Phase 2: Update Component Orchestrator**

**Update parameter passing to use new naming:**

```python
# In component_orchestrator.py
def _create_file_component(self, component: ComponentSpec, ...):
    # Generate the file using updated interface
    result_info = generator.generate(component.target_file, component.content, 
                                   component.config)  # ← Now properly named 'config'
```

### **Phase 3: Documentation Updates**

**Update all documentation to show hierarchical structure:**

1. **DATA_GENERATION.md**: Show `config.clutter` examples
2. **REFERENCE.md**: Update sandbox component documentation  
3. **Config files**: Provide migration examples

### **Phase 4: Variable Expansion Support**

**Add variable expansion for config properties:**

Since config can now contain numeric variables like `count: {{number1:3:8}}`, ensure the precheck generator processes config variables:

```python
# In precheck_generator.py - extend sandbox component processing
def _handle_sandbox_generation(self, precheck_entry, test_def, all_variables):
    for component in test_def.sandbox_components:
        # ... existing target_file and content processing ...
        
        # Process config variables
        if component.config:
            processed_config = self._substitute_with_all_variables(
                json.dumps(component.config), all_variables
            )
            component.config = json.loads(processed_config)
```

## Migration Strategy

### **Backwards Compatibility**

1. **Detection**: Check if config contains `clutter` key vs flat structure
2. **Graceful handling**: Support both formats during transition
3. **No breaking changes**: Existing test definitions continue working
4. **Deprecation warning**: Log when old flat format is detected

### **Migration Path**

```yaml
# Phase 1: Old format (still works)
config:
  count: 5
  pattern: "**/*.txt"

# Phase 2: New format (preferred)  
config:
  clutter:
    count: 5
    pattern: "**/*.txt"

# Phase 3: Extended format (future)
config:
  clutter:
    count: {{number1:3:8}}
    pattern: "**/*.{{entity1}}"
  performance:
    timeout: {{number2:30:120}}
  validation:
    strict_mode: true
```

## Benefits

### **Immediate Benefits**
- **Clearer semantics**: `config` used properly for component configuration
- **Variable expansion**: Enables `count: {{number1:3:8}}` in clutter config
- **Backwards compatibility**: No breaking changes to existing tests

### **Future Benefits**  
- **Infrastructure ready**: Proper config structure for Docker, services, etc.
- **Extensible**: Easy to add new config categories (performance, security, etc.)
- **Consistent**: Same config structure across all component types

## Success Criteria

- ✅ All existing test definitions continue working (backwards compatibility) **COMPLETED**
- ✅ New hierarchical `config.clutter` format works correctly **COMPLETED**
- ✅ Variable expansion works in config properties: `count: {{number1:5:10}}` **COMPLETED**
- ✅ Documentation reflects proper config structure **COMPLETED**
- ✅ Foundation laid for infrastructure component config needs **COMPLETED**

## Risk Assessment

**Low Risk**: 
- Backwards compatibility maintained throughout
- Internal refactoring only - no API changes
- Well-contained change scope

**Mitigation**:
- Comprehensive testing of both config formats
- Gradual rollout with old format support
- Clear migration documentation

## Implementation Status

### ✅ **COMPLETED - September 8, 2025**

**Implementation Summary:**
- Successfully implemented hierarchical config structure with full backwards compatibility
- All 6 file generators updated to support new `config` parameter instead of `clutter_spec`
- Added `_extract_clutter_config()` method for backwards-compatible clutter extraction
- Updated component orchestrator and precheck generator to use new structure
- Added variable expansion support for config properties (including clutter config)
- All test files updated to use new `config={'clutter': {...}}` format
- Updated documentation examples in REFERENCE.md to use new hierarchical syntax
- Comprehensive testing: 31/31 tests passing with no regressions

**Technical Details:**
- **Branch:** `fix/config-clutter-naming-in-sandbox`
- **Files Modified:** 6 (src/file_generators.py, src/component_orchestrator.py, src/precheck_generator.py, 3 test files)
- **Backwards Compatibility:** ✅ Old flat config format still works
- **Variable Support:** ✅ Config properties support `{{variable}}` expansion
- **Test Coverage:** ✅ All existing tests pass + new format validated

**Key Implementation Features:**
- Hierarchical config: `config.clutter.count` instead of flat `config.count`
- Automatic format detection for seamless backwards compatibility
- Variable expansion in all config properties (not just clutter)
- Foundation ready for future infrastructure components

**Commit:** `Fix clutter config naming and add hierarchical structure support`  
**Status:** Ready for code review and merge

---

*Plan created: September 6, 2025*  
*Implemented: September 8, 2025*  
*Priority: Medium (improves architecture, enables future features)*  
*Complexity: Low-Medium (mostly internal refactoring)*  
*Dependencies: None - self-contained improvement*