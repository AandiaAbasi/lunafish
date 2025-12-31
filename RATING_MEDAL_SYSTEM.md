# سیستم امتیاز، ستاره و مدال

## خلاصه سیستم

سیستم جامع برای:
1. **امتیاز و ستاره دانش‌آموزان** - معلم برای هر دانش‌آموز امتیاز و ستاره می‌دهد
2. **مدال‌های دانش‌آموزان** - معلم مدال اعطا می‌کند
3. **امتیاز معلمان** - دانش‌آموزان و والدین معلم را امتیاز می‌دهند

---

## 1️⃣ مدل‌های Database

### `StudentRating` (امتیاز دانش‌آموز)

ذخیره‌سازی امتیاز و ستاره‌ای که معلم به دانش‌آموز می‌دهد.

```python
class StudentRating:
    teacher = ForeignKey(User)              # معلمی که امتیاز می‌دهد
    student = ForeignKey(User)              # دانش‌آموز
    teachingsubject = ForeignKey(TeachingSubject)
    
    order = OneToOneField(Order, null=True)  # تمرین (اختیاری)
    rating_type = CharField()                # نوع امتیاز (exercise, activity, ...)
    
    score = IntegerField(0-100)              # امتیاز
    stars = IntegerField(0-5)                # ستاره
    comment = TextField()                    # نظر معلم
```

**انواع امتیاز:**
- `exercise`: امتیاز تمرین
- `activity`: فعالیت کلاس
- `participation`: مشارکت
- `behavior`: رفتار
- `other`: دیگر

---

### `StudentMedal` (مدال دانش‌آموز)

ذخیره‌سازی مدال‌هایی که معلم به دانش‌آموز می‌دهد.

```python
class StudentMedal:
    teacher = ForeignKey(User)               # معلم
    student = ForeignKey(User)               # دانش‌آموز
    teachingsubject = ForeignKey(TeachingSubject)
    
    order = ForeignKey(Order, null=True)     # تمرین (اختیاری)
    medal_type = CharField()                 # نوع مدال (gold, silver, bronze, ...)
    
    title = CharField()                      # عنوان مدال
    description = TextField()                # توضیح
    icon_url = CharField()                   # آدرس تصویر مدال
```

**انواع مدال:**
- `gold`: طلایی
- `silver`: نقره‌ای
- `bronze`: برنزی
- `star`: ستاره
- `heart`: قلب
- `trophy`: جام
- `certificate`: گواهی
- `badge`: نشان
- `achievement`: دستاورد
- `custom`: سفارشی

---

### `TeacherRating` (امتیاز معلم)

ذخیره‌سازی امتیاز‌هایی که دانش‌آموز یا والدین معلم را می‌دهند.

```python
class TeacherRating:
    teacher = ForeignKey(User)               # معلم
    rater = ForeignKey(User)                 # فردی که امتیاز می‌دهد
    
    rater_type = CharField()                 # student یا parent
    stars = IntegerField(1-5)                # ستاره
    comment = TextField()                    # نظر
    
    is_anonymous = BooleanField()            # آیا ناشناخت باشد؟
    is_verified = BooleanField()             # تایید شده؟
```

---

## 2️⃣ متدهای کمکی User

### `get_teacher_rating_stats()`

آمار امتیازات معلم.

```python
teacher = User.objects.get(id=5, role='teacher')
stats = teacher.get_teacher_rating_stats()

# نتیجه:
{
    'average_stars': 4.5,
    'total_ratings': 12,
    'total_comments': 8,
    'by_rater_type': {
        'student': {'count': 10, 'avg_stars': 4.4},
        'parent': {'count': 2, 'avg_stars': 4.8}
    }
}
```

---

### `get_student_rating_stats()`

آمار امتیازات دانش‌آموز.

```python
student = User.objects.get(id=2, role='user')
stats = student.get_student_rating_stats()

# نتیجه:
{
    'average_score': 85.5,
    'average_stars': 4.2,
    'total_ratings': 15,
    'by_subject': [
        {
            'teachingsubject__title': 'ریاضیات',
            'count': 5,
            'avg_score': 88.0,
            'avg_stars': 4.0
        },
        ...
    ]
}
```

---

### `get_received_medals_count()`

تعداد مدال‌های دریافت شده.

```python
student = User.objects.get(id=2, role='user')
count = student.get_received_medals_count()
# نتیجه: 7
```

---

### `get_received_medals_by_type()`

تعداد مدال‌ها بر اساس نوع.

```python
student = User.objects.get(id=2, role='user')
medals = student.get_received_medals_by_type()

# نتیجه:
{
    'gold': 3,
    'silver': 2,
    'bronze': 2,
    'star': 1,
    'heart': 0
}
```

---

## 3️⃣ متدهای Order

### `has_rating()`

بررسی اینکه تمرین امتیاز داده شده است.

```python
order = Order.objects.get(id=123)
if order.has_rating():
    print("این تمرین امتیاز دارد")
```

---

### `has_medals()`

بررسی اینکه تمرین مدال دارد.

```python
if order.has_medals():
    print("این تمرین مدال دارد")
```

---

### `get_rating_stats()`

