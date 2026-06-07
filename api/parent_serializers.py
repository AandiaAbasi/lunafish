"""
Serializers for Parent Portal - Class History, Payments, Teacher Selection, Usage Time Control
والدین می‌توانند با student_id + parent_password وارد شوند و:
1. تاریخچه کلاس‌های کودک را ببینند
2. ریز پرداخت‌های کودک را مشاهده کنند
3. معلم برای کودک انتخاب کنند
4. زمان مجاز استفاده اپلیکیشن را تعیین کنند
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import models
from account.models import ParentProfile, ParentAppUsageLog, User
from classroom.models import ClassBooking, StudentTransaction, TeachingSubject, TeacherAvailability
import jdatetime
from datetime import datetime, date


class JalaliDateField(serializers.DateField):
    """Custom field to handle Jalali dates"""
    def to_representation(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            value = value.date()
        jalali = jdatetime.datetime.fromgregorian(datetime=datetime.combine(value, datetime.min.time()))
        return jalali.strftime('%Y/%m/%d')
    
    def to_internal_value(self, data):
        try:
            # Try parsing as Jalali date first
            j_date = jdatetime.datetime.strptime(data, '%Y/%m/%d')
            gregorian = j_date.togregorian()
            return gregorian.date()
        except:
            # Fall back to gregorian
            return super().to_internal_value(data)


# ===== Parent Login Serializer =====
class ParentLoginSerializer(serializers.Serializer):
    """والدین برای ورود باید از نام کاربری دانش‌آموز استفاده کنند"""
    username = serializers.CharField(
        max_length=255,
        write_only=True,
        help_text=_("نام کاربری دانش‌آموز")
    )
    password = serializers.CharField(
        max_length=255,
        write_only=True,
        help_text=_("رمز والدین"),
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """بررسی صحت username و password"""
        username = data.get('username')
        password = data.get('password')
        
        # بررسی دانش‌آموز بر اساس نام کاربری
        student = None
        try:
            student = User.objects.get(username=username, role='user')
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'username': _("Student not found. Please check the student username.")
            })
        except Exception:
            raise serializers.ValidationError({
                'username': _("Invalid username format")
            })
        
        # بررسی والد
        try:
            parent = ParentProfile.objects.get(student=student, is_active=True)
        except ParentProfile.DoesNotExist:
            raise serializers.ValidationError({
                'password': _("No parent profile found for this student")
            })
        
        # بررسی رمز
        if not parent.verify_password(password):
            raise serializers.ValidationError({
                'password': _("Invalid parent password")
            })
        
        # ذخیره parent برای استفاده در view
        data['parent'] = parent
        
        return data


# ===== Child Class History Serializer =====
class ChildClassHistorySerializer(serializers.ModelSerializer):
    """تاریخچه کلاس‌های کودک"""
    class_date = JalaliDateField(source='availability.date', read_only=True)
    start_time = serializers.TimeField(source='availability.start_time', read_only=True)
    end_time = serializers.TimeField(source='availability.end_time', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    subject_id = serializers.IntegerField(source='subject.id', read_only=True)
    
    class Meta:
        model = ClassBooking
        fields = [
            'id',
            'class_date',
            'start_time',
            'end_time',
            'teacher_name',
            'teacher_id',
            'subject_title',
            'subject_id',
            'status',
            'price',
            'discount_amount',
            'final_price'
        ]
        read_only_fields = fields


# ===== Child Payment History Serializer =====
class ChildPaymentHistorySerializer(serializers.ModelSerializer):
    """ریز پرداخت‌های کودک"""
    booking_id = serializers.IntegerField(source='booking.id', read_only=True, allow_null=True)
    class_title = serializers.SerializerMethodField(read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = StudentTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'booking_id',
            'class_title',
            'teacher_name',
            'description',
            'status',
            'payment_date'
        ]
        read_only_fields = fields
    
    def get_class_title(self, obj):
        """دریافت عنوان کلاس"""
        if obj.booking and obj.booking.subject:
            return obj.booking.subject.title
        return None
    
    def get_teacher_name(self, obj):
        """دریافت نام معلم"""
        if obj.booking and obj.booking.teacher:
            return obj.booking.teacher.name or obj.booking.teacher.username
        return None


# ===== Child Payment Summary Serializer =====
class ChildPaymentSummarySerializer(serializers.Serializer):
    """خلاصه وضعیت مالی کودک"""
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_pending = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_refunded = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_failed = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)


# ===== Parent Dashboard Overview Serializer =====
class ChildProfileForParentSerializer(serializers.ModelSerializer):
    """نمایش اطلاعات کودک برای والد"""
    birth_date = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    selected_avatar_image = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'username',
            'birth_date',
            'gender',
            'bio',
            'profile_photo_path',
            'selected_avatar_image'
        ]
        read_only_fields = fields
    
    def get_selected_avatar_image(self, obj):
        """دریافت تصویر آواتار انتخاب‌شده"""
        if obj.selected_avatar:
            return obj.selected_avatar.image.url if obj.selected_avatar.image else None
        return None


class ParentDashboardSerializer(serializers.Serializer):
    """داشبورد والد - نمایش خلاصه‌ای از وضعیت کودک"""
    child = ChildProfileForParentSerializer(read_only=True)
    total_classes = serializers.IntegerField(read_only=True)
    completed_classes = serializers.IntegerField(read_only=True)
    cancelled_classes = serializers.IntegerField(read_only=True)
    no_show_classes = serializers.IntegerField(read_only=True)
    upcoming_classes = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_pending_payment = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


# ===== Parent Permissions & Usage Time Serializer =====
class ParentProfileSerializer(serializers.ModelSerializer):
    """اطلاعات والد و مجوزهایش"""
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    child_full_name = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = ParentProfile
        fields = [
            'id',
            'student_id',
            'student_name',
            'child_full_name',
            'parent_name',
            'phone',
            'email',
            'can_view_class_history',
            'can_view_payments',
            'can_select_teacher',
            'can_set_usage_time',
            'daily_usage_limit_minutes',
            'allowed_start_time',
            'allowed_end_time',
            'is_active',
            'last_login_at'
        ]
        read_only_fields = [
            'id',
            'student_id',
            'student_name',
            'child_full_name',
            'can_view_class_history',
            'can_view_payments',
            'can_select_teacher',
            'can_set_usage_time',
            'is_active',
            'last_login_at'
        ]


class ParentUpdateUsageTimeSerializer(serializers.ModelSerializer):
    """به‌روزرسانی محدودیت زمان استفاده کودک"""
    class Meta:
        model = ParentProfile
        fields = [
            'daily_usage_limit_minutes',
            'allowed_start_time',
            'allowed_end_time'
        ]
    
    def validate(self, data):
        """بررسی صحت داده‌ها"""
        if 'daily_usage_limit_minutes' in data and data['daily_usage_limit_minutes']:
            if data['daily_usage_limit_minutes'] < 0:
                raise serializers.ValidationError({
                    'daily_usage_limit_minutes': _("Usage limit cannot be negative")
                })
            if data['daily_usage_limit_minutes'] > 1440:  # 24 hours
                raise serializers.ValidationError({
                    'daily_usage_limit_minutes': _("Usage limit cannot exceed 24 hours (1440 minutes)")
                })
        
        start_time = data.get('allowed_start_time')
        end_time = data.get('allowed_end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'allowed_end_time': _("End time must be after start time")
            })
        
        return data


class ParentAppUsageLogSerializer(serializers.ModelSerializer):
    """ثبت استفاده روزانه"""
    date = JalaliDateField()
    
    class Meta:
        model = ParentAppUsageLog
        fields = [
            'id',
            'date',
            'total_minutes',
            'session_count'
        ]
        read_only_fields = fields


# ===== Teacher Selection Serializer =====
class TeachingSubjectForParentSelectionSerializer(serializers.ModelSerializer):
    """موضوعات تدریس برای انتخاب توسط والد"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)


