#!/usr/bin/env python3
"""
Deployment SenseVoice Model Download Script

Downloads the SenseVoiceSmall model from ModelScope for cloud deployment.
This script is specifically designed for Render.com deployment.
"""

import os
import sys
from pathlib import Path

def download_sensevoice_model_deploy():
    """Download SenseVoice model from ModelScope for deployment."""
    try:
        from modelscope.hub.snapshot_download import snapshot_download

        # Use ModelScope's default cache directory which is writable
        # This avoids the /app read-only issue during build
        cache_dir = Path.home() / ".cache" / "modelscope" / "hub"

        print("=" * 80)
        print("🔽 Downloading SenseVoice Model for Deployment")
        print("=" * 80)
        print(f"📁 Cache directory: {cache_dir}")
        print(f"📦 Model: iic/SenseVoiceSmall")
        print(f"🌐 Environment: Production/Deployment")
        print()

        # Download model to cache directory
        print("⏳ Downloading... (this may take several minutes)")
        model_path = snapshot_download(
            model_id="iic/SenseVoiceSmall",
            cache_dir=str(cache_dir),
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
        print("🎉 SenseVoice model is ready for deployment!")
        print()
        print("💡 Configuration:")
        print(f"   SENSEVOICE_MODEL_PATH={model_path}")
        print("   Backend will use this cached model path")
        print()

        return str(model_path)

    except ImportError:
        print("❌ Error: modelscope package not installed")
        print()
        print("Please ensure funasr is installed in requirements-deploy.txt")
        print("   funasr>=1.2.7")
        print()
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check internet connection")
        print("2. Ensure modelscope is installed: pip install modelscope")
        print("3. Verify Render build environment has sufficient disk space")
        print("4. Check Render build logs for detailed error information")
        print()
        sys.exit(1)


def main():
    """Main entry point."""
    print()
    download_sensevoice_model_deploy()
    print()


if __name__ == "__main__":
    main()
