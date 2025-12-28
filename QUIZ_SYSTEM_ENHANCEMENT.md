# 🎯 Quiz System Enhancement Documentation

## خلاصه تغییرات

Quiz System در classroom app بهبود یافت با اضافه شدن آپشن‌های پیشرفته.

---

## 1️⃣ Quiz Model - آپشن‌های جدید

### حداکثر تلاش‌ها
```python
max_attempts = models.IntegerField(default=1)
```
- دانش‌آموز می‌تواند چند بار امتحان دهد
- مثال: `max_attempts=3` یعنی سه بار می‌تونه تلاش کنه

### نمایش نتایج
```python
show_results_after_submit = models.BooleanField(default=True)
```
- آیا نتایج فوری نشان داده شود؟
- اگر `False`: معلم می‌تواند نتایج را بررسی کرد قبل نمایش

### بازنگری جوابات
```python
allow_review = models.BooleanField(default=True)
```
- دانش‌آموز می‌تواند پاسخ‌های خود را بازنگری کند؟
- شامل توضیح برای هر سوال

### تصادفی‌سازی سوالات
```python
shuffle_questions = models.BooleanField(default=False)
```
- سوالات در ترتیب تصادفی نمایش داده شود
- مثال: سوال 3، سوال 1، سوال 2 (نه ترتیب اصلی)

### تصادفی‌سازی گزینه‌ها
```python
shuffle_answers = models.BooleanField(default=False)
```
- گزینه‌های جواب تصادفی شود
- جلوگیری از الگوهای یادگیری غلط

### روش Submit
```python
submission_method = models.CharField(
    choices=[('manual', 'Manual'), ('automatic', 'Automatic on timeout')],
    default='manual'
)
```
- `manual`: دانش‌آموز خود کلیک کند
- `automatic`: وقتی زمان تمام شد خودکار submit شود

---

## 2️⃣ StudentQuizAttempt Model - تغییرات

### شماره تلاش
```python
attempt_number = models.IntegerField(default=1)
```
- کدام تلاش است؟ (1، 2، 3 و...)
- مفید برای معلمان برای دیدن پیشرفت دانش‌آموز

### مدت زمان صرف شده
```python
time_taken_minutes = models.DecimalField()
```
- دقیق چند دقیقه طول کشید
- مثال: `15.5` = 15 دقیقه و 30 ثانیه

### وضعیت Submit
```python
submission_status = models.CharField(
    choices=[
        ('in_progress', 'In progress'),
        ('submitted', 'Submitted'),
        ('timeout', 'Time out')
    ]
)
```
- `in_progress`: هنوز در حال انجام
- `submitted`: دانش‌آموز submit کرد
- `timeout`: زمان تمام شد و خودکار submit شد

### آیا Submit شده؟
```python
is_submitted = models.BooleanField(default=False)
```
- `True`: نتایج نهایی شد
- `False`: هنوز می‌تواند ادامه دهد (اگر وقت دارد)

### روش Submit
```python
submission_method = models.CharField(
    choices=[('manual', 'Manual'), ('automatic', 'Automatic')]
)
```
- چه طریقی submit شد؟
- `manual`: دانش‌آموز خود کلیک کرد
- `automatic`: timeout خودکار

---

## 3️⃣ StudentQuestionResponse Model - آپشن‌های جدید

### زمان پاسخ
```python
response_time_seconds = models.IntegerField(null=True)
```
- چند ثانیه برای این سوال صرف کرد؟
- مثال: `30` = 30 ثانیه
- مفید برای تجزیه و تحلیل سختی سوال

---

## 4️⃣ سرویس‌های جدید

### QuizService Class

#### `calculate_attempt_score(attempt)`
```python
score_data = QuizService.calculate_attempt_score(attempt)
# Returns: {
#     'score': 85,
#     'total_points': 100,
#     'earned_points': 85,
#     'correct_count': 17,
#     'wrong_count': 3,
#     'passed': True
# }
```

#### `submit_attempt(attempt, method='manual')`
```python
attempt = QuizService.submit_attempt(attempt, method='manual')
# خودکار محاسبه می‌کند:
# - نمره نهایی
# - مدت زمان صرف شده
# - پاس/رسوب
```

#### `can_attempt_quiz(quiz, student, attempts_made)`
```python
can_attempt, reason = QuizService.can_attempt_quiz(quiz, student, 2)
# Checks:
# - آیا quiz فعال است؟
# - آیا شاگرد تعداد تلاش بیشتری داشته؟
# Returns: (True/False, 'reason')
```

#### `auto_submit_on_timeout(attempt)`
```python
attempt = QuizService.auto_submit_on_timeout(attempt)
# اگر زمان تمام شد:
# - خودکار submit می‌کند
# - وضعیت = 'timeout'
# - روش = 'automatic'
```