اطلاعات امتیاز تمرین.

```python
order = Order.objects.get(id=123)
rating_info = order.get_rating_stats()

# نتیجه:
{
    'score': 85,
    'stars': 4,
    'comment': 'خوب انجام دادی',
    'rating_type': 'exercise',
    'given_at': datetime,
    'teacher_name': 'دکتر علی'
}
```

---

## 4️⃣ API Endpoints

### Student Rating APIs

#### اعطای امتیاز به دانش‌آموز

```
POST /api/rating/student/
Authorization: Token TEACHER_TOKEN

{
    "student": 2,
    "teachingsubject": 5,
    "order": 123,
    "rating_type": "exercise",
    "score": 85,
    "stars": 4,
    "comment": "خوب انجام دادی"
}
```

**Response:**
```json
{
    "success": true,
    "message": "امتیاز ثبت شد",
    "rating": {
        "id": 1,
        "teacher_name": "دکتر علی",
        "student_name": "احمد",
        "teachingsubject_title": "ریاضیات",
        "score": 85,
        "stars": 4,
        "comment": "خوب انجام دادی",
        "created_at": "2025-01-01T10:30:00Z"
    }
}
```

---

#### بروزرسانی امتیاز

```
PUT /api/rating/student/{rating_id}/
Authorization: Token TEACHER_TOKEN

{
    "score": 90,
    "stars": 5,
    "comment": "بهتر شد"
}
```

---

### Student Medal APIs

#### اعطای مدال به دانش‌آموز

```
POST /api/medal/student/
Authorization: Token TEACHER_TOKEN

{
    "student": 2,
    "teachingsubject": 5,
    "order": 123,
    "medal_type": "gold",
    "title": "حل صحیح تمام سؤالات",
    "description": "دانش‌آموز تمام سؤالات را درست پاسخ داد",
    "icon_url": "https://..."
}
```

---

#### حذف مدال

```
DELETE /api/medal/student/{medal_id}/
Authorization: Token TEACHER_TOKEN
```

---

#### دریافت امتیازات و مدال‌های دانش‌آموز

```
GET /api/student/{student_id}/rating-profile/
Authorization: Token AUTH_TOKEN

Response:
{
    "success": true,
    "profile": {
        "student_id": 2,
        "student_name": "احمد",
        "rating_stats": {
            "average_score": 85.5,
            "average_stars": 4.2,
            "total_ratings": 15,
            "by_subject": [...]
        },
        "total_medals": 7,
        "medals_by_type": {
            "gold": 3,
            "silver": 2,
            "bronze": 2
        },
        "recent_ratings": [...],
        "recent_medals": [...]
    }
}
```

---

#### دریافت امتیاز و مدال یک تمرین

```
GET /api/exercise/{exercise_id}/rating/
Authorization: Token AUTH_TOKEN

Response:
{
    "success": true,
    "data": {
        "exercise_id": 123,
        "has_rating": true,
        "has_medals": true,
        "rating": {
            "id": 1,
            "score": 85,
            "stars": 4,
            "comment": "خوب",
            ...
        },
        "medals": [
            {
                "id": 1,
                "medal_type": "gold",
                "title": "حل صحیح",
                ...
            }
        ]
    }
}
```

---

### Teacher Rating APIs

#### اعطای امتیاز به معلم

```
POST /api/rating/teacher/
Authorization: Token AUTH_TOKEN

{
    "teacher": 5,
    "stars": 5,
    "comment": "معلم خوبی هستید",
    "is_anonymous": false
}
```

---

#### دریافت امتیازات معلم

```
GET /api/teacher/{teacher_id}/ratings/?page=1&page_size=20
Authorization: Optional

Response:
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "rater_name": "احمد",
            "rater_type": "student",
            "stars": 5,
            "comment": "معلم خوبی هستید",
            "is_anonymous": false,
            "created_at": "2025-01-01T10:30:00Z"
        },
        ...
    ]
}
```

---

#### دریافت پروفایل امتیازات معلم

```
GET /api/teacher/{teacher_id}/rating-profile/
Authorization: Optional

Response:
{
    "success": true,
    "profile": {
        "teacher_id": 5,
        "teacher_name": "دکتر علی",
        "rating_stats": {
            "average_stars": 4.5,
            "total_ratings": 12,
            "total_comments": 8,
            "by_rater_type": {
                "student": {"count": 10, "avg_stars": 4.4},
                "parent": {"count": 2, "avg_stars": 4.8}
            }
        },
        "recent_ratings": [...]
    }
}
```

---

## 5️⃣ ORM Queries

### دریافت تمام امتیازات یک دانش‌آموز

```python
from exercise.models import StudentRating

student_id = 2
ratings = StudentRating.objects.filter(student_id=student_id).select_related(
    'teacher', 'student', 'teachingsubject'
).order_by('-created_at')

for rating in ratings:
    print(f"{rating.teacher.name}: {rating.score}/100 - {rating.stars}⭐")
```

---

### دریافت امتیازات یک دانش‌آموز برای یک درس

