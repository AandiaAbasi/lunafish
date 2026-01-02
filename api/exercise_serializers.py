"""
Serializers for Exercise App - Questions, Exams, and Answers
Supports: Typing, Multiple Choice (Checkbox), Single Choice (RadioButton)
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from exercise.models import Field, FieldDetail, CategoryField, Order, OrderDetail
from classroom.models import TeachingSubject
import jdatetime
from datetime import datetime, date


class FieldDetailSerializer(serializers.ModelSerializer):
    """Serializer for answer options/details"""
    class Meta:
        model = FieldDetail
        fields = [
            'id', 'title', 'second_title', 'image_path', 'is_correct',
            'correct_answer', 'guide', 'des', 'sort', 'is_required'
        ]
        read_only_fields = ['id']


class FieldCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating questions (Fields)
    
    Supports:
    - input (تایپی) - Typing questions (details contain correct_answer)
    - checkbox (چند گزینه‌ای) - Multiple choice (details contain options with is_correct)
    - radioButton (تک گزینه‌ای) - Single choice (details contain options with is_correct)
    """
    details = FieldDetailSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'image_path',
            'audio_path', 'video_path', 'guide', 'des', 'sort', 'details'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate that questions have appropriate details"""
        question_type = data.get('type')
        details = data.get('details', [])
        
        # ✅ سوالات choice باید دارای details باشند
        if question_type in ['checkbox', 'radioButton']:
            if not details:
                raise serializers.ValidationError(
                    _('سوالات انتخابی باید حداقل یک گزینه داشته باشند')
                )
        
        # ✅ سوالات input می‌توانند details داشته باشند (برای ذخیره correct_answer)
        # No restriction on input questions having details
        
        return data
    
    def create(self, validated_data):
        """Create Field with FieldDetail entries"""
        details_data = validated_data.pop('details', [])
        
        # Create the Field
        field = Field.objects.create(**validated_data)
        
        # Create FieldDetail entries
        for detail_data in details_data:
            FieldDetail.objects.create(field=field, **detail_data)
        
        # Reload to get the related details
        field.refresh_from_db()
        return field
    
    def update(self, instance, validated_data):
        """Update Field and its FieldDetail entries"""
        details_data = validated_data.pop('details', None)
        
        # Update field fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update details if provided
        if details_data is not None:
            # Delete existing details
            instance.details.all().delete()
            # Create new details
            for detail_data in details_data:
                FieldDetail.objects.create(field=instance, **detail_data)
        
        # Reload to get the related details
        instance.refresh_from_db()
        return instance


class FieldRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for retrieving questions with their options"""
    details = FieldDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'image_path',
            'audio_path', 'video_path', 'guide', 'des', 'sort', 'details'
        ]


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
