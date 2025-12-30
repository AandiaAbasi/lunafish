"""
Serializers for Classroom App - Time Slots, Bookings, Revenue, Transactions
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from classroom.models import (
    TeacherAvailability, TeachingSubject, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings
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
    
    class Meta:
        model = TeacherAvailability
        fields = [
            'id', 'teacher', 'teacher_name', 'date', 'start_time', 'end_time',
            'price', 'discount_price', 'is_available', 'is_booked', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BulkTeacherAvailabilitySerializer(serializers.ListSerializer):
    """Serializer for bulk creating TeacherAvailability"""
    def create(self, validated_data):
        availabilities = [
            TeacherAvailability(**item) for item in validated_data
        ]
        return TeacherAvailability.objects.bulk_create(availabilities)


class TeachingSubjectSerializer(serializers.ModelSerializer):
    """Serializer for TeachingSubject"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = TeachingSubject
        fields = [
            'id', 'teacher', 'teacher_name', 'title', 'description', 'level', 'level_display',
            'cover_image', 'demo_video', 'min_age', 'max_age', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """اضافه کردن تعداد student‌ها و rating"""
        data = super().to_representation(instance)
        data['students_count'] = instance.bookings.filter(status='completed').count()
        return data
        

class ClassBookingSerializer(serializers.ModelSerializer):
    """Serializer for ClassBooking"""
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ClassBooking
        fields = [
            'id', 'availability', 'teacher', 'teacher_name', 'student', 'student_name',
            'subject', 'subject_title', 'status', 'status_display', 'price',
            'discount_code', 'discount_amount', 'final_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'teacher', 'teacher_name', 'amount', 'revenues',
            'payment_method', 'payment_method_display', 'account_info',
            'transaction_id', 'status', 'status_display', 'notes', 'admin_notes',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
