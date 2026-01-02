"""
Serializers for Exercise App - Questions, Exams, and Answers
Supports: Typing, Multiple Choice (Checkbox), Single Choice (RadioButton)
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from exercise.models import Field, FieldDetail, CategoryField, Order, OrderDetail
from classroom.models import TeachingSubject

import re


class FieldDetailSerializer(serializers.ModelSerializer):
    """Serializer for answer options/details"""
    title = serializers.CharField(required=True, allow_blank=False)
    correct_answer = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_correct = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = FieldDetail
        fields = [
            'id', 'title', 'second_title', 'image_path', 'is_correct',
            'correct_answer', 'guide', 'des', 'sort', 'is_required'
        ]
        read_only_fields = ['id']


DETAIL_RE = re.compile(r"^details\[(\d+)\]\[([^\]]+)\]$")


def _parse_details_from_form_keys(data):
    """
    Converts multipart keys like:
      details[0][title], details[0][correct_answer], details[3][is_correct]
    into:
      [
        {'title':..., 'correct_answer':..., 'sort':...},
        ...
      ]
    Works even if indices are not continuous.
    """
    buckets = {}  # idx -> dict(fields)

    # QueryDict keys are strings
    for key in list(getattr(data, "keys", lambda: [])()):
        m = DETAIL_RE.match(str(key))
        if not m:
            continue

        idx = int(m.group(1))
        field = m.group(2)
        val = data.get(key)

        if idx not in buckets:
            buckets[idx] = {}
        buckets[idx][field] = val

    if not buckets:
        return []

    details = []
    for idx in sorted(buckets.keys()):
        raw = buckets[idx]

        # 최소 فیلدهای لازم
        title_val = raw.get('title', '')
        sort_val = raw.get('sort', idx)

        detail = {
            'title': title_val,
            'sort': int(sort_val) if str(sort_val).strip() != '' else idx,
        }

        # optional fields
        if 'second_title' in raw:
            detail['second_title'] = raw.get('second_title')

        if 'image_path' in raw:
            detail['image_path'] = raw.get('image_path')

        if 'guide' in raw:
            detail['guide'] = raw.get('guide')

        if 'des' in raw:
            detail['des'] = raw.get('des')

        if 'is_required' in raw:
            try:
                detail['is_required'] = int(raw.get('is_required') or 0)
            except Exception:
                detail['is_required'] = 0

        # checkbox/radioButton
        if 'is_correct' in raw:
            try:
                detail['is_correct'] = int(raw.get('is_correct') or 0)
            except Exception:
                detail['is_correct'] = 0

        # input
        if 'correct_answer' in raw:
            detail['correct_answer'] = raw.get('correct_answer')

        details.append(detail)

    return details


class FieldCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating questions (Fields)

    Supports:
    - input (تایپی) -> details contain correct_answer
    - checkbox (چند گزینه‌ای) -> details contain is_correct
    - radioButton (تک گزینه‌ای) -> details contain is_correct
    """
    details = FieldDetailSerializer(many=True, required=False, write_only=True)

    image_path = serializers.FileField(required=False, allow_null=True, write_only=True)
    audio_path = serializers.FileField(required=False, allow_null=True, write_only=True)
    video_path = serializers.FileField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'image_path',
            'audio_path', 'video_path', 'guide', 'des', 'sort', 'details'
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        """
        ✅ FIX:
        - Always returns super().to_internal_value(...)
        - Parses details[...] keys robustly (non-continuous indices supported)
        """
        # 1) parse details from form keys
        parsed_details = _parse_details_from_form_keys(data)

        # 2) make a mutable copy
        if hasattr(data, "copy"):
            data_mut = data.copy()
        else:
            data_mut = dict(data)

        # 3) inject details (if any)
        if parsed_details:
            data_mut['details'] = parsed_details

        # 4) always return
        return super().to_internal_value(data_mut)

    def validate(self, data):
        """Validate that questions have appropriate details"""
        question_type = data.get('type')
        details = data.get('details', [])

        if question_type in ['checkbox', 'radioButton']:
            if not details:
                raise serializers.ValidationError(_('سوالات انتخابی باید حداقل یک گزینه داشته باشند'))

        if question_type == 'input':
            if not details:
                raise serializers.ValidationError(_('سوالات تایپی باید حداقل یک detail برای ذخیره پاسخ صحیح داشته باشند'))

            has_correct_answer = any(detail.get('correct_answer') for detail in details)
            if not has_correct_answer:
                raise serializers.ValidationError(_('سوالات تایپی باید حداقل یک detail با correct_answer داشته باشند'))

        return data

    def create(self, validated_data):
        """Create Field with FieldDetail entries"""
        import logging
        import os
        import uuid
        from django.core.files.storage import default_storage

        logger = logging.getLogger(__name__)

        details_data = validated_data.pop('details', [])

        # Teacher assign (if field exists)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                Field._meta.get_field('teacher')
                validated_data['teacher'] = request.user
            except Exception:
                pass

        # Handle file uploads
        image_file = validated_data.pop('image_path', None)
        if image_file:
            ext = os.path.splitext(image_file.name)[1]
            filename = f"exercise_images/{uuid.uuid4().hex}{ext}"
            validated_data['image_path'] = default_storage.save(filename, image_file)

        audio_file = validated_data.pop('audio_path', None)
        if audio_file:
            ext = os.path.splitext(audio_file.name)[1]
            filename = f"exercise_audio/{uuid.uuid4().hex}{ext}"
            validated_data['audio_path'] = default_storage.save(filename, audio_file)

        video_file = validated_data.pop('video_path', None)
        if video_file:
            ext = os.path.splitext(video_file.name)[1]
            filename = f"exercise_videos/{uuid.uuid4().hex}{ext}"
            validated_data['video_path'] = default_storage.save(filename, video_file)

        field = Field.objects.create(**validated_data)

        for detail_data in details_data:
            FieldDetail.objects.create(field=field, **detail_data)

        return Field.objects.prefetch_related('details').get(pk=field.pk)

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data is not None:
            instance.details.all().delete()
            for detail_data in details_data:
                FieldDetail.objects.create(field=instance, **detail_data)

        return Field.objects.prefetch_related('details').get(pk=instance.pk)


