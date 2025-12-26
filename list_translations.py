#!/usr/bin/env python
"""
Script to list all translation strings in .po files
Run: python list_translations.py
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def extract_strings_from_po(po_file):
    """Extract all msgid strings from a .po file"""
    strings = []
    
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find all msgid entries
            pattern = r'msgid "([^"]*)"'
            matches = re.findall(pattern, content)
            
            for match in matches:
                if match and match != "":  # Skip empty strings
                    strings.append(match)
        
        return strings
    except Exception as e:
        print(f"Error reading {po_file}: {e}")
        return []

def list_translations():
    """List all translation strings"""
    locale_path = BASE_DIR / 'locale'
    
    if not locale_path.exists():
        print("❌ locale folder not found!")
        return
    
    languages = ['fa', 'en']
    
    for lang in languages:
        po_file = locale_path / lang / 'LC_MESSAGES' / 'django.po'
        
        if not po_file.exists():
            print(f"\n⚠️  {lang} .po file not found: {po_file.relative_to(BASE_DIR)}")
            continue
        
        strings = extract_strings_from_po(po_file)
        
        print(f"\n{'=' * 70}")
        print(f"📝 Translation Strings for Language: {lang.upper()}")
        print(f"{'=' * 70}")
        print(f"Total strings: {len(strings)}\n")
        
        for i, string in enumerate(strings, 1):
            # Truncate long strings
            display_str = string[:60] + "..." if len(string) > 60 else string
            print(f"{i:3d}. {display_str}")
        
        print(f"\n{'=' * 70}")

if __name__ == '__main__':
    list_translations()
