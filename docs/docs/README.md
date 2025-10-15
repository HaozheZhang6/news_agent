# Documentation Index

**Complete documentation for Voice News Agent development, deployment, and maintenance.**

Last Updated: 2025-10-14
Version: Backend v0.2.1

---

## Quick Navigation

| Category | Document | Description |
|----------|----------|-------------|
| 🚀 **Setup** | [LOCAL_SETUP.md](LOCAL_SETUP.md) | Complete local development setup guide |
| ☁️ **Deploy** | [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) | Render.com cloud deployment guide |
| 🧪 **Testing** | [TESTING.md](TESTING.md) | Testing strategy and WebSocket tests |
| 🏗️ **Architecture** | [../reference/SYSTEM_DESIGN_CURRENT.md](../reference/SYSTEM_DESIGN_CURRENT.md) | System architecture and design |

---

## Documentation Structure

```
docs/
├── README.md                  # This file - documentation index
├── LOCAL_SETUP.md            # ⭐ Local development setup
├── RENDER_DEPLOYMENT.md      # ⭐ Cloud deployment guide
└── TESTING.md                # Testing guide and WebSocket tests

reference/                     # Technical reference docs
├── SYSTEM_DESIGN_CURRENT.md # Complete architecture
├── IMPLEMENTATION_SUMMARY.md # Feature implementation details
├── WAV_IMPLEMENTATION_COMPLETE.md
├── WEBSOCKET_FIXES.md
├── VAD_FIXES.md
└── ... (20+ technical docs)

tests/
├── README.md                 # Test suite overview
├── TEST_STRUCTURE.md         # Test organization
└── testing_utils/
    └── AUDIO_TESTING_GUIDE.md

database/
└── README.md                 # Database schema docs

backend/
└── README.md                 # Backend API overview

frontend/
└── README.md                 # Frontend setup and architecture
```

---

## Getting Started

### 1. New Developers

**Start here in order:**

1. **Overview** (5 min)
   - Read: [../README.md](../README.md) - Project overview
   - Goal: Understand what the system does

2. **Local Setup** (15 min)
   - Read: [LOCAL_SETUP.md](LOCAL_SETUP.md)
   - Follow: Quick Start section
   - Goal: Get the system running locally

3. **Architecture** (30 min)
   - Read: [../reference/SYSTEM_DESIGN_CURRENT.md](../reference/SYSTEM_DESIGN_CURRENT.md)
   - Goal: Understand system components and data flow

4. **Testing** (15 min)
   - Read: [TESTING.md](TESTING.md)
   - Run: `make test-backend`
   - Goal: Verify your setup works

**Total Time: ~1 hour to productivity**

### 2. DevOps / Deployment

**Deployment workflow:**

1. **Read Deployment Guide**
   - [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
   - Understand Render configuration
   - Review environment variables

2. **Setup Render Account**
   - Connect GitHub repository
   - Configure environment variables
   - Review render.yaml

3. **Deploy**
   - Push to main branch
   - Monitor build logs
   - Verify health checks

### 3. Frontend Developers

**Frontend focus:**

1. [../frontend/README.md](../frontend/README.md) - Frontend setup
2. [../reference/CONTINUOUS_VOICE_GUIDE.md](../reference/CONTINUOUS_VOICE_GUIDE.md) - Voice interface
3. [../reference/WAV_IMPLEMENTATION_COMPLETE.md](../reference/WAV_IMPLEMENTATION_COMPLETE.md) - Audio pipeline
4. [../reference/WEBSOCKET_FIXES.md](../reference/WEBSOCKET_FIXES.md) - WebSocket communication

### 4. Backend Developers

**Backend focus:**

1. [../backend/README.md](../backend/README.md) - Backend overview
2. [../reference/SYSTEM_DESIGN_CURRENT.md](../reference/SYSTEM_DESIGN_CURRENT.md) - Architecture
3. [LOCAL_SETUP.md](LOCAL_SETUP.md) - SenseVoice setup
4. [TESTING.md](TESTING.md) - Backend testing

---

## Documentation by Category

### 🚀 Setup & Configuration

| Document | Description | Audience |
|----------|-------------|----------|
| [LOCAL_SETUP.md](LOCAL_SETUP.md) | Complete local setup with SenseVoice | All developers |
| [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) | Cloud deployment guide | DevOps, Backend |
| [../reference/SENSEVOICE_DEPLOYMENT_SETUP.md](../reference/SENSEVOICE_DEPLOYMENT_SETUP.md) | SenseVoice model configuration | Backend |

### 🏗️ Architecture & Design

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/SYSTEM_DESIGN_CURRENT.md](../reference/SYSTEM_DESIGN_CURRENT.md) | Complete system architecture | All developers |
| [../reference/API_DESIGN.md](../reference/API_DESIGN.md) | REST API design | Backend, Frontend |
| [../reference/IMPLEMENTATION_SUMMARY.md](../reference/IMPLEMENTATION_SUMMARY.md) | Feature implementation details | All developers |

