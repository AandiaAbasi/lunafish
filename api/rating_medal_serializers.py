"""
Serializers for Rating and Medal System
سریالایزرهای سیستم امتیاز، ستاره و مدال
"""
from rest_framework import serializers
from exercise.models import StudentRating, StudentMedal
from account.models import TeacherRating, User
from classroom.models import TeachingSubject
from django.utils.translation import gettext_lazy as _


# ========== Student Rating Serializers ==========

class StudentRatingCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای ایجاد امتیاز توسط معلم
    """
    class Meta:
        model = StudentRating
        fields = [
            'student', 'teachingsubject', 'order', 'rating_type',
            'score', 'stars', 'comment'
        ]
        read_only_fields = ['teacher']  # معلم خودکار از request تنظیم می‌شود
    
    def validate_score(self, value):
        if not (0 <= value <= 100):
            raise serializers.ValidationError(_("Score must be between 0 and 100"))
        return value
    
    def validate_stars(self, value):
        if not (0 <= value <= 5):
            raise serializers.ValidationError(_("Stars must be between 0 and 5"))
        return value
    
    def create(self, validated_data):
        # معلم از request گرفته می‌شود
        request = self.context.get('request')
        validated_data['teacher'] = request.user
        return super().create(validated_data)


class StudentRatingSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش امتیاز دانش‌آموز
    """
    teacher_name = serializers.CharField(source='teacher.name', read_only=True, allow_blank=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True, allow_blank=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    teachingsubject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    rating_type_display = serializers.CharField(source='get_rating_type_display', read_only=True)
    
    class Meta:
        model = StudentRating
        fields = [
            'id', 'teacher_name', 'teacher_username', 'student_name', 'student_username',
            'teachingsubject_title', 'order', 'rating_type', 'rating_type_display',
            'score', 'stars', 'comment', 'created_at'
        ]
        read_only_fields = [
            'id', 'teacher_name', 'teacher_username', 'student_name', 'student_username',
            'teachingsubject_title', 'rating_type_display', 'created_at'
        ]


class StudentRatingUpdateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای بروزرسانی امتیاز توسط معلم
    """
    class Meta:
        model = StudentRating
        fields = ['score', 'stars', 'comment', 'rating_type']


# ========== Student Medal Serializers ==========

class StudentMedalCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای اعطای مدال توسط معلم
    """
    class Meta:
        model = StudentMedal
        fields = [
            'student', 'teachingsubject', 'order', 'medal_type',
            'title', 'description', 'icon_url'
        ]
        read_only_fields = ['teacher']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['teacher'] = request.user
        return super().create(validated_data)


class StudentMedalSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش مدال دانش‌آموز
    """
    teacher_name = serializers.CharField(source='teacher.name', read_only=True, allow_blank=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True, allow_blank=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    teachingsubject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    medal_type_display = serializers.CharField(source='get_medal_type_display', read_only=True)
    
    class Meta:
        model = StudentMedal
        fields = [
            'id', 'teacher_name', 'teacher_username', 'student_name', 'student_username',
            'teachingsubject_title', 'order', 'medal_type', 'medal_type_display',
            'title', 'description', 'icon_url', 'created_at'
        ]
        read_only_fields = [
            'id', 'teacher_name', 'teacher_username', 'student_name', 'student_username',
            'teachingsubject_title', 'medal_type_display', 'created_at'
        ]


class StudentProfileMedalSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش مدال‌های دانش‌آموز در پروفایل
    """
    medal_type_display = serializers.CharField(source='get_medal_type_display', read_only=True)
    teachingsubject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    
    class Meta:
        model = StudentMedal
        fields = ['id', 'medal_type', 'medal_type_display', 'title', 'description', 
                  'icon_url', 'teachingsubject_title', 'created_at']
        read_only_fields = ['id', 'medal_type_display', 'teachingsubject_title', 'created_at']


# ========== Teacher Rating Serializers ==========

class TeacherRatingCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای اعطای امتیاز به معلم
    """
    class Meta:
        model = TeacherRating
        fields = ['teacher', 'stars', 'comment', 'is_anonymous']
        read_only_fields = ['rater', 'rater_type', 'is_verified']
    
    def validate_stars(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(_("Stars must be between 1 and 5"))
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # تعیین نوع ارائه‌دهنده (دانش‌آموز یا والدین)
        rater_type = 'student'
        if hasattr(request.user, 'parents'):
            # اگر والدینی برای این فرد وجود داشته باشد، والدین است
            rater_type = 'parent'
        
        validated_data['rater'] = request.user
        validated_data['rater_type'] = rater_type
        
        return super().create(validated_data)


class TeacherRatingSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش امتیاز معلم
    """
    rater_name = serializers.SerializerMethodField()
    rater_avatar = serializers.SerializerMethodField()
    rater_id = serializers.CharField(source='rater.id', read_only=True)
    rater_type_display = serializers.CharField(source='get_rater_type_display', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True, allow_blank=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    
    class Meta:
        model = TeacherRating
        fields = [
            'id', 'rater_name', 'rater_id', 'rater_avatar', 'rater_type', 'rater_type_display',
            'teacher_name', 'teacher_username', 'stars', 'comment',
            'is_anonymous', 'is_verified', 'created_at'
        ]
        read_only_fields = [
            'id', 'rater_name', 'rater_id', 'rater_avatar', 'rater_type_display', 'teacher_name',
            'teacher_username', 'is_verified', 'created_at'
        ]
    
    def get_rater_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.rater.name or obj.rater.username
    
    def get_rater_avatar(self, obj):
        if obj.is_anonymous:
            return None
        if obj.rater.selected_avatar and obj.rater.selected_avatar.image:
            return obj.rater.selected_avatar.image.url
        return None


class TeacherRatingStatsSerializer(serializers.Serializer):
    """
    خلاصه آمار امتیازات معلم
    """
    average_stars = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    by_rater_type = serializers.DictField()


class StudentRatingStatsSerializer(serializers.Serializer):
    """
    خلاصه آمار امتیازات دانش‌آموز
    """
    average_score = serializers.FloatField()
    average_stars = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    by_subject = serializers.ListField()


class StudentProfileRatingSerializer(serializers.Serializer):
    """
    سریالایزر برای نمایش امتیازات دانش‌آموز در پروفایل
    """
    rating_stats = StudentRatingStatsSerializer()
    total_medals = serializers.IntegerField()
    medals_by_type = serializers.DictField()
    recent_ratings = StudentRatingSerializer(many=True)
    recent_medals = StudentMedalSerializer(many=True)


class ExerciseRatingDetailSerializer(serializers.Serializer):
    """
    جزئیات امتیاز و مدال یک تمرین
    """
    exercise_id = serializers.IntegerField()
    has_rating = serializers.BooleanField()
    has_medals = serializers.BooleanField()
    rating = StudentRatingSerializer(allow_null=True)
    medals = StudentMedalSerializer(many=True)
