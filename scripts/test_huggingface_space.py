"""
Call the Space using gradio_client; works for public or private Spaces.

Requirements:
    pip install gradio_client
Env (only for private Spaces):
    export HF_TOKEN="hf_***"
"""
from __future__ import annotations

import os
from gradio_client import Client, handle_file


def transcribe_with_client(audio_path: str) -> str:
    """
    Invoke the Space endpoint '/predict' and return the transcript.

    Args:
        audio_path: Local path to audio (wav/ogg/opus/webm).

    Returns:
        Transcript string returned by the Space.
    """
    client = Client("hz6666/SenseVoiceSmall", hf_token=os.getenv("HF_TOKEN"))
    result = client.predict(handle_file(audio_path), api_name="/predict")
    return str(result)


if __name__ == "__main__":
    
    print(transcribe_with_client("tests/voice_samples/wav/test_analysis_aapl_deeper.wav"))
