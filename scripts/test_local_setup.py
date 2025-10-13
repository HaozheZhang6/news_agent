#!/usr/bin/env python3
"""
Test Local SenseVoice Setup

Verifies that the local SenseVoice model setup works correctly
with the models/ directory structure.
"""

import os
import sys
from pathlib import Path

def test_local_sensevoice_setup():
    """Test local SenseVoice model setup."""
    print("=" * 80)
    print("🧪 Testing Local SenseVoice Setup")
    print("=" * 80)
    
    # Check if we're in the right directory
    project_root = Path(__file__).parent.parent
    print(f"📁 Project root: {project_root}")
    
    # Check models directory structure
    models_dir = project_root / "models"
    print(f"📁 Models directory: {models_dir}")
    print(f"   Exists: {models_dir.exists()}")
    
    if models_dir.exists():
        print("   Contents:")
        for item in models_dir.iterdir():
            if item.is_dir():
                print(f"     📁 {item.name}/")
            else:
                print(f"     📄 {item.name}")
    
    # Check gitignore
    gitignore_path = project_root / ".gitignore"
    print(f"\n📄 .gitignore: {gitignore_path.exists()}")
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
            if "/models" in content:
                print("   ✅ models/ directory is properly ignored")
            else:
                print("   ⚠️  models/ directory not found in .gitignore")
    
    # Test model path resolution
    print(f"\n🔧 Model Path Resolution:")
    
    # Test src config
    sys.path.insert(0, str(project_root / "src"))
    try:
        from config import SENSEVOICE_MODEL_PATH
        print(f"   src/config.py: {SENSEVOICE_MODEL_PATH}")
        print(f"   Exists: {os.path.exists(SENSEVOICE_MODEL_PATH)}")
    except ImportError as e:
        print(f"   src/config.py: Import error - {e}")
    
    # Test backend config
    sys.path.insert(0, str(project_root / "backend"))
    try:
        from app.config import settings
        print(f"   backend/config.py: {settings.sensevoice_model_path}")
        print(f"   Exists: {os.path.exists(settings.sensevoice_model_path)}")
    except ImportError as e:
        print(f"   backend/config.py: Import error - {e}")
    
    print("\n" + "=" * 80)
    print("✅ Local setup test complete!")
    print("=" * 80)
    print()
    print("💡 Next steps:")
    print("   1. Run: uv run python scripts/download_sensevoice.py")
    print("   2. Test backend: uv run python -m backend.app.main")
    print("   3. Test src: uv run python src/main.py")
    print()


def main():
    """Main entry point."""
    test_local_sensevoice_setup()


if __name__ == "__main__":
    main()
