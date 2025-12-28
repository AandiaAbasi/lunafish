# 📚 Classroom App - مدل‌های سیستم کلاس آنلاین

## 📋 نمای کلی

اپ `classroom` برای مدیریت کلاس‌های آنلاین با **Agora** و تمام ابزارهای آموزشی طراحی شده است.

---

## 🏗️ معماری مدل‌ها

### 1️⃣ **مدل‌های سطح دوره و زبان**

#### `ClassLevel`
سطح‌های تدریس (مبتدی، متوسط، پیشرفته)
```
- name: نام سطح
- description: توضیح
- order: ترتیب نمایش
```

#### `Language`
زبان‌های آموزشی
```
- name: نام زبان
- code: کد ISO (en, fa, de)
```

---

### 2️⃣ **مدل‌های دوره و درس**

#### `Course` (دوره)
دوره‌های آموزشی توسط معلم
```
- teacher: معلم
- title: نام دوره
- description: توضیح
- language: زبان تدریس
- level: سطح
- max_students: حد اکثر دانش‌آموز
- duration_minutes: مدت درس
- hourly_rate: نرخ ساعتی
- cover_image: تصویر
- is_active: فعال/غیرفعال
```

#### `Lesson` (درس)
درس‌های جداگانه در یک دوره
```
- course: دوره
- title: عنوان درس
- scheduled_at: زمان برنامه‌ریزی شده
- agora_channel_id: ID کانال Agora (منحصربه‌فرد)
- agora_channel_name: نام کانال Agora
- status: scheduled / in_progress / completed / cancelled
- started_at: زمان شروع واقعی
- ended_at: زمان پایان واقعی
- recording_url: URL ضبط شده
- is_recorded: آیا ضبط شود
- teacher_notes: یادداشت‌های معلم
```

---

### 3️⃣ **مدل‌های ثبت‌نام و شرکت**

#### `LessonEnrollment` (ثبت‌نام)
ثبت‌نام دانش‌آموز در درس
```
- lesson: درس
- student: دانش‌آموز
- role: student / co_teacher / guest
- agora_uid: ID کاربر در Agora
- joined_at: زمان ورود
- left_at: زمان خروج
- status: registered / present / absent / cancelled
- paid: پرداخت انجام شد؟
- notes: یادداشت‌ها
```

#### `LessonMaterial` (مواد درسی)
فایل‌ها و مواد تکمیلی
```
- lesson: درس
- title: عنوان
- material_type: pdf / image / video / link / document
- file: فایل
- external_link: لینک بیرونی
- description: توضیح
- order: ترتیب
```

---

### 4️⃣ **مدل‌های تخته سفید و سازمان**

#### `Whiteboard` (تخته سفید)
تخته سفید برای درس
```
- lesson: درس (OneToOne)
- content: داده‌های JSON
- is_locked: قفل برای دانش‌آموزان
- last_modified_by: آخرین ویرایش‌کننده
- last_modified_at: زمان آخرین ویرایش
```

---

### 5️⃣ **مدل‌های کوییز**

#### `Quiz` (کوییز)
کوییز‌های درسی
```
- lesson: درس
- title: عنوان
- difficulty: easy / medium / hard
- time_limit_minutes: محدودیت زمانی
- passing_score: نمره قبول
- show_before_lesson: نمایش قبل درس
- show_during_lesson: نمایش حین درس
- show_after_lesson: نمایش بعد درس
- is_active: فعال
```

#### `QuizQuestion` (سؤال)
سؤالات کوییز
```
- quiz: کوییز
- question_text: متن سؤال
- question_type: multiple_choice / true_false / fill_blank / short_answer
- points: امتیاز
- order: ترتیب
- explanation: توضیح پاسخ
```

#### `QuizAnswer` (گزینه جواب)
گزینه‌های جواب
```
- question: سؤال
- answer_text: متن جواب
- is_correct: جواب درست
- order: ترتیب
```

