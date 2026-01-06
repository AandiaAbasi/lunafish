"""
Package Installment Services - Business Logic for Package Payments
All logic for installment verification, session access control, and payment processing
"""

from decimal import Decimal
from typing import Tuple, Dict, Optional, List
from django.utils.translation import gettext_lazy as _
from classroom.models import Package, StudentPackageEnrollment, StudentPackagePayment


class PackageInstallmentService:
    """
    سرویس مدیریت قسط‌بندی و دسترسی به جلسات
    """
    
    @staticmethod
    def can_student_attend_session(
        enrollment: StudentPackageEnrollment,
        session_number: int
    ) -> Tuple[bool, str]:
        """
        بررسی آیا دانش‌آموز می‌تواند به یک جلسه دسترسی داشته باشد
        
        منطق:
        - پیدا کردن آخرین قسطی که برای جلسه ≤ session_number تعریف شده
        - اگر آن قسط پرداخت شده → دسترسی مجاز
        - اگر نه → دسترسی محدود
        
        Args:
            enrollment: ثبت‌نام دانش‌آموز
            session_number: شماره جلسه
            
        Returns:
            Tuple[bool, str]: (آیا دسترسی دارد، پیام)
        """
        # بررسی وضعیت ثبت‌نام
        if enrollment.status != 'active':
            return False, _(f"وضعیت ثبت‌نام: {enrollment.get_status_display()}")
        
        # بررسی اینکه جلسه معتبر است
        if session_number > enrollment.package.total_sessions or session_number < 1:
            return False, _("شماره جلسه معتبر نیست")
        
        # پیدا کردن آخرین قسطی که باید قبل از این جلسه پرداخت شود
        required_payment = enrollment.installment_payments.filter(
            installment__session_number__lte=session_number
        ).order_by('-installment__session_number').first()
        
        # اگر هیچ قسطی برای این جلسه تعریف نشده
        if not required_payment:
            return True, _("دسترسی مجاز است")
        
        # بررسی پرداخت
        if required_payment.payment_status != 'paid':
            return False, _(
                f"قسط {required_payment.installment.installment_number} "
                f"(جلسه {required_payment.installment.session_number}) پرداخت نشده"
            )
        
        return True, _("دسترسی مجاز است")
    
    @staticmethod
    def get_payment_summary(enrollment: StudentPackageEnrollment) -> Dict:
        """
        دریافت خلاصه وضعیت پرداخت اقساط
        
        Returns:
            Dict: شامل مبالغ، تعدادها و درصد تکمیل
        """
        payments = enrollment.installment_payments.all()
        
        if not payments.exists():
            return {
                'total_amount': Decimal('0'),
                'paid_amount': Decimal('0'),
                'remaining_amount': Decimal('0'),
                'total_installments': 0,
                'paid_installments': 0,
                'pending_installments': 0,
                'completion_percentage': 0,
            }
        
        total_amount = sum(p.installment.amount for p in payments)
        paid_amount = sum(p.amount_paid for p in payments if p.payment_status == 'paid')
        
        paid_count = payments.filter(payment_status='paid').count()
        total_count = payments.count()
        
        return {
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'remaining_amount': total_amount - paid_amount,
            'total_installments': total_count,
            'paid_installments': paid_count,
            'pending_installments': total_count - paid_count,
            'completion_percentage': (paid_count / total_count * 100) if total_count > 0 else 0,
        }
    
    @staticmethod
    def get_pending_installments(enrollment: StudentPackageEnrollment) -> List[Dict]:
        """
        دریافت لیست اقساط پرداخت‌نشده
        
        Returns:
            List: لیست اقساط با جزئیات
        """
        payments = enrollment.installment_payments.filter(
            payment_status__in=['pending', 'partial']
        ).order_by('installment__installment_number')
        
        return [
            {
                'id': p.id,
                'installment_id': p.installment.id,
                'installment_number': p.installment.installment_number,
                'session_number': p.installment.session_number,
                'amount_due': p.installment.amount,
                'amount_paid': p.amount_paid,
                'remaining_amount': p.installment.amount - p.amount_paid,
                'payment_status': p.payment_status,
            }
            for p in payments
        ]
    
    @staticmethod
    def get_next_due_installment(enrollment: StudentPackageEnrollment) -> Optional[Dict]:
        """
        دریافت اولین قسط پرداخت‌نشده
        
        Returns:
            Dict or None: جزئیات قسط بعدی
        """
        payment = enrollment.installment_payments.filter(
            payment_status__in=['pending', 'partial']
        ).order_by('installment__installment_number').first()
        
        if not payment:
            return None
        
        return {
            'id': payment.id,
            'installment_number': payment.installment.installment_number,
            'session_number': payment.installment.session_number,
            'amount_due': payment.installment.amount,
            'amount_paid': payment.amount_paid,
            'remaining_amount': payment.installment.amount - payment.amount_paid,
        }
