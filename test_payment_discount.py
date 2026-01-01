"""
Unit Tests for Payment & Discount System

تست‌های واحد برای سیستم پرداخت و تخفیف
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta
import json

User = get_user_model()

class PaymentDiscountTestCase(TestCase):
    """
    تست محاسبه مبلغ نهایی و درخواست پرداخت
    """
    
    def setUp(self):
        """آماده سازی برای تست"""
        self.client = Client()
        
        # ایجاد معلم
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='pass123',
            role='teacher',
            phone='09123456789'
        )
        
        # ایجاد دانش‌آموز
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='pass123',
            role='user',
            phone='09987654321'
        )
        
        # ورود دانش‌آموز
        self.client.login(username='student1', password='pass123')
        
    def _create_teaching_subject(self, title='English', price=100000):
        """ایجاد موضوع درسی"""
        from classroom.models import TeachingSubject
        return TeachingSubject.objects.create(
            teacher=self.teacher,
            title=title,
            description='Test course',
            price=Decimal(str(price))
        )
    
    def _create_availability(self, teacher, hours=1):
        """ایجاد فاصله زمانی معلم"""
        from classroom.models import TeacherAvailability
        return TeacherAvailability.objects.create(
            teacher=teacher,
            date=datetime.now().date() + timedelta(days=1),
            start_time='10:00',
            end_time='11:00',
            status='available'
        )
    
    def _create_booking(self, subject, student, teacher, availability, 
                       price, discount_amount=0):
        """ایجاد رزرو"""
        from classroom.models import ClassBooking
        return ClassBooking.objects.create(
            availability=availability,
            teacher=teacher,
            student=student,
            subject=subject,
            status='reserved',
            price=Decimal(str(price)),
            discount_amount=Decimal(str(discount_amount)),
            final_price=Decimal(str(price - discount_amount))
        )
    
    # ===== تست‌های محاسبه مبلغ نهایی =====
    
    def test_booking_without_discount(self):
        """
        تست: رزروی بدون تخفیف
        Expected: final_price = price
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=0
        )
        
        self.assertEqual(booking.final_price, Decimal('100000'))
        self.assertEqual(booking.discount_amount, Decimal('0'))
        print("✅ تست بدون تخفیف: موفق")
    
    def test_booking_with_discount(self):
        """
        تست: رزروی با تخفیف
        Expected: final_price = price - discount_amount
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=30000
        )
        
        self.assertEqual(booking.final_price, Decimal('70000'))
        self.assertEqual(booking.discount_amount, Decimal('30000'))
        print("✅ تست با تخفیف: موفق")
    
    def test_booking_fully_discounted(self):
        """
        تست: رزروی رایگان (تخفیف 100%)
        Expected: final_price = 0
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=100000
        )
        
        self.assertEqual(booking.final_price, Decimal('0'))
        self.assertEqual(booking.discount_amount, Decimal('100000'))
        print("✅ تست رایگان (تخفیف 100%): موفق")
    
    # ===== تست‌های API پرداخت =====
    
    def test_initiate_payment_with_discount(self):
        """
        تست: شروع پرداخت با تخفیف
        Expected: مبلغ نهایی (شامل تخفیف) به API برگردانده شود
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=30000
        )
        
        # فراخوانی API
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/',
            content_type='application/json'
        )
        
        # بررسی پاسخ
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['amount'], '70000')
        self.assertFalse(data['data'].get('is_free', False))
        self.assertIsNotNone(data['data']['payment_url'])
        
        print("✅ تست API پرداخت با تخفیف: موفق")
    
    def test_initiate_payment_free_booking(self):
        """
        تست: شروع پرداخت برای رزروی رایگان
        Expected: payment_url = None, is_free = True, status = paid
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        # رزروی رایگان (تخفیف 100%)
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=100000
        )
        
        # فراخوانی API
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/',
            content_type='application/json'
        )
        
        # بررسی پاسخ
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['amount'], '0')
        self.assertTrue(data['data']['is_free'])
        self.assertIsNone(data['data']['payment_url'])
        
        # بررسی اینکه payment_status = 'paid'
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, 'paid')
        self.assertEqual(booking.paid_amount, Decimal('0'))
        self.assertIsNotNone(booking.paid_at)
        
        print("✅ تست API پرداخت رایگان: موفق")
    
    def test_initiate_payment_without_discount(self):
        """
        تست: شروع پرداخت بدون تخفیف
        Expected: مبلغ اصلی به API برگردانده شود
        """
        subject = self._create_teaching_subject(price=100000)
        availability = self._create_availability(self.teacher)
        
        booking = self._create_booking(
            subject=subject,
            student=self.student,
            teacher=self.teacher,
            availability=availability,
            price=100000,
            discount_amount=0
        )
        
        # فراخوانی API
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/',
            content_type='application/json'
        )
        
        # بررسی پاسخ
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['amount'], '100000')
        self.assertFalse(data['data'].get('is_free', False))
        self.assertIsNotNone(data['data']['payment_url'])
        
        print("✅ تست API پرداخت بدون تخفیف: موفق")


