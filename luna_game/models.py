from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class SyncableQuerySet(models.QuerySet):
    """Soft-delete records so offline clients can receive removals in delta sync."""

    def delete(self):
        count = self.update(is_active=False, updated_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self):
        return super().delete()

    def active(self):
        return self.filter(is_active=True)


class SyncableModel(models.Model):
    is_active = models.BooleanField("فعال", default=True, db_index=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True, db_index=True)

    objects = SyncableQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.updated_at = timezone.now()
        self.save(update_fields=["is_active", "updated_at"], using=using)
        return 1, {self._meta.label: 1}

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


class GameLevel(SyncableModel):
    class Audience(models.TextChoices):
        CHILD = "child", "کودک"
        TEEN = "teen", "نوجوان"
        ADULT = "adult", "بزرگسال"

    code = models.SlugField("کد سطح", max_length=50, unique=True)
    title = models.CharField("عنوان سطح", max_length=100)
    description = models.TextField("توضیحات", blank=True)
    audience = models.CharField("گروه سنی", max_length=10, choices=Audience.choices, default=Audience.CHILD)
    order = models.PositiveSmallIntegerField("ترتیب", default=1, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "سطح بازی"
        verbose_name_plural = "سطح‌های بازی"

    def __str__(self):
        return self.title


class GameStage(SyncableModel):
    level = models.ForeignKey(
        GameLevel,
        on_delete=models.PROTECT,
        related_name="stages",
        verbose_name="سطح",
    )
    code = models.SlugField("کد مرحله", max_length=70, unique=True)
    title = models.CharField("عنوان مرحله", max_length=100)
    order = models.PositiveSmallIntegerField("ترتیب در سطح", default=1)
    min_difficulty = models.PositiveSmallIntegerField(
        "حداقل سختی",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    max_difficulty = models.PositiveSmallIntegerField(
        "حداکثر سختی",
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    pairs_per_round = models.PositiveSmallIntegerField(
        "تعداد جفت در هر دور",
        default=8,
        validators=[MinValueValidator(2), MaxValueValidator(12)],
    )
    rounds_to_unlock = models.PositiveSmallIntegerField(
        "تعداد دور موفق برای عبور",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
    )
    max_mistakes = models.PositiveSmallIntegerField(
        "حداکثر اشتباه برای ثبت دور موفق",
        default=8,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    time_limit_seconds = models.PositiveIntegerField("محدودیت زمانی به ثانیه", null=True, blank=True)

    class Meta:
        ordering = ["level__order", "order", "id"]
        verbose_name = "مرحله بازی"
        verbose_name_plural = "مرحله‌های بازی"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_difficulty__lte=models.F("max_difficulty")),
                name="luna_stage_valid_difficulty_range",
            ),
        ]
        indexes = [
            models.Index(fields=["level", "is_active", "order"], name="luna_stage_level_idx"),
        ]

    def clean(self):
        super().clean()
        if self.min_difficulty > self.max_difficulty:
            raise ValidationError({"max_difficulty": "حداکثر سختی نمی‌تواند از حداقل سختی کمتر باشد."})

    def __str__(self):
        return f"{self.level.title} - {self.title}"


class WordTopic(SyncableModel):
    code = models.SlugField("کد موضوع", max_length=50, unique=True)
    title = models.CharField("عنوان موضوع", max_length=100)
    order = models.PositiveSmallIntegerField("ترتیب", default=1)

    class Meta:
        ordering = ["order", "title", "id"]
        verbose_name = "موضوع کلمه"
        verbose_name_plural = "موضوعات کلمات"

    def __str__(self):
        return self.title


class WordPair(SyncableModel):
    level = models.ForeignKey(
        GameLevel,
        on_delete=models.PROTECT,
        related_name="word_pairs",
        verbose_name="سطح",
    )
    topic = models.ForeignKey(
        WordTopic,
        on_delete=models.PROTECT,
        related_name="word_pairs",
        verbose_name="موضوع",
        null=True,
        blank=True,
    )
    en = models.CharField("کلمه انگلیسی", max_length=150)
    fa = models.CharField("معنی فارسی", max_length=150)
    difficulty = models.PositiveSmallIntegerField(
        "درجه سختی",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        db_index=True,
    )
    admin_note = models.CharField("یادداشت ادمین", max_length=255, blank=True)

    class Meta:
        ordering = ["level__order", "difficulty", "id"]
        verbose_name = "جفت کلمه"
        verbose_name_plural = "جفت‌های کلمه"
        constraints = [
            models.UniqueConstraint(fields=["level", "en", "fa"], name="luna_unique_pair_per_level"),
        ]
        indexes = [
            models.Index(fields=["level", "is_active", "difficulty"], name="luna_word_level_diff_idx"),
            models.Index(fields=["topic", "is_active"], name="luna_word_topic_idx"),
        ]

    def clean(self):
        super().clean()
        self.en = (self.en or "").strip()
        self.fa = (self.fa or "").strip()
        if not self.en:
            raise ValidationError({"en": "کلمه انگلیسی الزامی است."})
        if not self.fa:
            raise ValidationError({"fa": "معنی فارسی الزامی است."})

    def save(self, *args, **kwargs):
        self.en = (self.en or "").strip()
        self.fa = (self.fa or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.en} — {self.fa}"
