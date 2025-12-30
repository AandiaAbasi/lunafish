from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from account.models import User
from core.abstract_models import BaseModel
import jdatetime
from datetime import datetime
from decimal import Decimal
from core.utils import upload_to_dynamic


# ===== Classroom & Scheduling Models =====
class TeacherAvailability(BaseModel):
    """
    زمان‌های دسترسی معلم برای تدریس کلاس‌ها
    هر معلم می‌تواند بازه های زمانی خاص برای تاریخ‌های مشخص تنظیم کند
    """
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, verbose_name=_("معلم"), related_name='availabilities')
    date = models.DateField(verbose_name=_("تاریخ"), help_text=_("تاریخ مشخص برای این دسترسی"))
    start_time = models.TimeField(verbose_name=_("ساعت شروع"), help_text=_("زمانی که معلم تدریس را شروع می‌کند (مثال: 09:00)"))
    end_time = models.TimeField(verbose_name=_("ساعت پایان"), help_text=_("زمانی که معلم تدریس را پایان می‌دهد (مثال: 17:00)"))
    is_available = models.BooleanField(default=True, verbose_name=_("در دسترس"), help_text=_("آیا این بازه زمانی برای رزرو در دسترس است؟"))
    is_booked = models.BooleanField(default=False, verbose_name=_("رزرو شده"), help_text=_("آیا این بازه زمانی قبلاً رزرو شده است؟"))
    is_expired = models.BooleanField(default=False, verbose_name=_("منقضی شده"), help_text=_("آیا این بازه زمانی منقضی شده است؟"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("قیمت"), help_text=_("قیمت تدریس برای این بازه زمانی"))
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("قیمت با تخفیف"), help_text=_("قیمت تدریس با تخفیف برای این بازه زمانی"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("یادداشت‌ها"), help_text=_("یادداشت‌های اضافی درباره این دسترسی"))
    
    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = _("زمان‌بندی کلاس معلم")
        verbose_name_plural = _("زمان‌بندی کلاس‌های معلم")
        unique_together = ('teacher', 'date', 'start_time', 'end_time')
        indexes = [
            models.Index(fields=['teacher', 'date']),
            models.Index(fields=['teacher', 'is_available']),
            models.Index(fields=['date', 'is_available']),
            models.Index(fields=['is_expired']),
        ]
    
    def __str__(self):
        date_str = jdatetime.datetime.fromgregorian(
            datetime=datetime.combine(self.date, self.start_time)
        ).strftime('%Y/%m/%d')
        status = "منقضی" if self.is_expired else "فعال"
        return f"{self.teacher.name} - {date_str} {self.start_time}-{self.end_time} ({status})"
    
    def get_jalali_date(self):
        """نمایش تاریخ شمسی"""
        return jdatetime.datetime.fromgregorian(
            datetime=datetime.combine(self.date, self.start_time)
        ).strftime('%Y/%m/%d')
    
    def check_and_expire(self):
        """بررسی و منقضی کردن اگر زمان گذشته باشد"""
        from datetime import datetime as dt
        now = dt.now()
        slot_datetime = datetime.combine(self.date, self.end_time)
        
        if now > slot_datetime and not self.is_expired:
            self.is_expired = True
            self.is_available = False
            self.save()
            return True
        return False
    
    def is_past(self):
        """بررسی اینکه آیا زمان گذشته است"""
        from datetime import datetime as dt
        now = dt.now()
        slot_datetime = datetime.combine(self.date, self.end_time)
        return now > slot_datetime
    
    def reserve(self):
        """رزرو این بازه زمانی"""
        if not self.is_booked and not self.is_expired:
            self.is_booked = True
            self.save()
            return True
        return False
    
    def release(self):
        """آزاد کردن این بازه زمانی"""
        if self.is_booked:
            self.is_booked = False
            self.save()
            return True
        return False
    

class TeachingSubject(BaseModel):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='subjects', verbose_name=_("معلم"))
    title = models.CharField(max_length=200, verbose_name=_("عنوان"), help_text=_("مثال: انگلیسی مبتدی - الفبا"))
    description = models.TextField(verbose_name=_("توضیح"),help_text=_("توضیح در مورد آنچه در این درس تدریس خواهد شد"))
    cover_image = models.ImageField(upload_to=upload_to_dynamic, null=True, blank=True, verbose_name=_("عکس کاور"))
    demo_video = models.FileField(upload_to=upload_to_dynamic, null=True, blank=True, verbose_name=_("ویدیوی نمونه"), help_text=_("ویدیوی نمونه کوتاه تدریس (MP4, WebM, etc)"))
    min_age = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("حداقل سن"))
    max_age = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("حداکثر سن"))
    level = models.CharField(max_length=50, choices=[('beginner', _("مبتدی")), ('intermediate', _("متوسط")), ('advanced', _("پیشرفته"))], verbose_name=_("سطح"))
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"))

    class Meta:
        verbose_name = _("موضوع تدریس")
        verbose_name_plural = _("موضوعات تدریس")

    def __str__(self):
        return f"{self.title} - {self.teacher.name}"


