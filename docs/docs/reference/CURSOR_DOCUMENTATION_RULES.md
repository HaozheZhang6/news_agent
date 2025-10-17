# Cursor Documentation Alignment Rules

## Overview
This document defines rules for maintaining alignment between code development and documentation in the `docs/` directory, ensuring good traceability, version history, and modularized architecture.

## 1. Documentation-First Development Workflow

### Rule 1.1: Always Update Documentation Before Code Changes
```markdown
**MANDATORY**: Before making any code changes, update relevant documentation files:

1. **Architecture Changes**: Update `docs/reference/SYSTEM_DESIGN_CURRENT.md`
2. **API Changes**: Update `docs/reference/API_DESIGN.md`
3. **New Features**: Create/update feature-specific guides in `docs/reference/`
4. **Bug Fixes**: Update troubleshooting guides in `docs/reference/`
5. **Testing**: Update test documentation in `docs/TESTING.md`

**Process**:
1. Read existing documentation
2. Update documentation first
3. Implement code changes
4. Verify documentation accuracy
5. Update version history
```

### Rule 1.2: Documentation Update Checklist
```markdown
Before committing any changes, verify:

□ Updated relevant documentation files
□ Added version history entries
□ Updated function/module overviews
□ Added usage examples
□ Updated troubleshooting guides (if applicable)
□ Verified all links work
□ Checked for broken references
```

## 2. Traceability and Version History

### Rule 2.1: Version History Tracking
```markdown
**MANDATORY**: Every significant change must include version history:

**File**: `docs/VERSION.md`
**Format**:
```markdown
## Version History

### [Version] - [Date] - [Change Type]
- **Files Modified**: [list of files]
- **Documentation Updated**: [list of docs]
- **Breaking Changes**: [if any]
- **New Features**: [list]
- **Bug Fixes**: [list]
- **Performance Improvements**: [list]
- **Migration Notes**: [if applicable]
```

**Example**:
```markdown
### v2.1.0 - 2025-01-16 - Feature Release
- **Files Modified**: 
  - `src/agent.py` - Added streaming LLM support
  - `backend/app/core/streaming_handler.py` - New streaming pipeline
- **Documentation Updated**:
  - `docs/reference/SRC_STREAMING_GUIDE.md` - New streaming guide
  - `docs/reference/STREAMING_LLM_TTS_SUMMARY.md` - Implementation summary
- **New Features**: 
  - Streaming LLM responses with concurrent TTS
  - ~80% reduction in time-to-first-audio
- **Performance Improvements**:
  - Concurrent TTS generation
  - Sentence-based streaming triggers
```
```

### Rule 2.2: Change Documentation Template
```markdown
**MANDATORY**: Use this template for documenting changes:

```markdown
## Change Documentation Template

### Change ID: [CHG-YYYY-MM-DD-XXX]
**Date**: [YYYY-MM-DD]
**Type**: [Feature|Bug Fix|Refactor|Performance|Documentation]
**Priority**: [High|Medium|Low]

### Description
[Brief description of the change]

### Files Modified
- `path/to/file1.py` - [Description of changes]
- `path/to/file2.tsx` - [Description of changes]

### Documentation Updated
- `docs/reference/FILE.md` - [Description of updates]

### Testing
- [ ] Unit tests updated
- [ ] Integration tests updated
- [ ] E2E tests updated
- [ ] Documentation tests pass

### Migration Notes
[If applicable, describe any migration steps needed]

### Rollback Plan
[Describe how to rollback this change if needed]
```
```

## 3. Modularized Architecture Design

### Rule 3.1: Architecture Documentation Structure
```markdown
**MANDATORY**: Maintain these architecture documentation files:

1. **System Design**: `docs/reference/SYSTEM_DESIGN_CURRENT.md`
   - High-level architecture overview
   - Component relationships
   - Data flow diagrams
   - Technology stack

2. **API Design**: `docs/reference/API_DESIGN.md`
   - REST API endpoints
   - WebSocket events
   - Request/response schemas
   - Authentication

3. **Database Design**: `docs/reference/DATABASE_SETUP.md`
   - Database schema
   - Table relationships
   - Migration scripts
   - Data models

4. **Component Documentation**: `docs/reference/[COMPONENT]_GUIDE.md`
   - Individual component documentation
   - Usage examples
   - Configuration options
   - Troubleshooting
```

### Rule 3.2: Function Overview Documentation
```markdown
**MANDATORY**: Every major function/module must have documentation:

**Template**:
```markdown
## [Module/Function Name]

### Purpose
[What this function/module does]

### Parameters
- `param1` (type): [Description]
- `param2` (type): [Description]

### Returns
[What the function returns]

