"""
HuggingFace Space ASR Integration.

Uses the deployed SenseVoice model on HuggingFace Spaces for transcription.
Replaces local model loading to solve Render deployment issues.

Benefits:
- No model download needed (fast deployment)
- Low cold start time
- Scalable cloud infrastructure
- Consistent performance

Usage:
    from backend.app.core.hf_space_asr import HFSpaceASR

    asr = HFSpaceASR()
    transcription = await asr.transcribe_audio("audio.wav")
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

try:
    from gradio_client import Client, handle_file
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False


class HFSpaceASR:
    """HuggingFace Space ASR client."""

    def __init__(
        self,
        space_name: str = "hz6666/SenseVoiceSmall",
        hf_token: Optional[str] = None
    ):
        """
        Initialize HF Space ASR client.

        Args:
            space_name: HuggingFace Space name (user/space)
            hf_token: Optional HuggingFace token for private spaces
        """
        self.space_name = space_name
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self._client = None
        self._initialized = False

        if not GRADIO_CLIENT_AVAILABLE:
            raise ImportError(
                "gradio_client not installed. "
                "Install with: uv pip install gradio_client"
            )

    def _get_client(self) -> Client:
        """Get or create Gradio client."""
        if self._client is None:
            self._client = Client(
                self.space_name,
                hf_token=self.hf_token
            )
            self._initialized = True
            print(f"✅ Connected to HF Space: {self.space_name}")

        return self._client

    async def transcribe_audio(
        self,
        audio_path: str,
        cleanup: bool = True
    ) -> str:
        """
        Transcribe audio file using HuggingFace Space.

        Args:
            audio_path: Path to audio file (WAV format recommended)
            cleanup: Whether to cleanup temp file after transcription

        Returns:
            Transcription text

        Raises:
            Exception: If transcription fails
        """
        try:
            # Get client
            client = self._get_client()

            # Run prediction in executor to avoid blocking
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                lambda: client.predict(
                    handle_file(audio_path),
                    api_name="/predict"
                )
            )

            # Clean SenseVoice output format
            result = str(transcription)

            # Remove language tags, emotion tags, etc.
            # Format: <|en|><|NEUTRAL|><|Speech|><|woitn|>actual text
            if "<|woitn|>" in result:
                result = result.split("<|woitn|>", 1)[1].strip()
            elif "|>" in result:
                # Fallback: remove all tags
                parts = result.split("|>")
                result = parts[-1].strip() if parts else result

            return result

        except Exception as e:
            print(f"❌ HF Space ASR error: {e}")
            raise

    async def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        format: str = "wav"
    ) -> str:
        """
        Transcribe audio from bytes.

        Args:
            audio_bytes: Audio data as bytes
            sample_rate: Sample rate (Hz)
            format: Audio format (wav, ogg, opus)

        Returns:
            Transcription text
        """
        # Create temp file
        with tempfile.NamedTemporaryFile(
            suffix=f".{format}",
            delete=False
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            # Transcribe
            result = await self.transcribe_audio(tmp_path, cleanup=False)
            return result
        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def is_available(self) -> bool:
        """Check if HF Space ASR is available."""
        try:
            client = self._get_client()
            return client is not None
        except Exception:
            return False


# Singleton instance
_hf_space_asr: Optional[HFSpaceASR] = None


def get_hf_space_asr() -> HFSpaceASR:
    """Get singleton HFSpaceASR instance."""
    global _hf_space_asr

    if _hf_space_asr is None:
        _hf_space_asr = HFSpaceASR()

    return _hf_space_asr


async def transcribe_with_hf_space(
    audio_path: str,
    fallback: Optional[str] = None
) -> str:
    """
    Convenience function to transcribe audio.

    Args:
        audio_path: Path to audio file
        fallback: Fallback text if transcription fails

    Returns:
        Transcription text or fallback
    """
    try:
        asr = get_hf_space_asr()
        return await asr.transcribe_audio(audio_path)
    except Exception as e:
        print(f"⚠️ HF Space transcription failed: {e}")
        if fallback:
            print(f"   Using fallback: {fallback}")
            return fallback
        raise


# Example usage
async def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hf_space_asr.py <audio_file.wav>")
        sys.exit(1)

    audio_file = sys.argv[1]

    print(f"Transcribing: {audio_file}")
    asr = HFSpaceASR()

    try:
        transcription = await asr.transcribe_audio(audio_file)
        print(f"\nTranscription: {transcription}")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