#### `StudentQuizAttempt` (تلاش دانش‌آموز)
هر تلاش دانش‌آموز برای حل کوییز
```
- quiz: کوییز
- student: دانش‌آموز
- lesson_enrollment: ثبت‌نام درس
- started_at: زمان شروع
- submitted_at: زمان تکمیل
- score: نمره (۰-۱۰۰)
- total_points: کل امتیاز
- earned_points: امتیاز کسب‌شده
- passed: قبول شد؟
```

#### `StudentQuestionResponse` (پاسخ دانش‌آموز)
پاسخ هر دانش‌آموز به سؤال
```
- attempt: تلاش
- question: سؤال
- selected_answer: جواب انتخابی
- text_response: جواب متنی
- is_correct: درست یا نادرست
- points_earned: امتیاز کسب‌شده
- answered_at: زمان پاسخ
```

---

### 6️⃣ **مدل‌های حضور و مشارکت**

#### `Attendance` (حضور و غیاب)
ثبت حضور و غیاب
```
- lesson: درس
- student: دانش‌آموز
- status: present / absent / late / excused
- expected_at: زمان انتظار
- actual_joined_at: زمان ورود واقعی
- left_at: زمان خروج
- minutes_attended: دقیقه‌های حاضری
- notes: یادداشت‌ها
```

#### `Badge` (مدال)
مدال‌ها و جوایز
```
- name: نام مدال
- description: توضیح
- icon: تصویر آیکن
- color: رنگ
- criteria_type: معیار (lessons_completed / score_achieved / attendance_perfect / etc)
- criteria_value: مقدار معیار
```

#### `StudentBadge` (مدال‌های کسب‌شده)
مدال‌های کسب‌شده توسط دانش‌آموزان
```
- student: دانش‌آموز
- badge: مدال
- earned_at: تاریخ کسب
```

---

### 7️⃣ **مدل‌های پیشرفت و Agora**

#### `StudentProgress` (پیشرفت)
خلاصه پیشرفت دانش‌آموز در دوره
```
- student: دانش‌آموز (OneToOne)
- course: دوره
- total_lessons: کل درس‌ها
- lessons_completed: درس‌های تکمیل‌شده
- lessons_attended: درس‌های حاضر
- attendance_percentage: درصد حضور
- average_quiz_score: میانگین نمرات
- total_points: کل امتیاز
- badges_earned: مدال‌های کسب‌شده
- last_updated: آخرین بروزرسانی
```

#### `AgoraToken` (توکن Agora)
توکن‌های دسترسی محدود‌مدت برای Agora
```
- lesson: درس
- user: کاربر
- token: توکن JWT
- privilege: publisher / subscriber
- generated_at: زمان ایجاد
- expires_at: زمان انقضاء
- is_revoked: منسوخ شده
```

---

## 🔄 روابط مدل‌ها

```
Course
├── Lesson (1:M)
│   ├── LessonEnrollment (1:M)
│   │   └── Student (FK)
│   ├── LessonMaterial (1:M)
│   ├── Quiz (1:M)
│   │   ├── QuizQuestion (1:M)
│   │   │   └── QuizAnswer (1:M)
│   │   └── StudentQuizAttempt (1:M)
│   │       └── StudentQuestionResponse (1:M)
│   ├── Whiteboard (1:1)
│   ├── Attendance (1:M)
│   └── AgoraToken (1:M)
│       └── User (FK)
├── StudentProgress (1:M)
└── Teacher (FK to User)

Badge (M:M with Student via StudentBadge)
Language
ClassLevel
```

---

## 📡 API Endpoints

### **Courses**
- `GET /api/classroom/courses/` - لیست دوره‌ها
- `POST /api/classroom/courses/` - ایجاد دوره
- `GET /api/classroom/courses/{id}/` - جزئیات دوره
- `PUT/PATCH /api/classroom/courses/{id}/` - بروزرسانی
- `DELETE /api/classroom/courses/{id}/` - حذف

