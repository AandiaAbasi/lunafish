#!/usr/bin/env python
"""
Script to create and run migrations for the new AvatarTemplate model
Run: python manage_avatars.py
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def run_migrations():
    """Create and apply migrations for AvatarTemplate"""
    try:
        print("🔄 Managing Avatar Templates...")
        print("=" * 60)
        
        os.chdir(BASE_DIR)
        
        # Step 1: Make migrations
        print("\n1️⃣  Creating migration files...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'makemigrations', 'account'],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print("⚠️  Migration creation had issues")
        
        # Step 2: Apply migrations
        print("\n2️⃣  Applying migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate', 'account'],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Migrations applied successfully!")
        else:
            print("\n⚠️  Issue applying migrations")
        
        print("\n" + "=" * 60)
        print("📋 Next steps:")
        print("   1. Restart Django server")
        print("   2. Visit admin: /admin/account/avatartemplate/")
        print("   3. Add avatar templates with images")
        print("   4. Users can select from: /api/avatars/")
        print("   5. Users can select avatar at: /api/select-avatar/")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
