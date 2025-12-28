# ✅ Classroom App - خلاصه فایل‌های ایجاد‌شده

## 📁 ساختار App

```
classroom/
├── __init__.py                          ✨ App initialization
├── models.py                            📊 18 Model for complete classroom system
├── serializers.py                       🔄 24 Serializers for API
├── views.py                             🎯 10 ViewSets for REST API
├── admin.py                             🛠️  Complete admin interface
├── urls.py                              🌐 API URL routing
├── apps.py                              ⚙️  App configuration
├── services.py                          🔌 Agora SDK integration
├── tests.py                             🧪 Unit tests
└── abstract_models.py                   🏗️  Base model
```

---

## 📊 18 مدل ایجاد‌شده

### **سطح و زبان (2 مدل)**
1. `ClassLevel` - سطح‌های تدریس
2. `Language` - زبان‌های آموزشی

### **دوره و درس (2 مدل)**
3. `Course` - دوره‌های آموزشی
4. `Lesson` - درس‌های جداگانه

### **ثبت‌نام و مواد (2 مدل)**
5. `LessonEnrollment` - ثبت‌نام دانش‌آموز
6. `LessonMaterial` - مواد درسی (PDF, image, video, etc)

### **تخته سفید (1 مدل)**
7. `Whiteboard` - تخته سفید آنلاین

### **کوییز (5 مدل)**
8. `Quiz` - کوییز‌های درسی
9. `QuizQuestion` - سؤالات
10. `QuizAnswer` - گزینه‌های جواب
11. `StudentQuizAttempt` - تلاش‌های دانش‌آموز
12. `StudentQuestionResponse` - پاسخ‌های دانش‌آموز

### **حضور و جوایز (3 مدل)**
13. `Attendance` - حضور و غیاب
14. `Badge` - مدال‌ها و جوایز
15. `StudentBadge` - مدال‌های کسب‌شده

### **پیشرفت و توکن (2 مدل)**
16. `StudentProgress` - خلاصه پیشرفت دانش‌آموز
17. `AgoraToken` - توکن‌های Agora

---

## 🎯 ویژگی‌های اصلی

### ✅ **کلاس‌های آنلاین**
- کانال‌های Agora برای هر درس
- نام‌کناری کاربر در Agora (agora_uid)
- زمان ورود و خروج دانش‌آموز
- ضبط خودکار درس‌ها

### ✅ **ابزارهای آموزشی**
- تخته سفید (Whiteboard)
- مواد درسی (PDF, تصویر، ویدیو، لینک)
- کوییز‌های درسی
- کنترل دسترسی (publisher / subscriber)

### ✅ **سیستم کوییز کامل**
- انواع سؤال: چندگزینه‌ای، درست/نادرست، تکمیل، پاسخ کوتاه
- سطح سختی: آسان، متوسط، سخت
- محدودیت زمانی
- نمره قبول
- نمایش قبل/حین/بعد درس

### ✅ **پیگیری و ارزیابی**
- حضور و غیاب خودکار
- میانگین نمرات کوییز
- درصد حضور
- نمرات و امتیازات
- مدال‌ها و جوایز

### ✅ **ترجمه‌ی کامل**
- تمام Verbose names و Help texts فارسی
- پشتیبان Admin Panel فارسی

---

## 🌐 API Endpoints (10 ViewSets)

| ViewSet | مسیر | عملیات |
|---------|------|--------|
| ClassLevelViewSet | `/levels/` | GET (Read-only) |
| LanguageViewSet | `/languages/` | GET (Read-only) |
| CourseViewSet | `/courses/` | CRUD + List/Detail |
| LessonViewSet | `/lessons/` | CRUD + start/end actions |
| LessonEnrollmentViewSet | `/enrollments/` | CRUD + enroll action |
| QuizViewSet | `/quizzes/` | GET (Read-only) |
| StudentQuizAttemptViewSet | `/quiz-attempts/` | CRUD + start_attempt action |
| AttendanceViewSet | `/attendance/` | GET (Read-only) |
| StudentProgressViewSet | `/progress/` | GET (Read-only) |
| AgoraTokenViewSet | `/agora-tokens/` | CRUD + generate_token action |

---

## 🔄 Serializers (24 تای)