# ===== Parental Control Usage Tracking Serializers =====

class ParentalLimitsSerializer(serializers.Serializer):
    """دریافت محدودیت‌های والدین و وضعیت مصرف"""
    daily_usage_limit_minutes = serializers.IntegerField(
        allow_null=True,
        help_text=_("حداکثر دقایق استفاده روزانه")
    )
    allowed_start_time = serializers.TimeField(
        allow_null=True,
        help_text=_("ساعت شروع مجاز")
    )
    allowed_end_time = serializers.TimeField(
        allow_null=True,
        help_text=_("ساعت پایان مجاز")
    )
    server_now = serializers.DateTimeField(
        help_text=_("زمان فعلی سرور")
    )
    server_date = serializers.DateField(
        help_text=_("تاریخ فعلی سرور")
    )
    server_time = serializers.TimeField(
        help_text=_("ساعت فعلی سرور")
    )
    used_today_seconds = serializers.IntegerField(
        help_text=_("ثانیه‌های استفاده شده امروز")
    )
    remaining_seconds = serializers.IntegerField(
        allow_null=True,
        help_text=_("ثانیه‌های باقی‌مانده")
    )
    blocked = serializers.BooleanField(
        help_text=_("آیا دسترسی بلاک شده است")
    )
    block_reason = serializers.CharField(
        allow_null=True,
        help_text=_("دلیل بلاک")
    )