#### `get_response_summary(attempt)`
```python
summary = QuizService.get_response_summary(attempt)
# Returns: {
#     'attempt_id': 10,
#     'quiz_title': 'Quiz 1',
#     'student': 'ali_123',
#     'score': 85,
#     'passed': True,
#     'questions': [
#         {
#             'question_text': '...',
#             'selected_answer': '...',
#             'is_correct': True,
#             'points_earned': 10,
#             'explanation': '...'
#         }
#     ]
# }
```

---

## 5️⃣ فلو جدید Quiz

### ابتدای آزمون
```
1. Student: "Start Quiz"
2. System: چک کن attempt_number < max_attempts
3. System: ایجاد StudentQuizAttempt (submission_status='in_progress')
4. System: Shuffle questions/answers اگر enabled
5. UI: نمایش سوالات
```

### جواب دادن سوال
```
1. Student: سوال رو می‌خونه و جواب می‌دهد
2. System: ذخیره response_time_seconds
3. System: ذخیره selected_answer یا text_response
4. System: محاسبه is_correct
5. UI: نشان بدن explanation اگر allow_review=True
```

### پایان آزمون
```
Option A - Manual Submit:
  1. Student: کلیک "Submit Quiz"
  2. System: QuizService.submit_attempt(method='manual')
  3. System: محاسبه نمره نهایی
  4. UI: نمایش results اگر show_results_after_submit=True

Option B - Auto Submit on Timeout:
  1. Timer: به 0 رسید
  2. System: QuizService.auto_submit_on_timeout()
  3. System: submission_status = 'timeout'
  4. System: submission_method = 'automatic'
  5. UI: نمایش results
```

---

## 6️⃣ Serializers بروز شده

### QuizListSerializer / QuizDetailSerializer
```python
# اضافه شده:
'max_attempts',
'show_results_after_submit',
'allow_review',
'shuffle_questions',
'shuffle_answers',
'submission_method'
```

### StudentQuizAttemptListSerializer / DetailSerializer
```python
# اضافه شده:
'attempt_number',
'time_taken_minutes',
'submission_status',
'is_submitted',
'submission_method'
```

### StudentQuestionResponseSerializer
```python
# اضافه شده:
'response_time_seconds'
```

---

## 7️⃣ Views بروز شده

### `StudentQuizAttemptViewSet`

#### `start_attempt` (POST)
```python
POST /api/classroom/quiz-attempts/start_attempt/
{
  "quiz_id": 1
}
```
- چک می‌کند: max_attempts
- سازمان: LessonEnrollment
- برمی‌گرداند: attempt object

#### `submit` (POST)
```python
POST /api/classroom/quiz-attempts/{id}/submit/
{
  "method": "manual"  # optional
}
```
- محاسبه نمره خودکار
- محاسبه مدت زمان
- برمی‌گرداند: نتیجه نهایی

---

## 8️⃣ نمونه استفاده

### Backend
```python
from classroom.services import QuizService
from classroom.models import StudentQuizAttempt, Quiz

# 1. Start attempt
attempt = StudentQuizAttempt.objects.create(
    quiz=quiz,
    student=student,
    attempt_number=1
)

# 2. Student answers questions (already saved via API)

# 3. Submit attempt
attempt = QuizService.submit_attempt(attempt, method='manual')

# 4. Get summary
summary = QuizService.get_response_summary(attempt)

# 5. Check if can retry
can_retry, reason = QuizService.can_attempt_quiz(quiz, student, 1)
```

### Frontend (JavaScript/React)
```javascript
// 1. Start quiz
const response = await api.post('/quiz-attempts/start_attempt/', {
  quiz_id: 1
});
const attempt_id = response.data.id;

// 2. Start timer
const time_limit = response.data.quiz.time_limit_minutes * 60;
let timeLeft = time_limit;

// 3. User answers questions
// API call for each answer with response_time

// 4. Submit
const result = await api.post(
  `/quiz-attempts/${attempt_id}/submit/`,
  { method: 'manual' }
);

// 5. Show results
console.log(`Score: ${result.data.score}%`);
console.log(`Passed: ${result.data.passed}`);

// 6. Check for review
if (result.data.quiz.allow_review) {
  // Show detailed response review
}
```

---

## 9️⃣ Migration

فایل migration شامل:
- تمام فیلدهای جدید
- حذف constraint قدیمی
- اضافه کردن indexes برای performance

```bash
python manage.py migrate classroom
```

---

## ✅ نکات مهم

1. **Automatic Submit**: اگر `submission_method='automatic'`، timer باید کار کند و خودکار submit کند
2. **Shuffle**: اگر enabled، قبل از نمایش شافل کنید
3. **Review**: اگر `allow_review=False`، توضیحات را نشان ندهید
4. **Attempts**: درست تعداد تلاش‌ها را کنترل کنید
5. **Scoring**: نمره خودکار محاسبه می‌شود بر اساس correct/incorrect

---

**توضیح کافی است؟ سؤالی داری؟** 🎯
