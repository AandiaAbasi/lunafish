"""
خدمات (Services) برای پکیج و قسط‌بندی

توابع کمکی برای:
- بررسی دسترسی دانش‌آموز به جلسات
- مدیریت پرداخت اقساط
- محاسبات و گزارش‌های مربوط به قسط‌بندی
"""

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from decimal import Decimal
from typing import Tuple, Optional, List, Dict

from .models import (
    Package,
    PackageInstallment,
    StudentPackageEnrollment,
    StudentPackagePayment,
)


class PackageInstallmentService:
    """خدمات مربوط به قسط‌بندی پکیج"""
    
    @staticmethod
    def can_student_attend_session(
        enrollment: StudentPackageEnrollment,
        session_number: int
    ) -> Tuple[bool, str]:
        """
        بررسی آیا دانش‌آموز می‌تواند در یک جلسه شرکت کند
        
        شرط: تمام اقساطی که برای جلسه‌های قبل از این تعریف شده‌اند
              باید پرداخت شده باشند
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
            session_number: شماره جلسه
        
        Returns:
            Tuple[bool, str]: (آیا مجاز است، پیام)
        
        مثال:
            >>> enrollment = StudentPackageEnrollment.objects.get(id=1)
            >>> can_attend, message = PackageInstallmentService.can_student_attend_session(enrollment, 5)
            >>> if can_attend:
            ...     print("دانش‌آموز می‌تواند وارد شود")
            ... else:
            ...     print(message)  # "قسط برای جلسه 3 پرداخت نشده است"
        """
        
        # بررسی وضعیت ثبت‌نام
        if enrollment.status != 'active':
            return False, _(f"وضعیت ثبت‌نام '{enrollment.get_status_display()}' است")
        
        # بررسی شماره جلسه
        if session_number > enrollment.package.total_sessions:
            return False, _("شماره جلسه معتبر نیست")
        
        if session_number < 1:
            return False, _("شماره جلسه باید حداقل ۱ باشد")
        
        # پیدا کردن آخرین قسطی که باید قبل از این جلسه پرداخت شده باشد
        required_installment = enrollment.package.installments.filter(
            session_number__lte=session_number
        ).last()
        
        # اگر هیچ قسطی برای این جلسه تعریف نشده
        if not required_installment:
            return True, _("دسترسی مجاز است")
        
        # بررسی پرداخت این قسط
        payment = enrollment.installment_payments.filter(
            installment=required_installment
        ).first()
        
        if not payment:
            return False, _("رکورد پرداخت یافت نشد")
        
        if payment.payment_status != 'paid':
            return False, _(
                f"قسط {required_installment.installment_number} "
                f"برای جلسه {required_installment.session_number} "
                f"پرداخت نشده است"
            )
        
        return True, _("دسترسی مجاز است")
    
    @staticmethod
    def get_next_due_installment(
        enrollment: StudentPackageEnrollment
    ) -> Optional[Tuple[PackageInstallment, StudentPackagePayment]]:
        """
        دریافت اولین قسط پرداخت‌نشده
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
        
        Returns:
            Optional[Tuple]: (قسط، رکورد پرداخت) یا None
        """
        payment = enrollment.installment_payments.filter(
            payment_status__in=['pending', 'partial']
        ).order_by('installment__installment_number').first()
        
        if payment:
            return payment.installment, payment
        
        return None
    
    @staticmethod
    def get_enrollment_payment_summary(
        enrollment: StudentPackageEnrollment
    ) -> Dict:
        """
        دریافت خلاصه پرداخت اقساط یک ثبت‌نام
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
        
        Returns:
            Dict: شامل اطلاعات کل، پرداخت‌شده، باقی‌مانده و غیره
        
        مثال:
            >>> summary = PackageInstallmentService.get_enrollment_payment_summary(enrollment)
            >>> print(f"کل: {summary['total_amount']}")
            >>> print(f"پرداخت‌شده: {summary['paid_amount']}")
            >>> print(f"باقی‌مانده: {summary['remaining_amount']}")
        """
        payments = enrollment.installment_payments.all()
        
        total_amount = sum(p.amount_due for p in payments)
        paid_amount = sum(p.amount_paid for p in payments)
        remaining_amount = total_amount - paid_amount
        
        paid_count = payments.filter(payment_status='paid').count()
        pending_count = payments.filter(payment_status__in=['pending', 'partial']).count()
        
        return {
            'total_amount': Decimal(str(total_amount)),
            'paid_amount': Decimal(str(paid_amount)),
            'remaining_amount': Decimal(str(remaining_amount)),
            'total_installments': payments.count(),
            'paid_installments': paid_count,
            'pending_installments': pending_count,
            'completion_percentage': (
                (paid_count / payments.count() * 100) if payments.count() > 0 else 0
            ),
        }
    
    @staticmethod
    def process_installment_payment(
        enrollment: StudentPackageEnrollment,
        installment_id: int,
        amount_paid: Decimal,
        payment_ref: str = ""
    ) -> Tuple[bool, str, Optional[StudentPackagePayment]]:
        """
        ثبت پرداخت برای یک قسط
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
            installment_id: شناسه قسط
            amount_paid: مبلغ پرداخت‌شده
            payment_ref: شناسه تراکنش درگاه پرداخت
        
        Returns:
            Tuple[bool, str, Optional]: (موفق یا نه، پیام، رکورد پرداخت)
        
        مثال:
            >>> success, msg, payment = PackageInstallmentService.process_installment_payment(
            ...     enrollment, 1, Decimal('200000'), 'ref123'
            ... )
            >>> if success:
            ...     print("پرداخت ثبت شد")
        """
        try:
            payment = enrollment.installment_payments.get(
                installment_id=installment_id
            )
        except StudentPackagePayment.DoesNotExist:
            return False, _("رکورد پرداخت یافت نشد"), None
        
        # بررسی مبلغ
        if amount_paid <= 0:
            return False, _("مبلغ باید بیشتر از صفر باشد"), None
        
        # افزودن به مبلغ پرداخت‌شده
        payment.amount_paid = min(
            payment.amount_paid + amount_paid,
            payment.amount_due
        )
        payment.payment_ref = payment_ref
        payment.last_payment_date = payment.last_payment_date or __import__('django.utils.timezone', fromlist=['now']).now()
        
        if payment.first_payment_date is None:
            payment.first_payment_date = __import__('django.utils.timezone', fromlist=['now']).now()
        
        payment.save()
        
        return True, _("پرداخت با موفقیت ثبت شد"), payment
    
    @staticmethod
    def get_all_unpaid_installments(
        enrollment: StudentPackageEnrollment
    ) -> List[Tuple[PackageInstallment, StudentPackagePayment]]:
        """
        دریافت تمام اقساط پرداخت‌نشده
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
        
        Returns:
            List: لیست اقساط و رکوردهای پرداخت آن‌ها
        """
        unpaid_payments = enrollment.installment_payments.filter(
            payment_status__in=['pending', 'partial']
        ).order_by('installment__installment_number')
        
        return [(p.installment, p) for p in unpaid_payments]
    
    @staticmethod
    def get_installments_by_status(
        enrollment: StudentPackageEnrollment,
        status: str
    ) -> List[StudentPackagePayment]:
        """
        دریافت اقساط بر اساس وضعیت
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
            status: وضعیت ('paid', 'pending', 'partial', 'failed', 'refunded')
        
        Returns:
            List: لیست رکوردهای پرداخت
        """
        return enrollment.installment_payments.filter(
            payment_status=status
        ).order_by('installment__installment_number')


