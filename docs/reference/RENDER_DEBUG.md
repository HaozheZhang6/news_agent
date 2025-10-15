# Render Deployment Debug Report

**Issue:** Deploy timeout - Port scan timeout reached
**Date:** 2025-10-14
**Failed Commit:** 9b4808b

---

## Problem Analysis

### Symptoms
```
Deploy failed for 9b4808b: docs: ...
Timed out
Port scan timeout reached, no open ports detected.
```

### Root Causes (Likely)

1. **Build taking too long** (>15 minutes)
2. **Server failing to start** after build
3. **Health check failing** to respond

---

## Investigation Steps

### 1. Check uv.lock File

The recent `uv sync` might have updated dependencies. Check if uv.lock was committed:

```bash
git log --oneline -10 | grep "uv.lock"
git diff HEAD~2 uv.lock | head -50
```

**Issue:** If uv.lock changed significantly, build might be installing unexpected dependencies.

### 2. Verify pyproject.toml Changes

Recent changes moved heavy dependencies to optional group:

```toml
[project.dependencies]
# Should be lightweight (~500MB)

[project.optional-dependencies]
local-asr = [
    "funasr>=1.0.0",
    "torch>=2.8.0",
    ...
]
```

**Verify:** Render is NOT installing optional dependencies.

### 3. Check Render Build Logs

Look for:
- `Installing dependencies...` duration
- Any PyTorch/torch downloads
- Memory errors
- Timeout during dependency install

---

## Likely Issues & Fixes

### Issue 1: uv.lock Has Heavy Dependencies

**Symptom:** Build installs torch/funasr despite being optional

**Cause:** uv.lock was generated with `--extra local-asr` flag

**Fix:**
```bash
# Regenerate lock file without optional dependencies
rm uv.lock
uv sync --frozen  # Will fail without lock
uv lock --no-dev  # Regenerate production lock only
git add uv.lock
git commit -m "fix: regenerate uv.lock without optional dependencies"
git push origin main
```

### Issue 2: Python Version Mismatch

**Current:** `PYTHON_VERSION: 3.11.0`
**Issue:** Exact version might not be available on Render

**Fix:**
```yaml
# render.yaml
envVars:
  - key: PYTHON_VERSION
    value: 3.11  # Use minor version only
```

### Issue 3: uv Installation Failing

**Issue:** `curl -LsSf https://astral.sh/uv/install.sh | sh` might timeout

**Fix:**
```yaml
buildCommand: |
  # Add timeout and retry
  curl --max-time 60 --retry 3 -LsSf https://astral.sh/uv/install.sh | sh || exit 1
  source $HOME/.cargo/env
  uv --version  # Verify installation
  uv sync --frozen
```

### Issue 4: Server Startup Timeout

**Issue:** Server takes too long to start, health check fails

**Fix:** Add timeout to startCommand:
```yaml
startCommand: |
  timeout 120 uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 120
```

### Issue 5: Missing Environment Variables

**Issue:** Required env vars not set, causing startup failure

**Check Required Vars:**
- SUPABASE_URL
- SUPABASE_KEY
- UPSTASH_REDIS_REST_URL
- UPSTASH_REDIS_REST_TOKEN
- ZHIPUAI_API_KEY
- HF_TOKEN

**Fix:** Verify all are set in Render dashboard

---

## Recommended Fix (Most Likely)

### Problem: uv.lock Contains Heavy Dependencies

When we ran `uv sync --extra local-asr` locally, it updated uv.lock to include torch/funasr. When Render runs `uv sync --frozen`, it installs ALL dependencies from the lock file, including optional ones.

### Solution: Regenerate Lock File for Production

```bash
# 1. Clean environment
rm -rf .venv uv.lock

# 2. Create fresh venv
uv venv

# 3. Install ONLY production dependencies (no --extra)
uv sync

# 4. Lock file is now production-only
git add uv.lock
git commit -m "fix(deps): regenerate uv.lock for production (no optional deps)"
git push origin main
```

### Verify Locally First

```bash
# Simulate Render build
rm -rf .venv
uv venv
uv sync --frozen

# Check installed packages
uv pip list | grep -E "torch|funasr"
# Should return NOTHING

# Test server starts
USE_LOCAL_ASR=false uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# Should start in <5 seconds
```

---

## Alternative: Use pip Instead of uv

If uv continues to cause issues, fallback to pip:

```yaml
buildCommand: |
  pip install --upgrade pip
  pip install -e .
  echo "Build complete"

startCommand: |
  python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

---

## Debugging Commands

### Check Render Logs

1. Go to Render Dashboard
2. Click on service "voice-news-agent-api"
3. Click "Logs" tab
4. Look for last 100 lines before timeout

### Key Log Patterns to Find

**Good (should see):**
```
Installing dependencies...
Resolved XX packages in X.XXs
Installed XX packages in X.XXs
Starting server...
INFO: Uvicorn running on http://0.0.0.0:XXXX
```

**Bad (indicates problem):**
```
Downloading torch-2.8.0...  # Should NOT happen
Installing funasr...  # Should NOT happen
ERROR: Could not find package...
Timed out...
```

---

## Action Plan

### Immediate (Do This Now)

1. **Regenerate uv.lock:**
   ```bash
   rm uv.lock
   uv sync
   git add uv.lock
   git commit -m "fix: regenerate uv.lock without optional dependencies"
   git push origin main
   ```

2. **Monitor Render Build:**
   - Watch logs in real-time
   - Look for torch/funasr downloads
   - Check total build time

### If Still Fails

3. **Simplify Python Version:**
   ```yaml
   - key: PYTHON_VERSION
     value: 3.11
   ```

4. **Add Build Timeout Safety:**
   ```yaml
   buildCommand: |
     set -e  # Exit on error
     curl --max-time 60 -LsSf https://astral.sh/uv/install.sh | sh
     source $HOME/.cargo/env
     timeout 300 uv sync --frozen  # 5 min max
   ```

### If Still Fails After All Above

5. **Switch to pip:**
   ```yaml
   buildCommand: pip install -e .
   startCommand: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```

---

## Expected Outcome

After fix:
- Build time: <2 minutes
- Install size: ~500MB
- Server starts: <10 seconds
- Health check: Responds immediately

---

## Notes for Future

- Always regenerate uv.lock after changing pyproject.toml
- Test production lock file locally before pushing
- Never commit uv.lock generated with --extra flags
- Consider separate lock files for dev/prod

---

**Status:** Investigation complete, fix ready to apply
**Next Step:** Regenerate uv.lock and redeploy
