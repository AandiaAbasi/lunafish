#!/usr/bin/env python
"""Simple message compiler that doesn't require Django setup"""
import os
import polib
from pathlib import Path

locale_path = Path(__file__).parent / 'locale'

def compile_messages():
    """Compile .po files to .mo files"""
    compiled_count = 0
    
    for po_file in locale_path.glob('*/LC_MESSAGES/*.po'):
        print(f"Compiling {po_file}...")
        
        # Load the .po file
        po = polib.pofile(str(po_file))
        
        # Save as .mo file
        mo_file = po_file.with_suffix('.mo')
        po.save_as_mofile(str(mo_file))
        
        print(f"✅ Generated {mo_file}")
        compiled_count += 1
    
    if compiled_count > 0:
        print(f"\n✅ Successfully compiled {compiled_count} message file(s)!")
    else:
        print("❌ No .po files found!")

if __name__ == '__main__':
    compile_messages()
