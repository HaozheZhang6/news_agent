# SenseVoice Model Deployment Configuration

This document explains how the SenseVoice model is configured for both local development and cloud deployment on Render.com.

## Overview

The SenseVoice model is large (~1GB) and is not included in the Git repository. Instead, it's downloaded dynamically during deployment and locally when needed.

## Directory Structure

```
News_agent/
├── models/                    # Local model storage (gitignored)
│   ├── iic/
│   │   └── SenseVoiceSmall/   # Local model path
│   └── SenseVoiceSmall/       # Alternative local path
├── scripts/
│   ├── download_sensevoice.py         # Local download script
│   ├── download_sensevoice_deploy.py  # Deployment download script
│   └── test_local_setup.py           # Local setup verification
└── render.yaml                # Render deployment configuration
```

## Configuration Paths

### Local Development (src/)
- **Path**: `models/iic/SenseVoiceSmall`
- **Config**: `src/config.py`
- **Environment Variable**: `SENSEVOICE_MODEL_PATH` (optional)
- **Download Script**: `scripts/download_sensevoice.py`

### Backend API (backend/)
- **Local Path**: `models/SenseVoiceSmall` (fallback)
- **Deployment Path**: `/app/models/SenseVoiceSmall`
- **Config**: `backend/app/config.py`
- **Environment Variable**: `SENSEVOICE_MODEL_PATH`
- **Download Script**: `scripts/download_sensevoice_deploy.py`

## Local Development Setup

1. **Download the model locally**:
   ```bash
   uv run python scripts/download_sensevoice.py
   ```

2. **Verify setup**:
   ```bash
   uv run python scripts/test_local_setup.py
   ```

3. **Test the application**:
   ```bash
   # Test src (voice processing)
   uv run python src/main.py
   
   # Test backend API
   uv run python -m backend.app.main
   ```

## Render.com Deployment

The deployment is configured in `render.yaml`:

### Build Process
1. Install dependencies with `uv sync --frozen`
2. Download SenseVoice model using `scripts/download_sensevoice_deploy.py`
3. Model is cached in ModelScope's default cache directory (`~/.cache/modelscope/hub`)
4. Backend automatically detects the cached model path at runtime

### Environment Variables
- `SENSEVOICE_MODEL_PATH` is automatically detected (no manual setting needed)
- Backend uses ModelScope's cache directory for deployment

### Build Command
```yaml
buildCommand: |
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source $HOME/.cargo/env
  uv sync --frozen
  # Download SenseVoice model for deployment
  echo "Downloading SenseVoice model..."
  uv run python scripts/download_sensevoice_deploy.py
```

## Key Differences

| Aspect | Local Development | Render Deployment |
|--------|------------------|-------------------|
| Model Path | `models/iic/SenseVoiceSmall` | Auto-detected from ModelScope cache |
| Download Script | `download_sensevoice.py` | `download_sensevoice_deploy.py` |
| Base Directory | Project root | ModelScope cache (`~/.cache/modelscope/hub`) |
| Git Tracking | Ignored (`/models` in `.gitignore`) | Not tracked |
| Environment | Development | Production |
| Path Detection | Manual setup | Automatic detection |

## Troubleshooting

### Local Issues
- **Model not found**: Run `uv run python scripts/download_sensevoice.py`
- **Import errors**: Ensure `funasr` is installed: `uv pip install funasr`
- **Path issues**: Check `SENSEVOICE_MODEL_PATH` environment variable

### Deployment Issues
- **Build timeout**: Model download may take 5-10 minutes
- **Disk space**: Ensure Render plan has sufficient storage
- **Network issues**: Check Render build logs for download errors

## Files Modified

1. **`scripts/download_sensevoice_deploy.py`** - New deployment download script
2. **`render.yaml`** - Updated build command and environment variables
3. **`scripts/test_local_setup.py`** - New local setup verification script

## Verification

### Local
```bash
# Check model exists
ls -la models/iic/SenseVoiceSmall/

# Test configuration
uv run python scripts/test_local_setup.py
```

### Deployment
- Check Render build logs for successful model download
- Verify ModelScope cache directory contains the model
- Test API endpoints that use voice processing
- Backend will automatically detect the cached model path

## Notes

- The model download happens during the build phase, not at runtime
- Both local and deployment scripts use the same ModelScope source
- The `.gitignore` ensures models are not committed to the repository
- Environment variables allow flexible path configuration