### 🎙️ Audio & Voice

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/WAV_IMPLEMENTATION_COMPLETE.md](../reference/WAV_IMPLEMENTATION_COMPLETE.md) | WAV audio pipeline | Frontend, Backend |
| [../reference/VAD_FIXES.md](../reference/VAD_FIXES.md) | Voice Activity Detection | Frontend |
| [../reference/WEBM_CONVERSION_ISSUE.md](../reference/WEBM_CONVERSION_ISSUE.md) | Why WebM failed | Frontend |
| [../reference/AUDIO_PIPELINE_FIXES.md](../reference/AUDIO_PIPELINE_FIXES.md) | Audio bug fixes | Backend |
| [../tests/testing_utils/AUDIO_TESTING_GUIDE.md](../tests/testing_utils/AUDIO_TESTING_GUIDE.md) | Audio testing | QA, Backend |

### 🔌 WebSocket & Communication

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/WEBSOCKET_FIXES.md](../reference/WEBSOCKET_FIXES.md) | WebSocket bug fixes | Backend, Frontend |
| [../reference/FRONTEND_WEBSOCKET_FIX.md](../reference/FRONTEND_WEBSOCKET_FIX.md) | Frontend WS implementation | Frontend |
| [../reference/FRONTEND_WEBSOCKET_FIXED.md](../reference/FRONTEND_WEBSOCKET_FIXED.md) | Final WS solution | Frontend |
| [../reference/FRONTEND_WEBSOCKET_ROOT_CAUSE.md](../reference/FRONTEND_WEBSOCKET_ROOT_CAUSE.md) | WS debugging process | Frontend |

### 🧪 Testing

| Document | Description | Audience |
|----------|-------------|----------|
| [TESTING.md](TESTING.md) | Complete testing guide | All developers |
| [../tests/README.md](../tests/README.md) | Test suite overview | All developers |
| [../tests/TEST_STRUCTURE.md](../tests/TEST_STRUCTURE.md) | Test organization | Backend, QA |
| [../tests/testing_utils/AUDIO_TESTING_GUIDE.md](../tests/testing_utils/AUDIO_TESTING_GUIDE.md) | Audio testing | QA |

### 🗄️ Database

| Document | Description | Audience |
|----------|-------------|----------|
| [../database/README.md](../database/README.md) | Database schema | Backend, DevOps |
| [../reference/DATABASE_SETUP.md](../reference/DATABASE_SETUP.md) | Database configuration | Backend, DevOps |

### 📊 Performance & Optimization

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/LATENCY_OPTIMIZATION_GUIDE.md](../reference/LATENCY_OPTIMIZATION_GUIDE.md) | Performance tuning | Backend, DevOps |

