from django.db import models
from django.conf import settings
from safedelete import SOFT_DELETE_CASCADE
from core.abstract_models import BaseModel
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Field(BaseModel):
    _safedelete_policy = SOFT_DELETE_CASCADE
    
    TYPE_CHOICES = [
        ('input', _('تایپی')),          
        ('checkbox', _('چند گزینه ای')),   
        ('radioButton', _('تک گزینه ای')),             
    ]
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_fields',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Teacher"),
        help_text=_("Teacher who created this question")
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title")
    )

    sort = models.BigIntegerField(
        default=0,
        verbose_name=_("Sort")
    )

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name=_("Type")
    )

    is_required = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Is Required"),
        help_text=_("Is Required Help")  # 0 -> not required, 1 -> required
    )

    image_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Image")
    )

    audio_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Audio")
    )

    video_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Video")
    )

    icon_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Icon")
    )

    guide = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Guide")
    )

    des = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description")
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.title
    

class FieldDetail(BaseModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_("Question")
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title")
    )

    second_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Second Title")
    )

    is_required = models.SmallIntegerField(
        default=0,
        verbose_name=_("Is Required")
    )

    image_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Image")
    )

    is_correct = models.SmallIntegerField(
        default=-1,
        verbose_name=_("Is Correct")
    )

    correct_answer = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Correct Answer"),
        help_text=_("For text/input questions - teacher's answer key for grading")
    )

    guide = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Guide")
    )

    des = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description")
    )

    sort = models.BigIntegerField(
        default=0,
        verbose_name=_("Sort")
    )

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return f"{self.field} - {self.title}"


class CategoryField(BaseModel):
    _safedelete_policy = SOFT_DELETE_CASCADE
    
    TYPE_CHOICES = [
        ('input', _('تایپی')),          
        ('checkbox', _('چند گزینه ای')),   
        ('radioButton', _('تک گزینه ای')),             
    ]
    
    teachingsubject = models.ForeignKey(
        'classroom.TeachingSubject',
        on_delete=models.CASCADE,
        related_name='category_fields',
        verbose_name=_("Classroom Teaching Subject")
    )

    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='category_fields',
        verbose_name=_("Question")
    )

    step = models.BigIntegerField(
        verbose_name=_("Step")
    )

    sort = models.BigIntegerField(
        verbose_name=_("Sort")
    )

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name=_("Type")
    )

    is_conditional = models.BooleanField(
        default=False,
        verbose_name=_("Is Conditional")
    )

    class Meta:
        ordering = ['step', 'sort']
        verbose_name = _("Exam")
        verbose_name_plural = _("Exams")
    
    def __str__(self):
        return f"{self.teachingsubject} - {self.field}"


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_("User")
    )

    teachingsubject = models.ForeignKey(
        'classroom.TeachingSubject',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_("Teaching Subject")
    )

    score = models.IntegerField(
        default=0,
        verbose_name=_("Score")
    )

    correct = models.IntegerField(
        default=0,
        verbose_name=_("Correct")
    )

    incorrect = models.IntegerField(
        default=0,
        verbose_name=_("Incorrect")
    )

    class Meta:
        verbose_name = _("Attempt")
        verbose_name_plural = _("Attempts")

    def __str__(self):
        return f"Attempt #{self.id}"
    
    # ========== Rating & Medal Methods ==========
    
    def has_rating(self):
        """بررسی اینکه آیا این تمرین امتیاز داده شده است"""
        return hasattr(self, 'rating') and self.rating is not None
    
    def has_medals(self):
        """بررسی اینکه آیا این تمرین مدال دریافت کرده است"""
        return self.medals.exists()
    
    def get_rating(self):
        """دریافت امتیاز این تمرین"""
        return getattr(self, 'rating', None)
    
    def get_medals(self):
        """دریافت تمام مدال‌های این تمرین"""
        return self.medals.all()
    
    def get_rating_stats(self):
        """
        اطلاعات امتیاز و ستاره این تمرین
        """
        if self.has_rating():
            rating = self.get_rating()
            return {
                'score': rating.score,
                'stars': rating.stars,
                'comment': rating.comment,
                'rating_type': rating.rating_type,
                'given_at': rating.created_at,
                'teacher_name': rating.teacher.name or rating.teacher.username
            }
        return None


class OrderDetail(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_("Answer")
    )

    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='order_details',
        verbose_name=_("Question")
    )

    field_detail = models.ForeignKey(
        FieldDetail,
        on_delete=models.CASCADE,
        related_name='order_details',
        verbose_name=_("Option"),
        null=True,
        blank=True
    )

    value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Answer")
    )

    score = models.IntegerField(
        default=0,
        verbose_name=_("Score")
    )

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")

    def __str__(self):
        return f"Answer #{self.id} for Answer #{self.order.id}"


