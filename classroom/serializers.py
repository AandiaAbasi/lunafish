"""
Serializers برای مدل‌های پکیج و قسط‌بندی
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .models import (
    Package,
    PackageInstallment,
    StudentPackageEnrollment,
    StudentPackagePayment,
)
from .services import PackageInstallmentService


class PackageInstallmentSerializer(serializers.ModelSerializer):
    """Serializer برای اقساط پکیج"""
    
    class Meta:
        model = PackageInstallment
        fields = [
            'id', 'installment_number', 'amount', 'session_number',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PackageSerializer(serializers.ModelSerializer):
    """Serializer برای پکیج‌های آموزشی"""
    
    installments = PackageInstallmentSerializer(many=True, read_only=True)
    subjects = serializers.StringRelatedField(many=True, read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    installment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Package
        fields = [
            'id', 'title', 'description', 'cover_image', 'total_sessions',
            'total_price', 'has_installment', 'is_active', 'teacher_name',
            'subjects', 'installments', 'installment_count', 'created_at'
        ]
        read_only_fields = ['id', 'has_installment', 'created_at']
    
    def get_installment_count(self, obj):
        return obj.get_installment_count()


class StudentPackagePaymentSerializer(serializers.ModelSerializer):
    """Serializer برای پرداخت اقساط دانش‌آموز"""
    
    installment = PackageInstallmentSerializer(read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentPackagePayment
        fields = [
            'id', 'installment', 'amount_due', 'amount_paid',
            'payment_status', 'payment_ref', 'first_payment_date',
            'last_payment_date', 'completed_date', 'remaining_amount',
            'is_fully_paid', 'notes', 'created_at'
        ]
        read_only_fields = [
            'id', 'installment', 'first_payment_date', 'last_payment_date',
            'completed_date', 'created_at'
        ]
    
    def get_remaining_amount(self, obj):
        return obj.get_remaining_amount()
    
    def get_is_fully_paid(self, obj):
        return obj.is_fully_paid()


class StudentPackageEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer برای ثبت‌نام دانش‌آموز به پکیج"""
    
    package = PackageSerializer(read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    installment_payments = StudentPackagePaymentSerializer(many=True, read_only=True)
    payment_summary = serializers.SerializerMethodField()
    next_due_installment = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentPackageEnrollment
        fields = [
            'id', 'student_name', 'package', 'enrollment_date', 'status',
            'completed_sessions_count', 'installment_payments', 'notes',
            'payment_summary', 'next_due_installment', 'created_at'
        ]
        read_only_fields = [
            'id', 'enrollment_date', 'completed_sessions_count', 'created_at'
        ]
    
    def get_payment_summary(self, obj):
        return PackageInstallmentService.get_enrollment_payment_summary(obj)
    
    def get_next_due_installment(self, obj):
        result = PackageInstallmentService.get_next_due_installment(obj)
        if result:
            installment, payment = result
            return {
                'installment_number': installment.installment_number,
                'amount': str(payment.amount_due),
                'session_number': installment.session_number,
                'remaining_amount': str(payment.get_remaining_amount()),
            }
        return None


class ProcessPaymentSerializer(serializers.Serializer):
    """Serializer برای پردازش پرداخت قسط"""
    
    installment_id = serializers.IntegerField(required=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    payment_ref = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_amount_paid(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("مبلغ باید بیشتر از صفر باشد"))
        return value


class CheckSessionAccessSerializer(serializers.Serializer):
    """Serializer برای بررسی دسترسی به جلسه"""
    
    session_number = serializers.IntegerField(required=True, min_value=1)
    
    def validate_session_number(self, value):
        if value < 1:
            raise serializers.ValidationError(_("شماره جلسه باید حداقل ۱ باشد"))
        return value