### 🐛 Troubleshooting & Fixes

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/RENDER_DEPLOYMENT_FIX.md](../reference/RENDER_DEPLOYMENT_FIX.md) | Render timeout fix | DevOps |
| [../reference/HF_SPACE_MIGRATION_SUMMARY.md](../reference/HF_SPACE_MIGRATION_SUMMARY.md) | HuggingFace Space migration | Backend |
| [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md#troubleshooting) | Deployment troubleshooting | DevOps |
| [LOCAL_SETUP.md](LOCAL_SETUP.md#troubleshooting) | Local setup issues | All developers |

### 📝 Logging & Monitoring

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/FRONTEND_LOGGING_GUIDE.md](../reference/FRONTEND_LOGGING_GUIDE.md) | Frontend logging | Frontend |
| [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md#monitoring--logs) | Production monitoring | DevOps |

### 📚 Reference

| Document | Description | Audience |
|----------|-------------|----------|
| [../reference/DOCUMENTATION_INDEX.md](../reference/DOCUMENTATION_INDEX.md) | Detailed doc index | All |
| [../reference/CONTINUOUS_VOICE_GUIDE.md](../reference/CONTINUOUS_VOICE_GUIDE.md) | Voice interface guide | Frontend |
| [../reference/STREAMING_AND_DEPLOYMENT.md](../reference/STREAMING_AND_DEPLOYMENT.md) | Streaming architecture | Backend |

---

## Key Concepts

### Dual ASR Modes

The system supports two ASR (Automatic Speech Recognition) modes:

**Local ASR Mode (`USE_LOCAL_ASR=true`)**
- Uses local SenseVoice model
- Requires ~2.5GB dependencies (PyTorch, FunASR)
- Fast, offline transcription (~0.5s)
- Best for local development

**HuggingFace Space Mode (`USE_LOCAL_ASR=false`)**
- Uses HuggingFace Space API
- Lightweight dependencies (~500MB)
- Cloud-based transcription (~1-2s)
- Best for production (Render)

See: [LOCAL_SETUP.md](LOCAL_SETUP.md#installation-options)

### Audio Pipeline

```
[Microphone] → [VAD] → [PCM Capture] → [WAV Encoding] → [Base64]
                ↓
          [WebSocket] → [Backend] → [ASR] → [LLM] → [TTS]
                                      ↓
                                [Audio Response]
```

See: [../reference/WAV_IMPLEMENTATION_COMPLETE.md](../reference/WAV_IMPLEMENTATION_COMPLETE.md)

### Deployment Modes

```
┌─────────────────────┬──────────────────────┬──────────────────────┐
│ Environment         │ Local Development    │ Production (Render)  │
├─────────────────────┼──────────────────────┼──────────────────────┤
│ ASR Mode            │ Local or HF Space    │ HF Space only        │
│ USE_LOCAL_ASR       │ true or false        │ false (required)     │
│ Dependencies        │ Full or lightweight  │ Lightweight only     │
│ Install command     │ uv sync --extra...   │ uv sync --frozen     │
│ Model required      │ Optional             │ No                   │
│ Startup time        │ 10-30s (with model)  │ <2 min               │
│ Transcription speed │ ~0.5s (local)        │ ~1-2s (API)          │
└─────────────────────┴──────────────────────┴──────────────────────┘
```

See:
- [LOCAL_SETUP.md](LOCAL_SETUP.md#installation-options)
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md#key-configuration-points)

---

## Documentation Standards

### Creating New Documentation

When adding new documentation:

1. **Choose appropriate location:**
   - Setup/deployment guides → `docs/`
   - Technical deep-dives → `reference/`
   - Test documentation → `tests/`
   - API documentation → `backend/` or `frontend/`

2. **Follow naming conventions:**
   - Guides: `TOPIC_GUIDE.md` (e.g., `AUDIO_GUIDE.md`)
   - Fixes: `TOPIC_FIXES.md` (e.g., `WEBSOCKET_FIXES.md`)
   - Summaries: `TOPIC_SUMMARY.md` (e.g., `MIGRATION_SUMMARY.md`)

3. **Include standard sections:**
   - Table of contents
   - Prerequisites
   - Clear step-by-step instructions
   - Code examples with syntax highlighting
   - Troubleshooting section
   - Links to related docs

4. **Update this index:**
   - Add entry to appropriate category
   - Update navigation table if needed
   - Update "Last Updated" date

### Markdown Style Guide

```markdown
# Document Title

Brief description (1-2 sentences)

Last Updated: YYYY-MM-DD
Version: vX.Y.Z

---

## Table of Contents

1. [Section 1](#section-1)
2. [Section 2](#section-2)

---

## Section 1

Content here...

### Subsection

More content...

## Code Examples

```bash
# Always include comments
command --flag value
```

## Links

- Use relative paths: [Other Doc](./OTHER_DOC.md)
- External links: [FastAPI](https://fastapi.tiangolo.com)
```

---

## Frequently Asked Questions

### Q: Which documentation should I read first?

**A:** Start with [../README.md](../README.md), then [LOCAL_SETUP.md](LOCAL_SETUP.md), then [../reference/SYSTEM_DESIGN_CURRENT.md](../reference/SYSTEM_DESIGN_CURRENT.md).

### Q: How do I run the system locally without downloading the 1GB model?

**A:** Use lightweight mode with HuggingFace Space API:
```bash
uv sync --frozen  # No --extra local-asr
USE_LOCAL_ASR=false make run-server-hf
```

See: [LOCAL_SETUP.md](LOCAL_SETUP.md#option-1-lightweight-huggingface-space-asr-only)

### Q: Where are deployment instructions?

**A:** See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete Render.com deployment guide.

### Q: How do I run tests?

**A:** See [TESTING.md](TESTING.md) for comprehensive testing guide.

### Q: Why does my local ASR fail?

**A:** Ensure you have installed with `--extra local-asr` and downloaded the SenseVoice model. See [LOCAL_SETUP.md](LOCAL_SETUP.md#sensevoice-model-setup).

### Q: How do I switch between local and cloud ASR?

**A:** Set the `USE_LOCAL_ASR` environment variable:
- Local ASR: `USE_LOCAL_ASR=true make run-server`
- Cloud ASR: `USE_LOCAL_ASR=false make run-server-hf`

---

## Contributing to Documentation

We welcome documentation improvements! Please:

1. **Check existing docs** to avoid duplication
2. **Follow style guide** above
3. **Test all commands** and code examples
4. **Update this index** when adding new docs
5. **Submit PR** with clear description

---

## Support

- **Issues**: https://github.com/HaozheZhang6/news_agent/issues
- **Discussions**: GitHub Discussions
- **Email**: team@voicenewsagent.com

---

## Document Maintenance

| Task | Frequency | Last Done | Next Due |
|------|-----------|-----------|----------|
| Update outdated links | Monthly | 2025-10-14 | 2025-11-14 |
| Review for accuracy | Quarterly | 2025-10-14 | 2026-01-14 |
| Update code examples | On version bump | 2025-10-14 | Next release |
| Add new features | As implemented | 2025-10-14 | Ongoing |

---

**Documentation maintained by:** Development Team
**Last comprehensive review:** 2025-10-14
**Next scheduled review:** 2025-11-14

**All documentation is up-to-date and production-ready.** ✅
