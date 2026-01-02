"""
Serializers for Exercise App - Questions, Exams, and Answers
Supports: Typing, Multiple Choice (Checkbox), Single Choice (RadioButton)

TWO-STEP CREATION FLOW:
1. Create Field (multipart) - NO details
2. Create FieldDetails (JSON) - uses Field ID
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from exercise.models import Field, FieldDetail, CategoryField, Order, OrderDetail
from classroom.models import TeachingSubject
import jdatetime
from datetime import datetime, date
import os
import uuid
from django.core.files.storage import default_storage


# ==================== STEP 1: Create Field (Multipart, NO Details) ====================

class FieldCreateSerializer(serializers.ModelSerializer):
    """
    STEP 1: Create Field with file uploads (multipart/form-data)
    
    Does NOT handle details at all - details are created in Step 2.
    Accepts file uploads for image, audio, video.
    """
    # Override model CharField to accept file uploads
    image_path = serializers.FileField(required=False, allow_null=True, write_only=True)
    audio_path = serializers.FileField(required=False, allow_null=True, write_only=True)
    video_path = serializers.FileField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'sort',
            'guide', 'des', 'image_path', 'audio_path', 'video_path'
        ]
        read_only_fields = ['id']
    
    def validate_type(self, value):
        """Validate question type"""
        valid_types = ['input', 'checkbox', 'radioButton']
        if value not in valid_types:
            raise serializers.ValidationError(
                _('نوع سوال باید یکی از این مقادیر باشد: input, checkbox, radioButton')
            )
        return value
    
    def create(self, validated_data):
        """Create Field and handle file uploads"""
        # Handle file uploads
        image_file = validated_data.pop('image_path', None)
        if image_file:
            ext = os.path.splitext(image_file.name)[1]
            filename = f"exercise_images/{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(filename, image_file)
            validated_data['image_path'] = saved_path
        
        audio_file = validated_data.pop('audio_path', None)
        if audio_file:
            ext = os.path.splitext(audio_file.name)[1]
            filename = f"exercise_audio/{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(filename, audio_file)
            validated_data['audio_path'] = saved_path
        
        video_file = validated_data.pop('video_path', None)
        if video_file:
            ext = os.path.splitext(video_file.name)[1]
            filename = f"exercise_videos/{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(filename, video_file)
            validated_data['video_path'] = saved_path
        
        # Set teacher if available in context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                Field._meta.get_field('teacher')
                validated_data['teacher'] = request.user
            except Exception:
                pass
        
        return Field.objects.create(**validated_data)


# ==================== STEP 2: Create FieldDetails (JSON) ====================

class FieldDetailCreateSerializer(serializers.Serializer):
    """
    Serializer for individual detail item in Step 2
    Validation depends on parent Field.type
    """
    title = serializers.CharField(required=True, allow_blank=False, max_length=255)
    sort = serializers.IntegerField(required=False, allow_null=True)
    second_title = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    guide = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    des = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    image_path = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    is_required = serializers.IntegerField(required=False, allow_null=True, default=0)
    
    # For checkbox/radioButton types
    is_correct = serializers.IntegerField(required=False, allow_null=True)
    
    # For input types
    correct_answer = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class FieldDetailBulkSerializer(serializers.Serializer):
    """
    STEP 2: Create/Replace all FieldDetails for a Field (JSON)
    
    Validates based on the Field.type and replaces all existing details atomically.
    """
    details = FieldDetailCreateSerializer(many=True, required=True)
    
    def validate_details(self, value):
        """Validate that details array is not empty"""
        if not value:
            raise serializers.ValidationError(
                _('حداقل یک detail الزامی است')
            )
        return value
    
    def validate(self, data):
        """Validate details based on Field type"""
        field = self.context.get('field')
        if not field:
            raise serializers.ValidationError(_('Field not found in context'))
        
        details = data.get('details', [])
        field_type = field.type
        
        # Validate based on field type
        if field_type == 'input':
            # Input type: each detail must have correct_answer
            for idx, detail in enumerate(details):
                if not detail.get('correct_answer'):
                    raise serializers.ValidationError({
                        'details': {
                            idx: {
                                'correct_answer': [_('برای سوالات تایپی، correct_answer الزامی است')]
                            }
                        }
                    })
        
        elif field_type in ['checkbox', 'radioButton']:
            # Choice types: each detail must have is_correct
            for idx, detail in enumerate(details):
                if detail.get('is_correct') is None:
                    raise serializers.ValidationError({
                        'details': {
                            idx: {
                                'is_correct': [_('برای سوالات انتخابی، is_correct الزامی است')]
                            }
                        }
                    })
                # Validate is_correct value
                if detail['is_correct'] not in [0, 1, -1]:
                    raise serializers.ValidationError({
                        'details': {
                            idx: {
                                'is_correct': [_('is_correct باید 0 یا 1 یا -1 باشد')]
                            }
                        }
                    })
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Replace all FieldDetails for the Field"""
        field = self.context.get('field')
        details_data = validated_data.get('details', [])
        
        # Delete existing details
        FieldDetail.objects.filter(field=field).delete()
        
        # Create new details
        created_details = []
        for idx, detail_data in enumerate(details_data):
            # Set default sort if not provided
            if detail_data.get('sort') is None:
                detail_data['sort'] = idx
            
            detail = FieldDetail.objects.create(
                field=field,
                **detail_data
            )
            created_details.append(detail)
        
        return {
            'field_id': field.id,
            'details': created_details
        }


