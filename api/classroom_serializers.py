"""
Serializers for Classroom App - Time Slots, Bookings, Revenue, Transactions
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from classroom.models import (
    TeacherAvailability, TeachingSubject, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings,
    Package, PackageInstallment, StudentPackageEnrollment, StudentPackagePayment
)
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


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for TeacherAvailability - Time Slots"""
    date = JalaliDateField()
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    discount_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        allow_null=True,
        help_text='Discounted price (optional)'
    )
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherAvailability
        fields = [
            'id', 'teacher', 'teacher_name', 'date', 'start_time', 'end_time',
            'price', 'discount_price', 'is_available', 'is_booked', 'is_expired', 
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired']
    
    def get_is_expired(self, obj):
        """Check if slot has expired"""
        return obj.is_expired or obj.is_past()


class BulkTeacherAvailabilitySerializer(serializers.ListSerializer):
    """Serializer for bulk creating TeacherAvailability"""
    def create(self, validated_data):
        availabilities = [
            TeacherAvailability(**item) for item in validated_data
        ]
        return TeacherAvailability.objects.bulk_create(availabilities)


class TeachingSubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source='teacher.name',
        read_only=True
    )

    level_display = serializers.CharField(
        source='get_level_display',
        read_only=True
    )
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = TeachingSubject
        fields = [
            'id',
            'teacher_name',
            'title',
            'description',
            'level',
            'level_display',
            'cover_image',
            'demo_video',
            'min_age',
            'max_age',
            'is_active',
            'created_at',
            'status',
            'teacher',
            'rejection_reason'
        ]

        read_only_fields = [
            'id',
            'teacher_name',
            'level_display',
            'created_at',
            'teacher', 
        ]
        
    def get_teacher(self, obj):
            return {
                'id': obj.teacher.id,
                'name': obj.teacher.name # یا هر فیلدی که نام معلم در مدل User در آن ذخیره شده
            }


class TeachingSubjectUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating TeachingSubject with explicit file removal support.
    
    Supports removing files using boolean flags:
    - remove_cover_image: true - removes the cover_image file
    - remove_demo_video: true - removes the demo_video file
    """
    remove_cover_image = serializers.BooleanField(required=False, write_only=True, default=False)
    remove_demo_video = serializers.BooleanField(required=False, write_only=True, default=False)
    
    class Meta:
        model = TeachingSubject
        fields = [
            'title',
            'description',
            'level',
            'cover_image',
            'demo_video',
            'min_age',
            'max_age',
            'is_active',
            'remove_cover_image',
            'remove_demo_video',
        ]
    
    def update(self, instance, validated_data):
        """
        Update the TeachingSubject instance.
        Handle explicit file removal before saving.
        """
        # Extract removal flags
        remove_cover_image = validated_data.pop('remove_cover_image', False)
        remove_demo_video = validated_data.pop('remove_demo_video', False)
        
        # Handle cover_image removal
        if remove_cover_image:
            if instance.cover_image:
                instance.cover_image.delete(save=False)
            instance.cover_image = None
        
        # Handle demo_video removal
        if remove_demo_video:
            if instance.demo_video:
                instance.demo_video.delete(save=False)
            instance.demo_video = None
        
        # Update other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ClassBookingSerializer(serializers.ModelSerializer):
    """Serializer for ClassBooking - List & Detail"""
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    availability_date = serializers.DateField(source='availability.date', read_only=True)
    availability_time = serializers.SerializerMethodField()

    # OnlineClass (reverse OneToOne from OnlineClass.booking)
    online_class_id = serializers.UUIDField(source='booked_class.id', read_only=True)
    online_class_title = serializers.CharField(source='booked_class.title', read_only=True)
    online_class_status = serializers.CharField(source='booked_class.status', read_only=True)
    online_class_start = serializers.DateTimeField(source='booked_class.scheduled_start', read_only=True)
    online_class_end = serializers.DateTimeField(source='booked_class.scheduled_end', read_only=True)

    class Meta:
        model = ClassBooking
        fields = [
            'id', 'availability', 'availability_date', 'availability_time',
            'teacher', 'teacher_name', 'student', 'student_name',
            'subject', 'subject_title', 'status', 'status_display',
            'price', 'discount_amount', 'final_price',
            'online_class_id', 'online_class_title', 'online_class_status',
            'online_class_start', 'online_class_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student', 'teacher', 'created_at', 'updated_at',
            'discount_amount', 'final_price',
            'online_class_id', 'online_class_title', 'online_class_status',
            'online_class_start', 'online_class_end',
        ]

    def get_availability_time(self, obj):
        """Get formatted time range"""
        return f"{obj.availability.start_time.strftime('%H:%M')} - {obj.availability.end_time.strftime('%H:%M')}"


class CreateClassBookingSerializer(serializers.Serializer):
    """Serializer for Creating/Purchasing a Class"""
    availability = serializers.IntegerField(help_text="ID of the TeacherAvailability slot")
    subject = serializers.IntegerField(help_text="ID of the TeachingSubject")
    discount_code = serializers.CharField(required=False, allow_blank=True, help_text="Optional discount code")
    
    def validate_availability(self, value):
        """Validate that availability exists and is available"""
        try:
            availability = TeacherAvailability.objects.get(id=value)
        except TeacherAvailability.DoesNotExist:
            raise serializers.ValidationError(_("زمان‌بندی یافت نشد"))
        
        if not availability.is_available:
            raise serializers.ValidationError(_("این زمان‌بندی دیگر در دسترس نیست"))
        
        if availability.is_booked:
            raise serializers.ValidationError(_("این زمان‌بندی قبلاً رزرو شده است"))
        
        if availability.is_expired or availability.is_past():
            raise serializers.ValidationError(_("این زمان‌بندی منقضی شده است"))
        
        return value
    
    def validate_subject(self, value):
        """Validate that subject exists"""
        try:
            subject = TeachingSubject.objects.get(id=value)
        except TeachingSubject.DoesNotExist:
            raise serializers.ValidationError(_("درس یافت نشد"))
        
        if not subject.is_active:
            raise serializers.ValidationError(_("این درس فعال نیست"))
        
        return value
    
    def validate(self, data):
        """Validate that subject belongs to teacher of availability"""
        availability_id = data.get('availability')
        subject_id = data.get('subject')
        
        try:
            availability = TeacherAvailability.objects.get(id=availability_id)
            subject = TeachingSubject.objects.get(id=subject_id)
            
            if availability.teacher != subject.teacher:
                raise serializers.ValidationError(_("درس باید متعلق به همان معلم باشد"))
        except (TeacherAvailability.DoesNotExist, TeachingSubject.DoesNotExist):
            pass
        
        return data


class TeacherWalletSerializer(serializers.ModelSerializer):
    """Serializer for TeacherWallet"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    
    class Meta:
        model = TeacherWallet
        fields = [
            'id', 'teacher', 'teacher_name', 'balance', 'available_balance', 'pending_balance',
            'bank_name', 'account_number', 'iban', 'card_number', 'account_holder_name',
            'minimum_settlement_amount', 'next_settlement_date', 'total_earned', 'total_withdrawn',
            'is_active', 'is_verified', 'verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'total_earned', 'total_withdrawn', 'created_at', 'updated_at']


class BankInformationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bank information in TeacherWallet"""
    
    class Meta:
        model = TeacherWallet
        fields = ['bank_name', 'account_number', 'iban', 'card_number', 'account_holder_name']
    
    def validate_iban(self, value):
        """Validate IBAN format (IR + 24 digits)"""
        if value:
            value = value.strip().upper()
            if not value.startswith('IR'):
                raise serializers.ValidationError(_("شماره شبا باید با IR شروع شود"))
            if len(value) != 26:
                raise serializers.ValidationError(_("شماره شبا باید 26 کاراکتر باشد (IR + 24 رقم)"))
            if not value[2:].isdigit():
                raise serializers.ValidationError(_("شماره شبا باید فقط شامل اعداد باشد (بعد از IR)"))
        return value
    
    def validate_card_number(self, value):
        """Validate card number (16 digits)"""
        if value:
            value = value.strip().replace(' ', '').replace('-', '')
            if not value.isdigit():
                raise serializers.ValidationError(_("شماره کارت باید فقط شامل اعداد باشد"))
            if len(value) != 16:
                raise serializers.ValidationError(_("شماره کارت باید 16 رقم باشد"))
        return value


class ClassRevenueSerializer(serializers.ModelSerializer):
    """Serializer for ClassRevenue"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    booking_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassRevenue
        fields = [
            'id', 'teacher', 'teacher_name', 'booking', 'booking_detail',
            'original_price', 'discount_amount', 'total_amount',
            'platform_fee_percentage', 'platform_fee', 'teacher_share',
            'is_confirmed', 'confirmed_at', 'is_settled', 'settled_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'platform_fee', 'teacher_share', 'created_at', 'updated_at']
    
    def get_booking_detail(self, obj):
        return {
            'id': obj.booking.id,
            'subject': obj.booking.subject.title,
            'student': obj.booking.student.name
        }


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Serializer for WithdrawalRequest"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    receipt_image_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'teacher', 'teacher_name', 'amount', 'revenues',
            'payment_method', 'payment_method_display', 'account_info',
            'transaction_id', 'status', 'status_display', 'notes', 'admin_notes',
            'completed_at', 'created_at', 'updated_at', 'receipt_image', 'receipt_image_url'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'receipt_image_url']
    
    def get_receipt_image_url(self, obj):
        """دریافت URL کامل فیش واریزی"""
        if obj.receipt_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_image.url)
            return obj.receipt_image.url
        return None


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransaction"""
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    wallet_teacher_name = serializers.CharField(source='wallet.teacher.name', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'wallet_teacher_name', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_before', 'balance_after', 'revenue', 'withdrawal',
            'description', 'admin_note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for StudentTransaction"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StudentTransaction
        fields = [
            'id', 'student', 'student_name', 'transaction_type', 'transaction_type_display',
            'amount', 'booking', 'description', 'status', 'status_display',
            'payment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'payment_date', 'created_at', 'updated_at']


class PlatformSettingsSerializer(serializers.ModelSerializer):
    """Serializer for PlatformSettings"""
    class Meta:
        model = PlatformSettings
        fields = [
            'id', 'commission_rate_class', 'updated_by', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


# ============= Teacher List and Detail Serializers =============

class TeacherListSerializer(serializers.Serializer):
    """Serializer for Teacher List - Basic information for discovery"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=200, read_only=True)
    gender = serializers.CharField(max_length=20, read_only=True, allow_blank=True)
    qualifications = serializers.CharField(max_length=500, read_only=True, allow_blank=True)
    languages_taught = serializers.CharField(max_length=500, read_only=True, allow_blank=True)
    profile_photo_path = serializers.ImageField(read_only=True, allow_null=True)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    resume_summary = serializers.SerializerMethodField()
    experience_years = serializers.IntegerField(read_only=True)
    is_teacher_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Rating stats
    total_ratings = serializers.SerializerMethodField()
    average_rating_stars = serializers.SerializerMethodField()
    
    def get_resume_summary(self, obj):
        """Return truncated resume summary (first 200 characters)"""
        if hasattr(obj, 'resume_summary') and obj.resume_summary:
            return obj.resume_summary[:200] + ('...' if len(obj.resume_summary) > 200 else '')
        return ''
    
    def get_total_ratings(self, obj):
        """تعداد کل امتیازاتی که این معلم دریافت کرده"""
        from account.models import TeacherRating
        return TeacherRating.objects.filter(teacher=obj, is_verified=True).count()
    
    def get_average_rating_stars(self, obj):
        """میانگین ستاره‌های این معلم"""
        from account.models import TeacherRating
        from django.db.models import Avg
        result = TeacherRating.objects.filter(teacher=obj, is_verified=True).aggregate(
            average=Avg('stars')
        )
        return round(result['average'] or 0, 2)


class TeachingSubjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for TeachingSubject in Teacher Detail"""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = TeachingSubject
        fields = [
            'id', 'title', 'description', 'level', 'level_display',
            'cover_image', 'demo_video', 'min_age', 'max_age', 'is_active'
        ]
        read_only_fields = ['id', 'level_display']


class TeacherAvailabilityDetailSerializer(serializers.ModelSerializer):
    """Serializer for TeacherAvailability in Teacher Detail"""
    date = JalaliDateField(read_only=True)
    
    class Meta:
        model = TeacherAvailability
        fields = [
            'id', 'date', 'start_time', 'end_time', 'price',
            'discount_price', 'is_available', 'is_booked', 'is_expired', 'notes'
        ]
        read_only_fields = ['id', 'date', 'start_time', 'end_time', 'price', 'discount_price', 'is_available', 'is_booked', 'is_expired']


class TeacherDetailSerializer(serializers.Serializer):
    """Serializer for Teacher Detail - Complete teacher profile"""
    # Basic Information
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=200, read_only=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(max_length=20, read_only=True, allow_blank=True)
    
    # Teacher Qualifications
    qualifications = serializers.CharField(max_length=500, read_only=True, allow_blank=True)
    languages_taught = serializers.CharField(max_length=500, read_only=True, allow_blank=True)
    specialization = serializers.CharField(max_length=500, read_only=True, allow_blank=True)
    experience_years = serializers.IntegerField(read_only=True)
    is_teacher_verified = serializers.BooleanField(read_only=True)
    
    # Introduction Section
    resume_summary = serializers.CharField(read_only=True, allow_blank=True)
    introduction_video = serializers.FileField(read_only=True, allow_null=True)
    bio = serializers.CharField(read_only=True, allow_blank=True)
    profile_photo_path = serializers.ImageField(read_only=True, allow_null=True)
    
    # Teaching Information
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # Related Data
    teaching_subjects = serializers.SerializerMethodField()
    availability_slots = serializers.SerializerMethodField()
    
    def get_teaching_subjects(self, obj):
        """Get all teaching subjects for this teacher"""
        if not hasattr(obj, 'teaching_subjects'):
            # Query teaching subjects from database
            subjects = TeachingSubject.objects.filter(teacher=obj, is_active=True, status='approved')
        else:
            subjects = obj.teaching_subjects.filter(is_active=True)
        
        serializer = TeachingSubjectDetailSerializer(subjects, many=True)
        return serializer.data
    
    def get_availability_slots(self, obj):
        """Get upcoming and current availability slots (not expired, not booked)"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get slots from today onwards that are available
        today = timezone.now().date()
        if not hasattr(obj, 'availabilities'):
            slots = TeacherAvailability.objects.filter(
                teacher=obj,
                date__gte=today,
                is_available=True,
                is_booked=False,
                is_expired=False
            ).order_by('date', 'start_time')[:50]  # Limit to first 50 slots
        else:
            slots = obj.availabilities.filter(
                date__gte=today,
                is_available=True,
                is_booked=False,
                is_expired=False
            ).order_by('date', 'start_time')[:50]
        
        serializer = TeacherAvailabilityDetailSerializer(slots, many=True)
        return serializer.data


