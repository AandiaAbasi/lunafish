# Exercise & Exam Management System (سیستم تمرین و آزمون)

## Overview

سیستم جامع برای ایجاد و مدیریت تمرین‌ها و آزمون‌ها در پلتفرم آموزشی. معلمان می‌توانند:
- تمرین‌های پیچیده‌ای ایجاد کنند
- انواع مختلف سوالات اضافه کنند (تکمیلی، انتخاب‌گزینه‌ای، درست/غلط، تطابق، جاخالی، جواب کوتاه)
- برای هر سوال و گزینه رسانه‌های متنوع (عکس، صوت، ویدیو) اضافه کنند
- تمرین‌ها را برای دانش‌آموزان منتشر کنند
- جواب‌های دانش‌آموزان را نمره‌گذاری کنند

---

## Database Models

### 1. Exercise (تمرین)

**نقش**: تمرین اصلی که توسط معلم ایجاد می‌شود

**فیلدها:**
```
- teacher: معلم سازنده
- subject: موضوع تدریس مرتبط
- title: عنوان تمرین
- description: توضیح تفصیلی
- difficulty: درجه سختی (آسان، متوسط، سخت)
- duration_minutes: مدت زمان (پیش‌فرض: 30 دقیقه)
- total_points: کل امتیاز (پیش‌فرض: 100)
- pass_score: نمره قبولی (پیش‌فرض: 70%)
- is_published: منتشر شده یا خصوصی
```

**مثال:**
```json
{
  "teacher": 5,
  "subject": 1,
  "title": "تمرین شماره 1 - الفبا و تلفظ",
  "description": "تمرین شامل سوالات صوتی برای تمرین الفبا و تلفظ صحیح",
  "difficulty": "easy",
  "duration_minutes": 20,
  "total_points": 100,
  "pass_score": 70,
  "is_published": true
}
```

---

### 2. Question (سوال)

**نقش**: سوالات تشکیل‌دهنده تمرین

**انواع سوالات:**
- `completion`: تکمیلی
- `multiple_choice`: انتخاب‌گزینه‌ای (4 گزینه)
- `true_false`: درست/غلط
- `matching`: تطابق (جفت کردن)
- `fill_blank`: جاخالی
- `short_answer`: جواب کوتاه

**فیلدها:**
```
- exercise: تمرین مرتبط
- order: ترتیب نمایش سوال
- question_type: نوع سوال (فوق‌الذکر)
- text: متن سوال
- image: تصویر سوال
- audio: فایل صوتی سوال
- video: لینک ویدیو سوال
- explanation: توضیح جواب صحیح
- points: امتیاز این سوال
- is_required: آیا الزامی است؟
```

**مثال:**
```json
{
  "exercise": 1,
  "order": 1,
  "question_type": "multiple_choice",
  "text": "حرف اول الفبای انگلیسی کدام است؟",
  "image": "image.jpg",
  "audio": "question.mp3",
  "points": 10,
  "is_required": true,
  "explanation": "جواب صحیح A است زیرا..."
}
```

---

### 3. QuestionOption (گزینه سوال)

**نقش**: گزینه‌های جواب برای سوالات انتخاب‌گزینه‌ای و مشابه

**فیلدها:**
```
- question: سوال مرتبط
- order: ترتیب گزینه (A، B، C، D)
- text: متن گزینه
- image: تصویر گزینه (اختیاری)
- audio: فایل صوتی گزینه (اختیاری)
- is_correct: آیا این گزینه جواب صحیح است؟
- explanation: توضیح برای این گزینه
```

**مثال:**
```json
{
  "question": 1,
  "order": 1,
  "text": "A",
  "is_correct": true,
  "explanation": "A حرف اول الفبای انگلیسی است"
}
```

---

### 4. StudentExerciseAttempt (تلاش دانش‌آموز)

**نقش**: رکورد تلاش‌های دانش‌آموز برای انجام تمرین

**فیلدها:**
```
- student: دانش‌آموز
- exercise: تمرین
- status: در حال انجام / ارائه شده / نمره‌گذاری شده
- score: نمره (0-100)
- percentage: درصد امتیاز
- started_at: زمان شروع
- submitted_at: زمان ارائه نهایی
- graded_at: زمان نمره‌گذاری
- teacher_notes: نظرات معلم
```

