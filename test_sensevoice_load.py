#!/usr/bin/env python3
"""
Test SenseVoice Model Loading

Verifies that the SenseVoice model can be loaded correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_sensevoice_loading():
    """Test SenseVoice model loading."""
    print("=" * 80)
    print("🧪 Testing SenseVoice Model Loading")
    print("=" * 80)

    # Test 1: Check if model files exist
    print("\n1️⃣ Checking model files...")
    model_path = project_root / "models" / "iic" / "SenseVoiceSmall"

    if not model_path.exists():
        print(f"❌ Model directory not found: {model_path}")
        return False

    required_files = ["model.pt", "config.yaml", "tokens.json"]
    missing_files = []

    for file in required_files:
        file_path = model_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            missing_files.append(file)
            print(f"   ❌ {file} not found")

    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False

    # Test 2: Import FunASR
    print("\n2️⃣ Testing FunASR import...")
    try:
        from funasr import AutoModel
        print("   ✅ FunASR imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import FunASR: {e}")
        return False

    # Test 3: Load SenseVoice model
    print("\n3️⃣ Loading SenseVoice model...")
    try:
        print(f"   📁 Model path: {model_path}")
        print("   ⏳ Loading... (this may take a moment)")

        model = AutoModel(
            model=str(model_path),
            trust_remote_code=True
        )

        print("   ✅ SenseVoice model loaded successfully!")

        # Test 4: Get model info
        print("\n4️⃣ Model information:")
        print(f"   Model type: {type(model)}")
        print(f"   Model path: {model_path}")

        return True

    except Exception as e:
        print(f"   ❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    success = test_sensevoice_loading()

    print("\n" + "=" * 80)
    if success:
        print("✅ All tests passed! SenseVoice model is ready to use.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    print("=" * 80)
    print()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
