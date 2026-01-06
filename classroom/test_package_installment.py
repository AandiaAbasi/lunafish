"""
تست‌های واحد برای سیستم قسط‌بندی و دسترسی به جلسات

Test Cases:
1. ایجاد و اعتبارسنجی پکیج
2. ایجاد و اعتبارسنجی اقساط
3. ثبت‌نام دانش‌آموز و ایجاد رکوردهای پرداخت
4. پردازش پرداخت
5. بررسی دسترسی به جلسات
6. دریافت خلاصه پرداخت‌ها
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import (
    Package, PackageInstallment, StudentPackageEnrollment,
    StudentPackagePayment, TeachingSubject
)
from .services import PackageInstallmentService, PackageService

User = get_user_model()


class PackageModelTestCase(TestCase):
    """تست‌های مدل Package"""
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.teacher = User.objects.create(
            username='teacher_test',
            email='teacher@test.com',
            role='teacher'
        )
        
        self.subject = TeachingSubject.objects.create(
            teacher=self.teacher,
            title='English Basic',
            level='beginner'
        )
    
    def test_create_package(self):
        """تست ایجاد پکیج"""
        package = Package.objects.create(
            teacher=self.teacher,
            title='English 30 Sessions',
            total_sessions=30,
            total_price=Decimal('600000.00')
        )
        
        self.assertEqual(package.teacher, self.teacher)
        self.assertEqual(package.total_sessions, 30)
        self.assertEqual(package.total_price, Decimal('600000.00'))
        self.assertTrue(package.is_active)
    
    def test_package_clean_validation(self):
        """تست اعتبارسنجی Package"""
        package = Package(
            teacher=self.teacher,
            title='Invalid Package',
            total_sessions=0,  # غیر معتبر
            total_price=Decimal('600000.00')
        )
        
        with self.assertRaises(ValidationError):
            package.full_clean()
    
    def test_default_installment_creation(self):
        """تست ایجاد قسط پیش‌فرض"""
        package = Package.objects.create(
            teacher=self.teacher,
            title='English Package',
            total_sessions=10,
            total_price=Decimal('200000.00')
        )
        
        # بررسی ایجاد قسط پیش‌فرض
        self.assertTrue(package.has_installment)
        self.assertEqual(package.installments.count(), 1)
        
        default_inst = package.installments.first()
        self.assertEqual(default_inst.installment_number, 1)
        self.assertEqual(default_inst.amount, Decimal('200000.00'))
        self.assertEqual(default_inst.session_number, 1)


class PackageInstallmentTestCase(TestCase):
    """تست‌های مدل PackageInstallment"""
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.teacher = User.objects.create(
            username='teacher_test',
            email='teacher@test.com',
            role='teacher'
        )
        
        self.package = Package.objects.create(
            teacher=self.teacher,
            title='English Package',
            total_sessions=30,
            total_price=Decimal('600000.00')
        )
        # حذف قسط پیش‌فرض
        self.package.installments.all().delete()
    
    def test_create_installment(self):
        """تست ایجاد قسط"""
        installment = PackageInstallment.objects.create(
            package=self.package,
            installment_number=1,
            amount=Decimal('200000.00'),
            session_number=1
        )
        
        self.assertEqual(installment.package, self.package)
        self.assertEqual(installment.installment_number, 1)
        self.assertEqual(installment.amount, Decimal('200000.00'))
    
    def test_installment_validation_session_number(self):
        """تست اعتبارسنجی شماره جلسه"""
        installment = PackageInstallment(
            package=self.package,
            installment_number=1,
            amount=Decimal('200000.00'),
            session_number=50  # بیشتر از total_sessions
        )
        
        with self.assertRaises(ValidationError):
            installment.full_clean()
    
    def test_installment_unique_constraint(self):
        """تست قید unique برای شماره جلسه"""
        PackageInstallment.objects.create(
            package=self.package,
            installment_number=1,
            amount=Decimal('200000.00'),
            session_number=1
        )
        
        # سعی برای ایجاد قسط دوباره با شماره جلسه یکسان
        with self.assertRaises(Exception):
            PackageInstallment.objects.create(
                package=self.package,
                installment_number=2,
                amount=Decimal('200000.00'),
                session_number=1
            )


class StudentEnrollmentTestCase(TestCase):
    """تست‌های ثبت‌نام دانش‌آموز"""
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.teacher = User.objects.create(
            username='teacher_test',
            email='teacher@test.com',
            role='teacher'
        )
        
        self.student = User.objects.create(
            username='student_test',
            email='student@test.com',
            role='user'
        )
        
        self.package = Package.objects.create(
            teacher=self.teacher,
            title='English Package',
            total_sessions=30,
            total_price=Decimal('600000.00')
        )
    
    def test_create_enrollment(self):
        """تست ایجاد ثبت‌نام"""
        enrollment = StudentPackageEnrollment.objects.create(
            student=self.student,
            package=self.package
        )
        
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.package, self.package)
        self.assertEqual(enrollment.status, 'active')
    
    def test_payment_records_creation(self):
        """تست ایجاد رکوردهای پرداخت خودکار"""
        enrollment = StudentPackageEnrollment.objects.create(
            student=self.student,
            package=self.package
        )
        
        # بررسی ایجاد رکوردهای پرداخت
        payment_records = enrollment.installment_payments.all()
        self.assertEqual(
            payment_records.count(),
            self.package.installments.count()
        )
        
        # بررسی کیفیت رکوردهای پرداخت
        for payment in payment_records:
            self.assertEqual(payment.payment_status, 'pending')
            self.assertEqual(payment.amount_paid, Decimal('0.00'))


class PackageInstallmentServiceTestCase(TestCase):
    """تست‌های Service برای قسط‌بندی"""
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.teacher = User.objects.create(
            username='teacher_test',
            email='teacher@test.com',
            role='teacher'
        )
        
        self.student = User.objects.create(
            username='student_test',
            email='student@test.com',
            role='user'
        )
        
        # ایجاد پکیج با اقساط
        self.package = Package.objects.create(
            teacher=self.teacher,
            title='English Package',
            total_sessions=30,
            total_price=Decimal('600000.00')
        )
        
        # حذف قسط پیش‌فرض و ایجاد اقساط سفارشی
        self.package.installments.all().delete()
        
        self.inst1 = PackageInstallment.objects.create(
            package=self.package,
            installment_number=1,
            amount=Decimal('200000.00'),
            session_number=1
        )
        
        self.inst2 = PackageInstallment.objects.create(
            package=self.package,
            installment_number=2,
            amount=Decimal('200000.00'),
            session_number=10
        )
        
        self.inst3 = PackageInstallment.objects.create(
            package=self.package,
            installment_number=3,
            amount=Decimal('200000.00'),
            session_number=20
        )
        
        # ثبت‌نام دانش‌آموز
        self.enrollment = StudentPackageEnrollment.objects.create(
            student=self.student,
            package=self.package
        )
    
    def test_can_attend_session_without_payment(self):
        """تست دسترسی بدون پرداخت"""
        can_access, msg = PackageInstallmentService.can_student_attend_session(
            self.enrollment, 5
        )
        
        self.assertFalse(can_access)
        self.assertIn('پرداخت', msg)
    
    def test_can_attend_session_after_payment(self):
        """تست دسترسی بعد از پرداخت"""
        # پرداخت قسط اول
        payment = self.enrollment.installment_payments.get(
            installment=self.inst1
        )
        payment.amount_paid = Decimal('200000.00')
        payment.payment_status = 'paid'
        payment.save()
        
        # بررسی دسترسی
        can_access, msg = PackageInstallmentService.can_student_attend_session(
            self.enrollment, 5
        )
        
        self.assertTrue(can_access)
    
    def test_get_payment_summary(self):
        """تست دریافت خلاصه پرداخت"""
        summary = PackageInstallmentService.get_enrollment_payment_summary(
            self.enrollment
        )
        
        self.assertEqual(summary['total_amount'], Decimal('600000.00'))
        self.assertEqual(summary['paid_amount'], Decimal('0.00'))
        self.assertEqual(summary['remaining_amount'], Decimal('600000.00'))
        self.assertEqual(summary['total_installments'], 3)
        self.assertEqual(summary['paid_installments'], 0)
        self.assertEqual(summary['pending_installments'], 3)
    
    def test_process_payment(self):
        """تست پردازش پرداخت"""
        success, msg, payment = PackageInstallmentService.process_installment_payment(
            self.enrollment,
            self.inst1.id,
            Decimal('200000.00'),
            'ref_123'
        )
        
        self.assertTrue(success)
        self.assertEqual(payment.amount_paid, Decimal('200000.00'))
        self.assertEqual(payment.payment_status, 'paid')
        self.assertEqual(payment.payment_ref, 'ref_123')
    
    def test_get_next_due_installment(self):
        """تست دریافت قسط بعدی"""
        result = PackageInstallmentService.get_next_due_installment(
            self.enrollment
        )
        
        self.assertIsNotNone(result)
        installment, payment = result
        self.assertEqual(installment.installment_number, 1)