class ClassBooking(BaseModel):
    availability = models.OneToOneField(TeacherAvailability, on_delete=models.PROTECT, verbose_name=_("دسترسی"))
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, related_name='booked_classes', verbose_name=_("معلم"))
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name='classes', verbose_name=_("دانش‌آموز"))
    subject = models.ForeignKey(TeachingSubject, on_delete=models.PROTECT, related_name='bookings', verbose_name=_("موضوع"))
    status = models.CharField(max_length=20, choices=[('reserved', _("رزرو شده")), ('completed', _("تکمیل شده")), ('cancelled', _("لغو شده")), ('no_show', _("حاضر نشد"))], verbose_name=_("وضعیت"))
    
    # قیمت
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("قیمت"))
    
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("مبلغ تخفیف")) 
    final_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("قیمت نهایی"))

    class Meta:
        verbose_name = _("رزرو کلاس")
        verbose_name_plural = _("رزروهای کلاس")

    def __str__(self):
        return f"{self.subject.title} - {self.teacher.name} با {self.student.name} در {self.availability.date}"
    
    def apply_discount(self, discount_code):
        """اعمال کد تخفیف بر روی رزرو"""
        if not discount_code.is_valid():
            return False, _("Discount code is not valid")
        
        # محاسبه تخفیف
        discount_amount = discount_code.calculate_discount(self.price)
        
        if discount_amount <= 0:
            return False, _("Discount amount is zero")
        
        # اعمال تخفیف
        self.discount_code = discount_code
        self.discount_amount = discount_amount
        self.final_price = self.price - discount_amount
        self.save()
        
        # افزایش تعداد استفاده کد تخفیف
        discount_code.apply()
        
        return True, _("Discount applied successfully")
    
    def save(self, *args, **kwargs):
        # اگر final_price تعیین نشده، برابر با price باشد
        if not self.final_price or self.final_price == 0:
            self.final_price = self.price - self.discount_amount
        
        super().save(*args, **kwargs)

    