# ========== Student Rating & Medal System ==========

class StudentRating(BaseModel):
    """
    امتیاز و ستاره‌ای که معلم به دانش‌آموز می‌دهد
    
    معلم می‌تواند:
    - امتیاز (0-100) بدهد
    - ستاره (1-5) بدهد
    - این امتیاز برای تمرین یا فعالیت کلاس باشد
    """
    RATING_TYPE_CHOICES = [
        ('exercise', _('Exercise')),           # تمرین
        ('activity', _('Class Activity')),     # فعالیت کلاس
        ('participation', _('Participation')), # مشارکت
        ('behavior', _('Behavior')),           # رفتار
        ('other', _('Other')),                 # دیگر
    ]
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_ratings',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Teacher"),
        help_text=_("معلمی که این امتیاز را داده است")
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_ratings',
        limit_choices_to={'role': 'user'},
        verbose_name=_("Student"),
        help_text=_("دانش‌آموزی که امتیاز دریافت کرده است")
    )
    
    teachingsubject = models.ForeignKey(
        'classroom.TeachingSubject',
        on_delete=models.CASCADE,
        related_name='student_ratings',
        verbose_name=_("Teaching Subject"),
        help_text=_("درسی که این امتیاز برای آن است")
    )
    
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rating',
        verbose_name=_("Exercise/Attempt"),
        help_text=_("تمرین یا آزمونی که این امتیاز برای آن است (اختیاری)")
    )
    
    rating_type = models.CharField(
        max_length=20,
        choices=RATING_TYPE_CHOICES,
        default='exercise',
        verbose_name=_("Rating Type"),
        help_text=_("نوع امتیازدهی")
    )
    
    score = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name=_("Score"),
        help_text=_("امتیاز (0-100)")
    )
    
    stars = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        verbose_name=_("Stars"),
        help_text=_("ستاره (0-5)")
    )
    
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Comment"),
        help_text=_("نظر معلم در مورد عملکرد دانش‌آموز")
    )
    
    class Meta:
        verbose_name = _("Student Rating")
        verbose_name_plural = _("Student Ratings")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['teachingsubject']),
        ]
        unique_together = ('student', 'order')  # هر تمرین فقط یک امتیاز
    
    def __str__(self):
        return f"{self.student.name or self.student.username} - {self.score}/100 - {self.stars}⭐"


class StudentMedal(BaseModel):
    """
    مدال‌هایی که معلم به دانش‌آموز می‌دهد
    
    مدال معمولاً به خاطر:
    - حل درست تمرین
    - انجام بهتر فعالیت کلاس
    - بیشتر شرکت کردن
    - رفتار خوب
    """
    MEDAL_TYPE_CHOICES = [
        ('gold', _('Gold')),          # طلایی
        ('silver', _('Silver')),      # نقره‌ای
        ('bronze', _('Bronze')),      # برنزی
        ('star', _('Star')),          # ستاره
        ('heart', _('Heart')),        # قلب
        ('trophy', _('Trophy')),      # جام
        ('certificate', _('Certificate')),  # گواهی
        ('badge', _('Badge')),        # نشان
        ('achievement', _('Achievement')),  # دستاورد
        ('custom', _('Custom')),      # سفارشی
    ]
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_medals',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Teacher"),
        help_text=_("معلمی که این مدال را داده است")
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_medals',
        limit_choices_to={'role': 'user'},
        verbose_name=_("Student"),
        help_text=_("دانش‌آموزی که مدال دریافت کرده است")
    )
    
    teachingsubject = models.ForeignKey(
        'classroom.TeachingSubject',
        on_delete=models.CASCADE,
        related_name='student_medals',
        verbose_name=_("Teaching Subject"),
        help_text=_("درسی که این مدال برای آن است")
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medals',
        verbose_name=_("Exercise/Attempt"),
        help_text=_("تمرین یا آزمونی که این مدال برای آن است (اختیاری)")
    )
    
    medal_type = models.CharField(
        max_length=20,
        choices=MEDAL_TYPE_CHOICES,
        default='gold',
        verbose_name=_("Medal Type"),
        help_text=_("نوع مدال")
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_("Medal Title"),
        help_text=_("عنوان مدال (مثال: حل صحیح تمام سؤالات)")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("توضیح مدال")
    )
    
    icon_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Icon URL"),
        help_text=_("URL تصویر مدال")
    )
    
    class Meta:
        verbose_name = _("Student Medal")
        verbose_name_plural = _("Student Medals")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['teacher']),
            models.Index(fields=['teachingsubject']),
        ]
    
    def __str__(self):
        return f"{self.student.name or self.student.username} - {self.title}"
