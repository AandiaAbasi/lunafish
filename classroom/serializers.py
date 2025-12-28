from rest_framework import serializers
from .models import (
    ClassLevel, Language, Course, Lesson, LessonEnrollment,
    LessonMaterial, Whiteboard, Quiz, QuizQuestion, QuizAnswer,
    StudentQuizAttempt, StudentQuestionResponse, Attendance,
    Badge, StudentBadge, StudentProgress, AgoraToken
)
from account.models import User


class ClassLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassLevel
        fields = ['id', 'name', 'description', 'order', 'created_at', 'updated_at']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code', 'created_at', 'updated_at']


class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'teacher', 'teacher_name', 'title', 'description',
            'language', 'language_name', 'level', 'level_name',
            'max_students', 'duration_minutes', 'hourly_rate',
            'cover_image', 'is_active', 'created_at', 'updated_at'
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'teacher', 'teacher_name', 'title', 'description',
            'language', 'language_name', 'level', 'level_name',
            'max_students', 'duration_minutes', 'hourly_rate',
            'cover_image', 'is_active', 'lessons_count',
            'created_at', 'updated_at'
        ]
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()


class LessonListSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='course.teacher.username', read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'course_title', 'teacher_name', 'title',
            'scheduled_at', 'status', 'started_at', 'ended_at',
            'is_recorded', 'recording_url', 'created_at', 'updated_at'
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'title', 'description', 'scheduled_at',
            'agora_channel_id', 'agora_channel_name', 'status',
            'started_at', 'ended_at', 'duration_minutes',
            'recording_url', 'is_recorded', 'teacher_notes',
            'created_at', 'updated_at'
        ]
    
    def get_duration_minutes(self, obj):
        return obj.get_duration_minutes()


class LessonEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    attendance_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonEnrollment
        fields = [
            'id', 'lesson', 'lesson_title', 'student', 'student_name',
            'role', 'agora_uid', 'joined_at', 'left_at',
            'status', 'paid', 'notes', 'attendance_duration',
            'created_at', 'updated_at'
        ]
    
    def get_attendance_duration(self, obj):
        return obj.get_attendance_duration_minutes()


class LessonMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonMaterial
        fields = [
            'id', 'lesson', 'title', 'material_type',
            'file', 'external_link', 'description', 'order',
            'created_at', 'updated_at'
        ]


class WhiteboardSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Whiteboard
        fields = [
            'id', 'lesson', 'lesson_title', 'content', 'is_locked',
            'last_modified_by', 'last_modified_at'
        ]


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'question', 'answer_text', 'answer_image', 'is_correct', 'order']


class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'quiz', 'question_text',
            'question_image', 'question_audio', 'question_video',
            'question_type', 'points', 'order', 
            'explanation', 'explanation_image', 'explanation_video',
            'answers', 'created_at', 'updated_at'
        ]


class QuizListSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'lesson', 'lesson_title', 'title', 'description',
            'difficulty', 'time_limit_minutes', 'passing_score',
            'max_attempts', 'show_results_after_submit', 'allow_review',
            'shuffle_questions', 'shuffle_answers', 'submission_method',
            'show_before_lesson', 'show_during_lesson',
            'show_after_lesson', 'is_active', 'created_at', 'updated_at'
        ]


class QuizDetailSerializer(serializers.ModelSerializer):
    lesson = LessonListSerializer(read_only=True)
    questions = QuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'lesson', 'title', 'description', 'difficulty',
            'time_limit_minutes', 'passing_score', 'max_attempts',
            'show_results_after_submit', 'allow_review',
            'shuffle_questions', 'shuffle_answers', 'submission_method',
            'show_before_lesson', 'show_during_lesson',
            'show_after_lesson', 'is_active', 'questions',
            'created_at', 'updated_at'
        ]


class StudentQuestionResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    selected_answer_text = serializers.CharField(source='selected_answer.answer_text', read_only=True)
    
    class Meta:
        model = StudentQuestionResponse
        fields = [
            'id', 'attempt', 'question', 'question_text',
            'selected_answer', 'selected_answer_text', 'text_response',
            'response_time_seconds', 'is_correct', 'points_earned',
            'created_at', 'updated_at'
        ]


class StudentQuizAttemptListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = StudentQuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'student', 'student_name',
            'attempt_number', 'started_at', 'submitted_at', 'time_taken_minutes',
            'submission_status', 'is_submitted', 'submission_method',
            'score', 'earned_points', 'total_points', 'passed',
            'created_at', 'updated_at'
        ]


class StudentQuizAttemptDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    quiz = QuizDetailSerializer(read_only=True)
    responses = StudentQuestionResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentQuizAttempt
        fields = [
            'id', 'quiz', 'student', 'student_name', 'lesson_enrollment',
            'attempt_number', 'started_at', 'submitted_at', 'time_taken_minutes',
            'submission_status', 'is_submitted', 'submission_method',
            'score', 'earned_points', 'total_points', 'passed',
            'responses', 'created_at', 'updated_at'
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'lesson', 'lesson_title', 'student', 'student_name',
            'status', 'expected_at', 'actual_joined_at', 'left_at',
            'minutes_attended', 'notes', 'created_at', 'updated_at'
        ]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'criteria_type', 'criteria_value', 'created_at', 'updated_at'
        ]


class StudentBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = StudentBadge
        fields = [
            'id', 'student', 'student_name', 'badge',
            'earned_at', 'created_at', 'updated_at'
        ]


class StudentProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    badges = StudentBadgeSerializer(source='student.badges', many=True, read_only=True)
    
    class Meta:
        model = StudentProgress
        fields = [
            'id', 'student', 'student_name', 'course', 'course_title',
            'total_lessons', 'lessons_completed', 'lessons_attended',
            'attendance_percentage', 'average_quiz_score', 'total_points',
            'badges_earned', 'badges', 'last_updated', 'created_at', 'updated_at'
        ]


class AgoraTokenSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = AgoraToken
        fields = [
            'id', 'lesson', 'lesson_title', 'user', 'user_name',
            'token', 'privilege', 'generated_at', 'expires_at',
            'is_revoked', 'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['token', 'generated_at', 'is_revoked']
    
    def get_is_valid(self, obj):
        return obj.is_valid()
