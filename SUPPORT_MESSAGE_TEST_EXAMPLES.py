"""
نمونه‌های تست برای سیستم پیام‌های پشتیبانی
Support Message System Test Examples
"""

# Example 1: Creating a Support Message with Python requests
def test_create_support_message_with_text():
    """متن با پیام ارسال کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    data = {
        "teacher_id": 5,
        "sender_id": 5,
        "message_text": "درخواست برای حل مشکل تکنیکی"
    }
    
    response = requests.post(url, headers=headers, data=data)
    assert response.status_code == 201
    assert response.json()["status"] == "sent"
    print("✅ Test passed: Create message with text")


# Example 2: Creating a Support Message with File Attachment
def test_create_support_message_with_file():
    """فایل با پیام ارسال کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    with open("document.pdf", "rb") as f:
        files = {
            "attachments": f
        }
        data = {
            "teacher_id": 5,
            "sender_id": 5,
            "message_text": "سند ضمیمه است"
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        assert response.status_code == 201
        assert len(response.json()["attachments"]) > 0
        print("✅ Test passed: Create message with file")


# Example 3: Creating a Support Message with Multiple Files
def test_create_support_message_with_multiple_files():
    """چند فایل با پیام ارسال کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    files = [
        ("attachments", open("file1.pdf", "rb")),
        ("attachments", open("file2.jpg", "rb")),
    ]
    data = {
        "teacher_id": 5,
        "sender_id": 5,
        "message_text": "دو سند ضمیمه است"
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    assert response.status_code == 201
    assert len(response.json()["attachments"]) == 2
    print("✅ Test passed: Create message with multiple files")


# Example 4: Creating a Support Message with Only File (No Text)
def test_create_support_message_file_only():
    """فقط فایل بدون متن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    with open("screenshot.png", "rb") as f:
        files = {
            "attachments": f
        }
        data = {
            "teacher_id": 5,
            "sender_id": 5,
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        assert response.status_code == 201
        print("✅ Test passed: Create message with file only")


# Example 5: Fail Test - Neither Text nor File
def test_create_support_message_fail_no_content():
    """ناموفق: نه متن نه فایل"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    data = {
        "teacher_id": 5,
        "sender_id": 5,
    }
    
    response = requests.post(url, headers=headers, data=data)
    assert response.status_code == 400
    assert "Message text or attachment is required" in response.text
    print("✅ Test passed: Fail when no content provided")


# Example 6: Fail Test - Teacher Not Found
def test_create_support_message_fail_teacher_not_found():
    """ناموفق: معلم یافت نشد"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    data = {
        "teacher_id": 99999,  # غیر موجود
        "sender_id": 5,
        "message_text": "تست"
    }
    
    response = requests.post(url, headers=headers, data=data)
    assert response.status_code == 404
    assert "Teacher not found" in response.text
    print("✅ Test passed: Fail when teacher not found")


# Example 7: Get Messages List
def test_get_messages_list():
    """لیست پیام‌ها را دریافت کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    params = {"teacher_id": 5}
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    print(f"✅ Test passed: Get {data['count']} messages")


# Example 8: Filter Messages by Status
def test_filter_messages_by_status():
    """پیام‌ها را براساس وضعیت فیلتر کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    params = {"teacher_id": 5, "status": "sent"}
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200
    
    for message in response.json()["results"]:
        assert message["status"] == "sent"
    
    print("✅ Test passed: Filter by status works")


# Example 9: Pagination
def test_pagination():
    """صفحه‌بندی را تست کن"""
    import requests
    
    url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    # صفحه اول
    response = requests.get(url, headers=headers, params={"page": 1})
    assert response.status_code == 200
    data = response.json()
    
    if data["next"]:
        # صفحه دوم
        response = requests.get(url, headers=headers, params={"page": 2})
        assert response.status_code == 200
        assert response.json()["previous"] is not None
    
    print("✅ Test passed: Pagination works")


# Example 10: Mark Message as Read
def test_mark_message_as_read():
    """پیام را به عنوان خوانده شده علامت‌گذاری کن"""
    import requests
    
    # ابتدا یک پیام بسازید
    create_url = "http://localhost:8000/api/support-messages/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    data = {
        "teacher_id": 5,
        "sender_id": 5,
        "message_text": "تست"
    }
    response = requests.post(create_url, headers=headers, data=data)
    message_id = response.json()["id"]
    
    # سپس پیام را خوانده‌شده علامت‌گذاری کنید
    update_url = f"http://localhost:8000/api/support-messages/{message_id}/"
    response = requests.patch(update_url, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "read"
    assert response.json()["read_at"] is not None
    print("✅ Test passed: Mark as read works")


# ===== cURL Test Commands =====

"""
# Test 1: Create message with text
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "teacher_id=5&sender_id=5&message_text=تست"

# Test 2: Create message with file
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN" \
  -F "teacher_id=5" \
  -F "sender_id=5" \
  -F "message_text=فایل ضمیمه" \
  -F "attachments=@file.pdf"

# Test 3: Get messages list
curl http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN"

# Test 4: Get messages with filter
curl "http://localhost:8000/api/support-messages/?teacher_id=5&status=sent" \
  -H "Authorization: Bearer TOKEN"

# Test 5: Mark as read
curl -X PATCH http://localhost:8000/api/support-messages/1/ \
  -H "Authorization: Bearer TOKEN"

# Test 6: Fail test - no content
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN" \
  -d "teacher_id=5&sender_id=5"

# Test 7: Fail test - teacher not found
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN" \
  -d "teacher_id=99999&sender_id=5&message_text=تست"
"""


# ===== Django Test Cases (TestCase) =====

"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from classroom.models import SupportMessage, SupportMessageAttachment
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class SupportMessageAPITestCase(TestCase):
    
    def setUp(self):
        \"\"\"تنظیم اولیه برای تست‌ها\"\"\"
        self.client = APIClient()
        
        # ایجاد معلم
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='test123456',
            role='teacher',
            name='معلم یک'
        )
        
        # ایجاد Admin
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='test123456',
            role='admin',
            name='ادمین'
        )
        
        # دریافت توکن
        refresh = RefreshToken.for_user(self.teacher)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_create_message_with_text(self):
        \"\"\"تست ایجاد پیام با متن\"\"\"
        response = self.client.post('/api/support-messages/', {
            'teacher_id': self.teacher.id,
            'sender_id': self.teacher.id,
            'message_text': 'تست پیام'
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'sent')
    
    def test_create_message_without_content(self):
        \"\"\"تست ناموفق: بدون محتوا\"\"\"
        response = self.client.post('/api/support-messages/', {
            'teacher_id': self.teacher.id,
            'sender_id': self.teacher.id,
        })
        
        self.assertEqual(response.status_code, 400)
    
    def test_get_messages_list(self):
        \"\"\"تست دریافت لیست پیام‌ها\"\"\"
        # ایجاد چند پیام
        for i in range(5):
            SupportMessage.objects.create(
                teacher=self.teacher,
                sender=self.teacher,
                message_text=f'پیام {i}'
            )
        
        response = self.client.get('/api/support-messages/', {
            'teacher_id': self.teacher.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)
    
    def test_mark_as_read(self):
        \"\"\"تست علامت‌گذاری خوانده‌شده\"\"\"
        message = SupportMessage.objects.create(
            teacher=self.teacher,
            sender=self.teacher,
            message_text='پیام تست'
        )
        
        response = self.client.patch(f'/api/support-messages/{message.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'read')
        self.assertIsNotNone(response.data['read_at'])
"""


if __name__ == "__main__":
    print("Support Message System - Test Examples")
    print("=" * 50)
    print()
    print("برای اجرای تست‌ها:")
    print("1. کد را در یک فایل پایتون ذخیره کنید")
    print("2. توکن معتبر را جایگزین کنید")
    print("3. کد را اجرا کنید")
    print()
    print("To run tests:")
    print("1. Save code in a Python file")
    print("2. Replace with valid token")
    print("3. Run the code")