### **Lessons**
- `GET /api/classroom/lessons/` - لیست درس‌ها
- `POST /api/classroom/lessons/{id}/start_lesson/` - شروع درس
- `POST /api/classroom/lessons/{id}/end_lesson/` - پایان درس
- `GET /api/classroom/lessons/{id}/participants/` - شرکت‌کنندگان

### **Enrollments**
- `GET /api/classroom/enrollments/` - ثبت‌نام‌های من
- `POST /api/classroom/enrollments/enroll/` - ثبت‌نام در درس

### **Quizzes**
- `GET /api/classroom/quizzes/` - لیست کوییز‌ها
- `GET /api/classroom/quizzes/{id}/` - جزئیات کوییز
- `POST /api/classroom/quiz-attempts/start_attempt/` - شروع کوییز

### **Progress & Attendance**
- `GET /api/classroom/progress/` - پیشرفت من
- `GET /api/classroom/attendance/` - حضور و غیاب

### **Agora Tokens**
- `POST /api/classroom/agora-tokens/generate_token/` - ایجاد توکن Agora

---

## ⚙️ نصب و تنظیم

### 1. اضافه کردن به `INSTALLED_APPS`
```python
# settings.py
INSTALLED_APPS = [
    ...
    'classroom',
]
```

### 2. اضافه کردن URL‌ها
```python
# urls.py
urlpatterns = [
    ...
    path('api/classroom/', include('classroom.urls')),
]
```

### 3. تنظیم Agora
```python
# settings.py
AGORA_APP_ID = 'your_agora_app_id'
AGORA_APP_CERTIFICATE = 'your_agora_app_certificate'
```

### 4. Migration
```bash
python manage.py makemigrations classroom
python manage.py migrate classroom
```

---

## 🎯 نمونه استفاده

### ایجاد دوره
```python
from classroom.models import Course, ClassLevel, Language
from account.models import User

teacher = User.objects.get(username='teacher1')
level = ClassLevel.objects.get(name='Beginner')
language = Language.objects.get(code='en')

course = Course.objects.create(
    teacher=teacher,
    title='English for Kids',
    language=language,
    level=level,
    max_students=8,
    duration_minutes=60,
    hourly_rate=50.00
)
```

### ایجاد درس
```python
from classroom.models import Lesson
from django.utils import timezone

lesson = Lesson.objects.create(
    course=course,
    title='Lesson 1: Hello',
    scheduled_at=timezone.now() + timezone.timedelta(days=1),
    agora_channel_name='english-kids-01',
    agora_channel_id='ch-1001',
    is_recorded=True
)
```

### ثبت‌نام دانش‌آموز
```python
from classroom.models import LessonEnrollment

student = User.objects.get(username='student1')
enrollment = LessonEnrollment.objects.create(
    lesson=lesson,
    student=student,
    role='student'
)
```

### ایجاد کوییز
```python
from classroom.models import Quiz, QuizQuestion, QuizAnswer

quiz = Quiz.objects.create(
    lesson=lesson,
    title='Quiz 1',
    difficulty='medium',
    passing_score=70
)

question = QuizQuestion.objects.create(
    quiz=quiz,
    question_text='What is "Hello" in English?',
    question_type='multiple_choice',
    points=10,
    order=1
)

QuizAnswer.objects.create(
    question=question,
    answer_text='Greeting',
    is_correct=True,
    order=1
)
```

---

## 📊 Admin Panel

همه مدل‌ها در Django Admin ثبت‌شده‌اند با:
- ✅ List display مناسب
- ✅ Search و filter
- ✅ Inline editing
- ✅ Custom actions
- ✅ Readonly fields برای timestamps

---

## 🚀 بعدی

- [ ] Integration با Agora SDK
- [ ] Real-time updates (WebSocket)
- [ ] Payment integration
- [ ] Certificate generation
- [ ] Student reports
- [ ] Teacher analytics
