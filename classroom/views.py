"""
API Views برای پکیج‌ها و قسط‌بندی

Endpoints:
- POST /api/packages/ - ایجاد پکیج
- GET /api/packages/ - لیست پکیج‌ها
- GET /api/packages/{id}/ - جزئیات پکیج
- POST /api/enrollments/ - ثبت‌نام دانش‌آموز
- GET /api/enrollments/ - لیست ثبت‌نام‌های دانش‌آموز
- GET /api/enrollments/{id}/ - جزئیات ثبت‌نام
- POST /api/enrollments/{id}/process-payment/ - پردازش پرداخت
- GET /api/enrollments/{id}/check-session-access/ - بررسی دسترسی به جلسه
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .models import (
    Package,
    StudentPackageEnrollment,
    StudentPackagePayment,
)
from .serializers import (
    PackageSerializer,
    StudentPackageEnrollmentSerializer,
    StudentPackagePaymentSerializer,
    ProcessPaymentSerializer,
    CheckSessionAccessSerializer,
)
from .services import PackageInstallmentService, PackageService


class PackageViewSet(viewsets.ModelViewSet):
    """
    API برای مدیریت پکیج‌های آموزشی
    
    Endpoints:
    - GET /api/packages/ - لیست پکیج‌ها
    - POST /api/packages/ - ایجاد پکیج
    - GET /api/packages/{id}/ - جزئیات پکیج
    - PUT /api/packages/{id}/ - ویرایش پکیج
    - DELETE /api/packages/{id}/ - حذف پکیج
    """
    
    queryset = Package.objects.filter(is_active=True)
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن پکیج‌ها"""
        user = self.request.user
        
        # معلمان تنها پکیج‌های خود را می‌بینند
        if user.role == 'teacher':
            return Package.objects.filter(teacher=user, is_active=True)
        
        # دانش‌آموزان تمام پکیج‌های فعال را می‌بینند
        return Package.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """تنظیم معلم برای پکیج جدید"""
        # تنها معلمان می‌توانند پکیج بسازند
        if self.request.user.role != 'teacher':
            raise PermissionError(_("فقط معلمان می‌توانند پکیج بسازند"))
        
        serializer.save(teacher=self.request.user)
    
    @action(detail=True, methods=['post'])
    def validate_installments(self, request, pk=None):
        """
        بررسی صحت مجموع اقساط
        
        POST /api/packages/{id}/validate_installments/
        """
        package = self.get_object()
        is_valid, message = PackageService.validate_installment_total(package)
        
        return Response({
            'is_valid': is_valid,
            'message': str(message),
            'total_price': str(package.total_price),
            'total_installments': sum(
                inst.amount for inst in package.installments.all()
            ),
        })


