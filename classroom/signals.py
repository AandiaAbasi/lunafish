"""
Classroom Application Signals

Handles automatic business logic triggers:
- Creating TeacherWallet when a user becomes a teacher
- Creating ClassRevenue when a ClassBooking is made
- Updating wallet balances when revenue is confirmed
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from .models import ClassBooking, ClassRevenue, TeacherWallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_teacher_wallet(sender, instance, created, **kwargs):
    """
    Create TeacherWallet when user role becomes 'teacher'
    
    When:
        - User is created with role='teacher'
        - User's role is changed to 'teacher'
    
    Action:
        - Create TeacherWallet with initial balance of 0
    
    Example:
        >>> user = User.objects.create(username='ali', role='teacher')
        >>> # TeacherWallet is automatically created
        >>> wallet = TeacherWallet.objects.get(teacher=user)
    """
    if instance.role == 'teacher':
        # چک کن که کیف پول قبلاً وجود ندارد
        if not TeacherWallet.objects.filter(teacher=instance).exists():
            TeacherWallet.objects.create(
                teacher=instance,
                balance=Decimal('0.00'),
                available_balance=Decimal('0.00'),
                pending_balance=Decimal('0.00'),
                total_earned=Decimal('0.00'),
                total_withdrawn=Decimal('0.00'),
                minimum_settlement_amount=Decimal('50000.00')  # حداقل درخواست
            )


@receiver(post_save, sender=ClassBooking)
def create_class_revenue(sender, instance, created, **kwargs):
    """
    Create ClassRevenue when ClassBooking is created
    
    When:
        - New ClassBooking is created (student books a class)
    
    Action:
        - Create ClassRevenue record
        - Calculate platform fee and teacher share
        - Link revenue to the booking
    
    Notes:
        - Platform commission is 30% (default, from PlatformSettings)
        - Teacher share is 70%
        - Revenue is initially 'not confirmed' - awaits completion
    
    Example:
        >>> booking = ClassBooking.objects.create(
        ...     teacher=teacher,
        ...     student=student,
        ...     final_price=100000
        ... )
        >>> # ClassRevenue is automatically created
        >>> revenue = ClassRevenue.objects.get(booking=booking)
        >>> # revenue.teacher_share == 70000
        >>> # revenue.platform_fee == 30000
    """
    if created and instance.status == 'reserved':
        # چک کن که revenue قبلاً وجود ندارد
        if not ClassRevenue.objects.filter(booking=instance).exists():
            from django.db import transaction
            
            try:
                with transaction.atomic():
                    # دریافت نرخ کمیسیون (پیش‌فرض: 30%)
                    from .models import PlatformSettings
                    
                    platform_settings = PlatformSettings.objects.first()
                    commission_rate = Decimal('30')  # درصد
                    
                    if platform_settings:
                        commission_rate = Decimal(str(platform_settings.commission_rate_class))
                    
                    # محاسبه کارمزد و سهم معلم
                    original_price = instance.final_price or Decimal('0')
                    discount = instance.discount_amount or Decimal('0')
                    
                    platform_fee_percentage = commission_rate
                    platform_fee = (original_price * platform_fee_percentage) / Decimal('100')
                    teacher_share = original_price - platform_fee
                    
                    # ایجاد ClassRevenue
                    ClassRevenue.objects.create(
                        teacher=instance.teacher,
                        booking=instance,
                        original_price=original_price,
                        discount_amount=discount,
                        total_amount=original_price,
                        platform_fee_percentage=platform_fee_percentage,
                        platform_fee=platform_fee,
                        teacher_share=teacher_share,
                        is_confirmed=False
                    )
                    
                    # Update wallet with pending balance
                    wallet, _ = TeacherWallet.objects.get_or_create(
                        teacher=instance.teacher,
                        defaults={
                            'account_holder_name': instance.teacher.get_full_name() or instance.teacher.username
                        }
                    )
                    wallet.pending_balance += teacher_share
                    wallet.save()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating ClassRevenue for booking {instance.id}: {str(e)}")


@receiver(pre_save, sender=ClassRevenue)
def handle_revenue_confirmation(sender, instance, **kwargs):
    """
    Handle when ClassRevenue is confirmed
    
    When:
        - ClassRevenue is_confirmed changes from False to True
    
    Action:
        - Move amount from pending_balance to available_balance
        - Create WalletTransaction record
    
    Notes:
        - This signal updates wallet when revenue is confirmed
        - Uses atomic transaction for data consistency
    
    Example:
        >>> revenue = ClassRevenue.objects.get(id=1)
        >>> revenue.is_confirmed = True
        >>> revenue.save()
        >>> # Wallet is automatically updated
        >>> wallet = revenue.teacher.teacherwallet
        >>> # wallet.pending_balance decreases
        >>> # wallet.available_balance increases
    """
    try:
        old_instance = ClassRevenue.objects.get(pk=instance.pk)
    except ClassRevenue.DoesNotExist:
        # این درخواست جدید است
        return
    
    # چک کن که is_confirmed تغییر کرده است
    if not old_instance.is_confirmed and instance.is_confirmed:
        # تأیید شده است - حالا available_balance را آپدیت کن
        wallet = TeacherWallet.objects.filter(teacher=instance.teacher).first()
        
        if wallet:
            # تراکنش اتمی
            from django.db import transaction
            from .models import WalletTransaction
            
            try:
                with transaction.atomic():
                    # دوباره کیف پول را lock کن
                    wallet = TeacherWallet.objects.select_for_update().get(teacher=instance.teacher)
                    
                    # سهم معلم را از pending به available منتقل کن
                    wallet.pending_balance -= instance.teacher_share
                    wallet.available_balance += instance.teacher_share
                    wallet.save()
                    
                    # ثبت تراکنش
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='confirmation',
                        amount=instance.teacher_share,
                        balance_before=wallet.available_balance - instance.teacher_share,
                        balance_after=wallet.available_balance,
                        revenue=instance,
                        description=f'تأیید درآمد برای کلاس {instance.booking.subject.title if instance.booking.subject else ""}'
                    )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error confirming ClassRevenue {instance.id}: {str(e)}")
                raise

@receiver(post_save, sender=ClassBooking)
def create_student_transaction(sender, instance, created, **kwargs):
    """
    Create StudentTransaction when ClassBooking payment is successful
    
    When:
        - ClassBooking payment_status changes to 'paid'
    
    Action:
        - Create StudentTransaction record for audit trail
    """
    from .models import StudentTransaction
    
    # فقط هنگام پرداخت موفق
    if instance.payment_status == 'paid':
        # چک کن که StudentTransaction قبلاً وجود ندارد
        if not StudentTransaction.objects.filter(
            booking=instance,
            transaction_type='class_payment'
        ).exists():
            try:
                StudentTransaction.objects.create(
                    student=instance.student,
                    transaction_type='class_payment',
                    amount=instance.paid_amount,
                    booking=instance,
                    status='completed',
                    description=f'پرداخت برای کلاس {instance.subject.title if instance.subject else ""}'
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating StudentTransaction for booking {instance.id}: {str(e)}")


# ===== Package & Installment Signals =====
@receiver(pre_save, sender='classroom.PackageInstallment')
def validate_installment_before_save(sender, instance, **kwargs):
    """
    اعتبارسنجی قسط قبل از ذخیره‌سازی
    - شماره جلسه باید در محدوده باشد
    - شماره جلسات نباید تکراری باشند
    """
    from .models import PackageInstallment
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext_lazy as _
    
    if instance.package_id:
        # بررسی محدوده شماره جلسه
        if instance.session_number > instance.package.total_sessions:
            raise ValidationError(
                _("شماره جلسه نمی‌تواند بیشتر از %(total)d باشد") % {'total': instance.package.total_sessions}
            )
        
        if instance.session_number < 1:
            raise ValidationError(_("شماره جلسه باید حداقل ۱ باشد"))
        
        # بررسی تکرار شماره جلسه
        existing = PackageInstallment.objects.filter(
            package=instance.package,
            session_number=instance.session_number
        ).exclude(pk=instance.pk)
        
        if existing.exists():
            raise ValidationError(
                _("این شماره جلسه قبلاً برای یک قسط دیگر تعریف شده است")
            )


@receiver(pre_save, sender='classroom.StudentPackagePayment')
def update_payment_status(sender, instance, **kwargs):
    """
    به‌روزرسانی وضعیت پرداخت بر اساس مبالغ پرداختی
    """
    from django.utils import timezone
    
    # اگر مبلغ پرداختی برابر یا بیشتر از مبلغ مقرر باشد
    if instance.amount_paid >= instance.amount_due:
        instance.payment_status = 'paid'
        instance.completed_date = instance.last_payment_date or timezone.now()
    
    # اگر مبلغ پرداختی بیشتر از صفر اما کمتر از مقرر باشد
    elif instance.amount_paid > 0:
        instance.payment_status = 'partial'
    
    # اگر مبلغ پرداختی برابر صفر باشد
    else:
        instance.payment_status = 'pending'
        instance.completed_date = None


@receiver(post_save, sender='classroom.StudentPackagePayment')
def sync_enrollment_status(sender, instance, created, **kwargs):
    """
    سنکرون کردن وضعیت ثبت‌نام بر اساس وضعیت پرداخت‌ها
    """
    enrollment = instance.enrollment
    
    # محاسبه تعداد اقساط پرداخت‌شده
    paid_count = enrollment.installment_payments.filter(payment_status='paid').count()
    total_count = enrollment.installment_payments.count()
    
    # اگر تمام اقساط پرداخت شده باشند
    if paid_count == total_count and total_count > 0:
        enrollment.status = 'completed'
        enrollment.save(update_fields=['status', 'updated_at'])


@receiver(post_save, sender='classroom.StudentPackageEnrollment')
def create_installment_payments(sender, instance, created, **kwargs):
    """
    ایجاد رکوردهای پرداخت برای اقساط هنگام ثبت‌نام جدید
    """
    if created:
        instance.create_payment_records()