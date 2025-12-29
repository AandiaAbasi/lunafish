# Pagination & Authentication in TeacherAvailabilityListAPIView

## سوال 1️⃣: آیا این view توکن کاربر را می‌گیرد؟

### ✅ بله! مثبت است

```python
permission_classes = [IsAuthenticated]
```

این خط باعث می‌شود که:

1. **توکن الزامی است** - بدون توکن نمی‌تواند به این endpoint دسترسی پیدا کند
2. **توکن بررسی می‌شود** - Django REST Framework خودکار توکن را معتبر می‌کند
3. **کاربر تشخیص داده می‌شود** - `request.user` شامل اطلاعات کاربر است
4. **نقش بررسی می‌شود** - کد بررسی می‌کند `request.user.role`

### مثال درخواست با توکن

```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/' \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...'
```

اگر توکن نباشد:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## سوال 2️⃣: Pagination کجا اضافه شد؟

### ✅ اضافه شد! کاملاً پیاده‌سازی شد

```python
def get_paginator(self):
    """استفاده از pagination پیش‌فرض DRF"""
    from rest_framework.pagination import PageNumberPagination
    
    class StandardResultsSetPagination(PageNumberPagination):
        page_size = 20              # 20 نتیجه در هر صفحه
        page_size_query_param = 'page_size'  # پارامتر برای تغییر تعداد
        max_page_size = 100         # حداکثر 100 در هر صفحه
```

---

## 📊 نمونه پاسخ با Pagination

### درخواست

```bash
GET /api/teacher/availability/?page=1&page_size=10
```

### پاسخ

```json
{
  "count": 45,
  "next": "http://localhost:8000/api/teacher/availability/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher": 1,
      "date": "1403-01-15",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "price": 100000,
      "is_available": true
    },
    {
      "id": 2,
      "teacher": 1,
      "date": "1403-01-15",
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "price": 100000,
      "is_available": true
    },
    ...
  ]
}
```

---

## 🎯 پارامترهای Pagination

| پارامتر | نوع | پیش‌فرض | توضیح |
|---------|------|----------|-------|
| `page` | integer | 1 | شماره صفحه |
| `page_size` | integer | 20 | تعداد نتایج در هر صفحه |

### مثال‌های مختلف

```bash
# صفحه 1 (پیش‌فرض)
GET /api/teacher/availability/

# صفحه 2
GET /api/teacher/availability/?page=2

# 50 نتیجه در هر صفحه
GET /api/teacher/availability/?page_size=50

# ترکیب
GET /api/teacher/availability/?page=3&page_size=25
```

---

## 🔐 چگونه Authentication کار می‌کند؟

### مرحله 1: ارسال توکن

```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/' \
  -H 'Authorization: Bearer TOKEN_HERE'
```

### مرحله 2: بررسی توکن

Django REST Framework خودکار:
1. Header `Authorization` را می‌خواند
2. `Bearer` را جدا می‌کند
3. توکن را رمزگشایی می‌کند
4. کاربر را تشخیص می‌دهد
5. اطلاعات را در `request.user` قرار می‌دهد

### مرحله 3: استفاده در کد

```python
if request.user.role == 'teacher':
    queryset = TeacherAvailability.objects.filter(teacher=request.user)
```

---

## 🛡️ سطوح دسترسی

### معلم
```
- می‌بیند: فقط شکاف‌های خود
- می‌تواند: filter نکند، فقط نتایج خود
```

### ادمین
```
- می‌بیند: تمام شکاف‌ها
- می‌تواند: filter کند بر اساس teacher_id
```

### دانش‌آموز
```
- می‌بیند: تمام شکاف‌های فعال
- می‌تواند: filter کند بر اساس teacher_id
```

---

## 📱 مثال کامل برای اپ موبایل

### JavaScript/TypeScript

```javascript
// تابع برای دریافت شکاف‌ها
async function getAvailability(page = 1, pageSize = 20) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/teacher/availability/?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  
  return {
    total: data.count,
    results: data.results,
    nextPage: data.next ? true : false,
    previousPage: data.previous ? true : false
  };
}

// استفاده
const slots = await getAvailability(1, 10);
console.log(`کل نتایج: ${slots.total}`);
console.log(`نتایج صفحه حاضر: ${slots.results.length}`);
```

### Python

```python
import requests

# توکن را از جایی بگیرید (مثلاً login response)
token = 'your_access_token_here'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# درخواست
response = requests.get(
    'http://localhost:8000/api/teacher/availability/',
    params={'page': 1, 'page_size': 20},
    headers=headers
)

data = response.json()
print(f"کل نتایج: {data['count']}")
print(f"نتایج این صفحه: {len(data['results'])}")
print(f"صفحه بعدی: {data['next']}")
```

---

## ⚠️ خطاهای رایج

### خطا 1: بدون توکن

```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/'
```

**پاسخ:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**حل:** توکن را اضافه کنید
```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/' \
  -H 'Authorization: Bearer TOKEN'
```

---

### خطا 2: توکن اشتباه

```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/' \
  -H 'Authorization: Bearer wrong_token'
```

**پاسخ:**
```json
{
  "detail": "Invalid token."
}
```

**حل:** توکن صحیح را استفاده کنید

---

### خطا 3: صفحه‌ای که وجود ندارد

```bash
GET /api/teacher/availability/?page=999
```

**پاسخ:**
```json
{
  "detail": "Invalid page."
}
```

**حل:** صفحه‌ای که < count/page_size باشد استفاده کنید

---

## 📈 نمونه Flow

### 1. دریافت توکن (Login)

```bash
POST /api/teacher/login-password/
{
  "username": "teacher1",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1
}
```

### 2. دریافت شکاف‌ها (Pagination)

```bash
GET /api/teacher/availability/?page=1&page_size=20
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Response:
{
  "count": 45,
  "next": "http://.../api/teacher/availability/?page=2",
  "previous": null,
  "results": [...]
}
```

### 3. دریافت صفحه بعدی

```bash
GET /api/teacher/availability/?page=2&page_size=20
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Response:
{
  "count": 45,
  "next": "http://.../api/teacher/availability/?page=3",
  "previous": "http://.../api/teacher/availability/?page=1",
  "results": [...]
}
```

---

## 🎓 خلاصه

### ✅ Authentication
- **الزامی است**: `permission_classes = [IsAuthenticated]`
- **توکن JWT**: توکن Bearer را ارسال کنید
- **خودکار**: Django خودکار کاربر را تشخیص می‌دهد

### ✅ Pagination
- **20 در صفحه**: پیش‌فرض
- **Customizable**: `page_size` پارامتر را استفاده کنید
- **Navigation**: `next` و `previous` لینک‌ها
- **Count**: تعداد کل نتایج

### ✅ فیلتر + Pagination

```bash
GET /api/teacher/availability/?teacher_id=5&page=2&page_size=15
Authorization: Bearer TOKEN
```

یعنی: معلم 5 را ببینید، صفحه 2، 15 نتیجه در صفحه!

---

## 🚀 آماده استفاده!

API اکنون دارای:
- ✅ Authentication (توکن الزامی)
- ✅ Pagination ( 20 نتیجه پیش‌فرض)
- ✅ Filtering (teacher_id, date, is_available)
- ✅ Proper Response Format
- ✅ OpenAPI Documentation
