"""
Test script for field creation API
Run this to test the field creation endpoint
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8000/api/exercise/field/create/"  # Change to your server URL
# API_URL = "https://fofofish.app/api/exercise/field/create/"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token

def test_input_type():
    """Test creating an input-type field"""
    print("\n" + "="*80)
    print("TEST 1: Input Type Field (with form array notation)")
    print("="*80)
    
    data = {
        'title': 'تست سوال تایپی',
        'type': 'input',
        'is_required': '1',
        'sort': '0',
        'guide': 'پاسخ را وارد کنید',
        'details[0][title]': 'سوال اول',
        'details[0][correct_answer]': 'پاسخ صحیح اول',
        'details[0][sort]': '0',
        'details[1][title]': 'سوال دوم',
        'details[1][correct_answer]': 'پاسخ صحیح دوم',
        'details[1][sort]': '1',
    }
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }
    
    print("\nSending data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    try:
        response = requests.post(API_URL, data=data, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 201:
            print("\n✅ SUCCESS: Field created successfully!")
        else:
            print("\n❌ FAILED: Field creation failed")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_checkbox_type():
    """Test creating a checkbox-type field"""
    print("\n" + "="*80)
    print("TEST 2: Checkbox Type Field")
    print("="*80)
    
    data = {
        'title': 'تست چند گزینه‌ای',
        'type': 'checkbox',
        'is_required': '1',
        'sort': '0',
        'details[0][title]': 'گزینه اول',
        'details[0][is_correct]': '1',
        'details[0][sort]': '0',
        'details[1][title]': 'گزینه دوم',
        'details[1][is_correct]': '0',
        'details[1][sort]': '1',
        'details[2][title]': 'گزینه سوم',
        'details[2][is_correct]': '1',
        'details[2][sort]': '2',
    }
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }
    
    print("\nSending data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    try:
        response = requests.post(API_URL, data=data, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 201:
            print("\n✅ SUCCESS: Field created successfully!")
        else:
            print("\n❌ FAILED: Field creation failed")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_with_file():
    """Test creating field with file upload"""
    print("\n" + "="*80)
    print("TEST 3: Input Type with File Upload")
    print("="*80)
    
    data = {
        'title': 'تست با فایل',
        'type': 'input',
        'is_required': '1',
        'sort': '0',
        'details[0][title]': 'سوال',
        'details[0][correct_answer]': 'پاسخ',
        'details[0][sort]': '0',
    }
    
    # Create a dummy text file for testing
    files = {
        'image_path': ('test.txt', b'test file content', 'text/plain'),
    }
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }
    
    print("\nSending data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    print(f"  image_path: test.txt (dummy file)")
    
    try:
        response = requests.post(API_URL, data=data, files=files, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 201:
            print("\n✅ SUCCESS: Field created successfully!")
        else:
            print("\n❌ FAILED: Field creation failed")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("FIELD CREATION API TEST SUITE")
    print("="*80)
    print(f"\nAPI URL: {API_URL}")
    print(f"Token: {TOKEN[:20]}..." if len(TOKEN) > 20 else f"Token: {TOKEN}")
    
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your JWT token in the script!")
        print("Edit the TOKEN variable at the top of this file.")
        exit(1)
    
    # Run tests
    test_input_type()
    test_checkbox_type()
    test_with_file()
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
