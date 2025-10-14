#!/usr/bin/env python3
"""
Performance Comparison: WAV vs Base64 for HuggingFace Space ASR.

Comprehensive performance testing to determine the best audio format
for production deployment on Render.

Metrics:
- Latency (end-to-end)
- Accuracy (transcription quality)
- Data transfer size
- Success rate

Run:
    uv run python tests/backend_huggingface/performance/compare_formats.py
"""

import base64
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from gradio_client import Client, handle_file
except ImportError:
    print("❌ gradio_client not installed")
    print("   Install: uv pip install gradio_client")
    sys.exit(1)


@dataclass
class PerformanceResult:
    """Store performance metrics for one test."""
    method: str  # "wav" or "base64"
    audio_file: str
    file_size_bytes: int
    transfer_size_bytes: int  # Actual bytes transferred
    latency_ms: int
    transcription: str
    success: bool
    error: str = ""


class FormatComparison:
    """Compare WAV vs Base64 audio formats."""

    def __init__(self, hf_space: str = "hz6666/SenseVoiceSmall"):
        self.hf_space = hf_space
        self.hf_token = os.getenv("HF_TOKEN")
        self.client = Client(hf_space, hf_token=self.hf_token)
        self.results: List[PerformanceResult] = []

    def test_wav_upload(self, audio_path: Path) -> PerformanceResult:
        """Test WAV file upload."""
        file_size = audio_path.stat().st_size

        result = PerformanceResult(
            method="wav",
            audio_file=audio_path.name,
            file_size_bytes=file_size,
            transfer_size_bytes=file_size,  # WAV sends raw file
            latency_ms=0,
            transcription="",
            success=False
        )

        try:
            start_time = time.time()
            transcription = self.client.predict(
                handle_file(str(audio_path)),
                api_name="/predict"
            )
            result.latency_ms = int((time.time() - start_time) * 1000)
            result.transcription = str(transcription)
            result.success = True

        except Exception as e:
            result.error = str(e)

        return result

    def test_base64_upload(self, audio_path: Path) -> PerformanceResult:
        """Test base64-encoded audio upload."""
        file_size = audio_path.stat().st_size

        # Encode to base64
        with open(audio_path, 'rb') as f:
            wav_bytes = f.read()
        base64_str = base64.b64encode(wav_bytes).decode('utf-8')
        base64_size = len(base64_str)

        result = PerformanceResult(
            method="base64",
            audio_file=audio_path.name,
            file_size_bytes=file_size,
            transfer_size_bytes=base64_size,  # Base64 has ~33% overhead
            latency_ms=0,
            transcription="",
            success=False
        )

        try:
            audio_dict = {
                "name": audio_path.name,
                "data": base64_str
            }

            start_time = time.time()
            transcription = self.client.predict(
                audio_dict,
                api_name="/predict"
            )
            result.latency_ms = int((time.time() - start_time) * 1000)
            result.transcription = str(transcription)
            result.success = True

        except Exception as e:
            result.error = str(e)

        return result

    def compare_single_file(self, audio_path: Path):
        """Compare both methods on single file."""
        print(f"\n{'='*70}")
        print(f"Testing: {audio_path.name}")
        print(f"File size: {audio_path.stat().st_size:,} bytes")
        print(f"{'='*70}")

        # Test WAV
        print(f"\n📤 Testing WAV upload...")
        wav_result = self.test_wav_upload(audio_path)
        self.results.append(wav_result)

        if wav_result.success:
            print(f"✓ Success")
            print(f"  Latency: {wav_result.latency_ms}ms")
            print(f"  Transcription: {wav_result.transcription}")
        else:
            print(f"✗ Failed: {wav_result.error}")

        # Test Base64
        print(f"\n📤 Testing Base64 upload...")
        base64_result = self.test_base64_upload(audio_path)
        self.results.append(base64_result)

        if base64_result.success:
            print(f"✓ Success")
            print(f"  Latency: {base64_result.latency_ms}ms")
            print(f"  Transfer size: {base64_result.transfer_size_bytes:,} bytes (overhead: {base64_result.transfer_size_bytes / base64_result.file_size_bytes:.2f}x)")
            print(f"  Transcription: {base64_result.transcription}")
        else:
            print(f"✗ Failed: {base64_result.error}")

        # Comparison
        if wav_result.success and base64_result.success:
            print(f"\n📊 Comparison:")
            latency_diff = wav_result.latency_ms - base64_result.latency_ms
            faster = "WAV" if latency_diff > 0 else "Base64"
            print(f"  Faster method: {faster} (by {abs(latency_diff)}ms)")

            transcription_match = wav_result.transcription == base64_result.transcription
            print(f"  Transcription match: {'✓ Yes' if transcription_match else '✗ No'}")

            if not transcription_match:
                print(f"    WAV: {wav_result.transcription}")
                print(f"    Base64: {base64_result.transcription}")

    def run_full_comparison(self, audio_dir: Path, max_files: int = 5):
        """Run comparison on multiple files."""
        audio_files = sorted(audio_dir.glob("*.wav"))[:max_files]

        if not audio_files:
            print(f"❌ No WAV files found in {audio_dir}")
            return

        print(f"\n{'='*70}")
        print(f"HuggingFace Space ASR: WAV vs Base64 Performance Comparison")
        print(f"{'='*70}")
        print(f"Space: {self.hf_space}")
        print(f"Files to test: {len(audio_files)}")
        print(f"{'='*70}")

        # Test each file
        for audio_file in audio_files:
            self.compare_single_file(audio_file)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive summary."""
        if not self.results:
            print("\n❌ No results to summarize")
            return

        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE SUMMARY")
        print(f"{'='*70}")

        # Group results by method
        wav_results = [r for r in self.results if r.method == "wav"]
        base64_results = [r for r in self.results if r.method == "base64"]

        # Success rate
        wav_success = [r for r in wav_results if r.success]
        base64_success = [r for r in base64_results if r.success]

        print(f"\n📈 Success Rate:")
        print(f"  WAV: {len(wav_success)}/{len(wav_results)} ({len(wav_success)/len(wav_results)*100:.1f}%)")
        print(f"  Base64: {len(base64_success)}/{len(base64_results)} ({len(base64_success)/len(base64_results)*100:.1f}%)")

        # Latency statistics
        if wav_success:
            wav_latencies = [r.latency_ms for r in wav_success]
            print(f"\n⏱️  WAV Latency:")
            print(f"  Average: {sum(wav_latencies)/len(wav_latencies):.0f}ms")
            print(f"  Min: {min(wav_latencies)}ms")
            print(f"  Max: {max(wav_latencies)}ms")

        if base64_success:
            base64_latencies = [r.latency_ms for r in base64_success]
            print(f"\n⏱️  Base64 Latency:")
            print(f"  Average: {sum(base64_latencies)/len(base64_latencies):.0f}ms")
            print(f"  Min: {min(base64_latencies)}ms")
            print(f"  Max: {max(base64_latencies)}ms")

        # Transfer size comparison
        if base64_success:
            avg_overhead = sum(r.transfer_size_bytes / r.file_size_bytes for r in base64_success) / len(base64_success)
            print(f"\n💾 Data Transfer:")
            print(f"  Base64 overhead: {avg_overhead:.2f}x ({(avg_overhead-1)*100:.1f}% increase)")

        # Overall recommendation
        print(f"\n{'='*70}")
        print(f"RECOMMENDATION")
        print(f"{'='*70}")

        if wav_success and base64_success:
            wav_avg = sum(r.latency_ms for r in wav_success) / len(wav_success)
            base64_avg = sum(r.latency_ms for r in base64_success) / len(base64_success)

            if wav_avg < base64_avg:
                print(f"✓ Use WAV format")
                print(f"  Reason: {base64_avg - wav_avg:.0f}ms faster on average")
            else:
                print(f"✓ Use Base64 format")
                print(f"  Reason: {wav_avg - base64_avg:.0f}ms faster on average")
                print(f"  Note: {(avg_overhead-1)*100:.1f}% data transfer overhead")

        elif wav_success:
            print(f"✓ Use WAV format")
            print(f"  Reason: Base64 method not supported or failed all tests")

        elif base64_success:
            print(f"✓ Use Base64 format")
            print(f"  Reason: WAV method failed all tests")

        else:
            print(f"❌ Both methods failed")

        print(f"{'='*70}\n")


def main():
    """Main entry point."""
    # Configuration
    test_audio_dir = project_root / "tests" / "voice_samples" / "wav"

    if not test_audio_dir.exists():
        print(f"❌ Test audio directory not found: {test_audio_dir}")
        sys.exit(1)

    # Run comparison
    comparator = FormatComparison()
    comparator.run_full_comparison(test_audio_dir, max_files=5)


if __name__ == "__main__":
    main()