# ===== Wallet & Commission Models =====
class TeacherWallet(BaseModel):
    """کیف پول معلم برای مدیریت درآمد و تسویه"""
    teacher = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='wallet', verbose_name=_("معلم"))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("موجودی کل"), help_text=_("کل موجودی"))
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("موجودی در انتظار"), help_text=_("درآمدهای در انتظار تایید"))
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("موجودی قابل برداشت"), help_text=_("موجودی قابل برداشت")) 
    bank_name = models.CharField(max_length=100, blank=True, verbose_name=_("نام بانک"))
    account_number = models.CharField(max_length=50, blank=True, verbose_name=_("شماره حساب")) 
    iban = models.CharField(max_length=26, blank=True, verbose_name=_("شماب (IBAN)"), help_text=_("IR + 24 رقم"))
    card_number = models.CharField(max_length=16, blank=True, verbose_name=_("شماره کارت"))
    account_holder_name = models.CharField(max_length=255, blank=True, verbose_name=_("نام صاحب حساب"))
    minimum_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000, verbose_name=_("حداقل مبلغ تسویه"), help_text=_("حداقل موجودی برای درخواست تسویه"))
    next_settlement_date = models.DateField(null=True, blank=True, verbose_name=_("تاریخ تسویه بعدی"))
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("درآمد کل"), help_text=_("مجموع کل درآمدهای دریافتی"))
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("برداشت کل"), help_text=_("مجموع کل مبالغ تسویه شده"))
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"))
    is_verified = models.BooleanField(default=False, verbose_name=_("تایید شده"), help_text=_("اطلاعات بانکی تایید شده"))
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ تایید"))
    
    class Meta:
        verbose_name = _("کیف پول معلم")
        verbose_name_plural = _("کیف پول‌های معلم")
        ordering = ['-created_at']

    def __str__(self):
        return f"کیف پول {self.teacher.username} - {self.available_balance:,} تومان"
    
    def add_revenue(self, amount):
        """اضافه کردن درآمد به کیف پول"""
        self.balance += Decimal(str(amount))
        self.pending_balance += Decimal(str(amount))
        self.total_earned += Decimal(str(amount))
        self.save()
    
    def confirm_revenue(self, amount):
        """تایید درآمد و انتقال به موجودی قابل برداشت"""
        amount = Decimal(str(amount))
        if self.pending_balance >= amount:
            self.pending_balance -= amount
            self.available_balance += amount
            self.save()
            return True
        return False
    
    def withdraw(self, amount):
        """برداشت از کیف پول"""
        amount = Decimal(str(amount))
        if self.available_balance >= amount:
            self.available_balance -= amount
            self.balance -= amount
            self.total_withdrawn += amount
            self.save()
            return True
        return False
    
    def can_request_settlement(self):
        """بررسی امکان درخواست تسویه"""
        return (
            self.is_active and 
            self.is_verified and 
            self.available_balance >= self.minimum_settlement_amount
        )

    def save(self, *args, **kwargs):
        # If wallet is being verified for the first time
        if self.is_verified and self.verified_at is None:
            self.verified_at = timezone.now()

        # Optional: if verification is removed, clear date
        if not self.is_verified:
            self.verified_at = None

        super().save(*args, **kwargs)


# ===== Revenue & Commission Models =====
class ClassRevenue(BaseModel):
    """درآمد معلم از کلاس‌های تدریس شده"""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='class_revenues', verbose_name=_("معلم"))
    booking = models.OneToOneField(ClassBooking, on_delete=models.PROTECT, related_name='revenue', verbose_name=_("رزرو کلاس"))
    
    # مبلغ اصلی
    original_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("قیمت اولیه"), help_text=_("قیمت اولیه کلاس"))
    
    # تخفیف اعمال شده
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("مبلغ تخفیف"), help_text=_("مبلغ تخفیف اعمال شده"))
    
    # مبلغ نهایی (بعد از تخفیف)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("مبلغ کل"), help_text=_("قیمت نهایی کلاس"))
    
    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name=_("درصد کارمزد پلتفرم"), help_text=_("درصد کارمزد پلتفرم"))
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("کارمزد پلتفرم"), help_text=_("کارمزد پلتفرم (محاسبه خودکار)"))
    teacher_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("سهم معلم"), help_text=_("سهم معلم (محاسبه خودکار)"))
    is_confirmed = models.BooleanField(default=False, verbose_name=_("تایید شده"), help_text=_("درآمد توسط ادمین تایید شده است"))
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ تایید"))
    is_settled = models.BooleanField(default=False, verbose_name=_("تسویه شده"))
    settled_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ تسویه"))
    notes = models.TextField(blank=True, verbose_name=_("یادداشت‌ها"))
    
    class Meta:
        verbose_name = _("درآمد کلاس")
        verbose_name_plural = _("درآمدهای کلاس")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['is_confirmed', '-created_at']),
            models.Index(fields=['is_settled', '-created_at']),
        ]

    def __str__(self):
        return f"{self.teacher.username} - {self.total_amount} T ({self.booking})"
    
    def confirm(self):
        """تایید درآمد و انتقال به موجودی قابل برداشت"""
        if self.is_confirmed:
            return False, _("Revenue already confirmed")
        
        try:
            wallet = TeacherWallet.objects.get(teacher=self.teacher)
            
            # انتقال از pending به available
            if wallet.confirm_revenue(self.teacher_share):
                self.is_confirmed = True
                self.confirmed_at = timezone.now()
                self.save(update_fields=['is_confirmed', 'confirmed_at'])
                
                # ثبت تراکنش تایید
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='confirmation',
                    amount=self.teacher_share,
                    balance_before=wallet.pending_balance + self.teacher_share,
                    balance_after=wallet.available_balance,
                    revenue=self,
                    description=f"تایید درآمد کلاس: {self.booking}"
                )
                
                return True, _("Revenue confirmed successfully")
            else:
                return False, _("Insufficient pending balance")
        except TeacherWallet.DoesNotExist:
            return False, _("Wallet not found")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # محاسبه خودکار کارمزد و سهم بر اساس total_amount
        if self.platform_fee is None:
            self.platform_fee = self.total_amount * (self.platform_fee_percentage / Decimal('100'))
        if self.teacher_share is None:
            self.teacher_share = self.total_amount - self.platform_fee
        
        super().save(*args, **kwargs)
        
        # اضافه کردن درآمد به کیف پول (فقط برای رکوردهای جدید)
        if is_new:
            wallet, created = TeacherWallet.objects.get_or_create(
                teacher=self.teacher,
                defaults={
                    'account_holder_name': self.teacher.get_full_name() or self.teacher.username
                }
            )
            wallet.add_revenue(self.teacher_share)
            
            # ثبت تراکنش
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='revenue',
                amount=self.teacher_share,
                balance_before=wallet.balance - self.teacher_share,
                balance_after=wallet.balance,
                revenue=self,
                description=f"درآمد از کلاس: {self.booking}"
            )


