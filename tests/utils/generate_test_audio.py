#!/usr/bin/env python3
"""
Generate test audio samples from voice_samples.json configuration.

This script:
1. Reads voice_samples.json configuration
2. Generates WAV files using TTS (edge-tts or gtts)
3. Encodes WAV to OPUS compressed format
4. Saves encoded audio as base64 JSON files
5. Creates a lookup table for test usage

Usage:
    uv run python tests/utils/generate_test_audio.py [--regenerate-all] [--sample-id SAMPLE_ID]

Examples:
    # Generate all missing samples
    uv run python tests/utils/generate_test_audio.py

    # Regenerate all samples (overwrite existing)
    uv run python tests/utils/generate_test_audio.py --regenerate-all

    # Generate specific sample only
    uv run python tests/utils/generate_test_audio.py --sample-id news_nvda_latest
"""

import asyncio
import json
import logging
import os
import sys
import wave
from base64 import b64encode
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

# Try to import required libraries
try:
    import edge_tts
    TTS_ENGINE = "edge-tts"
    logger.info("Using edge-tts for speech synthesis")
except ImportError:
    try:
        from gtts import gTTS
        TTS_ENGINE = "gtts"
        logger.info("Using gtts for speech synthesis")
    except ImportError:
        logger.error("No TTS engine available. Install edge-tts or gtts:")
        logger.error("  uv pip install edge-tts")
        logger.error("  or")
        logger.error("  uv pip install gtts")
        sys.exit(1)

OPUS_AVAILABLE = True  # We'll use ffmpeg for OPUS encoding