# ===== Support Message Serializers =====
class SupportMessageAttachmentSerializer(serializers.Serializer):
    """Serializer for Support Message Attachments"""
    id = serializers.IntegerField(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    def get_file_url(self, obj):
        """دریافت URL فایل"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_name(self, obj):
        """دریافت نام فایل"""
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None


class SupportMessageSerializer(serializers.Serializer):
    """Serializer for Support Messages"""
    id = serializers.IntegerField(read_only=True)
    teacher_id = serializers.IntegerField(write_only=True)
    sender_id = serializers.IntegerField(write_only=True)
    message_text = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    read_at = serializers.DateTimeField(read_only=True, allow_null=True)
    attachments = serializers.SerializerMethodField(read_only=True)
    
    def get_attachments(self, obj):
        """دریافت فایل‌های پیوست"""
        attachments = obj.attachments.all()
        serializer = SupportMessageAttachmentSerializer(
            attachments,
            many=True,
            context=self.context
        )
        return serializer.data


class SupportMessageCreateSerializer(serializers.Serializer):
    """Serializer for Creating Support Messages"""
    teacher_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    message_text = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        """بررسی صحت داده‌ها"""
        message_text = data.get('message_text', '').strip()
        attachments = data.get('attachments', [])
        
        # حداقل یکی از پیام یا فایل باید وجود داشته باشد
        if not message_text and not attachments:
            raise serializers.ValidationError(
                _("Message text or attachment is required")
            )
        
        return data


# ===== Attendance Serializer =====
class AttendanceSerializer(serializers.Serializer):
    """Serializer for Attendance"""
    student_id = serializers.IntegerField()
    booking_id = serializers.IntegerField()
    status = serializers.CharField(max_length=10)
    created = serializers.BooleanField(read_only=True)


# ===== Teacher's Students & Classes APIs =====

class TeacherStudentSerializer(serializers.Serializer):
    """
    Serializer for Teacher's Students (from paid classes)
    
    Returns unique students who have paid classes with this teacher.
    Fields:
    - student_id: int - User ID
    - name: str - Student display name
    - username: str - Student username
    - selected_avatar: str - Avatar URL/path or null
    - total_classes: int - Total number of paid classes
    - average_attendance_percentage: float - Average attendance percentage (0-100)
    - last_paid_class_date: str - Date of last paid class (Jalali format)
    - total_paid_classes: int - Count of paid classes
    """
    student_id = serializers.IntegerField()
    name = serializers.CharField()
    username = serializers.CharField()
    selected_avatar = serializers.CharField(allow_null=True)
    total_classes = serializers.IntegerField()
    average_attendance_percentage = serializers.FloatField()
    last_paid_class_date = JalaliDateField()
    total_paid_classes = serializers.IntegerField()


class StudentPaidClassSerializer(serializers.Serializer):
    """
    Serializer for Student's Paid Classes
    
    Returns all classes with payment_status='paid' for a student.
    Uses same fields as ClassBookingSerializer for consistency.
    
    Fields:
    - id: int - ClassBooking ID
    - availability: int - TeacherAvailability ID
    - availability_date: str - Class date (Gregorian format)
    - availability_time: str - Time range (HH:MM - HH:MM)
    - teacher: int - Teacher user ID
    - teacher_name: str - Teacher name
    - student: int - Student user ID
    - student_name: str - Student name
    - subject: int - TeachingSubject ID
    - subject_title: str - TeachingSubject title
    - status: str - Class status (reserved/completed/cancelled/no_show)
    - status_display: str - Localized status display
    - price: str - Original price
    - discount_amount: str - Discount applied
    - final_price: str - Price after discount
    - created_at: str - Creation timestamp
    - updated_at: str - Last update timestamp
    """
    id = serializers.IntegerField()
    availability = serializers.IntegerField()
    availability_date = serializers.DateField()
    availability_time = serializers.CharField()
    teacher = serializers.IntegerField()
    teacher_name = serializers.CharField()
    student = serializers.IntegerField()
    student_name = serializers.CharField()
    subject = serializers.IntegerField()
    subject_title = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class TeacherDashboardSerializer(serializers.Serializer):
    """
    Serializer for Teacher Dashboard Summary
    
    Returns comprehensive dashboard metrics and statistics for teacher app.
    """
    # Overall Statistics
    total_students = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    total_paid_classes = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_student_attendance = serializers.FloatField()
    
    # Class Statistics
    completed_classes = serializers.IntegerField()
    pending_classes = serializers.IntegerField()
    cancelled_classes = serializers.IntegerField()
    
    # Payment Statistics
    total_paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_payment = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_class_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Recent Classes
    recent_classes = serializers.ListField(child=serializers.DictField())
    
    # Top Students
    top_students = serializers.ListField(child=serializers.DictField())
    
    # Teaching Subjects Summary
    subjects = serializers.ListField(child=serializers.DictField())
class StudentExerciseTemplateSerializer(serializers.Serializer):
    """
    Serializer for Student's Exercise Templates (CategoryField)
    
    Returns exercise templates from subjects where student has paid classes.
    Fields:
    - exercise_id: int - CategoryField ID
    - subject_id: int - TeachingSubject ID
    - subject_title: str - TeachingSubject title
    - field_id: int - Field (Question) ID
    - field_title: str - Field title
    - step: int - Exercise step
    - sort: int - Sort order
    - type: str - Exercise type (input/checkbox/radioButton)
    - is_conditional: bool - Is conditional exercise
    - answered: bool - Whether student has answered this question
    - answer_value: str - Student's answer value
    - answer_field_detail_id: int - Selected option ID (for choice questions)
    - answer_field_detail: dict - Details of selected option (id, title, second_title, image_path, is_correct)
    - is_correct: bool - Whether answer is correct
    """
    exercise_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    subject_title = serializers.CharField()
    field_id = serializers.IntegerField()
    field_title = serializers.CharField()
    step = serializers.IntegerField()
    sort = serializers.IntegerField()
    type = serializers.CharField()
    is_conditional = serializers.BooleanField()
    answered = serializers.BooleanField()
    answer_value = serializers.CharField(allow_null=True)
    answer_field_detail_id = serializers.IntegerField(allow_null=True)
    answer_field_detail = serializers.JSONField(allow_null=True)  # تغییر به JSONField
    is_correct = serializers.BooleanField(allow_null=True)
    correct_answer = serializers.JSONField(allow_null=True)


class StudentProfileDetailSerializer(serializers.Serializer):
    """
    Serializer for Student Profile Details (Teacher View)
    
    Returns comprehensive student profile information visible to their teacher.
    
    Fields:
    - student_id: int - User ID
    - name: str - Student display name
    - username: str - Student username
    - email: str - Email address (if available)
    - phone: str - Phone number (if available)
    - bio: str - Student bio/biography
    - gender: str - Gender (male/female/custom/prefer_not_to_say)
    - birth_date: str - Birth date in Jalali format
    - selected_avatar: str - Avatar image URL (if selected)
    - profile_photo_path: str - Profile photo URL (if available)
    - total_classes: int - Total paid classes with this teacher
    - average_attendance_percentage: float - Average attendance percentage (0-100)
    - last_class_date: str - Date of most recent paid class (Jalali format)
    - created_at: str - Account creation timestamp
    """
    student_id = serializers.IntegerField()
    name = serializers.CharField()
    username = serializers.CharField()
    email = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    bio = serializers.CharField(allow_null=True)
    gender = serializers.CharField(allow_null=True)
    birth_date = serializers.CharField(allow_null=True)
    selected_avatar = serializers.CharField(allow_null=True)
    profile_photo_path = serializers.CharField(allow_null=True)
    total_classes = serializers.IntegerField()
    average_attendance_percentage = serializers.FloatField()
    last_class_date = JalaliDateField(allow_null=True)
    created_at = serializers.DateTimeField()


# ============================================================================
# Package & Installment Serializers
# ============================================================================

class PackageInstallmentSerializer(serializers.Serializer):
    """
    Serializer for Package Installment
    نشان‌دهی قسط‌های پرداخت
    """
    id = serializers.IntegerField(read_only=True)
    installment_number = serializers.IntegerField(read_only=True)
    session_number = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        fields = ['id', 'installment_number', 'session_number', 'amount']


class PackageSerializer(serializers.ModelSerializer):
    """
    Serializer for Package with installments
    نشان‌دهی اطلاعات بسته آموزشی
    """
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    total_sessions = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'teacher_name', 'total_sessions', 
                  'total_price', 'has_installment', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class StudentPackagePaymentSerializer(serializers.Serializer):
    """
    Serializer for payment status of an installment
    نشان‌دهی وضعیت پرداخت یک قسط
    """
    id = serializers.IntegerField(read_only=True)
    installment_number = serializers.IntegerField()
    session_number = serializers.IntegerField()
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_amount = serializers.SerializerMethodField()
    payment_status = serializers.ChoiceField(
        choices=['pending', 'partial', 'paid', 'failed'],
        read_only=True
    )
    
    def get_remaining_amount(self, obj):
        return obj.get('amount_due', 0) - obj.get('amount_paid', 0)


class StudentPackageEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student Package Enrollment with payment summary
    نشان‌دهی ثبت‌نام دانش‌آموز در بسته
    """
    package_name = serializers.CharField(source='package.name', read_only=True)
    teacher_name = serializers.CharField(source='package.teacher.name', read_only=True)
    total_sessions = serializers.CharField(source='package.total_sessions', read_only=True)
    payment_summary = serializers.SerializerMethodField()
    pending_installments = serializers.SerializerMethodField()
    next_due = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentPackageEnrollment
        fields = ['id', 'package', 'package_name', 'teacher_name', 'status', 
                  'total_sessions', 'enrolled_at', 'payment_summary', 
                  'pending_installments', 'next_due']
        read_only_fields = ['enrolled_at']
    
    def get_payment_summary(self, obj):
        """
        دریافت خلاصه پرداخت از Service
        """
        from api.package_service import PackageInstallmentService
        summary = PackageInstallmentService.get_payment_summary(obj)
        return {
            'total_amount': str(summary['total_amount']),
            'paid_amount': str(summary['paid_amount']),
            'remaining_amount': str(summary['remaining_amount']),
            'total_installments': summary['total_installments'],
            'paid_installments': summary['paid_installments'],
            'pending_installments': summary['pending_installments'],
            'completion_percentage': summary['completion_percentage'],
        }
    
    def get_pending_installments(self, obj):
        """
        دریافت اقساط معلق از Service
        """
        from api.package_service import PackageInstallmentService
        return PackageInstallmentService.get_pending_installments(obj)
    
    def get_next_due(self, obj):
        """
        دریافت قسط بعدی از Service
        """
        from api.package_service import PackageInstallmentService
        return PackageInstallmentService.get_next_due_installment(obj)


class ProcessPackagePaymentSerializer(serializers.Serializer):
    """
    Serializer for processing package payment (Zibal)
    درخواست پرداخت قسط از طریق درگاه Zibal
    """
    enrollment_id = serializers.IntegerField(help_text="ID of student package enrollment")
    phone = serializers.CharField(max_length=11, help_text="شماره موبایل")
    description = serializers.CharField(
        max_length=255, 
        required=False,
        help_text="توضیح پرداخت"
    )
    
    def validate_phone(self, value):
        """
        بررسی اعتبار شماره تلفن
        """
        if not (value.isdigit() and len(value) >= 10):
            raise serializers.ValidationError(
                _("شماره موبایل معتبر نیست")
            )
        return value


class VerifyPackagePaymentSerializer(serializers.Serializer):
    """
    Serializer for verifying package payment (Zibal callback)
    تایید پرداخت بازگردانی شده از Zibal
    """
    status = serializers.IntegerField()
    order_id = serializers.IntegerField()
    track_id = serializers.CharField(max_length=100)
    ref_number = serializers.CharField(max_length=100)
    message = serializers.CharField(max_length=255, required=False)


# ============================================================================
# Teacher Package Management Serializers
# ============================================================================

class CreatePackageSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Package by teacher
    معلم می‌تواند بسه جدید برای اینجا بسازد
    """
    teaching_subjects = serializers.PrimaryKeyRelatedField(
        queryset=TeachingSubject.objects.all(),
        many=True,
        help_text="کلاس‌های آموزشی که این بسه مربوط به آن‌ها است"
    )
    
    class Meta:
        model = Package
        fields = [
            'name', 'description', 'image', 'total_sessions', 
            'total_price', 'teaching_subjects', 'has_installment', 'is_active'
        ]
    
    def validate_total_sessions(self, value):
        """
        total_sessions باید حداقل 1 باشد
        """
        if value < 1:
            raise serializers.ValidationError(
                _("تعداد جلسات باید حداقل 1 باشد")
            )
        return value
    
    def validate_total_price(self, value):
        """
        total_price باید بزرگتر از 0 باشد
        """
        if value <= 0:
            raise serializers.ValidationError(
                _("قیمت باید بزرگتر از 0 باشد")
            )
        return value
    
    def create(self, validated_data):
        """
        ایجاد پکیج جدید و ذخیره معلم
        """
        teaching_subjects = validated_data.pop('teaching_subjects')
        package = Package.objects.create(
            teacher=self.context['request'].user,
            **validated_data
        )
        package.teaching_subjects.set(teaching_subjects)
        return package


class TeacherPackageSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying packages created by teacher
    نمایش بسه‌های معلم
    """
    total_students_enrolled = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    total_paid_installments = serializers.SerializerMethodField()
    teaching_subject_names = serializers.StringRelatedField(
        source='teaching_subjects',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Package
        fields = [
            'id', 'name', 'description', 'image', 'total_sessions',
            'total_price', 'has_installment', 'is_active', 'created_at',
            'teaching_subject_names', 'total_students_enrolled',
            'total_revenue', 'total_paid_installments'
        ]
        read_only_fields = ['created_at']
    
    def get_total_students_enrolled(self, obj):
        """
        تعداد دانش‌آموزانی که در این بسه ثبت‌نام کرده‌اند
        """
        return obj.enrollments.filter(status='active').count()
    
    def get_total_revenue(self, obj):
        """
        کل درآمد از این بسه
        """
        from django.db.models import Sum
        total = obj.payments.filter(payment_status='paid').aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        return str(total)
    
    def get_total_paid_installments(self, obj):
        """
        تعداد اقساط پرداخت‌شده
        """
        return obj.payments.filter(payment_status='paid').count()


class CreatePackageInstallmentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating package installment by teacher
    ایجاد قسط جدید برای بسه
    """
    class Meta:
        model = PackageInstallment
        fields = ['session_number', 'amount']
    
    def validate_session_number(self, value):
        """
        session_number باید بین 1 و total_sessions بسه باشد
        """
        package = self.context.get('package')
        if package:
            if value < 1 or value > package.total_sessions:
                raise serializers.ValidationError(
                    _(f"شماره جلسه باید بین 1 و {package.total_sessions} باشد")
                )
        return value
    
    def validate(self, data):
        """
        بررسی اینکه session_number تکراری نباشد
        """
        package = self.context.get('package')
        if package:
            existing = PackageInstallment.objects.filter(
                package=package,
                session_number=data['session_number']
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    _("این شماره جلسه قبلاً برای این بسه تعریف شده است")
                )
        
        return data
    
    def validate_amount(self, value):
        """
        مبلغ قسط باید بزرگتر از 0 باشد
        """
        if value <= 0:
            raise serializers.ValidationError(
                _("مبلغ قسط باید بزرگتر از 0 باشد")
            )
        return value
    
    def create(self, validated_data):
        """
        ایجاد قسط و ثبت installment_number خودکار
        """
        package = self.context.get('package')
        if not package:
            raise serializers.ValidationError(
                _("بسه مشخص نشده است")
            )
        
        # محاسبه installment_number
        last_installment = PackageInstallment.objects.filter(
            package=package
        ).order_by('-installment_number').first()
        
        installment_number = (last_installment.installment_number + 1) if last_installment else 1
        
        installment = PackageInstallment.objects.create(
            package=package,
            installment_number=installment_number,
            **validated_data
        )
        return installment


class TeacherPackageInstallmentSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying package installments (teacher view)
    نمایش اقساط بسه برای معلم
    """
    paid_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    total_amount_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = PackageInstallment
        fields = [
            'id', 'installment_number', 'session_number', 'amount',
            'paid_count', 'pending_count', 'total_amount_paid'
        ]
        read_only_fields = ['installment_number']
    
    def get_paid_count(self, obj):
        """
        تعداد دانش‌آموزانی که این قسط را پرداخت کرده‌اند
        """
        return obj.payments.filter(payment_status='paid').count()
    
    def get_pending_count(self, obj):
        """
        تعداد دانش‌آموزانی که این قسط را پرداخت نکرده‌اند
        """
        return obj.payments.filter(
            payment_status__in=['pending', 'partial']
        ).count()
    
    def get_total_amount_paid(self, obj):
        """
        کل مبلغ پرداخت‌شده برای این قسط
        """
        from django.db.models import Sum
        total = obj.payments.filter(
            payment_status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        return str(total)
