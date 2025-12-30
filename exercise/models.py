from django.db import models
from django.conf import settings
from safedelete import SOFT_DELETE_CASCADE
from core.abstract_models import BaseModel
from django.utils.translation import gettext_lazy as _


class Field(BaseModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

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

    correct_answer = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Correct Answer"),
        help_text=_("For text/input questions - teacher's answer key for grading")
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
        verbose_name=_("Option")
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
