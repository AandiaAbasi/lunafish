from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from account.models import User
from core.abstract_models import BaseModel
import uuid


class ClassLevel(BaseModel):
    """سطح‌های کلاسی"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Level name"),
        help_text=_("e.g., Beginner, Elementary, Intermediate, Advanced")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display order")
    )
    
    class Meta:
        ordering = ['order']
        verbose_name = _("Class Level")
        verbose_name_plural = _("Class Levels")
    
    def __str__(self):
        return self.name


class Language(BaseModel):
    """زبان‌های آموزشی"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Language name")
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Language code"),
        help_text=_("ISO 639-1 code (e.g., en, fa, de)")
    )
    
    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
    
    def __str__(self):
        return self.name


class Course(BaseModel):
    """دوره‌های آموزشی"""
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Teacher")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Course title")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        verbose_name=_("Language taught")
    )
    
    level = models.ForeignKey(
        ClassLevel,
        on_delete=models.PROTECT,
        verbose_name=_("Class level")
    )
    
    # Course Details
    max_students = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name=_("Max students per class")
    )
    
    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        verbose_name=_("Lesson duration (minutes)")
    )
    
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Hourly rate"),
        help_text=_("Price per hour in default currency")
    )
    
    # Cover Image
    cover_image = models.ImageField(
        upload_to='courses/covers/',
        blank=True,
        null=True,
        verbose_name=_("Cover image")
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        indexes = [
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['level']),
            models.Index(fields=['language']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"


class Lesson(BaseModel):
    """درس‌های جداگانه در یک دوره"""
    
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_("Course")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Lesson title")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Lesson description")
    )
    
    # Schedule
    scheduled_at = models.DateTimeField(
        verbose_name=_("Scheduled start time")
    )
    
    # Agora Configuration
    agora_channel_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Agora channel ID"),
        help_text=_("Unique channel identifier from Agora")
    )
    
    agora_channel_name = models.CharField(
        max_length=255,
        verbose_name=_("Agora channel name")
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_("Status")
    )
    
    # Actual timing
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual start time")
    )
    
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual end time")
    )
    
    # Recording
    recording_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Recording URL")
    )
    
    is_recorded = models.BooleanField(
        default=True,
        verbose_name=_("Record this lesson")
    )
    
    # Notes
    teacher_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Teacher notes")
    )
    
    class Meta:
        ordering = ['-scheduled_at']
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['agora_channel_id']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title} ({self.scheduled_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_duration_minutes(self):
        """محاسبه مدت کلاس"""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return self.course.duration_minutes
    
    def is_upcoming(self):
        """آیا کلاس هنوز شروع نشده است؟"""
        return self.status == 'scheduled' and timezone.now() < self.scheduled_at
    
    def is_active(self):
        """آیا کلاس در حال برگزاری است؟"""
        return self.status == 'in_progress'
    
    def is_finished(self):
        """آیا کلاس تمام شده است؟"""
        return self.status == 'completed'


class LessonEnrollment(BaseModel):
    """ثبت‌نام دانش‌آموز در یک درس"""
    
    ROLE_CHOICES = [
        ('student', _('Student')),
        ('co_teacher', _('Co-teacher')),
        ('guest', _('Guest')),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Lesson")
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_enrollments',
        verbose_name=_("Student")
    )
    
    # Role in lesson
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name=_("Role")
    )
    
    # Agora Configuration
    agora_uid = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Agora user ID"),
        help_text=_("Assigned by Agora for this user in this channel")
    )
    
    # Attendance tracking
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Time joined")
    )
    
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Time left")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('registered', _('Registered')),
            ('present', _('Present')),
            ('absent', _('Absent')),
            ('cancelled', _('Cancelled')),
        ],
        default='registered',
        verbose_name=_("Status")
    )
    
    # Additional info
    paid = models.BooleanField(
        default=False,
        verbose_name=_("Payment completed")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        unique_together = ['lesson', 'student']
        verbose_name = _("Lesson Enrollment")
        verbose_name_plural = _("Lesson Enrollments")
        indexes = [
            models.Index(fields=['lesson', 'status']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"
    
    def get_attendance_duration_minutes(self):
        """مدت زمان حضور در کلاس"""
        if self.joined_at and self.left_at:
            delta = self.left_at - self.joined_at
            return int(delta.total_seconds() / 60)
        return 0


class LessonMaterial(BaseModel):
    """مواد تکمیلی برای درس"""
    
    MATERIAL_TYPE_CHOICES = [
        ('pdf', _('PDF')),
        ('image', _('Image')),
        ('video', _('Video')),
        ('link', _('External Link')),
        ('document', _('Document')),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name=_("Lesson")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title")
    )
    
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPE_CHOICES,
        verbose_name=_("Material type")
    )
    
    # File/Content
    file = models.FileField(
        upload_to='lesson_materials/',
        blank=True,
        null=True,
        verbose_name=_("File")
    )
    
    external_link = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("External link")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display order")
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = _("Lesson Material")
        verbose_name_plural = _("Lesson Materials")
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class Whiteboard(BaseModel):
    """تخته سفید برای کلاس‌های آنلاین"""
    
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='whiteboard',
        verbose_name=_("Lesson")
    )
    
    # Drawing data (JSON)
    content = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Drawing content"),
        help_text=_("JSON data containing drawing strokes and objects")
    )
    
    is_locked = models.BooleanField(
        default=False,
        verbose_name=_("Lock for students"),
        help_text=_("If locked, only teacher can draw")
    )
    
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whiteboard_edits',
        verbose_name=_("Last modified by")
    )
    
    last_modified_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified at")
    )
    
    class Meta:
        verbose_name = _("Whiteboard")
        verbose_name_plural = _("Whiteboards")
    
    def __str__(self):
        return f"Whiteboard - {self.lesson.title}"


