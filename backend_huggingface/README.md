---
title: SenseVoiceSmall ASR
emoji: 🗣️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

## Hugging Face Space - SenseVoice ASR (Gradio)

This folder contains a minimal Gradio app to run the SenseVoiceSmall model as a free Hugging Face Space.

### What you get
- Simple web UI to upload/record audio and get a transcript
- Public REST endpoint via Gradio `/api/predict`
- Model cached to `~/.cache/modelscope/hub` (avoids read-only paths like `/app`)

### Files
- `app.py`: Gradio application with model loading and inference
- `requirements.txt`: Minimal dependencies for the Space

### Deploy steps
1) Create a new Space on Hugging Face
   - SDK: Gradio
   - Runtime: Python 3.10 or 3.11
2) Upload the files from `backend_huggingface/` (or point your Space to this subfolder)
3) The Space will build and start automatically

### API usage (HTTP)
Default Gradio predict route (Space URL example: `https://<your-space>.hf.space`):

POST `https://<your-space>.hf.space/api/predict/`

Body (JSON):
```
{
  "data": [
    {
      "name": "audio.wav",
      "data": "<base64-encoded-wav-or-ogg-opus>"
    }
  ]
}
```

Response (JSON):
```
{
  "data": ["<transcript string>"]
}
```

Notes:
- Keep audio short (e.g., < 30s) to stay within free CPU limits.
- First request may be slower due to model cold start.