### Usage Example
```python
# Example usage
result = function_name(param1, param2)
```

### Dependencies
- [List of dependencies]

### Related Functions
- [List of related functions]

### Error Handling
[How errors are handled]

### Performance Notes
[Any performance considerations]
```

**Location**: Add to relevant guide in `docs/reference/`
```

## 4. Usage Inquiry and Examples

### Rule 4.1: Usage Documentation Requirements
```markdown
**MANDATORY**: Every feature must include:

1. **Quick Start Guide**: 5-minute setup
2. **Usage Examples**: Real-world examples
3. **Configuration Options**: All available settings
4. **Troubleshooting**: Common issues and solutions
5. **API Reference**: Complete API documentation

**Template Structure**:
```markdown
# [Feature Name] Guide

## Quick Start
[5-minute setup instructions]

## Usage Examples
### Basic Usage
[Simple example]

### Advanced Usage
[Complex example]

### Configuration
[All configuration options]

### Troubleshooting
[Common issues and solutions]

### API Reference
[Complete API documentation]
```
```

### Rule 4.2: Example Code Standards
```markdown
**MANDATORY**: All code examples must:

1. **Be Runnable**: Examples must work without modification
2. **Include Imports**: Show all necessary imports
3. **Show Error Handling**: Include proper error handling
4. **Be Documented**: Include comments explaining each step
5. **Be Tested**: All examples must be tested

**Template**:
```python
"""
Example: [Description]
Author: [Your Name]
Date: [Date]
Version: [Version]
"""

# Required imports
from typing import List, Dict, Any
import asyncio

async def example_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Example function demonstrating [feature].
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Returns:
        Dictionary containing results
        
    Raises:
        ValueError: If parameters are invalid
    """
    try:
        # Implementation here
        result = {"status": "success", "data": "example"}
        return result
    except Exception as e:
        # Error handling
        raise ValueError(f"Error in example_function: {e}")

# Usage example
if __name__ == "__main__":
    async def main():
        result = await example_function("test", 42)
        print(result)
    
    asyncio.run(main())
```
```

## 5. Documentation Maintenance Rules

### Rule 5.1: Regular Documentation Reviews
```markdown
**SCHEDULE**: Weekly documentation review

**Checklist**:
- [ ] All code changes have corresponding documentation
- [ ] All links are working
- [ ] All examples are runnable
- [ ] Version history is up to date
- [ ] Architecture diagrams are current
- [ ] API documentation matches implementation
- [ ] Troubleshooting guides cover recent issues
```

### Rule 5.2: Documentation Testing
```markdown
**MANDATORY**: Test documentation regularly:

1. **Link Testing**: Verify all internal links work
2. **Example Testing**: Run all code examples
3. **Accuracy Testing**: Verify documentation matches code
4. **Completeness Testing**: Ensure all features are documented

**Tools**:
- Use `markdown-link-check` for link validation
- Use `doctest` for Python example testing
- Use `jest` for JavaScript example testing
```

## 6. Cursor-Specific Rules

### Rule 6.1: Cursor AI Assistant Guidelines
```markdown
**When using Cursor AI Assistant**:

1. **Always Reference Documentation**: 
   - Start by reading relevant docs in `docs/reference/`
   - Reference existing patterns and examples
   - Follow established naming conventions

2. **Update Documentation First**:
   - Ask AI to update documentation before code changes
   - Ensure AI understands the current architecture
   - Verify AI suggestions align with existing patterns

3. **Maintain Consistency**:
   - Use AI to check for consistency with existing code
   - Ensure AI follows established error handling patterns
   - Verify AI suggestions match documentation standards
```

### Rule 6.2: Cursor Workspace Configuration
```markdown
**Recommended Cursor Settings**:

```json
{
  "cursor.ai.enableDocumentation": true,
  "cursor.ai.referenceDocs": [
    "docs/reference/SYSTEM_DESIGN_CURRENT.md",
    "docs/reference/API_DESIGN.md",
    "docs/reference/DATABASE_SETUP.md"
  ],
  "cursor.ai.codeStyle": "docs/reference/CODE_STYLE_GUIDE.md",
  "cursor.ai.testingPatterns": "docs/TESTING.md"
}
```

**Custom Instructions**:
```
Always reference the documentation in docs/reference/ before making suggestions.
Follow the established architecture patterns and naming conventions.
Update documentation when suggesting code changes.
Include proper error handling and testing in all suggestions.
```
```

## 7. Implementation Checklist

### Rule 7.1: Pre-Development Checklist
```markdown
Before starting any development work:

- [ ] Read relevant documentation in `docs/reference/`
- [ ] Understand current architecture from `SYSTEM_DESIGN_CURRENT.md`
- [ ] Check API design in `API_DESIGN.md`
- [ ] Review existing patterns and conventions
- [ ] Plan documentation updates needed
- [ ] Set up proper version tracking
```

### Rule 7.2: During Development Checklist
```markdown
During development:

- [ ] Update documentation as you code
- [ ] Add inline comments referencing docs
- [ ] Follow established patterns
- [ ] Test all code examples
- [ ] Verify error handling matches docs
- [ ] Check for breaking changes
```

### Rule 7.3: Post-Development Checklist
```markdown
After completing development:

- [ ] Update version history in `VERSION.md`
- [ ] Verify all documentation is current
- [ ] Test all examples work
- [ ] Check all links work
- [ ] Update troubleshooting guides if needed
- [ ] Review for consistency
- [ ] Commit documentation changes with code
```

## 8. Tools and Automation

### Rule 8.1: Documentation Automation
```markdown
**Recommended Tools**:

1. **Pre-commit Hooks**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-docs
        name: Check Documentation
        entry: python scripts/check_docs.py
        language: python
        files: \.(py|tsx|ts)$
```

2. **Documentation Testing**:
```python
# scripts/test_docs.py
import subprocess
import sys

def test_documentation():
    """Test all documentation examples."""
    # Test Python examples
    subprocess.run(["python", "-m", "doctest", "docs/reference/*.md"])
    
    # Test links
    subprocess.run(["markdown-link-check", "docs/reference/*.md"])
    
    # Test examples
    subprocess.run(["python", "scripts/test_examples.py"])

if __name__ == "__main__":
    test_documentation()
```

3. **Version Tracking**:
```python
# scripts/update_version.py
import datetime
import re

def update_version_history(change_type, description, files_modified):
    """Update version history automatically."""
    version_file = "docs/VERSION.md"
    today = datetime.date.today()
    
    # Generate version entry
    entry = f"""