**مثال:**
```json
{
  "student": 10,
  "exercise": 1,
  "status": "submitted",
  "score": 85,
  "percentage": 85.0,
  "teacher_notes": "خوب انجام دادی!"
}
```

---

### 5. StudentQuestionAnswer (جواب دانش‌آموز)

**نقش**: جواب هر دانش‌آموز برای هر سوال

**فیلدها:**
```
- attempt: تلاش مرتبط
- question: سوال
- answer_text: متن جواب
- selected_option: گزینه انتخاب شده (برای انتخاب‌گزینه‌ای)
- is_correct: صحیح یا غلط
- points_earned: امتیاز کسب شده
- answer_file: فایل اپلود شده (اختیاری)
- teacher_feedback: نظر معلم
```

**مثال:**
```json
{
  "attempt": 1,
  "question": 1,
  "selected_option": 5,
  "is_correct": true,
  "points_earned": 10
}
```

---

## API Endpoints

### Base URL
```
/api/exercises/
```

### Exercise Management

#### 1. List & Create Exercises
```
GET    /api/exercises/exercises/
POST   /api/exercises/exercises/
```

**Query Parameters:**
- `subject`: Filter by subject ID
- `teacher`: Filter by teacher ID
- `difficulty`: Filter by difficulty level
- `is_published`: Filter by published status

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/exercises/exercises/?subject=1&difficulty=easy" \
  -H "Authorization: Bearer <token>"
```

#### 2. Get Exercise Details
```
GET    /api/exercises/exercises/<id>/
```

#### 3. Update Exercise
```
POST   /api/exercises/exercises/<id>/update/
```

#### 4. Delete Exercise
```
POST   /api/exercises/exercises/<id>/delete/
```

---

### Question Management

#### 1. List Questions
```
GET    /api/exercises/questions/
```

**Query Parameters:**
- `exercise`: Filter by exercise ID
- `question_type`: Filter by question type

#### 2. Create Question
```
POST   /api/exercises/questions/
```

**Request (with media):**
```bash
curl -X POST "http://localhost:8000/api/exercises/questions/" \
  -H "Authorization: Bearer <token>" \
  -F "exercise=1" \
  -F "order=1" \
  -F "question_type=multiple_choice" \
  -F "text=What is the first letter?" \
  -F "audio=@question.mp3" \
  -F "image=@image.jpg" \
  -F "points=10"
```

#### 3. Get Question Details
```
GET    /api/exercises/questions/<id>/
```

#### 4. Update Question
```
POST   /api/exercises/questions/<id>/update/
```

#### 5. Delete Question
```
POST   /api/exercises/questions/<id>/delete/
```

---

### Question Option Management

#### 1. Create Option
```
POST   /api/exercises/options/
```

**Request:**
```bash
curl -X POST "http://localhost:8000/api/exercises/options/" \
  -H "Authorization: Bearer <token>" \
  -F "question=1" \
  -F "order=1" \
  -F "text=A" \
  -F "is_correct=true" \
  -F "audio=@option_audio.mp3"
```

#### 2. Update Option
```
POST   /api/exercises/options/<id>/update/
```

#### 3. Delete Option
```
POST   /api/exercises/options/<id>/delete/
```

---

### Student Exercise APIs

#### 1. List Student Attempts
```
GET    /api/exercises/attempts/
```

**Query Parameters:**
- `exercise`: Filter by exercise ID
- `status`: Filter by status (in_progress, submitted, graded)

#### 2. Get Attempt Details
```
GET    /api/exercises/attempts/<id>/
```

#### 3. Submit Exercise
```
POST   /api/exercises/attempts/<id>/submit/
```

تغییر وضعیت تمرین به "ارائه شده" و ثبت زمان ارائه.

#### 4. Grade Exercise
```
POST   /api/exercises/attempts/<id>/grade/
```

**Request:**
```json
{
  "score": 85,
  "percentage": 85.0,
  "teacher_notes": "خیلی خوب!"
}
```

---

### Student Answer APIs

#### 1. Create/Submit Answer
```
POST   /api/exercises/answers/
```

**Request (برای انتخاب‌گزینه‌ای):**
```json
{
  "attempt": 1,
  "question": 1,
  "selected_option": 5
}
```

**Request (برای جواب متنی):**
```bash
curl -X POST "http://localhost:8000/api/exercises/answers/" \
  -H "Authorization: Bearer <token>" \
  -F "attempt=1" \
  -F "question=2" \
  -F "answer_text=جواب من این است..." \
  -F "answer_file=@file.pdf"