class FieldRetrieveSerializer(serializers.ModelSerializer):
    details = FieldDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Field
        fields = [
            'id', 'title', 'type', 'is_required', 'image_path',
            'audio_path', 'video_path', 'guide', 'des', 'sort', 'details'
        ]


class FieldListSerializer(serializers.ModelSerializer):
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
        return obj.details.count()

    def get_type_display(self, obj):
        type_map = {
            'input': _('تایپی'),
            'checkbox': _('چند گزینه‌ای'),
            'radioButton': _('تک گزینه‌ای')
        }
        return type_map.get(obj.type, obj.type)

    def get_created_at_jalali(self, obj):
        if obj.created_at:
            import jdatetime
            from datetime import datetime
            return jdatetime.datetime.fromgregorian(
                datetime=obj.created_at
            ).strftime('%Y/%m/%d %H:%M')
        return None


# ---- پایین فایل رو (بقیه serializer ها) همون قبلی نگه داشته‌ام ----

class CategoryFieldCreateSerializer(serializers.ModelSerializer):
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
    field = FieldRetrieveSerializer(read_only=True)
    subject_title = serializers.CharField(source='teachingsubject.title', read_only=True)

    class Meta:
        model = CategoryField
        fields = [
            'id', 'teachingsubject', 'field', 'subject_title',
            'step', 'sort', 'type', 'is_conditional'
        ]


class OrderDetailSubmitSerializer(serializers.Serializer):
    field_id = serializers.IntegerField()
    field_detail_id = serializers.IntegerField(required=False, allow_null=True)
    value = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if not data.get('field_detail_id') and not data.get('value'):
            raise serializers.ValidationError(
                _("Either field_detail_id (for choice questions) or value (for typing) must be provided")
            )
        return data


class OrderCreateSubmitSerializer(serializers.Serializer):
    teachingsubject_id = serializers.IntegerField()
    answers = OrderDetailSubmitSerializer(many=True)

    def create(self, validated_data):
        user = self.context['request'].user
        teachingsubject_id = validated_data['teachingsubject_id']
        answers_data = validated_data['answers']

        subject = TeachingSubject.objects.get(id=teachingsubject_id)

        order = Order.objects.create(user=user, teachingsubject=subject)

        correct = 0
        incorrect = 0
        total_score = 0

        for answer_data in answers_data:
            field_id = answer_data['field_id']
            field_detail_id = answer_data.get('field_detail_id')
            value = answer_data.get('value', '')

            field = Field.objects.get(id=field_id)
            answer_score = 0

            if field_detail_id:
                field_detail = FieldDetail.objects.get(id=field_detail_id, field=field)
                if field_detail.is_correct == 1:
                    answer_score = 1
                    correct += 1
                else:
                    incorrect += 1
            else:
                field_detail = None
                if getattr(field, "correct_answer", None):
                    if value.strip().lower() == field.correct_answer.strip().lower():
                        answer_score = 1
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    incorrect += 1

            total_score += answer_score

            OrderDetail.objects.create(
                order=order,
                field=field,
                field_detail=field_detail,
                value=value,
                score=answer_score
            )

        order.correct = correct
        order.incorrect = incorrect
        order.score = total_score
        order.save()

        return order
