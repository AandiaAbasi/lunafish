#!/usr/bin/env python
"""
Test script for Teacher List and Detail APIs
Tests the new /api/teachers/ and /api/teachers/<id>/ endpoints
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
django.setup()

User = get_user_model()
client = Client()

print("=" * 80)
print("TESTING TEACHER APIS")
print("=" * 80)

# Test 1: Check if API URLs are registered
print("\n[Test 1] Checking if API URLs are registered...")
try:
    from django.urls import reverse
    teacher_list_url = reverse('api:teacher_list')
    print(f"✓ Teacher List API URL: {teacher_list_url}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 2: Test Teacher List API without authentication
print("\n[Test 2] Testing Teacher List API (no auth required)...")
try:
    response = client.get('/api/teachers/')
    print(f"✓ Response Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - Found {data.get('count', 0)} teachers")
        if 'results' in data:
            print(f"  - First page has {len(data['results'])} teachers")
            if data['results']:
                teacher = data['results'][0]
                print(f"  - Teacher fields: {list(teacher.keys())}")
                required_fields = ['id', 'name', 'qualifications', 'languages_taught', 'hourly_rate', 'experience_years']
                missing = [f for f in required_fields if f not in teacher]
                if missing:
                    print(f"  ⚠ Missing fields: {missing}")
                else:
                    print(f"  ✓ All required fields present")
    else:
        print(f"  Response: {response.json()}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Test Teacher Detail API
print("\n[Test 3] Testing Teacher Detail API...")
try:
    # Try with a teacher ID (if teachers exist)
    teacher = User.objects.filter(role='teacher', is_teacher_verified=True).first()
    if teacher:
        response = client.get(f'/api/teachers/{teacher.id}/')
        print(f"✓ Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Teacher: {data.get('name', 'N/A')}")
            print(f"  - Experience: {data.get('experience_years', 0)} years")
            print(f"  - Hourly Rate: {data.get('hourly_rate', 'N/A')}")
            print(f"  - Teaching Subjects: {len(data.get('teaching_subjects', []))} subjects")
            print(f"  - Available Slots: {len(data.get('availability_slots', []))} slots")
            required_fields = ['id', 'name', 'qualifications', 'teaching_subjects', 'availability_slots']
            missing = [f for f in required_fields if f not in data]
            if missing:
                print(f"  ⚠ Missing fields: {missing}")
            else:
                print(f"  ✓ All required fields present")
        else:
            print(f"  Response: {response.json()}")
    else:
        print("  ⚠ No verified teachers in database - skipping detail test")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Test Teacher Detail API with invalid ID
print("\n[Test 4] Testing Teacher Detail API with invalid ID...")
try:
    response = client.get('/api/teachers/99999/')
    print(f"✓ Response Status: {response.status_code}")
    if response.status_code == 404:
        data = response.json()
        print(f"  - Error message: {data.get('error', 'N/A')}")
        print("  ✓ Correctly returns 404 for invalid teacher")
    else:
        print(f"  ⚠ Expected 404, got {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Check pagination
print("\n[Test 5] Testing pagination...")
try:
    response = client.get('/api/teachers/?page=1&page_size=5')
    print(f"✓ Response Status: {response.status_code}")
    data = response.json()
    if 'count' in data:
        print(f"  - Total teachers: {data['count']}")
        print(f"  - Page size: {len(data.get('results', []))}")
        print(f"  - Next page: {data.get('next') is not None}")
        print("  ✓ Pagination working")
    else:
        print("  ⚠ Pagination response format unexpected")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
