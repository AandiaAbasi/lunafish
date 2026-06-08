from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ClassEnrollment, ClassMessage, ClassReaction, HandRaise, OnlineClass
from .utils import get_student_queryset, get_teacher_queryset
from classroom.models import ClassBooking

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField()
    lastName = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email', 'phone', 'role', 'firstName', 'lastName']
        read_only_fields = fields

    def get_firstName(self, obj):
        return obj.name or obj.first_name or obj.username

    def get_lastName(self, obj):
        return obj.last_name or ''


class OnlineClassSerializer(serializers.ModelSerializer):
    teacher = UserBasicSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=get_teacher_queryset(),
        source='teacher',
        write_only=True,
        required=False,
    )
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=ClassBooking.objects.all(),
        source='booking',
        write_only=True,
        required=True,
    )

    enrolled_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    actual_duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = OnlineClass
        fields = [
            'id',
            'title',
            'description',
            'teacher',
            'teacher_id',
            'booking_id',
            'scheduled_start',
            'scheduled_end',
            'actual_start',
            'actual_end',
            'room_id',
            'max_students',
            'allow_student_chat',
            'allow_student_reactions',
            'require_approval_to_join',
            'enable_recording',
            'status',
            'enrolled_count',
            'is_full',
            'duration_minutes',
            'actual_duration_minutes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'room_id',
            'status',
            'actual_start',
            'actual_end',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        teacher = attrs.get('teacher')
        booking = attrs.get('booking')
        request = self.context.get('request')

        if not self.instance and teacher is None and request and getattr(request.user, 'role', None) == 'teacher':
            attrs['teacher'] = request.user
            teacher = request.user

        if booking and teacher and hasattr(booking, 'teacher'):
            if booking.teacher != teacher:
                raise serializers.ValidationError({
                    'booking_id': 'این رزرو متعلق به این استاد نیست.'
                })

        return attrs



class ClassEnrollmentSerializer(serializers.ModelSerializer):
    student = UserBasicSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=get_student_queryset(),
        source='student',
        write_only=True,
        required=False,
    )

    class Meta:
        model = ClassEnrollment
        fields = [
            'id',
            'class_session',
            'student',
            'student_id',
            'can_unmute',
            'can_share_video',
            'can_share_screen',
            'is_moderator',
            'enrolled_at',
            'joined_at',
            'left_at',
            'is_active',
            'is_currently_joined',
        ]
        read_only_fields = ['id', 'class_session', 'enrolled_at', 'joined_at', 'left_at']


class HandRaiseSerializer(serializers.ModelSerializer):
    student = UserBasicSerializer(read_only=True)
    acknowledged_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = HandRaise
        fields = [
            'id',
            'class_session',
            'student',
            'raised_at',
            'lowered_at',
            'acknowledged_by',
            'acknowledged_at',
            'is_active',
            'is_acknowledged',
            'duration_seconds',
        ]
        read_only_fields = fields


class ClassMessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='recipient',
        write_only=True,
        required=False,
        allow_null=True,
    )
    deleted_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = ClassMessage
        fields = [
            'id',
            'class_session',
            'sender',
            'content',
            'is_private',
            'recipient',
            'recipient_id',
            'is_deleted',
            'deleted_by',
            'deleted_at',
            'created_at',
        ]
        read_only_fields = ['id', 'class_session', 'sender', 'is_deleted', 'deleted_by', 'deleted_at', 'created_at']

    def validate(self, attrs):
        is_private = attrs.get('is_private', getattr(self.instance, 'is_private', False))
        recipient = attrs.get('recipient', getattr(self.instance, 'recipient', None))
        if is_private and recipient is None:
            raise serializers.ValidationError({'recipient_id': 'This field is required for private messages.'})
        if not is_private:
            attrs['recipient'] = None
        return attrs


class ClassReactionSerializer(serializers.ModelSerializer):
    student = UserBasicSerializer(read_only=True)

    class Meta:
        model = ClassReaction
        fields = ['id', 'class_session', 'student', 'emoji', 'message', 'created_at']
        read_only_fields = ['id', 'class_session', 'student', 'created_at']
