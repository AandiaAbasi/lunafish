from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from recommendation.abstract_models import BaseModel
from django.conf import settings
class PsychologicalTest(BaseModel):
    """
    Psychological test created by adviser for students.
    """
    
    TEST_TYPES = (
        ("register", _("Register")),
        ("regular", _("Regular")),
        ("english_placement", _("English placement")),
    )
    
    title = models.CharField(
        _('عنوان تست'),
        max_length=255,
        help_text=_('مثال: تست مهاجرت تحصیلی')
    )
    description = models.TextField(
        _('توضیحات'),
        blank=True,
        help_text=_('توضیحات کلی درباره تست')
    )
    
    is_active = models.BooleanField(_('فعال'), default=True)
    test_type = models.CharField(max_length=50, choices=TEST_TYPES, default='english_placement', editable=False, verbose_name=_("Type"))
    class Meta:
        verbose_name = _('تست راهنمای مهاجرت')
        verbose_name_plural = _('Immigration Guide Tests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title}'


class TestQuestion(BaseModel):
    """
    Questions belonging to a psychological test.
    """
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', _('چند گزینه‌ای')
    
    test = models.ForeignKey(
        PsychologicalTest,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('تست')
    )
    icon = models.CharField(
        _('آیکون سوال'),
        max_length=191,
        null=True,
        blank=True,
        help_text=_('آیکون سوال را وارد کنید')
    )
    question_text = models.TextField(
        _('متن سوال'),
        help_text=_('سوال مورد نظر را وارد کنید')
    )
    question_type = models.CharField(
        _('نوع سوال'),
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    order = models.PositiveIntegerField(
        _('ترتیب'),
        default=0,
        help_text=_('ترتیب نمایش سوال در تست')
    )
    is_required = models.BooleanField(
        _('اجباری'),
        default=True,
        help_text=_('آیا پاسخ به این سوال اجباری است؟')
    )
    
    class Meta:
        verbose_name = _('سوال تست')
        verbose_name_plural = _('سوالات تست')
        ordering = ['test', 'order']
    
    def __str__(self):
        return f'{self.test.title} - سوال {self.order}'


class QuestionOption(BaseModel):
    """
    Options for multiple choice questions.
    Only applicable when question_type is MULTIPLE_CHOICE.
    """
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('سوال')
    )
    icon = models.CharField(
        _('آیکون گزینه'),
        max_length=191,
        null=True,
        blank=True,
        help_text=_('آیکون گزینه را وارد کنید')
    )
    option_text = models.CharField(
        _('متن گزینه'),
        max_length=255
    )
    order = models.PositiveIntegerField(
        _('ترتیب'),
        default=0
    )
    
    class Meta:
        verbose_name = _('گزینه سوال')
        verbose_name_plural = _('گزینه‌های سوال')
        ordering = ['question', 'order']
    
    def __str__(self):
        return f'{self.question.question_text[:30]} - {self.option_text}'



class StudentTestResponse(BaseModel):
    """
    Student's response to a psychological test.
    """
    class SubmissionStatus(models.TextChoices):
        NOT_STARTED = 'not_started', _('شروع نشده')
        IN_PROGRESS = 'in_progress', _('در حال پاسخ')
        COMPLETED = 'completed', _('تکمیل شده')
    
    test = models.ForeignKey(
        PsychologicalTest,
        on_delete=models.CASCADE,
        related_name='student_responses',
        verbose_name=_('تست')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_responses',
        verbose_name=_('کاربر')
    )
    status = models.CharField(
        _('وضعیت'),
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NOT_STARTED
    )
    started_at = models.DateTimeField(
        _('زمان شروع'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        _('زمان تکمیل'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('پاسخ کاربر')
        verbose_name_plural = _('پاسخ‌های کاربران')
        unique_together = ['test', 'user']
        ordering = ['-completed_at']
    
    def __str__(self):
        return f'{self.user.name} - {self.test.title}'
    
    def calculate_result(self):
        """
        Manually calculate result for this response.
        
        Returns:
            TestResult object if successful, None if error
        """
        if self.status != 'completed':
            return None
        
        try:
            from recommendation.utils import calculate_test_result
            return calculate_test_result(self)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating result for response {self.id}: {str(e)}")
            return None
    
    def has_result(self):
        """Check if result has been calculated."""
        return hasattr(self, 'result')
    
    def get_holland_code(self):
        """Get Holland code from result if available."""
        if self.has_result():
            return self.result.summary.get('holland_code', '')
        return ''


class StudentAnswer(BaseModel):
    """
    Individual answer to a specific question.
    """
    response = models.ForeignKey(
        StudentTestResponse,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('پاسخ')
    )
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name=_('سوال')
    )
    
    # For multiple choice questions
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_answers',
        verbose_name=_('گزینه انتخابی')
    )
    
    # For text/textarea questions
    text_answer = models.TextField(
        _('پاسخ متنی'),
        blank=True
    )
    
    answered_at = models.DateTimeField(
        _('زمان پاسخ'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('پاسخ به سوال')
        verbose_name_plural = _('پاسخ‌ها به سوالات')
        unique_together = ['response', 'question']
        ordering = ['question__order']
    
    def __str__(self):
        return f'{self.response.user.name} - سوال {self.question.order}'


class TestScale(BaseModel):
    """
    A scoring scale used by a test.

    English placement tests use LEVEL scales (A1...C1) and SKILL scales
    (GRAM, VOCAB, READ, USE). Existing tests can keep GENERAL.
    """

    class ScaleType(models.TextChoices):
        GENERAL = 'general', _('عمومی')
        LEVEL = 'level', _('سطح زبان')
        SKILL = 'skill', _('مهارت زبان')

    test = models.ForeignKey(
        PsychologicalTest,
        on_delete=models.CASCADE,
        related_name='scales',
        verbose_name=_('تست')
    )
    code = models.CharField(
        _('کد مقیاس'),
        max_length=20,
        help_text=_('مثال: R, I, A, S, E, C')
    )
    title = models.CharField(
        _('عنوان مقیاس'),
        max_length=255,
        help_text=_('مثال: واقع‌گرا، پژوهشگر')
    )
    description = models.TextField(
        _('توضیحات'),
        blank=True
    )
    scale_type = models.CharField(
        _('نوع مقیاس'),
        max_length=20,
        choices=ScaleType.choices,
        default=ScaleType.GENERAL,
        db_index=True,
    )
    rank = models.PositiveSmallIntegerField(
        _('ترتیب سطح'),
        null=True,
        blank=True,
        help_text=_('برای سطح‌ها: A1=1، A2=2، B1=3، B2=4، C1=5'),
    )
    pass_score = models.FloatField(
        _('حداقل امتیاز قبولی'),
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('حداقل امتیاز لازم برای عبور از این سطح'),
    )

    class Meta:
        verbose_name = _('مقیاس تست')
        verbose_name_plural = _('مقیاس‌های تست')
        unique_together = ['test', 'code']
        ordering = ['test', 'code']
    
    def __str__(self):
        return f'{self.test.title} - {self.code}: {self.title}'


class OptionScaleWeight(BaseModel):
    """
    Weight/score assigned to an option for a specific scale.
    Allows one option to contribute to multiple scales with different weights.
    """
    option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        related_name='scale_weights',
        verbose_name=_('گزینه')
    )
    scale = models.ForeignKey(
        TestScale,
        on_delete=models.CASCADE,
        related_name='option_weights',
        verbose_name=_('مقیاس')
    )
    weight = models.FloatField(
        _('وزن'),
        help_text=_('مثال: 1 ، 0.5 ، -1')
    )

    class Meta:
        verbose_name = _('وزن گزینه برای مقیاس')
        verbose_name_plural = _('وزن‌های گزینه‌ها برای مقیاس‌ها')
        unique_together = ['option', 'scale']
        ordering = ['scale', 'option']
    
    def __str__(self):
        return f'{self.option.option_text[:30]} → {self.scale.code}: {self.weight}'
        
class TestResult(BaseModel):
    """
    Calculated result for a student's test response.
    Contains raw scores per scale and final summary/interpretation.
    """
    response = models.OneToOneField(
        StudentTestResponse,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name=_('پاسخ دانش‌آموز')
    )
    calculated_at = models.DateTimeField(
        _('تاریخ محاسبه'),
        auto_now_add=True
    )

    # Raw scores per scale: {"R": 45.5, "I": 32.0, "A": 28.5, ...}
    raw_scores = models.JSONField(
        _('امتیازات خام'),
        help_text=_('امتیاز هر مقیاس به صورت دیکشنری')
    )

    # Final summary: {"code": "RIA", "top_scales": ["R", "I", "A"], ...}
    summary = models.JSONField(
        _('خلاصه نتیجه'),
        help_text=_('کد نهایی و اطلاعات خلاصه')
    )

    class Meta:
        verbose_name = _('نتیجه آزمون')
        verbose_name_plural = _('نتایج آزمون‌ها')
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f'نتیجه: {self.response.user.name} - {self.response.test.title}'
        
class EnglishPlacementAssessment(BaseModel):
    """
    Immutable history item for an English placement submission or an admin/teacher
    assessment. StudentTestResponse itself remains unique per test/user and keeps
    being updated exactly as before.
    """

    class EnglishLevel(models.TextChoices):
        PRE_A1 = 'pre_a1', _('Pre-A1')
        A1 = 'a1', _('A1 - Beginner')
        A2 = 'a2', _('A2 - Elementary')
        B1 = 'b1', _('B1 - Intermediate')
        B2 = 'b2', _('B2 - Upper Intermediate')
        C1 = 'c1', _('C1 - Advanced')
        C2 = 'c2', _('C2 - Proficient')

    class Status(models.TextChoices):
        PENDING = 'pending', _('در انتظار بررسی')
        CONFIRMED = 'confirmed', _('تأیید شده')
        OVERRIDDEN = 'overridden', _('تغییر داده شده توسط ارزیاب')

    class Source(models.TextChoices):
        TEST = 'test', _('آزمون تعیین سطح')
        ADMIN = 'admin', _('تعیین دستی ادمین')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='english_placement_assessments',
        verbose_name=_('دانش‌آموز'),
    )
    response = models.ForeignKey(
        StudentTestResponse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='placement_assessments',
        verbose_name=_('پاسخ آزمون'),
    )
    test = models.ForeignKey(
        PsychologicalTest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='placement_assessments',
        verbose_name=_('آزمون'),
    )
    suggested_level = models.CharField(
        _('سطح پیشنهادی سیستم'),
        max_length=10,
        choices=EnglishLevel.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    final_level = models.CharField(
        _('سطح نهایی'),
        max_length=10,
        choices=EnglishLevel.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    source = models.CharField(
        _('روش تعیین سطح'),
        max_length=20,
        choices=Source.choices,
        default=Source.TEST,
    )
    status = models.CharField(
        _('وضعیت بررسی'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_english_assessments',
        verbose_name=_('بررسی شده توسط'),
    )
    assessed_at = models.DateTimeField(
        _('زمان بررسی نهایی'),
        null=True,
        blank=True,
    )
    response_completed_at = models.DateTimeField(
        _('زمان ثبت این نوبت آزمون'),
        null=True,
        blank=True,
    )
    raw_scores_snapshot = models.JSONField(
        _('تصویر امتیازهای آزمون'),
        default=dict,
        blank=True,
    )
    result_summary_snapshot = models.JSONField(
        _('تصویر خلاصه نتیجه'),
        default=dict,
        blank=True,
    )
    note = models.TextField(_('یادداشت ارزیاب'), blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('تعیین سطح زبان')
        verbose_name_plural = _('تاریخچه تعیین سطح زبان')

    def __str__(self):
        level = self.final_level or self.suggested_level or '-'
        return f'{self.student} - {level}'


class ScaleInterpretation(BaseModel):
    """
    Interpretation text for a scale based on score range.
    Provides psychological interpretation for different score levels.
    """
    scale = models.ForeignKey(
        TestScale,
        on_delete=models.CASCADE,
        related_name='interpretations',
        verbose_name=_('مقیاس')
    )

    min_score = models.FloatField(
        _('حداقل امتیاز'),
        help_text=_('امتیاز شروع بازه')
    )
    max_score = models.FloatField(
        _('حداکثر امتیاز'),
        help_text=_('امتیاز پایان بازه')
    )

    title = models.CharField(
        _('عنوان تفسیر'),
        max_length=255,
        help_text=_('مثال: رغبت بالا، رغبت متوسط')
    )

    description = models.TextField(
        _('توضیحات تفسیر'),
        help_text=_('تفسیر روانشناختی کامل')
    )

    order = models.PositiveIntegerField(
        _('ترتیب'),
        default=0,
        help_text=_('ترتیب نمایش تفسیر')
    )

    class Meta:
        verbose_name = _('تفسیر مقیاس')
        verbose_name_plural = _('تفسیرهای مقیاس‌ها')
        ordering = ['scale', 'order', 'min_score']
        unique_together = ['scale', 'min_score', 'max_score']
    
    def __str__(self):
        return f'{self.scale.code} ({self.min_score}-{self.max_score}): {self.title}'
    
    def is_score_in_range(self, score):
        """Check if a given score falls within this interpretation's range."""
        return self.min_score <= score <= self.max_score