class AudioGenerator:
    """Generate test audio samples from text."""

    def __init__(self, config_path: Path):
        """Initialize audio generator with config."""
        self.config_path = config_path
        self.base_dir = config_path.parent
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load voice samples configuration."""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    async def generate_wav_edge_tts(self, text: str, output_path: Path) -> bool:
        """Generate WAV file using edge-tts."""
        try:
            # Use a clear, neutral voice
            voice = "en-US-GuyNeural"
            communicate = edge_tts.Communicate(text, voice)

            # Save to temporary MP3 first
            temp_mp3 = output_path.with_suffix('.mp3')
            await communicate.save(str(temp_mp3))

            # Convert MP3 to WAV using ffmpeg
            import subprocess
            cmd = [
                'ffmpeg', '-i', str(temp_mp3),
                '-ar', str(SAMPLE_RATE),
                '-ac', str(CHANNELS),
                '-sample_fmt', 's16',
                '-y',  # Overwrite
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False

            # Clean up temp file
            temp_mp3.unlink()

            logger.info(f"✓ Generated WAV: {output_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate WAV with edge-tts: {e}")
            return False

    def generate_wav_gtts(self, text: str, output_path: Path) -> bool:
        """Generate WAV file using gtts."""
        try:
            # Generate MP3 with gtts
            tts = gTTS(text=text, lang='en', slow=False)
            temp_mp3 = output_path.with_suffix('.mp3')
            tts.save(str(temp_mp3))

            # Convert MP3 to WAV using ffmpeg
            import subprocess
            cmd = [
                'ffmpeg', '-i', str(temp_mp3),
                '-ar', str(SAMPLE_RATE),
                '-ac', str(CHANNELS),
                '-sample_fmt', 's16',
                '-y',
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False

            # Clean up temp file
            temp_mp3.unlink()

            logger.info(f"✓ Generated WAV: {output_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate WAV with gtts: {e}")
            return False

    async def generate_wav(self, text: str, output_path: Path) -> bool:
        """Generate WAV file using available TTS engine."""
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if TTS_ENGINE == "edge-tts":
            return await self.generate_wav_edge_tts(text, output_path)
        else:
            return self.generate_wav_gtts(text, output_path)

    def encode_wav_to_opus(self, wav_path: Path, output_path: Path) -> bool:
        """Encode WAV file to OPUS and save as base64 JSON (matching existing format)."""
        try:
            import subprocess
            import uuid
            from datetime import datetime

            # Create temp opus file
            temp_opus = output_path.with_suffix('.opus')

            # Encode to Opus using ffmpeg (matches existing format: Ogg Opus)
            cmd = [
                'ffmpeg', '-i', str(wav_path),
                '-c:a', 'libopus',
                '-b:a', '64k',
                '-ar', str(SAMPLE_RATE),
                '-ac', str(CHANNELS),
                '-y',
                str(temp_opus)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg OPUS encoding error: {result.stderr}")
                return False

            # Read the opus file and encode to base64
            with open(temp_opus, 'rb') as f:
                opus_data = f.read()

            # Get WAV file size for compression stats
            wav_size = wav_path.stat().st_size
            opus_size = len(opus_data)
            compression_ratio = wav_size / opus_size if opus_size > 0 else 0

            # Create JSON in the same format as existing files
            output_data = {
                "event": "audio_chunk",
                "data": {
                    "audio_chunk": b64encode(opus_data).decode('utf-8'),
                    "format": "opus",
                    "is_final": True,
                    "session_id": str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "sample_rate": SAMPLE_RATE,
                    "file_size": opus_size,
                    "original_filename": wav_path.name,
                    "encoded_at": datetime.now().isoformat(),
                    "compression": {
                        "codec": "opus",
                        "original_size": wav_size,
                        "compressed_size": opus_size,
                        "compression_ratio": compression_ratio,
                        "bitrate": "64k",
                        "sample_rate": str(SAMPLE_RATE),
                        "description": "Opus - Best for real-time speech (WebRTC standard)"
                    }
                }
            }

            # Save JSON
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)

            # Clean up temp file
            temp_opus.unlink()

            logger.info(f"✓ Encoded OPUS: {output_path.name} (compression: {compression_ratio:.1f}x)")
            return True

        except Exception as e:
            logger.error(f"Failed to encode OPUS: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def generate_sample(self, sample_id: str, sample_data: Dict, regenerate: bool = False) -> bool:
        """Generate both WAV and OPUS for a single sample."""
        text = sample_data['text']
        wav_rel_path = sample_data['wav_path']
        encoded_rel_path = sample_data['encoded_path']

        wav_path = self.base_dir / wav_rel_path
        encoded_path = self.base_dir / encoded_rel_path

        logger.info(f"\n{'='*60}")
        logger.info(f"Sample: {sample_id}")
        logger.info(f"Text: {text}")
        logger.info(f"{'='*60}")

        # Generate WAV if needed
        if regenerate or not wav_path.exists():
            success = await self.generate_wav(text, wav_path)
            if not success:
                logger.error(f"✗ Failed to generate WAV for {sample_id}")
                return False
        else:
            logger.info(f"→ WAV exists: {wav_path.name}")

        # Generate OPUS if needed
        if OPUS_AVAILABLE and (regenerate or not encoded_path.exists()):
            success = self.encode_wav_to_opus(wav_path, encoded_path)
            if not success:
                logger.warning(f"⚠ Failed to encode OPUS for {sample_id}")
        elif not OPUS_AVAILABLE:
            logger.info(f"→ Skipping OPUS encoding (opuslib not available)")
        else:
            logger.info(f"→ OPUS exists: {encoded_path.name}")

        return True

    async def generate_all_samples(self, regenerate: bool = False, sample_filter: Optional[str] = None):
        """Generate all samples from configuration."""
        samples = self.config['samples']

        total_samples = 0
        generated_samples = 0
        failed_samples = []

        # Count total samples
        for category, sample_list in samples.items():
            if category == "multi_turn_scenarios":
                continue  # Skip scenarios, they reference existing samples
            total_samples += len(sample_list)

        logger.info(f"\n{'='*60}")
        logger.info(f"AUDIO SAMPLE GENERATION")
        logger.info(f"{'='*60}")
        logger.info(f"TTS Engine: {TTS_ENGINE}")
        logger.info(f"OPUS Encoding: {'Available' if OPUS_AVAILABLE else 'Not available'}")
        logger.info(f"Total samples: {total_samples}")
        logger.info(f"Regenerate: {regenerate}")
        if sample_filter:
            logger.info(f"Filter: {sample_filter}")
        logger.info(f"{'='*60}\n")

        # Generate samples by category
        for category, sample_list in samples.items():
            if category == "multi_turn_scenarios":
                continue

            logger.info(f"\n{'#'*60}")
            logger.info(f"# Category: {category.replace('_', ' ').title()}")
            logger.info(f"{'#'*60}\n")

            for sample in sample_list:
                sample_id = sample['id']

                # Apply filter if specified
                if sample_filter and sample_filter not in sample_id:
                    continue

                try:
                    success = await self.generate_sample(sample_id, sample, regenerate)
                    if success:
                        generated_samples += 1
                    else:
                        failed_samples.append(sample_id)
                except Exception as e:
                    logger.error(f"Error generating {sample_id}: {e}")
                    failed_samples.append(sample_id)

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"GENERATION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total samples: {total_samples}")
        logger.info(f"Successfully generated: {generated_samples}")
        logger.info(f"Failed: {len(failed_samples)}")

        if failed_samples:
            logger.error(f"\nFailed samples:")
            for sample_id in failed_samples:
                logger.error(f"  - {sample_id}")

        logger.info(f"\n{'='*60}\n")

        return len(failed_samples) == 0


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test audio samples")
    parser.add_argument(
        '--regenerate-all',
        action='store_true',
        help='Regenerate all samples (overwrite existing)'
    )
    parser.add_argument(
        '--sample-id',
        type=str,
        help='Generate specific sample only (partial match)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path(__file__).parent.parent / 'voice_samples' / 'voice_samples.json',
        help='Path to voice_samples.json config'
    )

    args = parser.parse_args()

    # Check config exists
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    # Check ffmpeg is available
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("ffmpeg is required but not found.")
        logger.error("Install with: brew install ffmpeg")
        sys.exit(1)

    # Generate samples
    generator = AudioGenerator(args.config)
    success = await generator.generate_all_samples(
        regenerate=args.regenerate_all,
        sample_filter=args.sample_id
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
