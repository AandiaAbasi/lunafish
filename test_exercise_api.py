#!/usr/bin/env python
"""
Exercise API - Test Cases
Quick test script to verify exercise API endpoints work correctly.
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEACHER_TOKEN = "YOUR_TEACHER_TOKEN_HERE"
STUDENT_TOKEN = "YOUR_STUDENT_TOKEN_HERE"

def test_create_question():
    """Test creating a question"""
    print("\n" + "="*60)
    print("TEST 1: Create Question")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/field/create/"
    
    data = {
        "title": "What is 2+2?",
        "type": "radioButton",
        "is_required": 1,
        "guide": "Choose the correct answer",
        "details": [
            {"title": "3", "is_correct": 0},
            {"title": "4", "is_correct": 1},
            {"title": "5", "is_correct": 0}
        ]
    }
    
    headers = {"Authorization": f"Bearer {TEACHER_TOKEN}"}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        question_id = response.json()['data']['id']
        print(f"✓ Question created with ID: {question_id}")
        return question_id
    else:
        print("✗ Failed to create question")
        return None


def test_create_exam(question_id):
    """Test creating an exam"""
    print("\n" + "="*60)
    print("TEST 2: Create Exam")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/exam/create/"
    
    data = {
        "teachingsubject_id": 5,  # Use actual subject ID
        "questions": [
            {
                "field_id": question_id,
                "step": 0,
                "sort": 0,
                "type": "radioButton"
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {TEACHER_TOKEN}"}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        exam_id = response.json()['data']['id']
        print(f"✓ Exam created for subject ID: {exam_id}")
        return exam_id
    else:
        print("✗ Failed to create exam")
        return None


def test_get_exam(subject_id):
    """Test retrieving exam"""
    print("\n" + "="*60)
    print("TEST 3: Get Exam")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/exam/{subject_id}/"
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Exam retrieved:")
        print(f"  - Subject: {data['subject_title']}")
        print(f"  - Total Questions: {data['total_questions']}")
        print(f"  Questions: {json.dumps(data['questions'], indent=2)}")
        return True
    else:
        print("✗ Failed to get exam")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return False


def test_submit_exam(subject_id, question_id):
    """Test submitting exam answers"""
    print("\n" + "="*60)
    print("TEST 4: Submit Exam")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/exam/{subject_id}/submit/"
    
    data = {
        "teachingsubject_id": subject_id,
        "answers": [
            {
                "field_id": question_id,
                "field_detail_id": 2  # The correct answer (4)
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()['data']
        print(f"✓ Exam submitted successfully:")
        print(f"  - Score: {result['score']}")
        print(f"  - Correct: {result['correct']}")
        print(f"  - Incorrect: {result['incorrect']}")
        print(f"  - Percentage: {result.get('percentage', 'N/A')}%")
        attempt_id = result['id']
        return attempt_id
    else:
        print("✗ Failed to submit exam")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return None


def test_get_results():
    """Test retrieving results list"""
    print("\n" + "="*60)
    print("TEST 5: Get Results List")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/results/"
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Results retrieved:")
        print(f"  - Total Attempts: {data.get('count', 0)}")
        print(f"  - Page: {data.get('page', 1)}")
        if data.get('results'):
            print(f"  - First Attempt: {data['results'][0]['subject_title']}")
        return True
    else:
        print("✗ Failed to get results")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return False


def test_get_attempt_details(attempt_id):
    """Test retrieving attempt details"""
    print("\n" + "="*60)
    print("TEST 6: Get Attempt Details")
    print("="*60)
    
    url = f"{API_BASE_URL}/exercise/results/{attempt_id}/"
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Attempt details retrieved:")
        print(f"  - Subject: {data['subject_title']}")
        print(f"  - Score: {data['score']}/{len(data.get('details', []))}")
        print(f"  - Details:")
        for detail in data.get('details', [])[:3]:
            print(f"    - {detail['field_title']}: {detail['score']} point(s)")
        return True
    else:
        print("✗ Failed to get attempt details")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "#"*60)
    print("# Exercise API Test Suite")
    print("#"*60)
    print(f"\nStarting tests at {datetime.now()}")
    
    # Test 1: Create Question
    question_id = test_create_question()
    if not question_id:
        print("\n✗ Cannot continue - question creation failed")
        return
    
    # Test 2: Create Exam
    subject_id = test_create_exam(question_id)
    if not subject_id:
        subject_id = 5  # Use default ID for testing
    
    # Test 3: Get Exam
    if not test_get_exam(subject_id):
        print("\n✗ Cannot continue - exam retrieval failed")
        return
    
    # Test 4: Submit Exam
    attempt_id = test_submit_exam(subject_id, question_id)
    if not attempt_id:
        print("\n✗ Cannot continue - exam submission failed")
        return
    
    # Test 5: Get Results
    test_get_results()
    
    # Test 6: Get Attempt Details
    test_get_attempt_details(attempt_id)
    
    print("\n" + "#"*60)
    print("# Tests Complete")
    print("#"*60)


if __name__ == "__main__":
    print("""
    Exercise API Test Suite
    ═══════════════════════════════════════════════════════════════
    
    Before running tests:
    1. Update TEACHER_TOKEN and STUDENT_TOKEN with real tokens
    2. Update subject IDs if different from defaults
    3. Make sure Django server is running on localhost:8000
    4. Ensure user is authenticated
    
    Run with: python test_exercise_api.py
    """)
    
    # Uncomment to run:
    # run_all_tests()
