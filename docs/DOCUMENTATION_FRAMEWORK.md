# Documentation Framework for Fast Root Causing

**Version:** 1.0
**Last Updated:** 2025-10-15
**Purpose:** Enable rapid problem diagnosis and maintain organized documentation structure

---

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [Tree-Based Architecture](#tree-based-architecture)
3. [Document Types & Templates](#document-types--templates)
4. [Root Cause Analysis System](#root-cause-analysis-system)
5. [Folder Organization Guidelines](#folder-organization-guidelines)
6. [Quick Navigation System](#quick-navigation-system)
7. [Maintenance Guidelines](#maintenance-guidelines)

---

## Framework Overview

### Core Principles

1. **Hierarchical Organization**: Tree structure from general to specific
2. **Fast Searchability**: Clear naming conventions and indexes
3. **Root Cause Focus**: Every fix documented with problem → diagnosis → solution
4. **Living Documentation**: Updated with every significant change
5. **Cross-Referencing**: Linked documents for related information

### Documentation Hierarchy (Docsify-Ready)

```
docs/                                    # Overview & Getting Started (Docsify root)
├── README.md                            # Documentation hub & landing page
├── overview.md                          # System overview & value proposition
├── getting-started.md                   # Quick start (5-10 min setup)
├── architecture-overview.md             # High-level architecture diagram
├── troubleshooting.md                   # Quick troubleshooting reference
├── faq.md                               # Frequently asked questions
├── _sidebar.md                          # Docsify sidebar navigation
├── _navbar.md                           # Docsify top navigation
├── index.html                           # Docsify entry point
├── .nojekyll                            # Disable GitHub Jekyll processing
│
└── reference/                           # Detailed technical documentation
    ├── README.md                        # Reference hub & index
    │
    ├── setup/                           # Setup & deployment details
    │   ├── README.md                    # Setup index
    │   ├── local-setup.md               # Detailed local development setup
    │   ├── production-deployment.md     # Render/production deployment
    │   ├── environment-config.md        # Environment variables & config
    │   └── testing.md                   # Testing setup & execution
    │
    ├── architecture/                    # System design deep-dive
    │   ├── README.md                    # Architecture index
    │   ├── system-design.md             # Complete system design doc
    │   ├── api-design.md                # REST & WebSocket API specs
    │   ├── data-flow.md                 # Data flow diagrams & sequences
    │   ├── database-schema.md           # Supabase schema & models
    │   ├── components/                  # Component-level documentation
    │   │   ├── README.md
    │   │   ├── frontend.md              # Frontend architecture
    │   │   ├── backend.md               # Backend architecture
    │   │   ├── database.md              # Database design
    │   │   ├── caching.md               # Redis caching strategy
    │   │   └── websocket.md             # WebSocket implementation
    │   └── decisions/                   # Architecture Decision Records (ADRs)
    │       ├── README.md                # ADR index
    │       ├── adr-001-asr-selection.md
    │       ├── adr-002-audio-format.md
    │       └── adr-003-deployment-strategy.md
    │
    ├── guides/                          # Implementation & how-to guides
    │   ├── README.md                    # Guides index
    │   ├── audio-pipeline.md            # Audio capture → encoding → transfer
    │   ├── voice-detection.md           # VAD implementation & tuning
    │   ├── websocket-streaming.md       # Real-time streaming setup
    │   ├── memory-system.md             # Conversation memory implementation
    │   ├── command-queue.md             # Priority queue system
    │   └── testing-guide.md             # Comprehensive testing guide
    │
    ├── troubleshooting/                 # Root cause analysis & fixes
    │   ├── README.md                    # Troubleshooting hub with diagnostic tree
    │   ├── symptoms/                    # Organized by user-visible symptom
    │   │   ├── README.md
    │   │   ├── connection-issues.md     # WebSocket disconnects, timeouts
    │   │   ├── audio-problems.md        # No audio, distorted audio
    │   │   ├── performance-issues.md    # Latency, slow response
    │   │   └── deployment-errors.md     # Render deployment failures
    │   ├── fixes/                       # Detailed fix documentation (RCA)
    │   │   ├── README.md
    │   │   ├── websocket-fixes.md       # WebSocket connection fixes
    │   │   ├── audio-pipeline-fixes.md  # Audio processing fixes
    │   │   ├── vad-fixes.md             # Voice detection fixes
    │   │   └── deployment-fixes.md      # Deployment issue fixes
    │   └── incidents/                   # Post-mortem incident reports
    │       ├── README.md                # Incident log & patterns
    │       ├── 2025-10-13-websocket-disconnect.md
    │       └── 2025-10-14-vad-threshold.md
    │
    ├── api/                             # API reference documentation
    │   ├── README.md                    # API overview
    │   ├── rest-endpoints.md            # REST API endpoints
    │   ├── websocket-protocol.md        # WebSocket message protocol
    │   ├── models.md                    # Request/response models
    │   └── errors.md                    # Error codes & handling
    │
    └── optimization/                    # Performance & optimization
        ├── README.md                    # Optimization index
        ├── latency-optimization.md      # Reducing end-to-end latency
        ├── caching-strategy.md          # Redis caching patterns
        ├── resource-usage.md            # Memory & CPU optimization
        └── monitoring.md                # Monitoring & observability
```

**Key Principles:**
- **docs/**: High-level overview docs (≤ 10 pages) for quick understanding
- **docs/reference/**: Deep-dive technical docs with full implementation details
- **Naming**: Use kebab-case for Docsify URL compatibility (e.g., `local-setup.md` → `/reference/setup/local-setup`)
- **Cross-linking**: Relative paths work across both structures
- **Docsify-ready**: All paths compatible with Docsify's routing

---

## Tree-Based Architecture

### Level 1: Root Documentation Hub

**Location:** [`docs/README.md`](README.md)

**Purpose:** Entry point for all documentation

**Contents:**
- Quick start guide
- Documentation tree map
- Common tasks shortcuts
- Emergency troubleshooting links

### Level 2: Category Indexes

**Locations:**
- `docs/README.md` - User guides
- `reference/DOCUMENTATION_INDEX.md` - Technical references
- `troubleshooting/README.md` - Problem solving
- `architecture/README.md` - System design

**Purpose:** Navigate to specific topic areas

### Level 3: Topic Documentation

**Examples:**
- `docs/LOCAL_SETUP.md` - Setup procedures
- `reference/SYSTEM_DESIGN_CURRENT.md` - Architecture
- `troubleshooting/symptoms/audio_problems.md` - Diagnosis

**Purpose:** Detailed information on specific topics

### Level 4: Implementation Details

**Examples:**
- Code files with inline documentation
- Test files with usage examples
- Configuration files with comments

**Purpose:** Specific implementation references

---

## Document Types & Templates

### 1. FIXES Documents (Root Cause Analysis)

**Template:** `troubleshooting/root_causes/PROBLEM_FIXES.md`

```markdown
# [Component] Fixes: [Problem Summary]

**Status:** ✅ Fixed | 🚧 In Progress | ⚠️ Workaround
**Severity:** Critical | High | Medium | Low
**Date Fixed:** YYYY-MM-DD
**Affected Versions:** vX.X.X - vX.X.X

---

## Symptoms

### User-Facing Symptoms
- What users experienced
- Error messages shown
- Behavior observed

### Technical Symptoms
- Logs/errors in console
- Specific failures
- Reproducible steps

---

## Root Cause Analysis

### Investigation Process
1. Initial hypothesis
2. Tests performed
3. Data collected
4. Actual root cause discovered

### Technical Explanation
- Why it failed
- What was wrong
- System interaction diagram

### Code References
- File: `path/to/file.ts:line_number`
- Function: `functionName()`
- Related components

---

## Solution Implemented

### Changes Made
1. **File:** `path/to/file.ts:lines`
   - What changed
   - Why this approach

2. **File:** `other/file.py:lines`
   - Related changes
   - Dependencies updated

### Configuration Changes
- Environment variables
- Config file updates
- Feature flags

---

## Verification

### Test Cases
- [ ] Test case 1
- [ ] Test case 2
- [ ] Regression test

### Performance Impact
- Before: [metrics]
- After: [metrics]
- Improvement: [percentage]

---

## Prevention

### Monitoring Added
- Logs added at: `file:line`
- Metrics tracked: [metrics]
- Alerts configured: [alert conditions]

### Documentation Updated
- [ ] User guide updated
- [ ] API docs updated
- [ ] Troubleshooting guide updated

---

## Related Issues

- **Similar Issues:** [#123](link), [#456](link)
- **Related Docs:** [SYSTEM_DESIGN.md](link)
- **Follow-up Tasks:** [TODO.md#task](link)

---

## Quick Reference

**To diagnose similar issues:**
1. Check logs at: [location]
2. Verify config: [settings]
3. Test with: [test command]

**Emergency rollback:**
```bash
git revert [commit-hash]
make deploy
```
```

### 2. GUIDE Documents (Implementation Guides)

**Template:** `reference/FEATURE_GUIDE.md`

```markdown
# [Feature] Implementation Guide

**Purpose:** [One-line description]
**Target Audience:** [Frontend/Backend/Full-stack] developers
**Estimated Time:** [X] hours
**Prerequisites:** [Required knowledge/setup]

---

## Overview

### What This Guide Covers
- Topic 1
- Topic 2
- Topic 3

### System Context
- Where this fits in the architecture
- Related components
- Dependencies

---

## Step-by-Step Implementation

### Step 1: [Task Name]

**What:** Brief description

**Why:** Rationale

**How:**
```typescript
// Code example with comments
function example() {
  // Implementation
}
```

**Files Modified:**
- `path/to/file.ts:lines`

**Testing:**
```bash
# Test command
npm test path/to/test
```

### Step 2: [Next Task]
[Repeat structure]

---

## Configuration

### Environment Variables
```bash
VARIABLE_NAME=value  # Description
```

### Feature Flags
```typescript
const config = {
  featureName: true,  // Enable this feature
};
```

---

## Testing

### Unit Tests
- Test file: `tests/unit/test_feature.ts`
- Run: `npm test unit/test_feature`

### Integration Tests
- Test file: `tests/integration/test_feature_integration.ts`
- Run: `npm test integration`

### Manual Testing Checklist
- [ ] Test case 1
- [ ] Test case 2
- [ ] Edge case 3

---

## Troubleshooting

### Common Issues

#### Issue: [Problem description]
**Symptom:** What you see
**Cause:** Why it happens
**Solution:** How to fix
**Related:** [Link to FIXES doc]

---

## Performance Considerations

- Metric 1: [expected value]
- Metric 2: [expected value]
- Optimization tips

---

## References

- **Architecture:** [SYSTEM_DESIGN.md](link)
- **API Spec:** [API_DESIGN.md](link)
- **Related Guides:** [OTHER_GUIDE.md](link)
```

### 3. TROUBLESHOOTING Documents

**Template:** `troubleshooting/symptoms/SYMPTOM_NAME.md`

```markdown
# Troubleshooting: [Symptom Category]

**Quick Links:**
- [Most Common Issue](#most-common)
- [Emergency Fixes](#emergency-fixes)
- [Root Cause Index](#root-causes)

---

## Symptom Index

### [Symptom 1]: [Brief Description]

**Indicators:**
- Error message: `error text`
- Log entry: `log pattern`
- User sees: [behavior]

**Quick Check:**
```bash
# Command to diagnose
make check-something
```

**Common Causes:**
1. **[Root Cause 1]** (70% of cases)
   - **Solution:** [Quick fix]
   - **Details:** [Link to FIXES doc]

2. **[Root Cause 2]** (20% of cases)
   - **Solution:** [Quick fix]
   - **Details:** [Link to FIXES doc]

3. **[Root Cause 3]** (10% of cases)
   - **Solution:** [Quick fix]
   - **Details:** [Link to FIXES doc]

**Diagnostic Tree:**
```
Is error X present?
├─ Yes → Check configuration Y
│  ├─ Y is correct → Issue: Root Cause 1
│  └─ Y is incorrect → Fix Y, restart
└─ No → Check logs Z
   ├─ Z shows error → Issue: Root Cause 2
   └─ Z is clean → Issue: Root Cause 3
```

---

## Emergency Fixes

### Quick Restart
```bash
make restart
# Fixes: transient connection issues
```

### Clear Cache
```bash
make clean-cache
# Fixes: stale data issues
```

### Reset Configuration
```bash
make reset-config
# Fixes: corrupted config
```

---

## Root Cause Details

### [Root Cause 1]: [Name]

**What Happens:**
- Technical explanation

**Why It Happens:**
- Underlying reason

**How to Fix:**
1. Step 1
2. Step 2
3. Verify: `test command`

**Prevent Future Occurrence:**
- Monitoring added
- Configuration validated

**Full Details:** [Link to detailed FIXES doc]

---

## Diagnostic Commands

### Check System Health
```bash
make health-check
# Expected output: all services "OK"
```

### View Recent Errors
```bash
make logs-errors
# Look for: [pattern]
```

### Test Components
```bash
make test-component NAME
# Tests specific component
```

---

## Getting Help

**Still stuck? Follow this order:**

1. **Check Recent Changes**
   - `git log --oneline -n 10`
   - Did a recent commit break it?

2. **Verify Environment**
   - `make verify-env`
   - Are all variables set?

3. **Review Related Issues**
   - [Similar Issue #123](link)
   - [Similar Issue #456](link)

4. **Create Debug Report**
   ```bash
   make debug-report > debug.txt
   # Attach to issue
   ```

---

## Related Documentation

- **Architecture:** [SYSTEM_DESIGN.md](link)
- **Detailed Fixes:** [FIXES_INDEX.md](link)
- **Performance:** [OPTIMIZATION_GUIDE.md](link)
```

### 4. ARCHITECTURE DECISION RECORDS (ADRs)

**Template:** `architecture/decisions/ADR-XXX-decision-name.md`

```markdown
# ADR-XXX: [Decision Title]

**Status:** Accepted | Rejected | Superseded | Deprecated
**Date:** YYYY-MM-DD
**Deciders:** [Names]
**Related ADRs:** [Links]

---

## Context

What is the issue we're facing?

- Current situation
- Constraints
- Requirements

---

## Decision

What did we decide?

Brief statement of the decision.

---

## Options Considered

### Option 1: [Name]

**Pros:**
- Advantage 1
- Advantage 2

**Cons:**
- Disadvantage 1
- Disadvantage 2

**Estimated Effort:** [Time/complexity]

### Option 2: [Name]
[Same structure]

### Option 3: [Name]
[Same structure]

---

## Rationale

Why did we choose this option?

- Key factors
- Trade-offs accepted
- Risk mitigation

---

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Trade-off 1
- Trade-off 2

### Neutral
- Impact 1

---

## Implementation

### Changes Required
- Component 1: [changes]
- Component 2: [changes]

### Migration Plan
1. Step 1
2. Step 2
3. Rollout strategy

### Success Metrics
- Metric 1: [target]
- Metric 2: [target]

---

## References

- **Technical Spec:** [Link]
- **Discussion:** [Issue/PR link]
- **Related Docs:** [Links]
```

---

## Root Cause Analysis System

### RCA Process Framework

#### Phase 1: Detection (Minutes 0-5)

```markdown
## Incident Detection

**When:** [Timestamp]
**Detected By:** [Monitoring/User report]
**Severity:** [Critical/High/Medium/Low]
**Impact:** [Services/users affected]

### Immediate Actions Taken
- [ ] Service status checked
- [ ] Error logs collected
- [ ] Recent changes reviewed
- [ ] Incident channel created
```

#### Phase 2: Triage (Minutes 5-15)

```markdown
## Triage

### Symptoms Observed
1. [User-facing symptom]
2. [System-level symptom]
3. [Metrics deviation]

### Initial Hypothesis
- **Primary hypothesis:** [What we think]
- **Confidence:** High/Medium/Low
- **Quick test:** [How to verify]

### Workaround Applied
- **Action:** [What was done]
- **Status:** [Working/Not working]
- **ETA for fix:** [Estimate]
```

#### Phase 3: Investigation (Minutes 15-60)

```markdown
## Root Cause Investigation

### Investigation Timeline

#### Test 1: [Hypothesis]
- **Tested:** [What was checked]
- **Method:** [How it was tested]
- **Result:** ✅ Confirmed | ❌ Ruled out
- **Conclusion:** [Finding]

#### Test 2: [Next hypothesis]
[Same structure]

### Root Cause Identified

**Component:** [System component]
**File:** `path/to/file:line`
**Issue:** [Technical explanation]
**Why it failed:** [Root cause analysis]

### Contributing Factors
1. Factor 1
2. Factor 2
3. Factor 3
```

#### Phase 4: Resolution (Minutes 60-120)

```markdown
## Solution Implementation

### Fix Applied

**Changes Made:**
1. **File:** `path/to/file:lines`
   ```diff
   - old code
   + new code
   ```

2. **Configuration:**
   ```
   VARIABLE=new_value
   ```

**Deployment:**
- Commit: [hash]
- Deploy time: [timestamp]
- Verification: [test results]

### Verification Steps
- [ ] Service health check passed
- [ ] Error rate returned to normal
- [ ] User functionality restored
- [ ] Regression tests passed
```

#### Phase 5: Prevention (Post-incident)

```markdown
## Prevention Measures

### Monitoring Added
1. **Metric:** [What to monitor]
   - **Alert:** [When to alert]
   - **Runbook:** [How to respond]

2. **Log:** [What to log]
   - **Location:** [Where]
   - **Format:** [How]

### Process Improvements
- [ ] Documentation updated
- [ ] Test coverage increased
- [ ] Alert configured
- [ ] Runbook created

### Follow-up Tasks
- [ ] [Task 1] - Owner: [Name] - Due: [Date]
- [ ] [Task 2] - Owner: [Name] - Due: [Date]
```

### RCA Document Template

**File:** `troubleshooting/incidents/YYYY-MM-DD-incident-name.md`

```markdown
# Incident: [Name] - [Date]

**Status:** Resolved | Investigating | Mitigated
**Severity:** P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)
**Duration:** [Start] to [End] ([Duration])
**Impact:** [Description]

---

## Executive Summary

[2-3 sentence summary for management]

**Root Cause:** [One sentence]
**Resolution:** [One sentence]
**Prevention:** [One sentence]

---

## Timeline

| Time | Event | Action Taken |
|------|-------|--------------|
| 14:23 | Incident detected | Team notified |
| 14:25 | Investigation started | Logs reviewed |
| 14:35 | Root cause identified | Fix deployed |
| 14:45 | Service restored | Monitoring confirmed |
| 15:00 | Post-mortem started | Documentation updated |

---

## Detection
[Phase 1 content]

## Triage
[Phase 2 content]

## Investigation
[Phase 3 content]

## Resolution
[Phase 4 content]

## Prevention
[Phase 5 content]

---

## Lessons Learned

### What Went Well
- Item 1
- Item 2

### What Could Be Improved
- Item 1
- Item 2

### Action Items
- [ ] [Action 1] - Owner - Due date
- [ ] [Action 2] - Owner - Due date

---

## References

- **Related Incidents:** [Links]
- **Documentation Updated:** [Links]
- **Code Changes:** [PR links]
```

---

## Folder Organization Guidelines

### Naming Conventions

#### Files

```
# Good examples
SYSTEM_DESIGN_CURRENT.md         # Current state emphasized
WEBSOCKET_FIXES.md                # Topic + document type
LOCAL_SETUP.md                    # Clear purpose
ADR-001-audio-format.md           # Numbered ADR

# Bad examples
design.md                         # Too vague
fixes.md                          # No topic specified
websocket.md                      # Missing document type
my-notes.md                       # Not descriptive
```

#### Folders

```
# Good examples
troubleshooting/symptoms/         # Organized by symptom
architecture/components/backend/  # Hierarchical structure
reference/guides/                 # Clear categorization

# Bad examples
misc/                             # Catch-all folder
temp/                             # Unclear purpose
docs2/                            # Duplicates existing
```

### Folder Structure Rules

1. **Maximum Depth:** 4 levels
   ```
   docs/category/subcategory/specific/file.md  # OK
   docs/a/b/c/d/e/file.md                      # Too deep
   ```

2. **README in Every Folder**
   - Purpose of folder
   - Index of contents
   - Quick links to key docs

3. **Related Files Together**
   ```
   reference/
   ├── AUDIO_PIPELINE_FIXES.md
   ├── AUDIO_FORMAT_CURRENT.md
   └── AUDIO_TESTING_GUIDE.md
   ```

4. **No Orphan Files**
   - Every file referenced in an index
   - Every file has a clear parent category

### Documentation Inventory

**File:** `.github/docs-inventory.json`

```json
{
  "last_audit": "2025-10-15",
  "total_docs": 87,
  "by_category": {
    "user_guides": 12,
    "technical_reference": 34,
    "troubleshooting": 15,
    "architecture": 26
  },
  "files": [
    {
      "path": "docs/LOCAL_SETUP.md",
      "category": "user_guides",
      "status": "up_to_date",
      "last_updated": "2025-10-15",
      "owner": "team",
      "related": ["docs/TESTING.md", "reference/SYSTEM_DESIGN.md"]
    }
  ]
}
```

---

## Quick Navigation System

### Documentation Hub

**File:** `docs/README.md`

```markdown
# Documentation Hub

## 🚨 Emergency

**System down?** → [Troubleshooting Index](troubleshooting/README.md)
**Recent change broke something?** → [Recent Incidents](troubleshooting/incidents/)
**Need to rollback?** → [Deployment Rollback](docs/DEPLOYMENT.md#rollback)

---

## 🎯 Quick Links by Role

### For Developers
- [Local Setup](docs/LOCAL_SETUP.md) - Get started in 5 minutes
- [System Architecture](architecture/overview/system_diagram.md)
- [API Reference](reference/API_DESIGN.md)
- [Testing Guide](docs/TESTING.md)

### For DevOps
- [Deployment Guide](docs/RENDER_DEPLOYMENT.md)
- [Monitoring Setup](reference/MONITORING.md)
- [Incident Runbooks](troubleshooting/runbooks/)

### For Product/QA
- [Feature Overview](reference/IMPLEMENTATION_SUMMARY.md)
- [User Flows](architecture/overview/user_flows.md)
- [Test Cases](tests/TEST_INDEX.md)

---

## 📚 Documentation by Topic

### Setup & Deployment
- [Local Setup](docs/LOCAL_SETUP.md)
- [Production Deployment](docs/RENDER_DEPLOYMENT.md)
- [Environment Configuration](reference/ENV_CONFIG.md)

### Architecture
- [System Design](architecture/overview/system_diagram.md)
- [Data Flow](architecture/overview/data_flow.md)
- [Component Details](architecture/components/)
- [Design Decisions](architecture/decisions/)

### Implementation Guides
- [Audio Pipeline](reference/AUDIO_PIPELINE_GUIDE.md)
- [WebSocket Streaming](reference/STREAMING_GUIDE.md)
- [Voice Detection](reference/VAD_GUIDE.md)

### Troubleshooting
- [Connection Issues](troubleshooting/symptoms/connection_issues.md)
- [Audio Problems](troubleshooting/symptoms/audio_problems.md)
- [Performance Issues](troubleshooting/symptoms/performance_issues.md)
- [All Incidents](troubleshooting/incidents/)

---

## 🔍 Find Documentation

### By Symptom
"WebSocket disconnects immediately" → [Connection Issues](troubleshooting/symptoms/connection_issues.md#websocket-disconnect)

"No audio capture" → [Audio Problems](troubleshooting/symptoms/audio_problems.md#no-capture)

"Slow response time" → [Performance Issues](troubleshooting/symptoms/performance_issues.md#latency)

### By Component
- **Frontend** → [architecture/components/frontend/](architecture/components/frontend/)
- **Backend** → [architecture/components/backend/](architecture/components/backend/)
- **Database** → [architecture/components/database/](architecture/components/database/)

### By Task
- "I want to add a new feature" → [Development Guide](docs/DEVELOPMENT.md)
- "I need to debug an issue" → [Debugging Guide](docs/DEBUGGING.md)
- "I'm deploying to production" → [Deployment Checklist](docs/DEPLOYMENT.md#checklist)

---

## 📋 Document Index

[Complete alphabetical index with descriptions]

---

## 🔧 Maintenance

**Documentation Owner:** Development Team
**Review Frequency:** Monthly
**Last Updated:** 2025-10-15
**Next Review:** 2025-11-15
```

### Search Helper Script

**File:** `scripts/search-docs.sh`

```bash
#!/bin/bash
# Quick documentation search

QUERY="$1"
DOCS_DIR="$(git rev-parse --show-toplevel)"

if [ -z "$QUERY" ]; then
  echo "Usage: ./search-docs.sh <search-term>"
  echo "Example: ./search-docs.sh 'websocket error'"
  exit 1
fi

echo "Searching documentation for: $QUERY"
echo "================================"

# Search in markdown files
grep -rn --color=always "$QUERY" \
  "$DOCS_DIR/docs" \
  "$DOCS_DIR/reference" \
  "$DOCS_DIR/troubleshooting" \
  "$DOCS_DIR/architecture" \
  --include="*.md"

echo ""
echo "Search complete. Files listed above."
```

---

## Maintenance Guidelines

### Regular Reviews

#### Weekly Review
- [ ] Check for outdated "Last Updated" dates
- [ ] Verify recent code changes reflected in docs
- [ ] Update status badges (🚧 → ✅)
- [ ] Review and close resolved issues

#### Monthly Audit
- [ ] Full documentation inventory
- [ ] Dead link check
- [ ] Consistency review (terminology, formatting)
- [ ] Update statistics (document count, lines, etc.)
- [ ] Archive outdated incident reports

#### Quarterly Overhaul
- [ ] Major documentation reorganization if needed
- [ ] Template updates
- [ ] Index regeneration
- [ ] External link verification
- [ ] Accessibility check

### Documentation Quality Checklist

#### New Document Checklist
- [ ] Clear title and purpose statement
- [ ] Table of contents (if >300 lines)
- [ ] Code examples tested
- [ ] Links verified
- [ ] Added to appropriate index
- [ ] Cross-references updated
- [ ] Peer reviewed
- [ ] Spellchecked

#### Update Checklist
- [ ] "Last Updated" date changed
- [ ] Version/status updated if relevant
- [ ] Related docs checked for consistency
- [ ] Index updated if title/location changed
- [ ] Git commit follows conventions

### Automated Checks

**File:** `.github/workflows/docs-check.yml`

```yaml
name: Documentation Check

on: [push, pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check for broken links
        run: |
          npm install -g markdown-link-check
          find . -name "*.md" -exec markdown-link-check {} \;

      - name: Check for outdated docs
        run: |
          # Find docs not updated in >90 days
          find docs reference troubleshooting architecture \
            -name "*.md" -mtime +90 \
            -exec echo "WARNING: {} may be outdated" \;

      - name: Verify index completeness
        run: |
          # Check all .md files are in an index
          python scripts/verify_doc_index.py
```

### Documentation Metrics

Track these metrics monthly:

```markdown
## Documentation Health Metrics (2025-10)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total documents | 87 | - | - |
| Avg age (days) | 45 | <90 | ✅ |
| Outdated docs | 3 | 0 | ���️ |
| Broken links | 0 | 0 | ✅ |
| Incident docs (last 30d) | 2 | - | - |
| Time to find info (avg) | 2 min | <5 | ✅ |
| Documentation coverage | 85% | >80% | ✅ |
```

---

## Summary

This framework provides:

1. **Tree-Based Structure** - Clear hierarchy from general to specific
2. **Fast Root Causing** - Symptom-based and RCA-based organization
3. **Standardized Templates** - Consistent documentation format
4. **Quick Navigation** - Multiple paths to find information
5. **Maintenance Process** - Keep documentation up-to-date

### Quick Start for New Team Members

1. Start at [`docs/README.md`](README.md)
2. Read [System Architecture](architecture/overview/system_diagram.md)
3. Follow [Local Setup](docs/LOCAL_SETUP.md)
4. Bookmark [Troubleshooting Index](troubleshooting/README.md)
5. Review recent [Incidents](troubleshooting/incidents/)

### When Something Breaks

1. Go to [Troubleshooting Hub](troubleshooting/README.md)
2. Find symptom in index
3. Follow diagnostic tree
4. Apply fix from linked FIXES doc
5. Document as incident if significant

---

**Next Steps:**
1. Review this framework
2. Create missing folders: `troubleshooting/`, `architecture/`
3. Migrate existing docs to new structure
4. Set up automated checks
5. Schedule first monthly audit