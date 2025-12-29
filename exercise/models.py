from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from account.models import User
from classroom.models import TeachingSubject
from core.abstract_models import BaseModel
from decimal import Decimal


# ===== Exercise (تمرین) Models =====

class Exercise(BaseModel):
    """
    تمرین‌های تابع به موضوع تدریس
    مدرس می‌تواند تمرین‌ها را طراحی کند
    """
    DIFFICULTY_CHOICES = [
        ('easy', _('آسان')),
        ('medium', _('متوسط')),
        ('hard', _('سخت')),
    ]
    
    EXERCISE_TYPE_CHOICES = [
        ('practice', _('تمرین معمولی')),
        ('homework', _('تکلیف خانگی')),
        ('quiz', _('کوئیز')),
        ('exam', _('آزمون')),
    ]
    
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'teacher'}, 
        related_name='exercises',
        verbose_name=_('معلم')
    )
    subject = models.ForeignKey(
        TeachingSubject,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name=_('موضوع تدریس')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=_('عنوان تمرین'),
        help_text=_('مثال: تمرین شماره 1 - الفبا و تلفظ')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('توضیح'),
        help_text=_('توضیح تفصیلی درباره این تمرین')
    )
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        default='practice',
        verbose_name=_('نوع تمرین')
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name=_('درجه سختی')
    )
    duration_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
        verbose_name=_('مدت زمان (دقیقه)'),
        help_text=_('زمان تخمینی برای انجام تمرین')
    )
    total_points = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name=_('کل امتیاز'),
        help_text=_('مجموع امتیازهای این تمرین')
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_('منتشر شده'),
        help_text=_('آیا این تمرین برای دانش‌آموزان نمایش یابد؟')
    )
    pass_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('نمره قبولی (درصد)'),
        help_text=_('حداقل درصد امتیاز برای قبول')
    )
    # تمرین‌های اختیاری
    is_optional = models.BooleanField(
        default=False,
        verbose_name=_('اختیاری'),
        help_text=_('آیا این تمرین اختیاری است؟')
    )
    # تمرین‌های چندگزینه‌ای (دانش‌آموز می‌تواند یکی را انتخاب کند)
    parent_exercise = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='variants',
        verbose_name=_('تمرین مادر'),
        help_text=_('اگر این تمرین یک نسخه متفاوت از تمرین دیگری است')
    )
    variant_order = models.IntegerField(
        default=0,
        verbose_name=_('ترتیب نسخه'),
        help_text=_('ترتیب نمایش این نسخه')
    )
    
    class Meta:
        verbose_name = _('تمرین')
        verbose_name_plural = _('تمرین‌ها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['subject', '-created_at']),
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['parent_exercise', 'variant_order']),
        ]
    
    def __str__(self):
        parent_info = f" (نسخه {self.variant_order})" if self.parent_exercise else ""
        return f'{self.title}{parent_info} - {self.teacher.name}'
    
    def get_question_count(self):
        """تعداد کل سوالات"""
        return self.questions.filter(is_required=True).count()
    
    def get_optional_question_count(self):
        """تعداد سوالات اختیاری"""
        return self.questions.filter(is_required=False).count()
    
    def calculate_points_per_question(self):
        """امتیاز هر سوال"""
        count = self.get_question_count()
        if count == 0:
            return 0
        return self.total_points / count
    
    def get_variants(self):
        """دریافت تمام نسخه‌های این تمرین"""
        return self.variants.all().order_by('variant_order')


class ExerciseChoice(BaseModel):
    """
    دسته‌بندی تمرین‌های گزینه‌ای
    معلم می‌تواند چندین تمرین متفاوت ایجاد کند و دانش‌آموزان یکی را انتخاب کنند
    مثال: دانش‌آموز می‌تواند سطح راحت‌تر یا سخت‌تر را انتخاب کند
    """
    CHOICE_TYPE_CHOICES = [
        ('difficulty', _('سطح سختی')),
        ('variant', _('نسخه متفاوت')),
        ('language', _('زبان')),
        ('topic', _('موضوع')),
        ('style', _('سبک')),
    ]
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='created_exercise_choices',
        verbose_name=_('معلم')
    )
    subject = models.ForeignKey(
        TeachingSubject,
        on_delete=models.CASCADE,
        related_name='exercise_choices',
        verbose_name=_('موضوع تدریس')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=_('عنوان گروه تمرین'),
        help_text=_('مثال: تمرین‌های متنوع - سطح‌های مختلف')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('توضیح'),
        help_text=_('توضیح گروه تمرین‌ها')
    )
    choice_type = models.CharField(
        max_length=20,
        choices=CHOICE_TYPE_CHOICES,
        default='difficulty',
        verbose_name=_('نوع انتخاب'),
        help_text=_('بر اساس چه معیاری دانش‌آموز انتخاب می‌کند؟')
    )
    exercises = models.ManyToManyField(
        Exercise,
        related_name='exercise_choice_groups',
        verbose_name=_('تمرین‌های موجود'),
        help_text=_('تمرین‌هایی که دانش‌آموز می‌تواند از بینشان انتخاب کند')
    )
    required_choices = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('تعداد تمرین‌های قابل انتخاب'),
        help_text=_('چند تمرین می‌تواند دانش‌آموز انتخاب کند؟')
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_('منتشر شده')
    )
    
    class Meta:
        verbose_name = _('گروه تمرین‌های گزینه‌ای')
        verbose_name_plural = _('گروه‌های تمرین‌های گزینه‌ای')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['subject', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.title} ({self.get_choice_type_display()})'
    
    def get_exercise_count(self):
        """تعداد تمرین‌های موجود"""
        return self.exercises.count()


