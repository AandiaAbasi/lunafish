from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

# class CourseSerializer(serializers.ModelSerializer):
#     teacher_name = serializers.CharField(source='subject.teacher.name', read_only=True)
#     final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     subject_title = serializers.CharField(source='subject.title', read_only=True)
#     cover_image = serializers.ImageField(required=False, allow_null=True)

#     class Meta:
#         model = Course
#         fields = [
#             'id', 'subject', 'subject_title', 'title', 'description',
#             'price', 'discounted_price', 'final_price', 'session_count',
#             'is_active', 'teacher_name', 'cover_image'
#         ]
#         read_only_fields = ['id']

#     def validate_subject(self, value):
#         """فقط subject‌های مربوط به معلم لاگین‌شده"""
#         request = self.context['request']
#         if value.teacher != request.user:
#             raise serializers.ValidationError("این موضوع متعلق به شما نیست.")
#         return value

#     def validate(self, attrs):
#         session_count = attrs.get('session_count', 0)
#         if session_count < 1:
#             raise serializers.ValidationError("تعداد جلسات باید حداقل ۱ باشد.")
#         return attrs

#     def validate_cover_image(self, image):
#         """اختیاری: محدودیت حجم فایل (۲ مگابایت)"""
#         if image and image.size > 2 * 1024 * 1024:
#             raise serializers.ValidationError("حداکثر سایز تصویر ۲ مگابایت است.")
#         return image


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='subject.teacher.name', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    
    # برای خواندن: URL کامل
    cover_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'subject', 'subject_title', 'title', 'description',
            'price', 'discounted_price', 'final_price', 'session_count',
            'is_active', 'teacher_name', 'cover_image', 'cover_image_url','status', 'rejection_reason'
        ]
        read_only_fields = ['id', 'final_price', 'teacher_name', 'subject_title']
        extra_kwargs = {
            'cover_image': {'write_only': False, 'required': False}
        }

    def get_cover_image_url(self, obj):
        """برای نمایش URL کامل عکس"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None

    def validate_subject(self, value):
        request = self.context['request']
        if value.teacher != request.user:
            raise serializers.ValidationError("این موضوع متعلق به شما نیست.")
        return value

    def validate(self, attrs):
        session_count = attrs.get('session_count', 0)
        if session_count < 1:
            raise serializers.ValidationError("تعداد جلسات باید حداقل ۱ باشد.")
        return attrs

    def validate_cover_image(self, image):
        """اعتبارسنجی سایز فایل"""
        if image and image.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("حداکثر سایز تصویر ۲ مگابایت است.")
        return image


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='course.subject.teacher.name', read_only=True)
    paid_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'course', 'course_title', 'teacher_name',
                  'paid_amount', 'payment_status', 'payment_ref', 'paid_at']
        read_only_fields = ['id', 'paid_amount', 'payment_status', 'payment_ref', 'paid_at']
        

class AssignTimeToEnrollmentSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    availability_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="لیست IDهای TeacherAvailability که می‌خواهید اختصاص دهید"
    )
    
    def validate_enrollment_id(self, value):
        try:
            enrollment = CourseEnrollment.objects.get(id=value, payment_status='paid')
        except CourseEnrollment.DoesNotExist:
            raise serializers.ValidationError("ثبت‌نام معتبر یافت نشد")
        return value
    
    def validate(self, data):
        enrollment = CourseEnrollment.objects.get(id=data['enrollment_id'])
        availability_ids = data['availability_ids']
        
        # بررسی تعداد تایم‌های قبلاً اختصاص داده شده
        assigned_count = enrollment.bookings.count()
        new_count = len(availability_ids)
        total_count = assigned_count + new_count
        
        # بررسی اینکه از تعداد جلسات دوره تجاوز نکند
        if total_count > enrollment.course.session_count:
            remaining = enrollment.course.session_count - assigned_count
            raise serializers.ValidationError(
                f"فقط {remaining} جلسه باقی مانده است. نمی‌توانید {new_count} تایم اختصاص دهید"
            )
        
        # بررسی اینکه تایم‌ها متعلق به معلم باشند و آزاد باشند
        availabilities = TeacherAvailability.objects.filter(
            id__in=availability_ids,
            teacher=enrollment.course.subject.teacher,
            is_booked=False,
            is_available=True,
            is_expired=False
        )
        
        if availabilities.count() != len(availability_ids):
            raise serializers.ValidationError("برخی تایم‌ها معتبر نیستند یا رزرو شده‌اند")
        
        data['enrollment'] = enrollment
        data['availabilities'] = list(availabilities)
        data['assigned_count'] = assigned_count
        data['total_count'] = total_count
        return data
        
        
class CourseEnrollmentWithBookingsSerializer(CourseEnrollmentSerializer):
    bookings = serializers.SerializerMethodField()
    
    class Meta(CourseEnrollmentSerializer.Meta):
        fields = CourseEnrollmentSerializer.Meta.fields + ['bookings']
    
    def get_bookings(self, obj):
        bookings = ClassBooking.objects.filter(
            enrollment=obj
        ).select_related('availability', 'subject', 'teacher', 'student').order_by('availability__start_time')
        
        return [{
            'id': booking.id,
            'availability': booking.availability.id,
            'availability_date': booking.availability.date,
            'availability_time': f"{booking.availability.start_time.strftime('%H:%M')} - {booking.availability.end_time.strftime('%H:%M')}",
            'teacher': booking.teacher.id,
            'teacher_name': booking.teacher.name,
            'student': booking.student.id,
            'student_name': booking.student.name,
            'subject': booking.subject.id,
            'subject_title': booking.subject.title,
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'price': str(booking.price),
            'discount_amount': str(booking.discount_amount),
            'final_price': str(booking.final_price),
            'created_at': booking.created_at,
            'updated_at': booking.updated_at,
        } for booking in bookings]
        
        
class CourseEnrollmentWithBookingsListSerializer(CourseEnrollmentSerializer):
    session_count = serializers.IntegerField(source='course.session_count', read_only=True)
    assigned_sessions = serializers.SerializerMethodField()
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta(CourseEnrollmentSerializer.Meta):
        fields = CourseEnrollmentSerializer.Meta.fields + ['session_count', 'assigned_sessions', 'student_name']
    
    def get_assigned_sessions(self, obj):
        return obj.bookings.count()

        