class PaymentPermissionTestCase(TestCase):
    """
    تست‌های مجوز دسترسی برای پرداخت
    """
    
    def setUp(self):
        """آماده سازی برای تست"""
        self.client = Client()
        
        # ایجاد معلم
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='pass123',
            role='teacher'
        )
        
        # ایجاد دو دانش‌آموز
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='pass123',
            role='user'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='pass123',
            role='user'
        )
    
    def _create_teaching_subject(self):
        """ایجاد موضوع درسی"""
        from classroom.models import TeachingSubject
        return TeachingSubject.objects.create(
            teacher=self.teacher,
            title='English',
            price=Decimal('100000')
        )
    
    def _create_availability(self):
        """ایجاد فاصله زمانی معلم"""
        from classroom.models import TeacherAvailability
        return TeacherAvailability.objects.create(
            teacher=self.teacher,
            date=datetime.now().date() + timedelta(days=1),
            start_time='10:00',
            end_time='11:00'
        )
    
    def _create_booking(self, student, availability, subject):
        """ایجاد رزرو"""
        from classroom.models import ClassBooking
        return ClassBooking.objects.create(
            availability=availability,
            teacher=self.teacher,
            student=student,
            subject=subject,
            status='reserved',
            price=Decimal('100000'),
            discount_amount=Decimal('0'),
            final_price=Decimal('100000')
        )
    
    def test_student_can_pay_own_booking(self):
        """تست: دانش‌آموز می‌تواند برای رزروی خود پرداخت کند"""
        subject = self._create_teaching_subject()
        availability = self._create_availability()
        booking = self._create_booking(self.student1, availability, subject)
        
        self.client.login(username='student1', password='pass123')
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/'
        )
        
        self.assertEqual(response.status_code, 200)
        print("✅ دانش‌آموز می‌تواند برای رزروی خود پرداخت کند")
    
    def test_student_cannot_pay_other_booking(self):
        """تست: دانش‌آموز نمی‌تواند برای رزروی دیگری پرداخت کند"""
        subject = self._create_teaching_subject()
        availability = self._create_availability()
        booking = self._create_booking(self.student2, availability, subject)
        
        self.client.login(username='student1', password='pass123')
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/'
        )
        
        self.assertEqual(response.status_code, 403)
        print("✅ دانش‌آموز نمی‌تواند برای رزروی دیگری پرداخت کند")
    
    def test_teacher_cannot_pay(self):
        """تست: معلم نمی‌تواند برای کلاس‌های خود پرداخت کند"""
        subject = self._create_teaching_subject()
        availability = self._create_availability()
        booking = self._create_booking(self.student1, availability, subject)
        
        self.client.login(username='teacher1', password='pass123')
        response = self.client.post(
            f'/api/class-booking/{booking.id}/initiate-payment/'
        )
        
        self.assertEqual(response.status_code, 403)
        print("✅ معلم نمی‌تواند برای کلاس‌های خود پرداخت کند")


# ===== اجرای تست‌ها =====
if __name__ == '__main__':
    import unittest
    unittest.main()
