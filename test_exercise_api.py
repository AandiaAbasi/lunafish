#!/usr/bin/env python
"""
سیستم تست API های سیستم آزمون
تست کردن ایجاد سوال، ایجاد آزمون، و جمع‌بندی نتایج
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from exercise.models import Field, FieldDetail, CategoryField, Order
from classroom.models import TeachingSubject

User = get_user_model()

# رنگ‌های خروجی
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
END = '\033[0m'

def print_test(msg):
    print(f"{BLUE}▶ {msg}{END}")

def print_ok(msg):
    print(f"{GREEN}✓ {msg}{END}")

def print_err(msg):
    print(f"{RED}✗ {msg}{END}")

def print_info(msg):
    print(f"{YELLOW}ℹ {msg}{END}")

def create_user(username, email, role='teacher'):
    """ایجاد کاربر تست"""
    User.objects.filter(username=username).delete()
    user = User.objects.create_user(
        username=username,
        email=email,
        phone=f"0910{username[-6:]}",
        password='Test123456!',
        role=role,
        is_active=True
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)

def test_1_create_question():
    """تست 1: ایجاد سوال"""
    print(f"\n{BOLD}═══ تست 1: ایجاد سوال ═══{END}")
    
    teacher, token = create_user('teacher1', 'teacher@test.com', 'teacher')
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # سوال تایپی
    print_test("ایجاد سوال تایپی...")
    data = {
        "title": "فرمول شیمیایی آب چیست؟",
        "type": "input",
        "correct_answer": "H2O",
        "is_required": 1,
        "guide": "فرمول شیمیایی را بنویسید"
    }
    
    response = client.post('/api/exercise/field/create/', data, format='json')
    if response.status_code == 201:
        field = response.json()['data']
        print_ok(f"سوال تایپی ایجاد شد (ID: {field['id']})")
        if field.get('correct_answer') == 'H2O':
            print_ok(f"correct_answer به درستی ذخیره شد: {field['correct_answer']}")
        else:
            print_err(f"correct_answer نادرست: {field.get('correct_answer')}")
    else:
        print_err(f"خرابی: {response.status_code}")
        print_info(response.json())
        return False
    
    # سوال چند گزینه‌ای
    print_test("ایجاد سوال چند گزینه‌ای...")
    data = {
        "title": "پایتخت فرانسه کدام است؟",
        "type": "radioButton",
        "correct_answer": "پاریس",
        "details": [
            {"title": "لندن", "is_correct": 0},
            {"title": "پاریس", "is_correct": 1},
            {"title": "برلین", "is_correct": 0}
        ]
    }
    
    response = client.post('/api/exercise/field/create/', data, format='json')
    if response.status_code == 201:
        field2 = response.json()['data']
        print_ok(f"سوال چند گزینه‌ای ایجاد شد (ID: {field2['id']})")
    else:
        print_err(f"خرابی: {response.status_code}")
        return False
    
    return {'field1': field['id'], 'field2': field2['id'], 'teacher': teacher, 'token': token}

def test_2_create_exam(data1):
    """تست 2: ایجاد آزمون"""
    print(f"\n{BOLD}═══ تست 2: ایجاد آزمون ═══{END}")
    
    teacher = data1['teacher']
    token = data1['token']
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # ایجاد درس
    TeachingSubject.objects.filter(teacher=teacher).delete()
    subject = TeachingSubject.objects.create(
        teacher=teacher,
        title="کلاس ریاضی تست"
    )
    
    print_test("اضافه کردن سوالات به آزمون...")
    data = {
        "teachingsubject_id": subject.id,
        "questions": [
            {"field_id": data1['field1'], "step": 0, "sort": 0, "type": "input"},
            {"field_id": data1['field2'], "step": 0, "sort": 1, "type": "radioButton"}
        ]
    }
    
    response = client.post('/api/exercise/exam/create/', data, format='json')
    if response.status_code == 201:
        exam_response = response.json()
        # Response دارای 'data' key است
        exam = exam_response.get('data', exam_response)
        print_ok(f"آزمون ایجاد شد با {len(exam.get('questions', []))} سوال")
        return {'subject': subject, 'token': token, 'teacher': teacher}
    else:
        print_err(f"خرابی: {response.status_code}")
        print_info(response.json())
        return False

def test_3_get_exam(data2):
    """تست 3: دریافت آزمون"""
    print(f"\n{BOLD}═══ تست 3: دریافت آزمون ═══{END}")
    
    subject = data2['subject']
    student, student_token = create_user('student1', 'student@test.com', 'user')
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token}')
    
    print_test("دریافت جزئیات آزمون...")
    response = client.get(f'/api/exercise/exam/{subject.id}/', format='json')
    
    if response.status_code == 200:
        # Response مستقیماً شی است، نه dict با 'data' key
        exam = response.json()
        print_ok(f"آزمون دریافت شد: {len(exam.get('questions', []))} سوال")
        
        for i, q in enumerate(exam.get('questions', []), 1):
            ans = q.get('correct_answer')
            if ans:
                print_ok(f"سوال {i}: پاسخ صحیح = '{ans}'")
            else:
                print_info(f"سوال {i}: بدون پاسخ صحیح")
        
        return {'subject': subject, 'student': student, 'student_token': student_token, 'exam': exam}
    else:
        print_err(f"خرابی: {response.status_code}")
        print_info(response.json())
        return False

def test_4_submit_exam(data3):
    """تست 4: ارسال پاسخ‌ها"""
    print(f"\n{BOLD}═══ تست 4: ارسال پاسخ‌ها ═══{END}")
    
    subject = data3['subject']
    student_token = data3['student_token']
    exam = data3['exam']
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token}')
    
    print_test("ارسال پاسخ‌های صحیح...")
    
    answers = []
    for question in exam.get('questions', []):
        field_id = question['id']
        field_type = question['type']
        
        if field_type == 'input':
            # پاسخ تایپی: پاسخ صحیح
            answers.append({
                'field_id': field_id,
                'value': 'H2O'
            })
        else:
            # انتخاب اول (باید صحیح باشد)
            first_option = question.get('details', [])[0] if question.get('details') else None
            if first_option:
                answers.append({
                    'field_id': field_id,
                    'field_detail_id': first_option['id']
                })
    
    data = {
        "teachingsubject_id": subject.id,
        "answers": answers
    }
    
    response = client.post(f'/api/exercise/exam/{subject.id}/submit/', data, format='json')
    
    if response.status_code == 201:
        result = response.json()['data']
        print_ok(f"پاسخ‌ها ارسال شدند")
        print_info(f"امتیاز: {result['score']} | صحیح: {result['correct']} | غلط: {result['incorrect']}")
        return {'attempt_id': result['id'], 'student_token': student_token, 'subject': subject}
    else:
        print_err(f"خرابی: {response.status_code}")
        print_info(response.json())
        return False

def test_5_get_results(data4):
    """تست 5: دریافت نتایج"""
    print(f"\n{BOLD}═══ تست 5: دریافت نتایج ═══{END}")
    
    student_token = data4['student_token']
    attempt_id = data4['attempt_id']
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token}')
    
    print_test("دریافت فهرست نتایج...")
    response = client.get('/api/exercise/results/', format='json')
    
    if response.status_code == 200:
        results = response.json().get('data', [])  # می‌تواند 'data' key داشته باشد یا نه
        if not results and isinstance(response.json(), list):
            results = response.json()
        print_ok(f"تعداد تلاش‌ها: {len(results)}")
    else:
        print_err(f"خرابی: {response.status_code}")
        return False
    
    print_test("دریافت جزئیات تلاش...")
    response = client.get(f'/api/exercise/results/{attempt_id}/', format='json')
    
    if response.status_code == 200:
        detail = response.json().get('data', response.json())
        print_ok(f"نتایج دریافت شدند")
        print_info(f"کل امتیاز: {detail.get('score', 0)}")
        
        for answer in detail.get('details', []):
            print_info(f"- {answer.get('field_title', 'سوال')}: {answer.get('score', 0)} امتیاز")
        
        return True
    else:
        print_err(f"خرابی: {response.status_code}")
        return False

def main():
    """اجرای تمام تست‌ها"""
    print(f"\n{BOLD}{BLUE}╔═══════════════════════════════════════╗{END}")
    print(f"{BOLD}{BLUE}║   تست جامع API های سیستم آزمون     ║{END}")
    print(f"{BOLD}{BLUE}╚═══════════════════════════════════════╝{END}")
    
    try:
        # تست 1
        data1 = test_1_create_question()
        if not data1:
            print_err("تست 1 ناموفق")
            return False
        
        # تست 2
        data2 = test_2_create_exam(data1)
        if not data2:
            print_err("تست 2 ناموفق")
            return False
        
        # تست 3
        data3 = test_3_get_exam(data2)
        if not data3:
            print_err("تست 3 ناموفق")
            return False
        
        # تست 4
        data4 = test_4_submit_exam(data3)
        if not data4:
            print_err("تست 4 ناموفق")
            return False
        
        # تست 5
        if not test_5_get_results(data4):
            print_err("تست 5 ناموفق")
            return False
        
        print(f"\n{BOLD}{GREEN}╔═══════════════════════════════════════╗{END}")
        print(f"{BOLD}{GREEN}║      ✓ تمام تست‌ها موفق بود!       ║{END}")
        print(f"{BOLD}{GREEN}╚═══════════════════════════════════════╝{END}\n")
        return True
        
    except Exception as e:
        print_err(f"خرابی: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)


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
