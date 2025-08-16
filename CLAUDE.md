# Claude Code Configuration for PICARD

This file contains configuration and workflow information for working with Claude Code on the PICARD project.

## Git Practices

### Commit Messages
All commits should follow this format:
```
Brief summary of changes (50 chars or less)

Optional detailed description explaining:
- What was changed
- Why it was changed  
- Any important implementation details

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Co-Authorship
Always include Claude as co-author on commits when working collaboratively:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Preferred Workflow

### Development Cycle
We follow a **small, frequent commits** approach:

1. **Small Code Changes** 
   - Focus on single features or fixes
   - Keep changes manageable and reviewable
   - Prefer multiple small commits over giant commits

2. **Commit + Push**
   - Commit immediately after completing a logical unit of work
   - Push to remote frequently to share progress
   - Use descriptive commit messages

3. **Test** *(Once pytest migration is complete)*
   - Run relevant tests after each commit
   - Ensure no regressions introduced
   - Add tests for new functionality

### Benefits of This Approach
- **Reduced Risk**: Smaller changes are easier to debug and revert
- **Better Collaboration**: Clear, focused commits improve code review
- **Faster Feedback**: Quick iterations catch issues early
- **Maintainable History**: Clean git history aids debugging and understanding
- **Reduced Merge Conflicts**: Frequent pushes minimize integration issues

## Commands for Quick Reference

### Standard Development Flow
```bash
# Make small, focused changes to code
# ...

# Stage and commit changes
git add <files>
git commit -m "Brief description

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push

# Run tests (once pytest is set up)
pytest
```

### Testing Commands *(Future)*
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_file_generators.py

# Run tests with coverage
pytest --cov=src

# Run only fast tests
pytest -m "not slow"
```

## File Organization for Claude Code

### Key Directories
- `src/` - Production code
- `tests/` - Test code (pytest-based)
- `PLANS/` - Planning documents and roadmaps
- `config/` - Configuration files and templates
- `results/` - Test run results and analysis

### Files Claude Should Know About
- `picard_config.py` - Main configuration
- `requirements.txt` - Python dependencies  
- `src/file_generators.py` - File generation infrastructure
- `src/template_functions.py` - Template processing functions
- `src/scorer.py` - Scoring and evaluation logic

## Quality Standards

### Code Quality
- Follow existing code patterns and conventions
- Include docstrings for new functions and classes
- Handle errors gracefully with meaningful messages
- Use type hints where beneficial

### Testing Philosophy
- Write tests for new functionality
- Maintain existing test coverage
- Prefer deterministic tests over probabilistic ones
- Use fixtures for reusable test data

### Documentation
- Update relevant documentation when making changes
- Keep README.md current with new features
- Document breaking changes clearly
- Maintain this CLAUDE.md file as workflow evolves

---

*This file serves as the working agreement between human and AI for collaborative development on PICARD.*