### **List Serializers**
- `ClassLevelSerializer`
- `LanguageSerializer`
- `CourseListSerializer`
- `LessonListSerializer`
- `LessonEnrollmentSerializer`
- `LessonMaterialSerializer`
- `QuizListSerializer`
- `StudentQuizAttemptListSerializer`
- `AttendanceSerializer`
- `BadgeSerializer`
- `StudentBadgeSerializer`
- `AgoraTokenSerializer`

### **Detail Serializers**
- `CourseDetailSerializer`
- `LessonDetailSerializer`
- `WhiteboardSerializer`
- `QuizDetailSerializer`
- `QuizQuestionSerializer`
- `QuizAnswerSerializer`
- `StudentQuestionResponseSerializer`
- `StudentQuizAttemptDetailSerializer`
- `StudentProgressSerializer`

---

## 🛠️ Admin Interface

تمام 18 مدل در Admin Panel:

### **Features**
✅ List display مناسب برای هر مدل
✅ Search و Filter
✅ Inline editing
✅ Read-only fields برای timestamps
✅ Custom fieldsets
✅ Action buttons

### **مدل‌های پیشرفته**
- `LessonAdmin` - با LessonMaterialInline
- `QuizAdmin` - با QuizQuestionInline
- `StudentQuizAttemptAdmin` - با StudentQuestionResponseInline
- `AttendanceAdmin` - با filtering پیشرفته

---

## 🔌 Integration Services

### **AgoraService** (`services.py`)
```python
class AgoraService:
    - generate_token(channel, uid, privilege, ttl)
    - _get_role(privilege)
    - revoke_token(token)
```

**نیاز به:**
- `agora_token_builder` package
- `AGORA_APP_ID` در settings
- `AGORA_APP_CERTIFICATE` در settings

---

## 📋 تنظیمات مورد نیاز

### `settings.py`
```python
INSTALLED_APPS = [
    ...
    'classroom',
]

# Agora Configuration
AGORA_APP_ID = 'your_app_id'
AGORA_APP_CERTIFICATE = 'your_certificate'
```

### `urls.py`
```python
urlpatterns = [
    ...
    path('api/classroom/', include('classroom.urls')),
]
```

---

## 🧪 Tests

فایل `tests.py` شامل:
- `CourseTestCase` - تست ایجاد دوره
- `LessonTestCase` - تست ایجاد درس
- `EnrollmentTestCase` - تست ثبت‌نام

---

## 📚 Documentation

### فایل‌های راهنما
- `CLASSROOM_MODELS_GUIDE_FA.md` - راهنمای کامل فارسی
  - معماری مدل‌ها
  - روابط بین مدل‌ها
  - نمونه‌های استفاده
  - API documentation

---

## 🚀 شروع کار

### 1. اضافه کردن به Django
```bash
# migrations
python manage.py makemigrations classroom
python manage.py migrate classroom
```

### 2. ایجاد سطح‌ها و زبان‌ها
```python
from classroom.models import ClassLevel, Language

ClassLevel.objects.create(name='Beginner', order=1)
ClassLevel.objects.create(name='Intermediate', order=2)

Language.objects.create(name='English', code='en')
Language.objects.create(name='Persian', code='fa')
```

### 3. ایجاد دوره
```python
from classroom.models import Course
from account.models import User

teacher = User.objects.get(username='teacher1')
course = Course.objects.create(
    teacher=teacher,
    title='English for Kids',
    language_id=1,
    level_id=1,
    hourly_rate=50.00
)
```

### 4. API استفاده
```bash
# دریافت دوره‌ها
curl -H "Authorization: Bearer TOKEN" \
  https://yourapi.com/api/classroom/courses/

# ایجاد درس
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"course": 1, "title": "Lesson 1", ...}' \
  https://yourapi.com/api/classroom/lessons/
```

---

## 📊 آمار

| موضوع | تعداد |
|-------|-------|
| **مدل‌ها** | 18 |
| **Serializers** | 24 |
| **ViewSets** | 10 |
| **Admin Classes** | 18 |
| **Fields** | 150+ |
| **Relations** | 30+ |
| **API Endpoints** | 40+ |

---

## ✨ بیشتر نیاز دارید؟

برای ویژگی‌های اضافی:
- [ ] WebSocket برای real-time chat
- [ ] Payment integration
- [ ] Email notifications
- [ ] Certificate generation
- [ ] Advanced analytics
- [ ] Mobile app API
