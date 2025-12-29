from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Exercise, Question, QuestionOption, ExerciseChoice, StudentExerciseChoice,
    StudentExerciseAttempt, StudentQuestionAnswer
)


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Serializer for Question Options"""
    
    class Meta:
        model = QuestionOption
        fields = [
            'id', 'order', 'text', 'image', 'audio',
            'is_correct', 'explanation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # پنهان کردن پاسخ صحیح از دانش‌آموزان
        }


class QuestionOptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for Question Options (بدون نمایش پاسخ صحیح)"""
    
    class Meta:
        model = QuestionOption
        fields = [
            'id', 'order', 'text', 'image', 'audio', 'explanation'
        ]
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Questions with Options"""
    options = QuestionOptionDetailSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'order', 'question_type', 'question_type_display',
            'text', 'image', 'audio', 'video', 'explanation', 'points',
            'is_required', 'options', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed Serializer for Question (برای معلمان)"""
    options = QuestionOptionSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'exercise', 'order', 'question_type', 'question_type_display',
            'text', 'image', 'audio', 'video', 'explanation', 'points',
            'is_required', 'options', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseListSerializer(serializers.ModelSerializer):
    """List Serializer for Exercises"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    exercise_type_display = serializers.CharField(source='get_exercise_type_display', read_only=True)
    question_count = serializers.SerializerMethodField()
    optional_question_count = serializers.SerializerMethodField()
    parent_exercise_title = serializers.CharField(source='parent_exercise.title', read_only=True, required=False)
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'teacher', 'teacher_name', 'subject', 'subject_title',
            'title', 'description', 'exercise_type', 'exercise_type_display',
            'difficulty', 'difficulty_display',
            'duration_minutes', 'total_points', 'pass_score', 'is_published',
            'is_optional', 'parent_exercise', 'parent_exercise_title', 'variant_order',
            'question_count', 'optional_question_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_question_count(self, obj):
        return obj.get_question_count()
    
    def get_optional_question_count(self, obj):
        return obj.get_optional_question_count()


class ExerciseDetailSerializer(serializers.ModelSerializer):
    """Detailed Serializer for Exercise"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    exercise_type_display = serializers.CharField(source='get_exercise_type_display', read_only=True)
    questions = QuestionDetailSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    optional_question_count = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'teacher', 'teacher_name', 'subject', 'subject_title',
            'title', 'description', 'exercise_type', 'exercise_type_display',
            'difficulty', 'difficulty_display',
            'duration_minutes', 'total_points', 'pass_score', 'is_published',
            'is_optional', 'parent_exercise', 'variant_order',
            'question_count', 'optional_question_count', 'variants', 'questions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'questions']
    
    def get_question_count(self, obj):
        return obj.get_question_count()
    
    def get_optional_question_count(self, obj):
        return obj.get_optional_question_count()
    
    def get_variants(self, obj):
        """نسخه‌های این تمرین"""
        if obj.parent_exercise:
            return None
        variants = obj.get_variants()
        if variants.exists():
            return ExerciseListSerializer(variants, many=True).data
        return None


class StudentQuestionAnswerSerializer(serializers.ModelSerializer):
    """Serializer for Student Answers"""
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_option_text = serializers.CharField(source='selected_option.text', read_only=True)
    
    class Meta:
        model = StudentQuestionAnswer
        fields = [
            'id', 'question', 'question_text', 'answer_text',
            'selected_option', 'selected_option_text', 'answer_file',
            'is_correct', 'points_earned', 'teacher_feedback',
            'answered_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_correct', 'points_earned', 'teacher_feedback', 'created_at', 'updated_at']


class StudentExerciseAttemptSerializer(serializers.ModelSerializer):
    """Serializer for Student Exercise Attempts"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    question_answers = StudentQuestionAnswerSerializer(many=True, read_only=True)
    pass_status = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentExerciseAttempt
        fields = [
            'id', 'student', 'student_name', 'exercise', 'exercise_title',
            'status', 'status_display', 'score', 'percentage', 'pass_status',
            'started_at', 'submitted_at', 'graded_at', 'teacher_notes',
            'question_answers', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student', 'exercise', 'started_at', 'submitted_at',
            'graded_at', 'created_at', 'updated_at', 'question_answers'
        ]
    
    def get_pass_status(self, obj):
        result = obj.pass_exercise()
        if result is None:
            return 'not_graded'
        return 'passed' if result else 'failed'


class ExerciseChoiceSerializer(serializers.ModelSerializer):
    """Serializer for Exercise Choice Groups"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    choice_type_display = serializers.CharField(source='get_choice_type_display', read_only=True)
    exercise_count = serializers.SerializerMethodField()
    exercises_detail = ExerciseListSerializer(source='exercises', many=True, read_only=True)
    
    class Meta:
        model = ExerciseChoice
        fields = [
            'id', 'teacher', 'teacher_name', 'subject', 'subject_title',
            'title', 'description', 'choice_type', 'choice_type_display',
            'exercises', 'exercises_detail', 'required_choices', 'exercise_count', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'exercises_detail']
    
    def get_exercise_count(self, obj):
        return obj.get_exercise_count()


class StudentExerciseChoiceSerializer(serializers.ModelSerializer):
    """Serializer for Student Exercise Choices"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    choice_group_title = serializers.CharField(source='exercise_choice_group.title', read_only=True)
    selected_exercises_detail = ExerciseListSerializer(
        source='selected_exercises', many=True, read_only=True
    )
    
    class Meta:
        model = StudentExerciseChoice
        fields = [
            'id', 'student', 'student_name', 'exercise_choice_group',
            'choice_group_title', 'selected_exercises', 'selected_exercises_detail',
            'confirmed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'confirmed_at', 'created_at', 'updated_at', 'selected_exercises_detail']