class StudentExerciseChoice(BaseModel):
    """
    انتخاب‌های دانش‌آموز برای تمرین‌های گزینه‌ای
    ثبت اینکه دانش‌آموز کدام تمرین را انتخاب کرده است
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='student_exercise_choices',
        verbose_name=_('دانش‌آموز')
    )
    exercise_choice_group = models.ForeignKey(
        ExerciseChoice,
        on_delete=models.CASCADE,
        related_name='student_choices',
        verbose_name=_('گروه تمرین')
    )
    selected_exercises = models.ManyToManyField(
        Exercise,
        related_name='chosen_by_students',
        verbose_name=_('تمرین‌های انتخاب شده'),
        help_text=_('تمرین‌هایی که دانش‌آموز انتخاب کرده است')
    )
    confirmed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان تأیید انتخاب')
    )
    
    class Meta:
        verbose_name = _('انتخاب تمرین دانش‌آموز')
        verbose_name_plural = _('انتخاب‌های تمرین دانش‌آموز')
        ordering = ['-confirmed_at']
        unique_together = ['student', 'exercise_choice_group']
        indexes = [
            models.Index(fields=['student', '-confirmed_at']),
            models.Index(fields=['exercise_choice_group', '-confirmed_at']),
        ]
    
    def __str__(self):
        count = self.selected_exercises.count()
        return f'{self.student.username} - {count} تمرین انتخاب شده'


class Question(BaseModel):
    """
    سوالات تمرین
    هر سوال می‌تواند انواع مختلفی داشته باشد:
    - تکمیلی (Completion)
    - انتخاب‌گزینه‌ای (Multiple Choice)
    - درست/غلط (True/False)
    - تطابق (Matching)
    - جاخالی (Fill in the Blank)
    """
    QUESTION_TYPE_CHOICES = [
        ('completion', _('تکمیلی')),
        ('multiple_choice', _('انتخاب‌گزینه‌ای')),
        ('true_false', _('درست/غلط')),
        ('matching', _('تطابق')),
        ('fill_blank', _('جاخالی')),
        ('short_answer', _('جواب کوتاه')),
    ]
    
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('تمرین')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('ترتیب'),
        help_text=_('ترتیب نمایش سوال')
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        verbose_name=_('نوع سوال')
    )
    text = models.TextField(
        verbose_name=_('متن سوال'),
        help_text=_('متن اصلی سوال')
    )
    # فایل‌های رسانه‌ای برای سوال
    image = models.ImageField(
        upload_to='exercises/questions/images/',
        null=True,
        blank=True,
        verbose_name=_('تصویر'),
        help_text=_('تصویر مرتبط با سوال')
    )
    audio = models.FileField(
        upload_to='exercises/questions/audio/',
        null=True,
        blank=True,
        verbose_name=_('فایل صوتی'),
        help_text=_('فایل صوتی مرتبط با سوال (mp3, wav)')
    )
    video = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('ویدیو'),
        help_text=_('لینک ویدیوی مرتبط با سوال (YouTube, etc)')
    )
    explanation = models.TextField(
        blank=True,
        verbose_name=_('توضیح جواب'),
        help_text=_('توضیح درباره جواب صحیح')
    )
    points = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name=_('امتیاز'),
        help_text=_('امتیاز این سوال')
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name=_('الزامی'),
        help_text=_('آیا این سوال الزامی است؟')
    )
    
    class Meta:
        verbose_name = _('سوال')
        verbose_name_plural = _('سوالات')
        ordering = ['exercise', 'order']
        indexes = [
            models.Index(fields=['exercise', 'order']),
            models.Index(fields=['question_type']),
        ]
    
    def __str__(self):
        return f'{self.exercise.title} - سوال {self.order}: {self.text[:50]}'


class QuestionOption(BaseModel):
    """
    گزینه‌های سوال (برای سوالات انتخاب‌گزینه‌ای، درست/غلط، تطابق)
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('سوال')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('ترتیب'),
        help_text=_('ترتیب نمایش گزینه')
    )
    text = models.CharField(
        max_length=500,
        verbose_name=_('متن گزینه'),
        help_text=_('متن این گزینه')
    )
    # رسانه‌های تکمیلی برای گزینه
    image = models.ImageField(
        upload_to='exercises/options/images/',
        null=True,
        blank=True,
        verbose_name=_('تصویر'),
        help_text=_('تصویر برای این گزینه')
    )
    audio = models.FileField(
        upload_to='exercises/options/audio/',
        null=True,
        blank=True,
        verbose_name=_('فایل صوتی'),
        help_text=_('فایل صوتی برای این گزینه')
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name=_('پاسخ صحیح'),
        help_text=_('آیا این گزینه پاسخ صحیح است؟')
    )
    explanation = models.TextField(
        blank=True,
        verbose_name=_('توضیح'),
        help_text=_('توضیح درباره این گزینه')
    )
    
    class Meta:
        verbose_name = _('گزینه سوال')
        verbose_name_plural = _('گزینه‌های سوال')
        ordering = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'is_correct']),
        ]
    
    def __str__(self):
        return f'{self.question.text[:30]} - گزینه {self.order}: {self.text[:40]}'


