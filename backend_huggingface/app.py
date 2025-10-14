import base64
import io
import os
from pathlib import Path
from typing import Tuple

import gradio as gr
import numpy as np
import soundfile as sf


# Global model handle (lazy-loaded)
_model = None


def _download_or_resolve_model() -> str:
    """Ensure model exists in a writable cache dir and return local path.

    Uses ModelScope's default cache (~/.cache/modelscope/hub) which is
    writable on Hugging Face Spaces.
    """
    try:
        from modelscope.hub.snapshot_download import snapshot_download

        cache_dir = Path.home() / ".cache" / "modelscope" / "hub"
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_path = snapshot_download(
            model_id="iic/SenseVoiceSmall",
            cache_dir=str(cache_dir),
            revision="master",
        )
        return str(model_path)
    except Exception as e:
        # If anything goes wrong, fall back to a conventional project path
        # (still try to keep it writable on Spaces)
        fallback = str(Path.home() / "models" / "SenseVoiceSmall")
        os.makedirs(fallback, exist_ok=True)
        print(f"[WARN] Model download failed, using fallback dir: {e}")
        return fallback


def _load_model():
    global _model
    if _model is not None:
        return _model

    model_path = _download_or_resolve_model()
    print(f"[INIT] Loading SenseVoice model from: {model_path}")
    from funasr import AutoModel

    _model = AutoModel(model=model_path, trust_remote_code=True)
    print("[INIT] SenseVoice model loaded")
    return _model


def _decode_audio_b64(b64_data: str) -> Tuple[np.ndarray, int]:
    """Decode base64-encoded audio (wav/ogg/opus) into mono float32 PCM and sample rate."""
    audio_bytes = base64.b64decode(b64_data)
    with sf.SoundFile(io.BytesIO(audio_bytes)) as f:
        audio = f.read(dtype='float32')
        sr = f.samplerate
    # Convert to mono if multi-channel
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio, sr


def transcribe_audio(gr_audio) -> str:
    """Gradio fn: accepts audio either from microphone (temp file) or from base64 JSON.

    - If gradio mic/upload is used, `gr_audio` is (sr, numpy.ndarray)
    - If a dict with {"name":"...","data":"<base64>"} is posted via /api/predict,
      handle that path too.
    """
    try:
        model = _load_model()

        # Case 1: standard Gradio input: (sample_rate, np.ndarray)
        if isinstance(gr_audio, tuple) and len(gr_audio) == 2:
            sr, audio = gr_audio
            if audio is None or len(audio) == 0:
                return "No audio received"
            # funasr expects file path or raw array; we'll save temp wav for simplicity
            wav_path = "_tmp.wav"
            sf.write(wav_path, audio, sr)
            result = model.generate(input=wav_path)
            text = result[0]["text"] if isinstance(result, list) else str(result)
            try:
                os.remove(wav_path)
            except Exception:
                pass
            return text

        # Case 2: API style: dict with base64
        if isinstance(gr_audio, dict) and "data" in gr_audio:
            try:
                audio, sr = _decode_audio_b64(gr_audio["data"])
                wav_path = "_tmp.wav"
                sf.write(wav_path, audio, sr)
                result = model.generate(input=wav_path)
                text = result[0]["text"] if isinstance(result, list) else str(result)
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
                return text
            except Exception as e:
                return f"Failed to decode/process audio: {e}"

        return "Unsupported input format"
    except Exception as e:
        return f"Error during transcription: {str(e)}"


with gr.Blocks() as demo:
    gr.Markdown("""
    # SenseVoiceSmall ASR (Gradio)
    Upload a short audio file or record via microphone to get a transcript.
    """)

    with gr.Row():
        audio = gr.Audio(sources=["microphone", "upload"], type="numpy", label="Audio")
    with gr.Row():
        out = gr.Textbox(label="Transcript")

    btn = gr.Button("Transcribe")
    btn.click(fn=transcribe_audio, inputs=audio, outputs=out)


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))