```

#### 2. Update Answer
```
POST   /api/exercises/answers/<id>/update/
```

---

## Workflow Examples

### 1. معلم ایجاد تمرین

```bash
# 1. ایجاد تمرین
curl -X POST "http://localhost:8000/api/exercises/exercises/" \
  -H "Authorization: Bearer <teacher_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": 1,
    "title": "تمرین الفبا",
    "description": "تمرین شامل سوالات صوتی",
    "difficulty": "easy",
    "duration_minutes": 20,
    "total_points": 100,
    "pass_score": 70,
    "is_published": false
  }'
# Response: Exercise ID = 1

# 2. اضافه کردن سوال
curl -X POST "http://localhost:8000/api/exercises/questions/" \
  -H "Authorization: Bearer <teacher_token>" \
  -F "exercise=1" \
  -F "order=1" \
  -F "question_type=multiple_choice" \
  -F "text=حرف اول الفبا کدام است؟" \
  -F "audio=@question.mp3" \
  -F "points=10"
# Response: Question ID = 1

# 3. اضافه کردن گزینه‌ها
for option in "A" "B" "C" "D"; do
  curl -X POST "http://localhost:8000/api/exercises/options/" \
    -H "Authorization: Bearer <teacher_token>" \
    -F "question=1" \
    -F "order=$i" \
    -F "text=$option" \
    -F "is_correct=$([ $option = 'A' ] && echo 'true' || echo 'false')"
done

# 4. منتشر کردن تمرین
curl -X POST "http://localhost:8000/api/exercises/exercises/1/update/" \
  -H "Authorization: Bearer <teacher_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_published": true}'
```

### 2. دانش‌آموز تمرین را انجام دهد

```bash
# 1. دریافت تمرین
curl -X GET "http://localhost:8000/api/exercises/exercises/1/" \
  -H "Authorization: Bearer <student_token>"

# 2. ارسال جواب برای سوال 1
curl -X POST "http://localhost:8000/api/exercises/answers/" \
  -H "Authorization: Bearer <student_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "attempt": 1,
    "question": 1,
    "selected_option": 5
  }'

# 3. ارائه تمرین
curl -X POST "http://localhost:8000/api/exercises/attempts/1/submit/" \
  -H "Authorization: Bearer <student_token>"
```

### 3. معلم نمره‌گذاری کند

```bash
curl -X POST "http://localhost:8000/api/exercises/attempts/1/grade/" \
  -H "Authorization: Bearer <teacher_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 85,
    "percentage": 85.0,
    "teacher_notes": "خیلی خوب! فقط در سوال 3 نزدیک بود"
  }'
```

---

## File Upload Guidelines

### Supported Media Types

**Images:**
- JPG, PNG, GIF
- Max size: 5MB
- Use for: سوالات و گزینه‌ها

**Audio:**
- MP3, WAV, OGG
- Max size: 10MB
- Use for: سوالات صوتی، گزینه‌های صوتی

**Video:**
- URLs only (YouTube, Vimeo, etc.)
- Max length: 10 minutes

**Answer Files:**
- PDF, DOC, DOCX, TXT
- Max size: 5MB
- For: جواب‌های دانش‌آموزان

---

## Features

✅ Multiple question types (6 types)
✅ Rich media support (image, audio, video)
✅ Teacher grading system
✅ Student attempt tracking
✅ Detailed feedback mechanism
✅ Score calculation
✅ Pass/fail determination
✅ Detailed analytics

---

## Notes

1. **Permissions**: Teachers can only manage their own exercises
2. **Publishing**: Only published exercises are visible to students
3. **Attempts**: One active attempt per student per exercise
4. **Auto-grading**: Multiple choice questions can be auto-graded
5. **Feedback**: Teachers can provide detailed feedback on answers
