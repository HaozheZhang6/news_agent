# Documentation Framework for Fast Root Causing

**Version:** 1.0
**Last Updated:** 2025-10-15
**Purpose:** Enable rapid problem diagnosis with tree-based documentation structure

---

## Table of Contents

1. [Overview](#overview)
2. [Documentation Structure](#documentation-structure)
3. [Document Types](#document-types)
4. [Root Cause Analysis System](#root-cause-analysis-system)
5. [Navigation & Discovery](#navigation--discovery)
6. [Implementation Guide](#implementation-guide)
7. [Maintenance](#maintenance)

---

## Overview

### Core Principles

1. **Tree-Based Hierarchy**: General overview → Detailed reference
2. **Fast Root Causing**: Symptom-based troubleshooting index
3. **Modular Templates**: Reusable document templates
4. **Docsify Integration**: Clean URLs and navigation
5. **Traceability**: Every fix linked to root cause analysis

### Quick Reference

| Need | Go To |
|------|-------|
| 🚀 Get started quickly | [docs/getting-started.md](getting-started.md) |
| 🏗️ Understand architecture | [docs/architecture-overview.md](architecture-overview.md) |
| 🔧 Fix a problem | [docs/troubleshooting.md](troubleshooting.md) |
| 📚 Deep technical details | [docs/reference/](reference/) |
| 📝 Write new docs | [Templates](#document-types) |

---

## Documentation Structure

### Folder Hierarchy

```
docs/                                    # Overview documentation (Docsify root)
│
├── README.md                            # Landing page & navigation hub
├── overview.md                          # System overview (what/why/how)
├── getting-started.md                   # Quick start guide (5-10 min)
├── architecture-overview.md             # High-level architecture
├── troubleshooting.md                   # Common issues quick reference
├── faq.md                               # Frequently asked questions
│
├── _sidebar.md                          # Docsify sidebar (auto-generated)
├── _navbar.md                           # Docsify navbar (optional)
├── index.html                           # Docsify config
├── .nojekyll                            # GitHub Pages compatibility
│
└── reference/                           # Detailed technical docs
    │
    ├── README.md                        # Reference hub
    │
    ├── setup/                           # Setup & deployment
    │   ├── README.md
    │   ├── local-setup.md
    │   ├── production-deployment.md
    │   ├── environment-config.md
    │   └── testing.md
    │
    ├── architecture/                    # System design
    │   ├── README.md
    │   ├── system-design.md
    │   ├── api-design.md
    │   ├── data-flow.md
    │   ├── components/
    │   │   ├── README.md
    │   │   ├── frontend.md
    │   │   ├── backend.md
    │   │   └── database.md
    │   └── decisions/                   # ADRs
    │       ├── README.md
    │       └── adr-XXX-title.md
    │
    ├── guides/                          # How-to guides
    │   ├── README.md
    │   ├── audio-pipeline.md
    │   ├── websocket-streaming.md
    │   └── voice-detection.md
    │
    ├── troubleshooting/                 # Root cause analysis
    │   ├── README.md                    # Diagnostic hub
    │   ├── symptoms/
    │   │   ├── README.md
    │   │   ├── connection-issues.md
    │   │   ├── audio-problems.md
    │   │   └── performance-issues.md
    │   ├── fixes/                       # Detailed RCA docs
    │   │   ├── README.md
    │   │   ├── websocket-fixes.md
    │   │   └── audio-pipeline-fixes.md
    │   └── incidents/                   # Post-mortems
    │       ├── README.md
    │       └── YYYY-MM-DD-incident.md
    │
    ├── api/                             # API reference
    │   ├── README.md
    │   ├── rest-endpoints.md
    │   └── websocket-protocol.md
    │
    └── optimization/                    # Performance
        ├── README.md
        └── latency-optimization.md
```

### Design Decisions

**Why this structure?**

1. **docs/**: Quick overview docs (<10 pages) for fast onboarding
2. **docs/reference/**: Deep technical docs organized by topic
3. **Kebab-case filenames**: Clean Docsify URLs (`/reference/setup/local-setup`)
4. **README.md in every folder**: Navigation and context
5. **Modular templates**: Consistent structure across all docs

---

## Document Types

### 1. Overview Documents (in docs/)

**Location:** `docs/*.md`
**Purpose:** High-level understanding
**Max Length:** 300 lines
**Template:** [templates/overview-template.md](reference/templates/overview-template.md)

**Structure:**
```markdown
# [Topic Name]

> Brief one-sentence description

## What is it?
- Concise explanation (3-5 bullets)

## Why do we need it?
- Value proposition

## How does it work?
- High-level flow diagram
- Key concepts

## Quick Links
- → [Detailed Guide](reference/guides/topic.md)
- → [Architecture](reference/architecture/component.md)
```

**Example:** [docs/overview.md](overview.md)

---

### 2. Reference Documents (in docs/reference/)

**Location:** `docs/reference/guides/*.md`
**Purpose:** Detailed implementation guides
**Template:** [templates/guide-template.md](reference/templates/guide-template.md)

**Structure:**
```markdown
# [Feature] Implementation Guide

**Purpose:** [One-line]
**Audience:** [Developer type]
**Time:** [Estimate]
**Prerequisites:** [Links]

## Overview
- What this covers
- System context

## Implementation Steps

### Step 1: [Task]
**What:** Description
**Why:** Rationale
**How:** Code example
**Files:** Links with line numbers
**Test:** Verification commands

### Step 2: [Next Task]
[Repeat]

## Configuration
- Environment variables
- Feature flags

## Testing
- Unit tests
- Integration tests
- Manual checklist

## Troubleshooting
- Common issues → [Link to fixes](../troubleshooting/fixes/)

## References
- Related docs
```

**Example:** [reference/guides/audio-pipeline.md](reference/guides/audio-pipeline.md)

---

### 3. Troubleshooting Documents

#### 3a. Symptom Index

**Location:** `docs/reference/troubleshooting/symptoms/*.md`
**Purpose:** Quick problem diagnosis
**Template:** [templates/symptom-template.md](reference/templates/symptom-template.md)

**Structure:**
```markdown
# Troubleshooting: [Symptom Category]

## Quick Diagnosis

### Symptom: [Description]

**Indicators:**
- Error: `error message`
- Log: `log pattern`
- Behavior: [what user sees]

**Quick Check:**
```bash
make check-something
```

**Common Causes:**

| Cause | Frequency | Solution | Details |
|-------|-----------|----------|---------|
| [Root Cause 1] | 70% | [Quick fix] | [Link to fixes/](../fixes/component-fixes.md#cause-1) |
| [Root Cause 2] | 20% | [Quick fix] | [Link to fixes/](../fixes/component-fixes.md#cause-2) |
| [Root Cause 3] | 10% | [Quick fix] | [Link to fixes/](../fixes/component-fixes.md#cause-3) |

**Diagnostic Tree:**
```
Error X present?
├─ Yes → Check config Y
│  ├─ Y correct → Root Cause 1
│  └─ Y wrong → Fix Y, restart
└─ No → Check logs Z
   ├─ Z shows error → Root Cause 2
   └─ Z clean → Root Cause 3
```

## Emergency Fixes

### Quick Restart
```bash
make restart
```

### Clear Cache
```bash
make clean-cache
```

## Related
- [Detailed Fixes](../fixes/component-fixes.md)
- [Architecture](../../architecture/components/component.md)
```

**Example:** [reference/troubleshooting/symptoms/connection-issues.md](reference/troubleshooting/symptoms/connection-issues.md)

---

#### 3b. Fix Documents (Root Cause Analysis)

**Location:** `docs/reference/troubleshooting/fixes/*.md`
**Purpose:** Detailed RCA documentation
**Template:** [templates/rca-template.md](reference/templates/rca-template.md)

**Structure:**
```markdown
# [Component] Fixes

**Last Updated:** YYYY-MM-DD
**Total Fixes:** N

## Quick Index

| Fix ID | Issue | Status | Date |
|--------|-------|--------|------|
| [FIX-001](#fix-001) | [Brief description] | ✅ Fixed | YYYY-MM-DD |
| [FIX-002](#fix-002) | [Brief description] | ✅ Fixed | YYYY-MM-DD |

---

## FIX-001: [Problem Summary]

**Status:** ✅ Fixed | 🚧 In Progress | ⚠️ Workaround
**Severity:** Critical | High | Medium | Low
**Date Fixed:** YYYY-MM-DD
**Affected Versions:** vX.X.X - vX.X.X
**Related Incident:** [Link if exists](../incidents/YYYY-MM-DD-incident.md)

### Symptoms

**User-Facing:**
- What users experienced
- Error messages

**Technical:**
- Logs/console errors
- Reproducible steps

### Root Cause Analysis

**Investigation:**
1. Initial hypothesis
2. Tests performed
3. Data collected
4. Actual root cause

**Technical Explanation:**
- Why it failed
- System interaction

**Code References:**
- [backend/app/core/websocket_manager.py:145-167](../../../backend/app/core/websocket_manager.py)
- [frontend/src/components/VoiceInterface.tsx:89](../../../frontend/src/components/VoiceInterface.tsx)

### Solution

**Changes Made:**

1. **File:** [backend/app/core/websocket_manager.py:145-167](../../../backend/app/core/websocket_manager.py)
   ```python
   # Before
   await websocket.send_text(message)

   # After
   await websocket.send_json({"type": "audio", "data": message})
   ```
   **Why:** Standardize message format

2. **Configuration:**
   ```bash
   # Added to .env
   WEBSOCKET_PING_INTERVAL=30
   ```

**Verification:**
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual verification

**Performance Impact:**
- Before: 5s latency
- After: 100ms latency
- Improvement: 98%

### Prevention

**Monitoring:**
- Added metrics: `websocket_message_errors`
- Alert threshold: >10 errors/min
- Dashboard: [Link]

**Tests Added:**
- [tests/backend/test_websocket_format.py](../../../tests/backend/test_websocket_format.py)

**Documentation:**
- [x] User guide updated
- [x] API docs updated
- [x] This RCA doc

### Related

- **Similar Issues:** [FIX-003](#fix-003)
- **Architecture:** [WebSocket Design](../../architecture/components/websocket.md)
- **API Spec:** [WebSocket Protocol](../../api/websocket-protocol.md)

---

## FIX-002: [Next Problem]

[Repeat structure]
```

**Example:** [reference/troubleshooting/fixes/websocket-fixes.md](reference/troubleshooting/fixes/websocket-fixes.md)

---

#### 3c. Incident Reports (Post-Mortems)

**Location:** `docs/reference/troubleshooting/incidents/*.md`
**Purpose:** Learn from production incidents
**Template:** [templates/incident-template.md](reference/templates/incident-template.md)

**Naming:** `YYYY-MM-DD-brief-description.md`

**Structure:**
```markdown
# Incident: [Name]

**Date:** YYYY-MM-DD
**Duration:** HH:MM
**Severity:** P0 (Critical) | P1 | P2 | P3
**Status:** Resolved
**Impact:** [User-facing description]

## Executive Summary

[2-3 sentences for management]

**Root Cause:** [One sentence]
**Resolution:** [One sentence]
**Prevention:** [One sentence]

## Timeline

| Time | Event | Action |
|------|-------|--------|
| 14:23 | Incident detected | Alerted team |
| 14:25 | Investigation started | Logs reviewed |
| 14:35 | Root cause found | Fix deployed |
| 14:45 | Service restored | Monitoring confirmed |
| 15:00 | Post-mortem started | Doc updated |

## Detection

**When:** [Timestamp]
**How:** Monitoring alert / User report
**Initial Assessment:** [Quick summary]

## Root Cause

**Component:** [System component]
**Issue:** [Technical explanation]
**Why It Happened:** [Underlying cause]

**Details:** [Link to RCA](../fixes/component-fixes.md#fix-xxx)

## Resolution

**Fix Applied:** [What was changed]
**Verification:** [How we confirmed]

**Details:** [Link to PR/commit]

## Prevention

**Immediate:**
- [x] Monitoring added
- [x] Alert configured
- [x] Tests added

**Follow-up:**
- [ ] [Task 1] - Owner - Due date
- [ ] [Task 2] - Owner - Due date

## Lessons Learned

**What Went Well:**
- Fast detection
- Quick resolution

**What Could Improve:**
- Earlier detection
- Better monitoring

## References

- **RCA Doc:** [websocket-fixes.md](../fixes/websocket-fixes.md#fix-001)
- **PR:** [#123](https://github.com/user/repo/pull/123)
- **Related Incidents:** [2025-10-13-similar-issue.md](2025-10-13-similar-issue.md)
```

**Example:** [reference/troubleshooting/incidents/2025-10-13-websocket-disconnect.md](reference/troubleshooting/incidents/2025-10-13-websocket-disconnect.md)

---

### 4. Architecture Decision Records (ADRs)

**Location:** `docs/reference/architecture/decisions/*.md`
**Purpose:** Document key technical decisions
**Template:** [templates/adr-template.md](reference/templates/adr-template.md)

**Naming:** `adr-XXX-decision-title.md` (sequential numbering)

**Structure:**
```markdown
# ADR-XXX: [Decision Title]

**Status:** Accepted | Rejected | Superseded | Deprecated
**Date:** YYYY-MM-DD
**Deciders:** [Names]
**Related ADRs:** [ADR-001](adr-001-title.md), [ADR-002](adr-002-title.md)

## Context

What problem are we solving?

- Current situation
- Constraints
- Requirements

## Decision

What did we decide?

[Clear statement of decision]

## Options Considered

### Option 1: [Name]

**Pros:**
- Advantage 1
- Advantage 2

**Cons:**
- Disadvantage 1
- Disadvantage 2

**Effort:** [Low/Medium/High]

### Option 2: [Name]
[Same structure]

### Option 3: [Name]
[Same structure]

## Rationale

Why this option?

- Key factors
- Trade-offs accepted
- Risk mitigation

## Consequences

**Positive:**
- Benefit 1
- Benefit 2

**Negative:**
- Trade-off 1
- Trade-off 2

**Neutral:**
- Impact 1

## Implementation

**Changes Required:**
- Component 1: [description]
- Component 2: [description]

**Migration Plan:**
1. Step 1
2. Step 2
3. Rollout strategy

**Success Metrics:**
- Metric 1: [target value]
- Metric 2: [target value]

## References

- **Technical Spec:** [Link]
- **Discussion:** [Issue #123](link)
- **Related Docs:** [Architecture](../system-design.md)
```

**Example:** [reference/architecture/decisions/adr-001-asr-selection.md](reference/architecture/decisions/adr-001-asr-selection.md)

---

## Root Cause Analysis System

### RCA Process (5 Phases)

```
Detection → Triage → Investigation → Resolution → Prevention
(0-5 min)  (5-15 min)  (15-60 min)   (60-120 min)  (Post-incident)
```

### Phase Checklist

**1. Detection (0-5 min)**
- [ ] Incident logged with timestamp
- [ ] Severity assessed
- [ ] Team notified
- [ ] Impact assessed

**2. Triage (5-15 min)**
- [ ] Symptoms documented
- [ ] Initial hypothesis formed
- [ ] Quick diagnostic tests run
- [ ] Workaround attempted

**3. Investigation (15-60 min)**
- [ ] Root cause identified
- [ ] Code/config reviewed
- [ ] Tests performed
- [ ] Solution designed

**4. Resolution (60-120 min)**
- [ ] Fix implemented
- [ ] Tests pass
- [ ] Deployed to production
- [ ] Monitoring confirms fix

**5. Prevention (Post-incident)**
- [ ] RCA document created
- [ ] Monitoring/alerts added
- [ ] Tests added
- [ ] Documentation updated
- [ ] Incident report written

### Document Flow

```
Incident Occurs
     ↓
Create: incidents/YYYY-MM-DD-incident.md (Post-mortem)
     ↓
Document RCA: fixes/component-fixes.md (Add FIX-XXX section)
     ↓
Update: symptoms/issue-category.md (Add to common causes)
     ↓
Update: guides/component-guide.md (Add troubleshooting section)
     ↓
Update: architecture/components/component.md (If design changed)
```

---

## Navigation & Discovery

### Primary Entry Points

1. **docs/README.md** - Main documentation hub
2. **docs/troubleshooting.md** - Problem? Start here
3. **docs/reference/README.md** - Deep technical docs
4. **docs/reference/troubleshooting/README.md** - Diagnostic hub

### Search Paths

**By Role:**
- Developer → [getting-started.md](getting-started.md) → [reference/guides/](reference/guides/)
- DevOps → [troubleshooting.md](troubleshooting.md) → [reference/troubleshooting/](reference/troubleshooting/)
- PM/QA → [overview.md](overview.md) → [architecture-overview.md](architecture-overview.md)

**By Task:**
- Setup → [getting-started.md](getting-started.md)
- Debug → [troubleshooting.md](troubleshooting.md)
- Understand → [architecture-overview.md](architecture-overview.md)
- Implement → [reference/guides/](reference/guides/)

**By Symptom:**
- Error message → Search in [reference/troubleshooting/symptoms/](reference/troubleshooting/symptoms/)
- Slow performance → [reference/troubleshooting/symptoms/performance-issues.md](reference/troubleshooting/symptoms/performance-issues.md)
- Connection fails → [reference/troubleshooting/symptoms/connection-issues.md](reference/troubleshooting/symptoms/connection-issues.md)

### Cross-Reference Standards

**Link Format:**
```markdown
<!-- Relative links within docs/ -->
See [Guide](reference/guides/feature.md)

<!-- Links with line numbers (code) -->
[websocket_manager.py:145-167](../../../backend/app/core/websocket_manager.py)

<!-- Links to specific sections -->
[WebSocket Fixes](reference/troubleshooting/fixes/websocket-fixes.md#fix-001)
```

**Bi-directional Links:**
- Every fix → Links to related incident
- Every symptom → Links to fixes
- Every guide → Links to architecture
- Every component doc → Links to guides

---

## Implementation Guide

### Step 1: Create Folder Structure

```bash
# Create new folders
mkdir -p docs/reference/{setup,architecture/components,architecture/decisions,guides,troubleshooting/{symptoms,fixes,incidents},api,optimization,templates}

# Create README.md in each folder
find docs/reference -type d -exec touch {}/README.md \;

# Create Docsify files
touch docs/{index.html,_sidebar.md,_navbar.md,.nojekyll}
```

### Step 2: Create Templates

Create modular templates in `docs/reference/templates/`:

```bash
cd docs/reference/templates

# Create template files
touch overview-template.md
touch guide-template.md
touch symptom-template.md
touch rca-template.md
touch incident-template.md
touch adr-template.md
```

See [templates/](reference/templates/) folder for full templates.

### Step 3: Migrate Existing Docs

**Migration Priority:**

1. **High Priority** (move to `docs/`):
   - README.md → Update for Docsify
   - PRD.md → Convert to overview.md
   - MVP.md → Part of getting-started.md

2. **Medium Priority** (move to `docs/reference/`):
   - reference/*.md → Organize by category
   - Fixes docs → troubleshooting/fixes/
   - guides → reference/guides/

3. **Low Priority** (archive or remove):
   - Outdated docs
   - Duplicate content
   - Temporary notes

**Migration Checklist:**
- [ ] Read existing doc
- [ ] Identify document type
- [ ] Apply appropriate template
- [ ] Update links
- [ ] Add to index
- [ ] Test links

### Step 4: Setup Docsify

**index.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Voice News Agent Docs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/vue.css">
</head>
<body>
  <div id="app"></div>
  <script>
    window.$docsify = {
      name: 'Voice News Agent',
      repo: 'HaozheZhang6/news_agent',
      loadSidebar: true,
      subMaxLevel: 3,
      auto2top: true,
      search: {
        paths: 'auto',
        placeholder: 'Search docs...',
        depth: 3
      }
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
</body>
</html>
```

**_sidebar.md:**
```markdown
* Getting Started
  * [Overview](overview.md)
  * [Quick Start](getting-started.md)
  * [Architecture](architecture-overview.md)
  * [Troubleshooting](troubleshooting.md)
  * [FAQ](faq.md)

* Reference
  * [Reference Hub](reference/README.md)
  * Setup
    * [Local Setup](reference/setup/local-setup.md)
    * [Production](reference/setup/production-deployment.md)
  * Architecture
    * [System Design](reference/architecture/system-design.md)
    * [Components](reference/architecture/components/)
    * [Decisions](reference/architecture/decisions/)
  * Guides
    * [Audio Pipeline](reference/guides/audio-pipeline.md)
    * [WebSocket](reference/guides/websocket-streaming.md)
  * Troubleshooting
    * [Symptoms](reference/troubleshooting/symptoms/)
    * [Fixes](reference/troubleshooting/fixes/)
    * [Incidents](reference/troubleshooting/incidents/)
```

**.nojekyll:**
```
(empty file - disables Jekyll on GitHub Pages)
```

### Step 5: Update README.md

Transform root README.md into documentation hub.

---

## Maintenance

### Regular Tasks

**Weekly:**
- [ ] Check "Last Updated" dates
- [ ] Verify recent code changes reflected
- [ ] Update status badges

**Monthly:**
- [ ] Full link check
- [ ] Documentation inventory
- [ ] Archive old incidents
- [ ] Update metrics

**Quarterly:**
- [ ] Template review
- [ ] Structure review
- [ ] External link verification

### Quality Checklist

**New Document:**
- [ ] Uses correct template
- [ ] Has clear title/purpose
- [ ] Code examples tested
- [ ] Links verified
- [ ] Added to sidebar
- [ ] Cross-references updated

**Update:**
- [ ] "Last Updated" date changed
- [ ] Related docs checked
- [ ] Index updated
- [ ] Links still valid

### Metrics to Track

| Metric | Target | Check |
|--------|--------|-------|
| Docs up-to-date | 100% | Monthly |
| Avg doc age | <90 days | Monthly |
| Broken links | 0 | Weekly |
| Time to find info | <2 min | Quarterly |
| RCA coverage | 100% | Per incident |

---

## Summary

This framework provides:

✅ **Tree-based structure**: Overview (docs/) → Details (docs/reference/)
✅ **Fast root causing**: Symptom → Diagnostic tree → Fix
✅ **Modular templates**: Consistent, reusable
✅ **Docsify-ready**: Clean URLs, searchable
✅ **Full traceability**: Every fix linked to RCA and incident

### Next Steps

1. [ ] Review this framework
2. [ ] Create folder structure (`mkdir -p ...`)
3. [ ] Create templates in `docs/reference/templates/`
4. [ ] Setup Docsify (`index.html`, `_sidebar.md`)
5. [ ] Migrate existing docs
6. [ ] Test locally: `npx docsify serve docs`
7. [ ] Deploy to GitHub Pages

### Resources

- **Templates:** [docs/reference/templates/](reference/templates/)
- **Examples:** See existing docs in [reference/](reference/)
- **Docsify Docs:** https://docsify.js.org
- **Markdown Guide:** https://www.markdownguide.org

---

**Framework Version:** 1.0
**Maintained by:** Development Team
**Next Review:** 2025-11-15