class StudentPackageEnrollmentViewSet(viewsets.ModelViewSet):
    """
    API برای مدیریت ثبت‌نام دانش‌آموزان به پکیج‌ها
    
    Endpoints:
    - GET /api/enrollments/ - لیست ثبت‌نام‌ها
    - POST /api/enrollments/ - ثبت‌نام جدید
    - GET /api/enrollments/{id}/ - جزئیات ثبت‌نام
    - POST /api/enrollments/{id}/process-payment/ - پردازش پرداخت
    - GET /api/enrollments/{id}/check-session-access/ - بررسی دسترسی
    - GET /api/enrollments/{id}/payment-summary/ - خلاصه پرداخت‌ها
    """
    
    queryset = StudentPackageEnrollment.objects.all()
    serializer_class = StudentPackageEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن ثبت‌نام‌ها"""
        user = self.request.user
        
        # دانش‌آموزان تنها ثبت‌نام‌های خود را می‌بینند
        if user.role == 'user':
            return StudentPackageEnrollment.objects.filter(student=user)
        
        # معلمان می‌توانند ثبت‌نام‌های دانش‌آموزان پکیج‌های خود را ببینند
        if user.role == 'teacher':
            return StudentPackageEnrollment.objects.filter(
                package__teacher=user
            )
        
        return StudentPackageEnrollment.objects.all()
    
    def perform_create(self, serializer):
        """تنظیم دانش‌آموز برای ثبت‌نام جدید"""
        # تنها دانش‌آموزان می‌توانند ثبت‌نام کنند
        if self.request.user.role != 'user':
            raise PermissionError(_("فقط دانش‌آموزان می‌توانند ثبت‌نام کنند"))
        
        serializer.save(student=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """
        پردازش پرداخت برای یک قسط
        
        POST /api/enrollments/{id}/process-payment/
        
        Body:
        {
            "installment_id": 1,
            "amount_paid": 200000,
            "payment_ref": "ref_123"
        }
        
        Response:
        {
            "success": true,
            "message": "پرداخت با موفقیت ثبت شد",
            "payment": {...}
        }
        """
        enrollment = self.get_object()
        serializer = ProcessPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # پردازش پرداخت
        success, message, payment = PackageInstallmentService.process_installment_payment(
            enrollment,
            serializer.validated_data['installment_id'],
            serializer.validated_data['amount_paid'],
            serializer.validated_data.get('payment_ref', '')
        )
        
        if success:
            return Response({
                'success': True,
                'message': str(message),
                'payment': StudentPackagePaymentSerializer(payment).data,
            })
        else:
            return Response(
                {'success': False, 'message': str(message)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def check_session_access(self, request, pk=None):
        """
        بررسی دسترسی دانش‌آموز به یک جلسه
        
        POST /api/enrollments/{id}/check-session-access/
        
        Body:
        {
            "session_number": 5
        }
        
        Response:
        {
            "can_access": true,
            "message": "دسترسی مجاز است",
            "session_number": 5
        }
        """
        enrollment = self.get_object()
        serializer = CheckSessionAccessSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی دسترسی
        can_access, message = PackageInstallmentService.can_student_attend_session(
            enrollment,
            serializer.validated_data['session_number']
        )
        
        return Response({
            'can_access': can_access,
            'message': str(message),
            'session_number': serializer.validated_data['session_number'],
        })
    
    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        """
        دریافت خلاصه وضعیت پرداخت‌ها
        
        GET /api/enrollments/{id}/payment-summary/
        
        Response:
        {
            "total_amount": 600000,
            "paid_amount": 200000,
            "remaining_amount": 400000,
            "total_installments": 3,
            "paid_installments": 1,
            "pending_installments": 2,
            "completion_percentage": 33.33
        }
        """
        enrollment = self.get_object()
        summary = PackageInstallmentService.get_enrollment_payment_summary(enrollment)
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def unpaid_installments(self, request, pk=None):
        """
        دریافت لیست اقساط پرداخت‌نشده
        
        GET /api/enrollments/{id}/unpaid_installments/
        """
        enrollment = self.get_object()
        unpaid = PackageInstallmentService.get_all_unpaid_installments(enrollment)
        
        data = []
        for installment, payment in unpaid:
            data.append({
                'installment': {
                    'id': installment.id,
                    'installment_number': installment.installment_number,
                    'amount': str(installment.amount),
                    'session_number': installment.session_number,
                },
                'payment': StudentPackagePaymentSerializer(payment).data,
            })
        
        return Response(data)


class StudentPackagePaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API برای مشاهده تراکنش‌های پرداخت قسط‌ها (فقط خواندن)
    
    Endpoints:
    - GET /api/payments/ - لیست پرداخت‌ها
    - GET /api/payments/{id}/ - جزئیات پرداخت
    """
    
    serializer_class = StudentPackagePaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن پرداخت‌ها"""
        user = self.request.user
        
        # دانش‌آموزان تنها پرداخت‌های خود را می‌بینند
        if user.role == 'user':
            return StudentPackagePayment.objects.filter(
                enrollment__student=user
            )
        
        # معلمان می‌توانند پرداخت‌های دانش‌آموزان پکیج‌های خود را ببینند
        if user.role == 'teacher':
            return StudentPackagePayment.objects.filter(
                enrollment__package__teacher=user
            )
        
        return StudentPackagePayment.objects.all()