class PackageService:
    """خدمات مربوط به مدیریت پکیج"""
    
    @staticmethod
    def create_package_with_installments(
        teacher,
        title: str,
        total_sessions: int,
        total_price: Decimal,
        installments_data: List[Dict],
        **kwargs
    ) -> Tuple[bool, str, Optional[Package]]:
        """
        ایجاد پکیج به همراه اقساط
        
        Args:
            teacher: معلم
            title: نام پکیج
            total_sessions: تعداد جلسات
            total_price: قیمت کل
            installments_data: لیست دیکشنری‌های قسط
                [{
                    'installment_number': 1,
                    'amount': 200000,
                    'session_number': 1,
                    'description': 'قسط اول'
                }, ...]
            **kwargs: دیگر فیلدهای Package
        
        Returns:
            Tuple[bool, str, Optional]: (موفق یا نه، پیام، Package)
        
        مثال:
            >>> installments = [
            ...     {'installment_number': 1, 'amount': 200000, 'session_number': 1},
            ...     {'installment_number': 2, 'amount': 200000, 'session_number': 10},
            ... ]
            >>> success, msg, pkg = PackageService.create_package_with_installments(
            ...     teacher, 'انگلیسی', 20, 400000, installments
            ... )
        """
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # ایجاد پکیج
                package = Package.objects.create(
                    teacher=teacher,
                    title=title,
                    total_sessions=total_sessions,
                    total_price=total_price,
                    **kwargs
                )
                
                # ایجاد اقساط
                for inst_data in installments_data:
                    PackageInstallment.objects.create(
                        package=package,
                        **inst_data
                    )
                
                package.has_installment = True
                package.save(skip_create_default_installment=True)
                
                return True, _("پکیج با موفقیت ایجاد شد"), package
        
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_installment_total(package: Package) -> Tuple[bool, str]:
        """
        بررسی اینکه مجموع اقساط برابر قیمت کل باشد
        
        Args:
            package: پکیج
        
        Returns:
            Tuple[bool, str]: (معتبر یا نه، پیام)
        """
        total_installments = sum(
            inst.amount for inst in package.installments.all()
        )
        
        if total_installments != package.total_price:
            return False, _(
                f"مجموع اقساط ({total_installments:,}) "
                f"برابر قیمت کل ({package.total_price:,}) نیست"
            )
        
        return True, _("مجموع اقساط صحیح است")
