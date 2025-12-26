#!/usr/bin/env python
"""
Script to extract all translation strings from the project
and update .po files for all languages
Run: python extract_translations.py
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def extract_messages():
    """Extract all translation strings from the project"""
    try:
        print("🔍 Extracting translation strings from the project...")
        print("=" * 60)
        
        # Change to project directory
        os.chdir(BASE_DIR)
        
        # List of languages
        languages = ['fa', 'en']
        
        print(f"\n📝 Languages to process: {', '.join(languages)}")
        print("\nSearching in:")
        print("  ✓ Python files (.py)")
        print("  ✓ Template files (.html, .txt)")
        print("  ✓ All application directories")
        
        # Run makemessages for each language
        for lang in languages:
            print(f"\n{'=' * 60}")
            print(f"🔄 Processing language: {lang}")
            print(f"{'=' * 60}")
            
            try:
                # Run Django's makemessages command
                # Use --no-input to avoid interactive prompts
                result = subprocess.run(
                    [sys.executable, 'manage.py', 'makemessages', '-l', lang, '--no-input', '-v', '2'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                
                if result.returncode == 0:
                    po_file = BASE_DIR / 'locale' / lang / 'LC_MESSAGES' / 'django.po'
                    if po_file.exists():
                        # Count entries
                        with open(po_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Count msgid entries (rough estimate)
                            count = content.count('msgid "')
                        print(f"✅ Updated: {po_file.relative_to(BASE_DIR)}")
                        print(f"   Found approximately {count} translation strings")
                else:
                    print(f"⚠️  Issue processing {lang}, but .po file may still exist")
                    
            except subprocess.TimeoutExpired:
                print(f"⚠️  Timeout processing {lang}")
            except Exception as e:
                print(f"⚠️  Error processing {lang}: {e}")
        
        print(f"\n{'=' * 60}")
        print("✅ Translation extraction completed!")
        print(f"{'=' * 60}")
        
        print("\n📁 Generated .po files:")
        locale_path = BASE_DIR / 'locale'
        if locale_path.exists():
            po_files = list(locale_path.rglob('django.po'))
            if po_files:
                for po_file in sorted(po_files):
                    print(f"   ✓ {po_file.relative_to(BASE_DIR)}")
            else:
                print("   (No .po files found)")
        
        print("\n📋 Next steps:")
        print("   1. Edit the .po files to add translations")
        print("   2. Run: python compile_translations.py")
        print("   3. Restart the Django server")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting messages: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = extract_messages()
    sys.exit(0 if success else 1)