# ===== Withdrawal Request Models =====
class WithdrawalRequest(BaseModel):
    """درخواست برداشت درآمد توسط معلم"""
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', _("انتقال بانکی")),
        ('card_to_card', _("کارت به کارت")),
        ('wallet', _("کیف پول")),
        ('other', _("سایر")),
    ]
    STATUS_CHOICES = [
        ('pending', _("در انتظار")),
        ('processing', _("در حال پردازش")),
        ('completed', _("تکمیل شده")),
        ('failed', _("ناموفق")),
        ('cancelled', _("لغو شده")),
    ]
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}, related_name='withdrawal_requests', verbose_name=_("معلم"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("مبلغ"))
    revenues = models.ManyToManyField(ClassRevenue, related_name='withdrawal_request', verbose_name=_("درآمدها"))
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, verbose_name=_("روش پرداخت"))
    account_info = models.JSONField(verbose_name=_("اطلاعات حساب"), help_text=_("شماره کارت، شماب و غیره"))
    transaction_id = models.CharField(max_length=255, blank=True, verbose_name=_("شناسه تراکنش"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("وضعیت"))
    notes = models.TextField(blank=True, verbose_name=_("یادداشت‌ها"))
    admin_notes = models.TextField(blank=True, verbose_name=_("یادداشت‌های ادمین"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاریخ تکمیل")) 
    
    class Meta:
        verbose_name = _("درخواست برداشت")
        verbose_name_plural = _("درخواست‌های برداشت")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Withdrawal {self.amount} from {self.teacher.username} - {self.get_status_display()}"
    
    def complete_withdrawal(self):
        """Complete withdrawal and deduct from wallet"""
        if self.status == 'pending' or self.status == 'processing':
            try:
                wallet = self.teacher.wallet
                
                # بررسی موجودی کافی
                if wallet.available_balance >= self.amount:
                    # کسر از کیف پول
                    if wallet.withdraw(self.amount):
                        # تغییر وضعیت برداشت
                        self.status = 'completed'
                        self.completed_at = timezone.now()
                        self.save()
                        
                        # ثبت تراکنش
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='withdrawal',
                            amount=self.amount,
                            balance_before=wallet.balance + self.amount,
                            balance_after=wallet.balance,
                            withdrawal=self,
                            description=f"Withdrawal by {self.get_payment_method_display()}"
                        )
                        
                        # علامت‌گذاری درآمدها به عنوان برداشت شده
                        self.revenues.update(is_settled=True, settled_at=timezone.now())
                        
                        return True, _("Withdrawal completed successfully")
                    else:
                        return False, _("Error withdrawing from wallet")
                else:
                    return False, f"Insufficient balance. Available: {wallet.available_balance:,} Toman"
            except TeacherWallet.DoesNotExist:
                return False, _("Wallet not found")
        
        return False, _("Withdrawal status cannot be completed")
    
    def cancel_withdrawal(self):
        """Cancel withdrawal"""
        if self.status in ['pending', 'processing']:
            self.status = 'cancelled'
            self.save()
            return True, _("Withdrawal cancelled")
        return False, _("Cannot cancel withdrawal in current status")


# ===== Transaction Models =====
class WalletTransaction(BaseModel):
    """تراکنش‌های کیف پول معلم"""
    TRANSACTION_TYPE_CHOICES = [
        ('revenue', _("درآمد")),
        ('confirmation', _("تایید")),
        ('withdrawal', _("برداشت")),
        ('refund', _("بازگشت")),
        ('adjustment', _("تعدیل")),
        ('bonus', _("جایزه")),
        ('penalty', _("جریمه")),
    ]
    wallet = models.ForeignKey(TeacherWallet, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("کیف پول"))
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name=_("نوع تراکنش"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("مبلغ"))
    balance_before = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("موجودی قبل"))
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("موجودی بعد"))
    revenue = models.ForeignKey(ClassRevenue, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions', verbose_name=_("درآمد"))
    withdrawal = models.ForeignKey(WithdrawalRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions', verbose_name=_("برداشت"))
    description = models.TextField(blank=True, verbose_name=_("توضیح"))
    admin_note = models.TextField(blank=True, verbose_name=_("یادداشت ادمین"))
    
    class Meta:
        verbose_name = _("تراکنش کیف پول")
        verbose_name_plural = _("تراکنش‌های کیف پول")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]

    def __str__(self):
        sign = '+' if self.transaction_type in ['revenue', 'refund', 'bonus'] else '-'
        return f"{self.get_transaction_type_display()}: {sign}{self.amount:,} T"


class StudentTransaction(BaseModel):
    """تراکنش‌های دانش‌آموز (پرداخت برای کلاس‌ها)"""
    TRANSACTION_TYPE_CHOICES = [
        ('class_payment', _("پرداخت کلاس")),
        ('refund', _("بازگشت")),
    ]
    STATUS_CHOICES = [
        ('pending', _("در انتظار")),
        ('completed', _("تکمیل شده")),
        ('failed', _("ناموفق")),
        ('refunded', _("بازگشت‌شده")),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='class_transactions', verbose_name=_("دانش‌آموز"))
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name=_("نوع تراکنش"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("مبلغ"))
    booking = models.ForeignKey(ClassBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_transactions', verbose_name=_("رزرو کلاس")) 
    description = models.TextField(blank=True, verbose_name=_("توضیح"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', verbose_name=_("وضعیت"))
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ پرداخت"))
    
    class Meta:
        verbose_name = _("تراکنش دانش‌آموز")
        verbose_name_plural = _("تراکنش‌های دانش‌آموز")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.get_transaction_type_display()}: {self.amount:,} T"


# ===== Platform Settings (Commission Configuration) =====
class PlatformSettings(models.Model):
    """
    تنظیمات پلتفرم کمیسیون و نرخ‌ها
    Singleton model - فقط یک نمونه وجود دارد
    """
    # نرخ کمیسیون برای انواع مختلف (به صورت درصد)
    commission_rate_class = models.DecimalField(max_digits=5, decimal_places=2, default=30.00, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name=_("درصد کمیسیون کلاس"), help_text=_("درصد کمیسیون پلتفرم برای کلاس‌های تدریس شده (0-100)"))
    # سایر تنظیمات
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='platform_settings_updates', verbose_name=_("به‌روزرسانی‌شده توسط"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاریخ به‌روزرسانی"))
    
    class Meta:
        verbose_name = _("تنظیمات پلتفرم")
        verbose_name_plural = _("تنظیمات پلتفرم")

    def __str__(self):
        return f"Platform Settings - Class Commission: {self.commission_rate_class}%"
    
    @staticmethod
    def get_settings():
        """دریافت تنظیمات (یا ایجاد اگر وجود ندارد)"""
        obj, created = PlatformSettings.objects.get_or_create(pk=1)
        return obj