```python
ratings = StudentRating.objects.filter(
    student_id=2,
    teachingsubject_id=5
).order_by('-created_at')

avg_score = ratings.aggregate(Avg('score'))['score__avg']
avg_stars = ratings.aggregate(Avg('stars'))['stars__avg']

print(f"میانگین امتیاز: {avg_score}")
print(f"میانگین ستاره: {avg_stars}")
```

---

### دریافت تمام امتیازات معلم

```python
from account.models import TeacherRating

teacher_id = 5
ratings = TeacherRating.objects.filter(
    teacher_id=teacher_id,
    is_verified=True
).select_related('rater').order_by('-created_at')

for rating in ratings:
    rater_name = "Anonymous" if rating.is_anonymous else rating.rater.name
    print(f"{rater_name}: {rating.stars}⭐")
```

---

### دریافت میانگین امتیاز معلم

```python
from django.db.models import Avg

avg_rating = TeacherRating.objects.filter(
    teacher_id=5,
    is_verified=True
).aggregate(avg_stars=Avg('stars'))['avg_stars']

print(f"میانگین امتیاز: {avg_rating}⭐")
```

---

### دریافت مدال‌های یک دانش‌آموز

```python
from exercise.models import StudentMedal

medals = StudentMedal.objects.filter(student_id=2).select_related(
    'teacher', 'teachingsubject'
).order_by('-created_at')

for medal in medals:
    print(f"{medal.title} - {medal.get_medal_type_display()}")
```

---

### دریافت آمار مدال‌ها بر اساس نوع

```python
from django.db.models import Count

medal_stats = StudentMedal.objects.filter(student_id=2).values(
    'medal_type'
).annotate(count=Count('id')).order_by('-count')

for stat in medal_stats:
    print(f"{stat['medal_type']}: {stat['count']}")
```

---

## 6️⃣ مثال‌های استفاده

### مثال 1: اعطای امتیاز توسط معلم

```python
from exercise.models import StudentRating, Order

# دریافت تمرین
order = Order.objects.get(id=123)
teacher = order.teachingsubject.teacher

# ایجاد امتیاز
rating = StudentRating.objects.create(
    teacher=teacher,
    student=order.user,
    teachingsubject=order.teachingsubject,
    order=order,
    rating_type='exercise',
    score=85,
    stars=4,
    comment='خوب انجام دادی'
)

print(f"امتیاز ثبت شد: {rating.score}/100 - {rating.stars}⭐")
```

---

### مثال 2: اعطای مدال برای حل صحیح

```python
from exercise.models import StudentMedal, Order

order = Order.objects.get(id=123)

# اگر تمام پاسخ‌ها صحیح بود
if order.correct == order.details.count():
    medal = StudentMedal.objects.create(
        teacher=order.teachingsubject.teacher,
        student=order.user,
        teachingsubject=order.teachingsubject,
        order=order,
        medal_type='gold',
        title='حل صحیح تمام سؤالات',
        description='دانش‌آموز تمام سؤالات را درست پاسخ داد',
        icon_url='https://...'
    )
    print(f"مدال طلایی اعطا شد!")
```

---

### مثال 3: دریافت امتیازات برای نمایش در پروفایل

```python
from account.models import User

student = User.objects.get(id=2, role='user')

# آمار امتیازات
stats = student.get_student_rating_stats()
print(f"میانگین امتیاز: {stats['average_score']}")
print(f"میانگین ستاره: {stats['average_stars']}")
print(f"تعداد امتیازات: {stats['total_ratings']}")

# مدال‌ها
medal_count = student.get_received_medals_count()
medals_by_type = student.get_received_medals_by_type()
print(f"تعداد مدال‌ها: {medal_count}")
print(f"مدال‌ها: {medals_by_type}")
```

---

## 7️⃣ Serializers

### StudentRatingSerializer

```python
from api.rating_medal_serializers import StudentRatingSerializer

rating = StudentRating.objects.get(id=1)
serializer = StudentRatingSerializer(rating)
print(serializer.data)
```

### StudentMedalSerializer

```python
from api.rating_medal_serializers import StudentMedalSerializer

medal = StudentMedal.objects.get(id=1)
serializer = StudentMedalSerializer(medal)
print(serializer.data)
```

### TeacherRatingSerializer

```python
from api.rating_medal_serializers import TeacherRatingSerializer

rating = TeacherRating.objects.get(id=1)
serializer = TeacherRatingSerializer(rating)
print(serializer.data)
```

---

## 8️⃣ Migration

```bash
python manage.py makemigrations exercise account
python manage.py migrate exercise account
```

---

## 9️⃣ خلاصه

| موضوع | فایل | توضیح |
|-------|------|--------|
| **مدل‌ها** | `exercise/models.py` | StudentRating، StudentMedal |
| **مدل‌ها** | `account/models.py` | TeacherRating |
| **متدهای کمکی** | `account/models.py` | get_teacher_rating_stats()، get_student_rating_stats() |
| **متدهای کمکی** | `exercise/models.py` | Order methods |
| **Serializers** | `api/rating_medal_serializers.py` | تمام سریالایزرها |
| **Views** | `api/views.py` | تمام API endpoints |
| **URLs** | `api/urls.py` | تمام مسیرهای API |

