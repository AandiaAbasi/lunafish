from django.contrib.auth import get_user_model
from rest_framework import serializers
from datetime import datetime
from .models import ClassAttachment, ClassEnrollment, ClassMessage, ClassReaction, HandRaise, OnlineClass, TeacherArchivedFile, TeacherArchiveFolder
from .utils import get_student_queryset, get_teacher_queryset
from classroom.models import ClassBooking
from recommendation.models import EnglishPlacementAssessment

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField()
    lastName = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'email', 'phone', 'role',
            'firstName', 'lastName', 'profile_photo',
        ]
        read_only_fields = fields

    def get_firstName(self, obj):
        return obj.name or obj.first_name or obj.username

    def get_lastName(self, obj):
        return obj.last_name or ''

    def get_profile_photo(self, obj):
        selected_avatar = getattr(obj, 'selected_avatar', None)
        avatar_image = getattr(selected_avatar, 'image', None) if selected_avatar else None
        if not avatar_image:
            return None

        try:
            url = avatar_image.url
        except (ValueError, AttributeError):
            return None

        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


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
        required=False,
        allow_null=True,
    )
    placement_assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=EnglishPlacementAssessment.objects.select_related('student', 'test'),
        source='placement_assessment',
        write_only=True,
        required=False,
        allow_null=True,
    )
    placement_assessment = serializers.SerializerMethodField()
    class_source = serializers.CharField(source='source_type', read_only=True)

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
            'placement_assessment_id',
            'placement_assessment',
            'class_source',
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
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
        }

    def get_placement_assessment(self, obj):
        assessment = getattr(obj, 'placement_assessment', None)
        if not assessment:
            return None

        level = assessment.final_level or assessment.suggested_level
        return {
            'id': assessment.id,
            'student': UserBasicSerializer(
                assessment.student,
                context=self.context,
            ).data,
            'suggested_level': assessment.suggested_level,
            'final_level': assessment.final_level,
            'display_level': level,
            'status': assessment.status,
            'status_display': assessment.get_status_display(),
            'source': assessment.source,
            'source_display': assessment.get_source_display(),
        }

    def validate(self, attrs):
        request = self.context.get('request')
        teacher = attrs.get('teacher')

        if not self.instance and teacher is None and request and getattr(request.user, 'role', None) == 'teacher':
            attrs['teacher'] = request.user
            teacher = request.user

        current_booking = getattr(self.instance, 'booking', None) if self.instance else None
        current_assessment = (
            getattr(self.instance, 'placement_assessment', None)
            if self.instance else None
        )
        booking = attrs.get('booking', current_booking)
        assessment = attrs.get('placement_assessment', current_assessment)

        if booking and assessment:
            raise serializers.ValidationError({
                'non_field_errors': [
                    'کلاس نمی‌تواند هم‌زمان به رزرو و نتیجه تعیین سطح متصل باشد.'
                ]
            })

        if not self.instance and not booking and not assessment:
            raise serializers.ValidationError({
                'non_field_errors': [
                    'برای ساخت کلاس باید booking_id یا placement_assessment_id ارسال شود.'
                ]
            })

        if booking and teacher and hasattr(booking, 'teacher') and booking.teacher != teacher:
            raise serializers.ValidationError({
                'booking_id': 'این رزرو متعلق به این استاد نیست.'
            })

        if assessment:
            if getattr(assessment.student, 'role', None) == 'teacher':
                raise serializers.ValidationError({
                    'placement_assessment_id': 'این نتیجه متعلق به دانش‌آموز نیست.'
                })

            display_level = assessment.final_level or assessment.suggested_level
            if not display_level:
                raise serializers.ValidationError({
                    'placement_assessment_id': 'برای این نتیجه هنوز سطح قابل استفاده‌ای ثبت نشده است.'
                })

            duplicate = OnlineClass.objects.filter(
                placement_assessment=assessment
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError({
                    'placement_assessment_id': 'برای این نتیجه تعیین سطح قبلاً کلاس ساخته شده است.'
                })

            if not attrs.get('title') and not (self.instance and self.instance.title):
                student_name = (
                    getattr(assessment.student, 'name', None)
                    or getattr(assessment.student, 'username', '')
                )
                attrs['title'] = f'کلاس سطح {str(display_level).replace("_", "-").upper()} - {student_name}'

            if not self.instance and 'max_students' not in attrs:
                attrs['max_students'] = 1

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


class TeacherArchiveFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherArchiveFolder
        fields = ['id', 'title', 'created_at']
        read_only_fields = ['id', 'created_at']


class TeacherArchivedFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    file_url = serializers.SerializerMethodField()
    folder_ids = serializers.PrimaryKeyRelatedField(
        source='folders',
        queryset=TeacherArchiveFolder.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = TeacherArchivedFile
        fields = [
            'id', 'file', 'file_url', 'title', 'folder_ids', 'original_filename', 'file_size',
            'content_type', 'created_at',
        ]
        read_only_fields = [
            'id', 'file_url', 'original_filename', 'file_size', 'content_type', 'created_at',
        ]

    def validate_folder_ids(self, folders):
        request = self.context.get('request')
        if request:
            for folder in folders:
                if folder.teacher_id != request.user.id or folder.is_deleted:
                    raise serializers.ValidationError('Folder not found.')
        return folders

    def get_file_url(self, obj):
        request = self.context.get('request')
        if not obj.file:
            return ''
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class ClassAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserBasicSerializer(read_only=True)
    deleted_by = UserBasicSerializer(read_only=True)
    file = serializers.FileField(write_only=True)

    class Meta:
        model = ClassAttachment
        fields = [
            'id',
            'class_session',
            'uploaded_by',
            'file',
            'original_filename',
            'title',
            'file_size',
            'content_type',
            'archive_file',
            'is_presented',
            'is_deleted',
            'deleted_by',
            'deleted_at',
            'created_at',
        ]
        read_only_fields = [
            'id', 'class_session', 'uploaded_by', 'original_filename', 'title', 'file_size', 'content_type',
            'archive_file', 'is_presented', 'is_deleted', 'deleted_by', 'deleted_at', 'created_at',
        ]


class ClassReactionSerializer(serializers.ModelSerializer):
    student = UserBasicSerializer(read_only=True)

    class Meta:
        model = ClassReaction
        fields = ['id', 'class_session', 'student', 'emoji', 'message', 'created_at']
        read_only_fields = ['id', 'class_session', 'student', 'created_at']


class NextOnlineClassSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    booking_id = serializers.UUIDField(source='booking.id', read_only=True)
    booking_start_at = serializers.SerializerMethodField()
    booking_end_at = serializers.SerializerMethodField()

    class Meta:
        model = OnlineClass
        fields = [
            'id', 'title', 'status',
            'scheduled_start', 'scheduled_end',
            'teacher', 'teacher_name',
            'room_id',
            'booking_id', 'booking_start_at', 'booking_end_at','description'
        ]

    def _to_iso_naive(self, date_obj, time_obj):
        return datetime.combine(date_obj, time_obj).strftime('%Y-%m-%dT%H:%M:%S')

    def get_booking_start_at(self, obj):
        bk = getattr(obj, 'booking', None)
        av = getattr(bk, 'availability', None) if bk else None
        return self._to_iso_naive(av.date, av.start_time) if av else None

    def get_booking_end_at(self, obj):
        bk = getattr(obj, 'booking', None)
        av = getattr(bk, 'availability', None) if bk else None
        return self._to_iso_naive(av.date, av.end_time) if av else None