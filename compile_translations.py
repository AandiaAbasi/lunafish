#!/usr/bin/env python
"""
Script to compile translation files (.po to .mo)
Run: python compile_translations.py
"""
import os
import sys
import glob
from pathlib import Path
import subprocess

# Add project directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def compile_messages():
    """Compile .po files to .mo files"""
    try:
        print("🔄 Compiling translation messages...")
        print("=" * 50)
        
        # Change to project directory
        os.chdir(BASE_DIR)
        
        # Run Django's compilemessages command via subprocess to avoid database connection
        result = subprocess.run(
            [sys.executable, 'manage.py', 'compilemessages', '-v', '2'],
            capture_output=False
        )
        
        if result.returncode != 0:
            print(f"❌ Error compiling messages")
            return False
        
        print("=" * 50)
        print("✅ Translation files compiled successfully!")
        print("\n📁 Generated .mo files:")
        
        # List generated .mo files
        locale_path = BASE_DIR / 'locale'
        if locale_path.exists():
            mo_files = list(locale_path.rglob('*.mo'))
            if mo_files:
                for mo_file in mo_files:
                    print(f"   ✓ {mo_file.relative_to(BASE_DIR)}")
            else:
                print("   (No .mo files found)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error compiling messages: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = compile_messages()
    sys.exit(0 if success else 1)