class StudentExerciseAttempt(BaseModel):
    """
    تلاش‌های دانش‌آموز برای انجام تمرین
    """
    STATUS_CHOICES = [
        ('in_progress', _('در حال انجام')),
        ('submitted', _('ارائه شده')),
        ('graded', _('نمره‌گذاری شده')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='exercise_attempts',
        verbose_name=_('دانش‌آموز')
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name=_('تمرین')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name=_('وضعیت')
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('نمره'),
        help_text=_('نمره دانش‌آموز')
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('درصد'),
        help_text=_('درصد امتیاز')
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان شروع')
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('زمان ارائه'),
        help_text=_('زمان ارائه نهایی تمرین')
    )
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('زمان نمره‌گذاری')
    )
    teacher_notes = models.TextField(
        blank=True,
        verbose_name=_('یادداشت‌های معلم'),
        help_text=_('نظرات و بازخورد معلم')
    )
    
    class Meta:
        verbose_name = _('تلاش تمرین دانش‌آموز')
        verbose_name_plural = _('تلاش‌های تمرین دانش‌آموز')
        ordering = ['-created_at']
        unique_together = ['student', 'exercise']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['exercise', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.student.username} - {self.exercise.title}: {self.score or "نمره نشده"}'
    
    def pass_exercise(self):
        """بررسی قبول شدن در تمرین"""
        if self.percentage is None:
            return None
        return self.percentage >= self.exercise.pass_score


class StudentQuestionAnswer(BaseModel):
    """
    جواب‌های دانش‌آموز برای هر سوال
    """
    attempt = models.ForeignKey(
        StudentExerciseAttempt,
        on_delete=models.CASCADE,
        related_name='question_answers',
        verbose_name=_('تلاش')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name=_('سوال')
    )
    answer_text = models.TextField(
        blank=True,
        verbose_name=_('متن جواب'),
        help_text=_('جواب متنی دانش‌آموز')
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_selections',
        verbose_name=_('گزینه انتخاب شده'),
        help_text=_('برای سوالات انتخاب‌گزینه‌ای')
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_('صحیح/غلط'),
        help_text=_('آیا جواب صحیح است؟')
    )
    points_earned = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('امتیاز کسب شده'),
        help_text=_('امتیازی که دانش‌آموز برای این سوال کسب کرد')
    )
    answer_file = models.FileField(
        upload_to='exercises/answers/',
        null=True,
        blank=True,
        verbose_name=_('فایل جواب'),
        help_text=_('فایل اپلود شده توسط دانش‌آموز (اختیاری)')
    )
    answered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان جواب')
    )
    teacher_feedback = models.TextField(
        blank=True,
        verbose_name=_('بازخورد معلم'),
        help_text=_('نظرات معلم درباره این جواب')
    )
    
    class Meta:
        verbose_name = _('جواب سوال دانش‌آموز')
        verbose_name_plural = _('جواب‌های سوال دانش‌آموز')
        ordering = ['attempt', 'question__order']
        unique_together = ['attempt', 'question']
        indexes = [
            models.Index(fields=['attempt', 'question']),
            models.Index(fields=['is_correct']),
        ]
    
    def __str__(self):
        return f'{self.attempt.student.username} - سوال {self.question.order}: {self.answer_text[:50] if self.answer_text else "بدون جواب"}'