class UsageReportRequestSerializer(serializers.Serializer):
    """گزارش مصرف از طرف دانش‌آموز"""
    session_seconds = serializers.IntegerField(
        min_value=1,
        max_value=86400,
        help_text=_("تعداد ثانیه‌های این جلسه (حداکثر 24 ساعت)")
    )
    device_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text=_("شناسه دستگاه (اختیاری)")
    )
    client_started_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text=_("زمان شروع در دستگاه کاربر (غیرقابل اعتماد)")
    )
    client_ended_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text=_("زمان پایان در دستگاه کاربر (غیرقابل اعتماد)")
    )


class ParentChangePasswordSerializer(serializers.Serializer):
    """تغییر رمز والد"""
    current_password = serializers.CharField(
        write_only=True,
        help_text=_("رمز فعلی والد")
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text=_("رمز جدید (حداقل 8 کاراکتر)")
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text=_("تکرار رمز جدید")
    )
    
    def validate(self, data):
        """Validate password match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _("Passwords do not match")
            })
        return data


class TeachingSubjectForParentSelectionSerializer(serializers.ModelSerializer):
    """موضوعات تدریس برای انتخاب توسط والد"""
    cover_image_url = serializers.SerializerMethodField()
    demo_video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TeachingSubject
        fields = [
            'id',
            'teacher_id',
            'teacher_name',
            'title',
            'description',
            'cover_image_url',
            'demo_video_url',
            'min_age',
            'max_age',
            'level'
        ]
        read_only_fields = fields
    
    def get_cover_image_url(self, obj):
        return obj.cover_image.url if obj.cover_image else None
    
    def get_demo_video_url(self, obj):
        return obj.demo_video.url if obj.demo_video else None


class TeacherAvailabilityForParentSelectionSerializer(serializers.ModelSerializer):
    """زمان‌های دسترس معلم برای انتخاب کلاس توسط والد"""
    date = JalaliDateField()
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    
    class Meta:
        model = TeacherAvailability
        fields = [
            'id',
            'teacher_id',
            'teacher_name',
            'date',
            'start_time',
            'end_time',
            'price',
            'discount_price'
        ]
        read_only_fields = fields


# ===== Parent Registration Serializer =====
class ParentRegistrationSerializer(serializers.ModelSerializer):
    """ثبت‌نام والد برای یک دانش‌آموز"""
    parent_password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={'input_type': 'password'},
        help_text=_("رمز والدین (برای ورود به درگاه والدین)")
    )
    parent_password_confirm = serializers.CharField(
        max_length=255,
        write_only=True,
        style={'input_type': 'password'},
        help_text=_("تایید رمز")
    )
    
    class Meta:
        model = ParentProfile
        fields = [
            'parent_name',
            'phone',
            'email',
            'parent_password',
            'parent_password_confirm'
        ]
    
    def validate(self, data):
        """بررسی رمز‌ها"""
        password = data.get('parent_password')
        password_confirm = data.get('parent_password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'parent_password_confirm': _("Passwords do not match")
            })
        
        if len(password) < 6:
            raise serializers.ValidationError({
                'parent_password': _("Password must be at least 6 characters")
            })
        
        return data
    
    def create(self, validated_data):
        """ایجاد والد"""
        # حذف password_confirm
        validated_data.pop('parent_password_confirm')
        password = validated_data.pop('parent_password')
        
        # ایجاد والد
        parent = ParentProfile(**validated_data)
        parent.set_password(password)
        parent.save()
        
        return parent
