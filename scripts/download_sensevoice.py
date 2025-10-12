#!/usr/bin/env python3
"""
Download SenseVoice Model Script

Downloads the SenseVoiceSmall model from ModelScope for offline ASR.
"""

import os
import sys
from pathlib import Path

def download_sensevoice_model():
    """Download SenseVoice model from ModelScope."""
    try:
        from modelscope.hub.snapshot_download import snapshot_download

        # Get project root
        project_root = Path(__file__).parent.parent
        model_dir = project_root / "models" / "SenseVoiceSmall"

        print("=" * 80)
        print("🔽 Downloading SenseVoice Model")
        print("=" * 80)
        print(f"📁 Target directory: {model_dir}")
        print(f"📦 Model: iic/SenseVoiceSmall")
        print()

        # Create directory
        model_dir.mkdir(parents=True, exist_ok=True)

        # Download model
        print("⏳ Downloading... (this may take a few minutes)")
        model_path = snapshot_download(
            model_id="iic/SenseVoiceSmall",
            cache_dir=str(model_dir.parent),
            revision="master"
        )

        print()
        print("=" * 80)
        print("✅ Download Complete!")
        print("=" * 80)
        print(f"📁 Model location: {model_path}")
        print()
        print("📊 Model Contents:")

        # List downloaded files
        if os.path.exists(model_path):
            for item in os.listdir(model_path):
                item_path = os.path.join(model_path, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    print(f"   📄 {item} ({size:,} bytes)")
                else:
                    print(f"   📁 {item}/")

        print()
        print("🎉 SenseVoice model is ready to use!")
        print()
        print("💡 Usage:")
        print(f"   Set SENSEVOICE_MODEL_PATH={model_path}")
        print("   Or place in: models/SenseVoiceSmall/")
        print()

        return model_path

    except ImportError:
        print("❌ Error: modelscope package not installed")
        print()
        print("Please install funasr which includes modelscope:")
        print("   uv pip install funasr")
        print()
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check internet connection")
        print("2. Ensure modelscope is installed: uv pip install modelscope")
        print("3. Try manual download from: https://modelscope.cn/models/iic/SenseVoiceSmall")
        print()
        sys.exit(1)


def main():
    """Main entry point."""
    print()
    download_sensevoice_model()
    print()


if __name__ == "__main__":
    main()
