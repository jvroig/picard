# PICARD Demos

This directory contains demonstration scripts that showcase PICARD's features and capabilities. These are separate from the formal test suite and serve as:

- **User-facing examples** of how to use PICARD features
- **Feature showcases** for stakeholders and documentation
- **End-to-end validation** of real-world usage patterns
- **Living documentation** that demonstrates value and usability

## Available Demos

### `enhanced_variable_substitution.py`
Demonstrates the enhanced variable substitution system with:
- Semantic variables using all 42 data types
- Numeric range variables with different formatting types
- Enhanced entity pools (colors, metals, gems, nature)
- Legacy backwards compatibility
- Variable consistency across templates

**Usage:**
```bash
source venv/bin/activate
python demos/enhanced_variable_substitution.py
```

## Demo Standards

### Purpose
Demos should show **real-world value** and **practical usage patterns**, not just technical correctness. Focus on:
- Business scenarios that users would actually encounter
- Multiple features working together seamlessly
- Clear output that demonstrates the benefits

### Organization
- Each demo should be a standalone script that can run independently
- Include clear output showing what each feature does
- Provide examples that users can adapt for their own needs
- Document any setup requirements or dependencies

### Maintenance
- Keep demos updated when new features are added
- Ensure demos continue to work as the codebase evolves
- Remove or update demos if underlying features change

## Relationship to Tests

**Demos complement but don't replace the formal test suite:**

| Aspect | Formal Tests | Demos |
|--------|-------------|-------|
| **Purpose** | Validation & regression testing | Feature showcase & documentation |
| **Audience** | CI/CD systems, developers | Users, stakeholders, new developers |
| **Focus** | Edge cases, error conditions | Real-world usage patterns |
| **Design** | Isolated, fast, deterministic | Comprehensive, demonstrative |
| **Maintenance** | Must never change behavior | Can be updated to show new features |

Both are essential for a complete feature implementation.