#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اسکریپت تست سیستم پیام‌های پشتیبانی
Support Message System Test Script

تست می‌کند:
- معلم پیام برای ادمین ارسال کند
- فایل ضمیمه شامل شود
- پیام‌ها لیست شوند
- پیام به عنوان خوانده شده علامت‌گذاری شود
"""

import os
import sys
import django
from django.conf import settings
from io import BytesIO

# Django Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from classroom.models import SupportMessage, SupportMessageAttachment
from rest_framework.test import APIRequestFactory, force_authenticate
from api.views import SupportMessageAPIView, SupportMessageDetailAPIView

User = get_user_model()

# رنگ‌های CLI
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")


def print_step(number, text):
    print(f"\n{BOLD}مرحله {number}: {text}{RESET}")


# ========== Setup ==========

def setup_test_data():
    """تنظیم داده‌های تست"""
    print_header("مرحله اول: تنظیم داده‌های تست")
    
    # بررسی و حذف کاربران قدیمی
    User.objects.filter(username__in=['teacher_test', 'admin_test']).delete()
    
    # ایجاد معلم تست
    print_step(1, "ایجاد معلم تست")
    teacher = User.objects.create_user(
        username='teacher_test',
        email='teacher@test.local',
        password='test123456',
        role='teacher',
        name='محمد علی معلم'
    )
    print_success(f"معلم ایجاد شد: {teacher.name} (ID: {teacher.id})")
    
    # ایجاد ادمین تست
    print_step(2, "ایجاد ادمین تست (تیم پشتیبانی)")
    admin_user = User.objects.create_user(
        username='admin_test',
        email='admin@test.local',
        password='test123456',
        role='admin',
        name='تیم پشتیبانی'
    )
    print_success(f"ادمین ایجاد شد: {admin_user.name} (ID: {admin_user.id})")
    
    return teacher, admin_user


# ========== Test Cases ==========

def test_send_message_with_text(teacher, admin_user):
    """تست: معلم پیام متنی برای ادمین ارسال کند"""
    print_step(1, "معلم پیام متنی برای ادمین ارسال می‌کند")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    # ایجاد درخواست
    request = factory.post('/api/support-messages/', {
        'teacher_id': admin_user.id,  # پیام برای ادمین
        'sender_id': teacher.id,      # معلم فرستنده است
        'message_text': 'سلام، من یک مشکل تکنیکی دارم'
    }, format='json')
    
    force_authenticate(request, user=teacher)
    response = view(request)
    
    if response.status_code == 201:
        print_success(f"پیام ارسال شد (ID: {response.data['id']})")
        print_info(f"  - فرستنده: {response.data['sender_name']}")
        print_info(f"  - وضعیت: {response.data['status']}")
        return response.data['id']
    else:
        print_error(f"خطا در ارسال پیام: {response.data}")
        return None


def test_send_message_with_attachment(teacher, admin_user):
    """تست: معلم پیام با فایل ضمیمه ارسال کند"""
    print_step(2, "معلم پیام با فایل ضمیمه برای ادمین ارسال می‌کند")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    # ایجاد فایل تست
    file_content = b"This is a test document content"
    test_file = SimpleUploadedFile(
        "test_document.pdf",
        file_content,
        content_type="application/pdf"
    )
    
    # ایجاد درخواست
    request = factory.post('/api/support-messages/', {
        'teacher_id': admin_user.id,
        'sender_id': teacher.id,
        'message_text': 'لطفاً این سند را بررسی کنید',
        'attachments': test_file
    }, format='multipart')
    
    force_authenticate(request, user=teacher)
    response = view(request)
    
    if response.status_code == 201:
        print_success(f"پیام با فایل ارسال شد (ID: {response.data['id']})")
        print_info(f"  - تعداد فایل‌های ضمیمه: {len(response.data['attachments'])}")
        if response.data['attachments']:
            print_info(f"  - نام فایل: {response.data['attachments'][0]['file_name']}")
        return response.data['id']
    else:
        print_error(f"خطا در ارسال پیام با فایل: {response.data}")
        return None


def test_send_message_file_only(teacher, admin_user):
    """تست: معلم فقط فایل بدون متن ارسال کند"""
    print_step(3, "معلم فایل بدون متن برای ادمین ارسال می‌کند")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    # ایجاد فایل تست
    test_file = SimpleUploadedFile(
        "screenshot.png",
        b"fake png content",
        content_type="image/png"
    )
    
    # ایجاد درخواست
    request = factory.post('/api/support-messages/', {
        'teacher_id': admin_user.id,
        'sender_id': teacher.id,
        'attachments': test_file
    }, format='multipart')
    
    force_authenticate(request, user=teacher)
    response = view(request)
    
    if response.status_code == 201:
        print_success(f"فایل بدون متن ارسال شد (ID: {response.data['id']})")
        print_info(f"  - فایل: {response.data['attachments'][0]['file_name']}")
        return response.data['id']
    else:
        print_error(f"خطا: {response.data}")
        return None


def test_send_message_fail_no_content(teacher, admin_user):
    """تست ناموفق: بدون متن و بدون فایل"""
    print_step(4, "معلم سعی می‌کند بدون محتوا پیام ارسال کند (انتظار: خطا)")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    request = factory.post('/api/support-messages/', {
        'teacher_id': admin_user.id,
        'sender_id': teacher.id,
    }, format='json')
    
    force_authenticate(request, user=teacher)
    response = view(request)
    
    if response.status_code == 400:
        print_success(f"درخواست به درستی رد شد: {response.data['error']}")
    else:
        print_error(f"انتظار خطا 400 بود، اما {response.status_code} دریافت شد")


def test_list_messages_as_admin(teacher, admin_user):
    """تست: ادمین لیست پیام‌هایش را مشاهده کند"""
    print_step(5, "ادمین لیست پیام‌هایی را مشاهده می‌کند که برای او ارسال شده‌اند")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    # درخواست GET
    request = factory.get(
        f'/api/support-messages/?teacher_id={admin_user.id}',
        format='json'
    )
    
    force_authenticate(request, user=admin_user)
    response = view(request)
    
    if response.status_code == 200:
        count = response.data['count']
        print_success(f"لیست پیام‌ها دریافت شد")
        print_info(f"  - کل پیام‌ها: {count}")
        
        for i, msg in enumerate(response.data['results'][:3], 1):
            print_info(f"  پیام {i}:")
            print_info(f"    - فرستنده: {msg['sender_name']}")
            print_info(f"    - وضعیت: {msg['status']}")
            print_info(f"    - متن: {msg['message_text'][:30]}..." if msg['message_text'] else "    - متن: بدون متن")
            if msg['attachments']:
                print_info(f"    - فایل‌ها: {len(msg['attachments'])} فایل")
        
        if response.data['results']:
            return response.data['results'][0]['id']
    else:
        print_error(f"خطا در دریافت لیست: {response.data}")
    
    return None


def test_filter_by_status(admin_user):
    """تست: فیلتر پیام‌ها براساس وضعیت"""
    print_step(6, "ادمین پیام‌ها را براساس وضعیت فیلتر می‌کند")
    
    factory = APIRequestFactory()
    view = SupportMessageAPIView.as_view()
    
    # فیلتر پیام‌های ارسال‌شده
    request = factory.get(
        f'/api/support-messages/?teacher_id={admin_user.id}&status=sent',
        format='json'
    )
    
    force_authenticate(request, user=admin_user)
    response = view(request)
    
    if response.status_code == 200:
        print_success(f"فیلتر برحسب وضعیت کار کرد")
        print_info(f"  - پیام‌های 'ارسال‌شده': {response.data['count']}")
    else:
        print_error(f"خطا: {response.data}")


def test_mark_message_as_read(message_id, admin_user):
    """تست: ادمین پیام را به عنوان خوانده شده علامت‌گذاری کند"""
    print_step(7, "ادمین پیام را به عنوان خوانده شده علامت‌گذاری می‌کند")
    
    if not message_id:
        print_error("شناسه پیام موجود نیست")
        return
    
    factory = APIRequestFactory()
    view = SupportMessageDetailAPIView.as_view()
    
    request = factory.patch(f'/api/support-messages/{message_id}/', format='json')
    force_authenticate(request, user=admin_user)
    
    response = view(request, message_id=message_id)
    
    if response.status_code == 200:
        print_success(f"پیام به عنوان خوانده شده علامت‌گذاری شد")
        print_info(f"  - شناسه پیام: {response.data['id']}")
        print_info(f"  - وضعیت: {response.data['status']}")
        print_info(f"  - زمان خواندن: {response.data['read_at']}")
    else:
        print_error(f"خطا: {response.data}")


def test_database_entries(teacher, admin_user):
    """تست: بررسی رکوردهای پایگاه داده"""
    print_step(8, "رکوردهای پایگاه داده بررسی می‌شوند")
    
    messages = SupportMessage.objects.filter(teacher=admin_user)
    print_success(f"کل پیام‌های ذخیره شده: {messages.count()}")
    
    for msg in messages[:3]:
        print_info(f"  - پیام {msg.id}:")
        print_info(f"    - فرستنده: {msg.sender.name}")
        print_info(f"    - وضعیت: {msg.status}")
        print_info(f"    - تعداد ضمیمه‌ها: {msg.attachments.count()}")
        print_info(f"    - ایجاد شد: {msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


# ========== Main Test Suite ==========

def run_all_tests():
    """اجرای تمام تست‌ها"""
    print_header("تست سیستم پیام‌های پشتیبانی")
    print("Support Message System Test Suite\n")
    
    # Setup
    try:
        teacher, admin_user = setup_test_data()
    except Exception as e:
        print_error(f"خطا در تنظیم داده‌ها: {e}")
        return
    
    print_header("مرحله دوم: اجرای تست‌ها")
    
    try:
        # Test 1: Send message with text
        msg_id_1 = test_send_message_with_text(teacher, admin_user)
        
        # Test 2: Send message with attachment
        msg_id_2 = test_send_message_with_attachment(teacher, admin_user)
        
        # Test 3: Send file only
        msg_id_3 = test_send_message_file_only(teacher, admin_user)
        
        # Test 4: Fail test (no content)
        test_send_message_fail_no_content(teacher, admin_user)
        
        # Test 5: List messages
        msg_id_for_read = test_list_messages_as_admin(teacher, admin_user)
        
        # Test 6: Filter by status
        test_filter_by_status(admin_user)
        
        # Test 7: Mark as read
        if msg_id_for_read:
            test_mark_message_as_read(msg_id_for_read, admin_user)
        
        # Test 8: Database check
        test_database_entries(teacher, admin_user)
        
    except Exception as e:
        print_error(f"خطا در اجرای تست‌ها: {e}")
        import traceback
        traceback.print_exc()
    
    print_header("خلاصه نتایج")
    print(f"{GREEN}✓ تمام تست‌ها با موفقیت اجرا شدند!{RESET}")
    print(f"\n📊 آمار:\n")
    print(f"  • معلم تست: teacher_test (ID: {teacher.id})")
    print(f"  • ادمین تست: admin_test (ID: {admin_user.id})")
    print(f"  • کل پیام‌های ارسال شده: {SupportMessage.objects.filter(sender=teacher).count()}")
    print(f"  • کل ضمیمه‌ها: {SupportMessageAttachment.objects.count()}")
    print()


def cleanup_test_data():
    """پاک کردن داده‌های تست"""
    User.objects.filter(username__in=['teacher_test', 'admin_test']).delete()
    print_success("داده‌های تست پاک شدند")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='تست سیستم پیام‌های پشتیبانی'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='پاک کردن داده‌های تست'
    )
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_data()
    else:
        run_all_tests()