class Quiz(BaseModel):
    """کوییز‌های درسی"""
    
    DIFFICULTY_CHOICES = [
        ('easy', _('Easy')),
        ('medium', _('Medium')),
        ('hard', _('Hard')),
    ]
    
    SUBMISSION_CHOICES = [
        ('manual', _('Manual submission')),
        ('automatic', _('Automatic on timeout')),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quizzes',
        verbose_name=_("Lesson")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Quiz title")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name=_("Difficulty level")
    )
    
    # Quiz Settings
    time_limit_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Time limit (minutes)"),
        help_text=_("Leave empty for no time limit")
    )
    
    passing_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Passing score (%)")
    )
    
    # Attempt settings
    max_attempts = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Maximum attempts"),
        help_text=_("Number of times student can take the quiz")
    )
    
    # When to show
    show_before_lesson = models.BooleanField(
        default=False,
        verbose_name=_("Show before lesson")
    )
    
    show_during_lesson = models.BooleanField(
        default=True,
        verbose_name=_("Show during lesson")
    )
    
    show_after_lesson = models.BooleanField(
        default=True,
        verbose_name=_("Show after lesson")
    )
    
    # Result display settings
    show_results_after_submit = models.BooleanField(
        default=True,
        verbose_name=_("Show results after submit"),
        help_text=_("Show score and results immediately after submission")
    )
    
    allow_review = models.BooleanField(
        default=True,
        verbose_name=_("Allow answer review"),
        help_text=_("Allow students to review answers after submission")
    )
    
    # Randomization
    shuffle_questions = models.BooleanField(
        default=False,
        verbose_name=_("Shuffle questions"),
        help_text=_("Display questions in random order")
    )
    
    shuffle_answers = models.BooleanField(
        default=False,
        verbose_name=_("Shuffle answers"),
        help_text=_("Display answer options in random order")
    )
    
    # Submission method
    submission_method = models.CharField(
        max_length=20,
        choices=SUBMISSION_CHOICES,
        default='manual',
        verbose_name=_("Submission method")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active")
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class QuizQuestion(BaseModel):
    """سؤالات کوییز"""
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', _('Multiple choice')),
        ('true_false', _('True/False')),
        ('fill_blank', _('Fill in the blank')),
        ('short_answer', _('Short answer')),
    ]
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Quiz")
    )
    
    # Question Content
    question_text = models.TextField(
        verbose_name=_("Question text")
    )
    
    # Media attachments
    question_image = models.ImageField(
        upload_to='quiz_questions/images/',
        blank=True,
        null=True,
        verbose_name=_("Question image"),
        help_text=_("Optional image to display with question")
    )
    
    question_audio = models.FileField(
        upload_to='quiz_questions/audio/',
        blank=True,
        null=True,
        verbose_name=_("Question audio"),
        help_text=_("Optional audio file (MP3, WAV, etc.)")
    )
    
    question_video = models.FileField(
        upload_to='quiz_questions/videos/',
        blank=True,
        null=True,
        verbose_name=_("Question video"),
        help_text=_("Optional video file (MP4, WebM, etc.)")
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice',
        verbose_name=_("Question type")
    )
    
    points = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Points")
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=_("Question order")
    )
    
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Explanation"),
        help_text=_("Explanation shown after student answers")
    )
    
    class Meta:
        ordering = ['order']
        verbose_name = _("Quiz Question")
        verbose_name_plural = _("Quiz Questions")
    
    def __str__(self):
        return f"Q{self.order + 1}: {self.question_text[:50]}..."