# ==================== Read Serializers ====================

class FieldDetailSerializer(serializers.ModelSerializer):
    """Serializer for reading answer options/details"""
    class Meta:
        model = FieldDetail
        fields = [
            'id', 'title', 'second_title', 'image_path', 'is_correct',
            'correct_answer', 'guide', 'des', 'sort', 'is_required'
        ]
        read_only_fields = ['id']


class FieldRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving questions with their options"""
    details = FieldDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'image_path',
            'audio_path', 'video_path', 'guide', 'des', 'sort', 'details'
        ]


class FieldListSerializer(serializers.ModelSerializer):
    """Serializer for listing questions with summary information"""
    details_count = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'type_display', 'is_required',
            'image_path', 'guide', 'des', 'sort',
            'details_count', 'created_at', 'created_at_jalali'
        ]
    
    def get_details_count(self, obj):
        """Get count of answer options/details"""
        return obj.details.count()
    
    def get_type_display(self, obj):
        """Get human-readable type name"""
        type_map = {
            'input': _('تایپی'),
            'checkbox': _('چند گزینه‌ای'),
            'radioButton': _('تک گزینه‌ای')
        }
        return type_map.get(obj.type, obj.type)
    
    def get_created_at_jalali(self, obj):
        """Get Jalali formatted creation date"""
        if obj.created_at:
            import jdatetime
            from datetime import datetime
            return jdatetime.datetime.fromgregorian(
                datetime=obj.created_at
            ).strftime('%Y/%m/%d %H:%M')
        return None


class CategoryFieldCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating exam questions (CategoryField)
    
    This links a question to a teaching subject/class with step and sort order.
    """
    field_details = FieldRetrieveSerializer(source='field', read_only=True)
    field_id = serializers.IntegerField(write_only=True)
    subject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    
    class Meta:
        model = CategoryField
        fields = [
            'id', 'teachingsubject', 'field_id', 'field_details', 'subject_title',
            'step', 'sort', 'type', 'is_conditional'
        ]
        read_only_fields = ['id', 'field_details', 'subject_title']
    
    def create(self, validated_data):
        field_id = validated_data.pop('field_id')
        field = Field.objects.get(id=field_id)
        validated_data['field'] = field
        return CategoryField.objects.create(**validated_data)


class CategoryFieldRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving exam with all its questions"""
    field = FieldRetrieveSerializer(read_only=True)
    subject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    
    class Meta:
        model = CategoryField
        fields = [
            'id', 'teachingsubject', 'field', 'subject_title',
            'step', 'sort', 'type', 'is_conditional'
        ]


class OrderDetailSubmitSerializer(serializers.Serializer):
    """Serializer for submitting answer details in exam"""
    field_id = serializers.IntegerField()
    field_detail_id = serializers.IntegerField(required=False, allow_null=True)
    value = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate(self, data):
        # Validate that either field_detail_id or value is provided
        if not data.get('field_detail_id') and not data.get('value'):
            raise serializers.ValidationError(
                _("Either field_detail_id (for choice questions) or value (for typing) must be provided")
            )
        return data


class OrderCreateSubmitSerializer(serializers.Serializer):
    """Serializer for submitting exam answers"""
    teachingsubject_id = serializers.IntegerField()
    answers = OrderDetailSubmitSerializer(many=True)
    
    def create(self, validated_data):
        """Process submitted answers and calculate score"""
        user = self.context['request'].user
        teachingsubject_id = validated_data['teachingsubject_id']
        answers_data = validated_data['answers']
        
        # Verify user has access to this teaching subject
        subject = TeachingSubject.objects.get(id=teachingsubject_id)
        # You might want to verify enrollment here
        
        # Create order
        order = Order.objects.create(
            user=user,
            teachingsubject=subject
        )
        
        correct = 0
        incorrect = 0
        total_score = 0
        
        # Process each answer
        for answer_data in answers_data:
            field_id = answer_data['field_id']
            field_detail_id = answer_data.get('field_detail_id')
            value = answer_data.get('value', '')
            
            field = Field.objects.get(id=field_id)
            answer_score = 0
            
            if field_detail_id:
                # Choice-based answer (checkbox or radioButton)
                field_detail = FieldDetail.objects.get(id=field_detail_id, field=field)
                if field_detail.is_correct == 1:
                    answer_score = 1
                    correct += 1
                else:
                    incorrect += 1
            else:
                # Text-based answer (input/typing)
                # Compare with correct_answer from the Field model
                field_detail = None
                if field.correct_answer:
                    # Simple exact match comparison (case-insensitive)
                    if value.strip().lower() == field.correct_answer.strip().lower():
                        answer_score = 1
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    # No correct answer defined, cannot grade
                    incorrect += 1
            
            total_score += answer_score
            
            OrderDetail.objects.create(
                order=order,
                field=field,
                field_detail=field_detail,
                value=value,
                score=answer_score
            )
        
        # Update order statistics
        order.correct = correct
        order.incorrect = incorrect
        order.score = total_score
        order.save()
        
        return order


class OrderDetailRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving submitted answers"""
    field_title = serializers.CharField(source='field.title', read_only=True)
    field_type = serializers.CharField(source='field.type', read_only=True)
    option_title = serializers.CharField(source='field_detail.title', read_only=True, allow_null=True)
    
    class Meta:
        model = OrderDetail
        fields = [
            'id', 'field', 'field_title', 'field_type', 'field_detail',
            'option_title', 'value', 'score'
        ]


class OrderRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving exam attempt with results"""
    subject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    details = OrderDetailRetrieveSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'teachingsubject', 'subject_title',
            'score', 'correct', 'incorrect', 'created_at', 'details'
        ]
        read_only_fields = ['id', 'created_at', 'score', 'correct', 'incorrect', 'details']


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing exam attempts"""
    subject_title = serializers.CharField(source='teachingsubject.title', read_only=True)
    total_questions = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'teachingsubject', 'subject_title', 'score', 'correct',
            'incorrect', 'total_questions', 'percentage', 'created_at'
        ]
    
    def get_total_questions(self, obj):
        """Get total number of questions in the exam"""
        return obj.details.count()
    
    def get_percentage(self, obj):
        """Calculate percentage score"""
        total = obj.details.count()
        if total == 0:
            return 0
        return round((obj.score / total) * 100, 2)


class ExamSerializer(serializers.Serializer):
    """Serializer for exam structure with all questions"""
    id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    subject_title = serializers.CharField()
    questions = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of all questions in this exam"
    )
    total_questions = serializers.IntegerField()
