# Render Deployment - Proper Fix Strategy

**Date:** 2025-10-14
**Status:** In Progress - Need Proper Solution

---

## Summary of Events

1. ✅ Created USE_LOCAL_ASR configuration system
2. ✅ Moved heavy dependencies to optional group
3. ❌ Regenerated uv.lock without optional deps
4. ❌ Pushed without running tests
5. ❌ 47 tests failed
6. ✅ Reverted the breaking commit
7. ⏳ Need proper solution

---

## The Core Problem

**Render Deployment Timeout:**
- Render times out because it's installing heavy dependencies
- Even with `USE_LOCAL_ASR=false`, the build installs torch/funasr
- Root cause: `uv sync --frozen` installs everything in uv.lock
- uv.lock includes optional dependencies when generated with `--extra` flags

**Testing Requirement:**
- Many tests depend on local-asr dependencies (funasr, torch, pygame)
- Can't remove these from dev environment
- Need full dependencies locally, minimal on Render

---

## Proper Solutions

### Solution 1: Use requirements.txt for Render (RECOMMENDED)

**Strategy:** Generate a minimal requirements.txt for Render, keep uv for local dev

```bash
# Generate production requirements
uv pip compile pyproject.toml --no-dev --output-file=requirements-render.txt

# Update render.yaml
buildCommand: |
  pip install --upgrade pip
  pip install -r requirements-render.txt
```

**Pros:**
- ✅ Render uses minimal dependencies
- ✅ Local dev keeps full uv workflow
- ✅ Tests continue to work
- ✅ Clear separation of concerns

**Cons:**
- Two dependency management systems
- Need to regenerate requirements-render.txt when deps change

### Solution 2: Use Custom Lock File for Render

**Strategy:** Maintain two lock files

```bash
# Production lock (no optional deps)
uv lock --no-dev -o uv-prod.lock

# Development lock (with optional deps)
uv lock -o uv.lock

# render.yaml
buildCommand: |
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source $HOME/.cargo/env
  uv sync --frozen --lockfile uv-prod.lock
```

**Pros:**
- ✅ Uses uv everywhere
- ✅ Explicit production lock
- ✅ Tests work locally

**Cons:**
- Need to maintain two lock files
- More complex workflow

### Solution 3: Skip Tests That Need Local ASR

**Strategy:** Make tests conditional on dependencies

```python
# tests/conftest.py
import pytest

HAS_FUNASR = False
try:
    import funasr
    HAS_FUNASR = True
except ImportError:
    pass

skipif_no_funasr = pytest.mark.skipif(
    not HAS_FUNASR,
    reason="Requires local-asr dependencies"
)

# In tests:
@skipif_no_funasr
def test_sensevoice_model():
    ...
```

**Pros:**
- ✅ Tests adapt to environment
- ✅ Can test without local-asr

**Cons:**
- ❌ Doesn't solve Render deployment issue
- ❌ Many tests to update
- ❌ Reduces test coverage

---

## Recommended Approach: Solution 1 (requirements.txt)

### Implementation Steps

#### 1. Generate Minimal Requirements

```bash
# Create virtual environment with production deps only
python -m venv .venv-prod
source .venv-prod/bin/activate
pip install --upgrade pip

# Install from pyproject.toml (no extras)
pip install -e .

# Freeze to requirements
pip freeze > requirements-render.txt

# Clean up
deactivate
rm -rf .venv-prod
```

#### 2. Update render.yaml

```yaml
buildCommand: |
  pip install --upgrade pip
  pip install -r requirements-render.txt
  echo "✅ Production dependencies installed"

startCommand: |
  python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

#### 3. Test Locally

```bash
# Simulate Render build
python -m venv .venv-render-test
source .venv-render-test/bin/activate
pip install -r requirements-render.txt

# Test server starts
USE_LOCAL_ASR=false python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Verify no heavy deps
pip list | grep -E "torch|funasr"  # Should be empty

deactivate
rm -rf .venv-render-test
```

#### 4. Update Documentation

Add to docs/RENDER_DEPLOYMENT.md:
- Explain requirements-render.txt
- How to regenerate when dependencies change
- Why we use requirements.txt instead of uv

#### 5. Add to .gitignore

```gitignore
# Development virtual environments
.venv-prod/
.venv-render-test/
```

#### 6. Commit and Test

```bash
git add requirements-render.txt render.yaml
git commit -m "fix(deploy): use requirements.txt for Render deployment

Use minimal requirements.txt for Render instead of uv.lock.
This ensures Render only installs production dependencies.

- requirements-render.txt: Generated from pyproject.toml (no extras)
- render.yaml: Use pip with requirements-render.txt
- Local dev: Continue using uv with full dependencies"

# DO NOT PUSH YET - Test first!

# Run full test suite
make test-backend

# Verify all tests pass
# Then push
git push origin main
```

---

## Alternative Quick Fix (Temporary)

If we need Render working ASAP, use Docker:

```yaml
# render.yaml
services:
  - type: web
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only production dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application
COPY backend/ ./backend/
COPY src/ ./src/

# Set environment
ENV USE_LOCAL_ASR=false
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Testing Checklist (MUST FOLLOW BEFORE ANY PUSH)

### Local Development Environment

- [ ] `uv sync --extra local-asr --extra test --extra dev`
- [ ] `make test-backend` → All tests pass
- [ ] `make run-server` → Server starts with local ASR
- [ ] `USE_LOCAL_ASR=false make run-server-hf` → Server starts with HF Space

### Render Simulation

- [ ] Create clean venv
- [ ] Install from requirements-render.txt
- [ ] Start server with USE_LOCAL_ASR=false
- [ ] Verify no torch/funasr installed
- [ ] Test /health and /live endpoints
- [ ] Test WebSocket connection

### After Passing All Tests

- [ ] Review all changed files
- [ ] Update documentation
- [ ] Write clear commit message
- [ ] Push to main
- [ ] Monitor Render build logs
- [ ] Verify deployment succeeds
- [ ] Test deployed service

---

## Current Status

**Reverted:** Commit a9212bb reverted in 9be670a
**Lock File:** Back to version with all dependencies
**Tests:** Should pass now (need to verify)
**Render:** Still failing, needs proper fix
**Action:** Implement Solution 1 (requirements.txt)

---

## Next Steps

1. ✅ Revert completed
2. ⏳ Verify tests pass with reverted lock file
3. ⏳ Implement requirements-render.txt solution
4. ⏳ Test thoroughly locally
5. ⏳ Push and monitor Render deployment
6. ⏳ Document the process

---

**Priority:** HIGH
**Estimated Time:** 1-2 hours to implement properly
**Risk Level:** LOW (with proper testing)