class QuizAnswer(BaseModel):
    """گزینه‌های جواب برای سؤالات"""
    
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_("Question")
    )
    
    answer_text = models.TextField(
        verbose_name=_("Answer text")
    )
    
    # Optional image for answer
    answer_image = models.ImageField(
        upload_to='quiz_answers/images/',
        blank=True,
        null=True,
        verbose_name=_("Answer image"),
        help_text=_("Optional image to represent this answer option")
    )
    
    is_correct = models.BooleanField(
        default=False,
        verbose_name=_("Is correct answer")
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name=_("Answer order")
    )
    
    class Meta:
        ordering = ['order']
        verbose_name = _("Quiz Answer")
        verbose_name_plural = _("Quiz Answers")
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text[:30]}..."


class StudentQuizAttempt(BaseModel):
    """تلاش دانش‌آموز برای حل کوییز"""
    
    SUBMISSION_STATUS_CHOICES = [
        ('in_progress', _('In progress')),
        ('submitted', _('Submitted')),
        ('timeout', _('Time out')),
    ]
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name=_("Quiz")
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_("Student")
    )
    
    lesson_enrollment = models.ForeignKey(
        LessonEnrollment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Lesson enrollment")
    )
    
    # Attempt details
    attempt_number = models.IntegerField(
        default=1,
        verbose_name=_("Attempt number"),
        help_text=_("Which attempt is this (1st, 2nd, etc.)")
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Started at")
    )
    
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Submitted at")
    )
    
    # Time tracking
    time_taken_minutes = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Time taken (minutes)"),
        help_text=_("Exact duration of quiz attempt")
    )
    
    # Status
    submission_status = models.CharField(
        max_length=20,
        choices=SUBMISSION_STATUS_CHOICES,
        default='in_progress',
        verbose_name=_("Submission status")
    )
    
    is_submitted = models.BooleanField(
        default=False,
        verbose_name=_("Is submitted"),
        help_text=_("Whether student submitted or timeout occurred")
    )
    
    submission_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', _('Manual submission')),
            ('automatic', _('Automatic on timeout')),
        ],
        null=True,
        blank=True,
        verbose_name=_("Submission method")
    )
    
    # Score
    score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Score"),
        help_text=_("Out of 100")
    )
    
    total_points = models.IntegerField(
        default=0,
        verbose_name=_("Total points")
    )
    
    earned_points = models.IntegerField(
        default=0,
        verbose_name=_("Earned points")
    )
    
    passed = models.BooleanField(
        default=False,
        verbose_name=_("Passed quiz")
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = _("Student Quiz Attempt")
        verbose_name_plural = _("Student Quiz Attempts")
        indexes = [
            models.Index(fields=['student', 'quiz']),
            models.Index(fields=['is_submitted']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Attempt {self.attempt_number})"


class StudentQuestionResponse(BaseModel):
    """پاسخ دانش‌آموز به یک سؤال"""
    
    attempt = models.ForeignKey(
        StudentQuizAttempt,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_("Quiz attempt")
    )
    
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        verbose_name=_("Question")
    )
    
    # Answer
    selected_answer = models.ForeignKey(
        QuizAnswer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Selected answer"),
        help_text=_("For multiple choice questions")
    )
    
    text_response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Text response"),
        help_text=_("For short answer questions")
    )
    
    # Time tracking
    response_time_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Response time (seconds)"),
        help_text=_("How long student spent on this question")
    )
    
    # Grading
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_("Is correct")
    )
    
    points_earned = models.IntegerField(
        default=0,
        verbose_name=_("Points earned")
    )
    
    class Meta:
        ordering = ['question__order']
        verbose_name = _("Student Question Response")
        verbose_name_plural = _("Student Question Responses")
        indexes = [
            models.Index(fields=['attempt', 'question']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗" if self.is_correct is False else "?"
        return f"{status} {self.question.question_text[:40]}..."


class Attendance(BaseModel):
    """ثبت حضور و غیاب"""
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_("Lesson")
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_("Student")
    )
    
    STATUS_CHOICES = [
        ('present', _('Present')),
        ('absent', _('Absent')),
        ('late', _('Late')),
        ('excused', _('Excused')),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name=_("Status")
    )
    
    # Timing
    expected_at = models.DateTimeField(
        verbose_name=_("Expected time")
    )
    
    actual_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual join time")
    )
    
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Time left")
    )
    
    # Duration
    minutes_attended = models.IntegerField(
        default=0,
        verbose_name=_("Minutes attended")
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        unique_together = ['lesson', 'student']
        ordering = ['lesson', 'student']
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendance")
        indexes = [
            models.Index(fields=['lesson', 'status']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} ({self.status})"


class Badge(BaseModel):
    """مدال‌ها و جوایز"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Badge name")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    icon = models.ImageField(
        upload_to='badges/',
        verbose_name=_("Badge icon")
    )
    
    color = models.CharField(
        max_length=7,
        default='#FFD700',
        verbose_name=_("Badge color"),
        help_text=_("Hex color code")
    )
    
    # Criteria
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ('lessons_completed', _('Lessons completed')),
            ('score_achieved', _('Quiz score achieved')),
            ('attendance_perfect', _('Perfect attendance')),
            ('participation', _('Active participation')),
            ('custom', _('Custom criteria')),
        ],
        default='custom',
        verbose_name=_("Criteria type")
    )
    
    criteria_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Criteria value"),
        help_text=_("e.g., number of lessons for 'lessons_completed'")
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Badge")
        verbose_name_plural = _("Badges")
    
    def __str__(self):
        return self.name


class StudentBadge(BaseModel):
    """مدال‌های کسب‌شده توسط دانش‌آموزان"""
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_("Student")
    )
    
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='student_badges',
        verbose_name=_("Badge")
    )
    
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Earned at")
    )
    
    class Meta:
        unique_together = ['student', 'badge']
        ordering = ['-earned_at']
        verbose_name = _("Student Badge")
        verbose_name_plural = _("Student Badges")
    
    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"


class StudentProgress(BaseModel):
    """پیشرفت کلی دانش‌آموز"""
    
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name=_("Student")
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name=_("Course")
    )
    
    # Statistics
    total_lessons = models.IntegerField(
        default=0,
        verbose_name=_("Total lessons")
    )
    
    lessons_completed = models.IntegerField(
        default=0,
        verbose_name=_("Lessons completed")
    )
    
    lessons_attended = models.IntegerField(
        default=0,
        verbose_name=_("Lessons attended")
    )
    
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Attendance percentage")
    )
    
    # Scores
    average_quiz_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Average quiz score")
    )
    
    total_points = models.IntegerField(
        default=0,
        verbose_name=_("Total points earned")
    )
    
    # Badges
    badges_earned = models.IntegerField(
        default=0,
        verbose_name=_("Badges earned")
    )
    
    # Last update
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last updated")
    )
    
    class Meta:
        unique_together = ['student', 'course']
        verbose_name = _("Student Progress")
        verbose_name_plural = _("Student Progress")
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class AgoraToken(BaseModel):
    """توکن‌های Agora برای دسترسی محدود‌مدت"""
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='agora_tokens',
        verbose_name=_("Lesson")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agora_tokens',
        verbose_name=_("User")
    )
    
    # Token details
    token = models.TextField(
        verbose_name=_("Access token"),
        help_text=_("JWT token from Agora")
    )
    
    privilege = models.CharField(
        max_length=20,
        choices=[
            ('publisher', _('Publisher')),
            ('subscriber', _('Subscriber')),
        ],
        default='publisher',
        verbose_name=_("Privilege")
    )
    
    # Validity
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Generated at")
    )
    
    expires_at = models.DateTimeField(
        verbose_name=_("Expires at")
    )
    
    is_revoked = models.BooleanField(
        default=False,
        verbose_name=_("Is revoked")
    )
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = _("Agora Token")
        verbose_name_plural = _("Agora Tokens")
        indexes = [
            models.Index(fields=['lesson', 'user']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"
    
    def is_valid(self):
        """آیا توکن هنوز معتبر است؟"""
        return not self.is_revoked and timezone.now() < self.expires_at