### v{get_next_version()} - {today} - {change_type}
- **Files Modified**: {', '.join(files_modified)}
- **Description**: {description}
- **Documentation Updated**: [Auto-generated]
"""
    
    # Append to version file
    with open(version_file, "a") as f:
        f.write(entry)
```

### Rule 8.2: Cursor Integration Scripts
```markdown
**Create these helper scripts**:

1. **`scripts/sync_docs.py`**: Sync code changes with documentation
2. **`scripts/validate_examples.py`**: Validate all code examples
3. **`scripts/check_consistency.py`**: Check code-docs consistency
4. **`scripts/generate_api_docs.py`**: Auto-generate API documentation
```

## 9. Quality Assurance

### Rule 9.1: Documentation Quality Metrics
```markdown
**Track these metrics**:

1. **Coverage**: % of code covered by documentation
2. **Accuracy**: % of docs matching current code
3. **Completeness**: % of features documented
4. **Usability**: % of examples that work
5. **Maintenance**: Time since last doc update

**Targets**:
- Coverage: >90%
- Accuracy: >95%
- Completeness: >95%
- Usability: >90%
- Maintenance: <7 days
```

### Rule 9.2: Review Process
```markdown
**Documentation Review Process**:

1. **Self-Review**: Developer reviews own documentation
2. **Peer Review**: Another developer reviews documentation
3. **Technical Review**: Senior developer reviews technical accuracy
4. **User Testing**: Test documentation with new users
5. **Continuous Improvement**: Regular feedback and updates
```

## 10. Emergency Procedures

### Rule 10.1: Documentation Recovery
```markdown
**If documentation becomes out of sync**:

1. **Immediate**: Stop all development
2. **Assess**: Determine scope of inconsistency
3. **Prioritize**: Fix critical documentation first
4. **Update**: Bring documentation up to date
5. **Verify**: Test all examples and links
6. **Prevent**: Implement better processes
```

### Rule 10.2: Rollback Procedures
```markdown
**If documentation changes cause issues**:

1. **Identify**: Find the problematic documentation
2. **Revert**: Rollback to last known good version
3. **Fix**: Correct the issue
4. **Test**: Verify the fix works
5. **Deploy**: Re-deploy corrected documentation
6. **Monitor**: Watch for similar issues
```

---

## Summary

These rules ensure that:

1. **Traceability**: Every change is tracked and documented
2. **Version History**: Complete history of all changes
3. **Modular Architecture**: Well-documented, maintainable design
4. **Usage Inquiry**: Clear examples and guides for all features
5. **Quality Assurance**: Regular testing and validation
6. **Cursor Integration**: AI assistant follows established patterns

**Remember**: Documentation is not an afterthought—it's a core part of the development process. Always update documentation first, then implement code changes.
