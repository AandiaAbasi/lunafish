# Teacher Package Management API - Quick Reference

## 📍 Base URL
```
/api/teacher/packages/
```

## 🔐 Authentication
تمام درخواست‌ها نیازمند Bearer Token هستند:
```
Authorization: Bearer <jwt_token>
```

---

## 📋 Endpoints Quick Map

| عملیات | متد | مسیر | توضیح |
|--------|------|------|--------|
| لیست بسه‌ها | GET | `/api/teacher/packages/` | دریافت تمام بسه‌های معلم |
| ایجاد بسه | POST | `/api/teacher/packages/` | ایجاد بسه جدید |
| جزئیات بسه | GET | `/api/teacher/packages/{id}/` | جزئیات یک بسه |
| بروزرسانی بسه | PUT | `/api/teacher/packages/{id}/` | تغییر اطلاعات بسه |
| حذف بسه | DELETE | `/api/teacher/packages/{id}/` | حذف بسه |
| لیست اقساط | GET | `/api/teacher/packages/{id}/installments/` | دریافت اقساط |
| اضافه قسط | POST | `/api/teacher/packages/{id}/installments/` | اضافه کردن قسط |
| جزئیات قسط | GET | `/api/teacher/packages/{id}/installments/{inst_id}/` | جزئیات یک قسط |
| بروزرسانی قسط | PUT | `/api/teacher/packages/{id}/installments/{inst_id}/` | تغییر قسط |
| حذف قسط | DELETE | `/api/teacher/packages/{id}/installments/{inst_id}/` | حذف قسط |

---

## 1️⃣ ایجاد بسه

### 📤 درخواست
```http
POST /api/teacher/packages/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Python Advanced",
  "description": "دوره پیشرفته پایتون",
  "total_sessions": 12,
  "total_price": "1200000",
  "teaching_subjects": [1, 2, 3],
  "has_installment": true,
  "is_active": true
}
```

### ✅ پاسخ موفق (201)
```json
{
  "success": true,
  "message": "بسه با موفقیت ایجاد شد",
  "data": {
    "id": 5,
    "name": "Python Advanced",
    "total_sessions": 12,
    "total_price": "1200000",
    "total_students_enrolled": 0,
    "total_revenue": "0",
    "created_at": "2024-01-15T10:30:00Z",
    "has_installment": true,
    "is_active": true
  }
}
```

### ⚠️ خطاهای ممکن
```json
{
  "success": false,
  "message": "خطا در ایجاد بسه",
  "errors": {
    "name": "نام الزامی است",
    "total_sessions": "باید بزرگتر از 0 باشد",
    "total_price": "قیمت الزامی است"
  }
}
```

---

## 2️⃣ لیست بسه‌های معلم

### 📤 درخواست
```http
GET /api/teacher/packages/
Authorization: Bearer <token>
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "اطلاعات بسه‌ها دریافت شد",
  "count": 3,
  "data": [
    {
      "id": 1,
      "name": "Python 101",
      "total_sessions": 10,
      "total_price": "1000000",
      "total_students_enrolled": 25,
      "total_revenue": "500000",
      "total_paid_installments": 12,
      "created_at": "2024-01-10T08:00:00Z",
      "is_active": true
    },
    {
      "id": 2,
      "name": "Web Development",
      "total_sessions": 15,
      "total_price": "1500000",
      "total_students_enrolled": 18,
      "total_revenue": "900000",
      "total_paid_installments": 20,
      "created_at": "2024-01-12T09:15:00Z",
      "is_active": true
    }
  ]
}
```

---

## 3️⃣ بروزرسانی بسه

### 📤 درخواست
```http
PUT /api/teacher/packages/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Python Advanced (Updated)",
  "description": "نسخه بروزرسانی شده",
  "total_sessions": 14,
  "total_price": "1400000",
  "teaching_subjects": [1, 2, 3, 4],
  "is_active": true
}
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "بسه با موفقیت بروزرسانی شد",
  "data": {
    "id": 5,
    "name": "Python Advanced (Updated)",
    "total_sessions": 14,
    "total_price": "1400000",
    "total_students_enrolled": 5,
    "total_revenue": "350000"
  }
}
```

### 🚫 خطاهای ممکن
```json
// 403 - دسترسی رد شد (فقط سازنده می‌تواند ویرایش کند)
{
  "success": false,
  "message": "شما مالک این بسه نیستید",
  "code": "permission_denied"
}

// 404 - بسه یافت نشد
{
  "success": false,
  "message": "بسه یافت نشد",
  "code": "not_found"
}
```

---

## 4️⃣ حذف بسه

### 📤 درخواست
```http
DELETE /api/teacher/packages/{id}/
Authorization: Bearer <token>
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "بسه با موفقیت حذف شد"
}
```

### 🚫 خطاهای ممکن
```json
// 400 - نمی‌توان حذف کرد (دانش‌آموزان ثبت‌نام کرده‌اند)
{
  "success": false,
  "message": "نمی‌توان بسه را حذف کرد. دانش‌آموزان ثبت‌نام شده‌اند",
  "code": "cannot_delete"
}
```

---

## 5️⃣ اضافه کردن قسط

### 📤 درخواست
```http
POST /api/teacher/packages/{package_id}/installments/
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_number": 4,
  "amount": "300000"
}
```

### ℹ️ قوانین
- `session_number` باید بین 1 تا `total_sessions` باشد
- نمی‌توان `session_number` تکراری داشت
- `amount` باید بزرگتر از 0 باشد
- هنگام اضافه کردن قسط، خودکار برای تمام دانش‌آموزان ثبت‌نام شده `StudentPackagePayment` ایجاد می‌شود

### ✅ پاسخ موفق (201)
```json
{
  "success": true,
  "message": "قسط با موفقیت اضافه شد",
  "data": {
    "id": 8,
    "package_id": 5,
    "installment_number": 2,
    "session_number": 4,
    "amount": "300000",
    "paid_count": 0,
    "pending_count": 12,
    "total_amount_paid": "0",
    "created_at": "2024-01-15T11:45:00Z"
  }
}
```

### ⚠️ خطاهای ممکن
```json
// 400 - session_number خارج از محدوده
{
  "success": false,
  "message": "خطا در ایجاد قسط",
  "errors": {
    "session_number": "شماره جلسه باید بین 1 تا 12 باشد"
  }
}

// 400 - session_number تکراری
{
  "success": false,
  "message": "خطا در ایجاد قسط",
  "errors": {
    "session_number": "قسط برای این جلسه قبلا اضافه شده است"
  }
}
```

---

## 6️⃣ لیست اقساط

### 📤 درخواست
```http
GET /api/teacher/packages/{package_id}/installments/
Authorization: Bearer <token>
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "اقساط دریافت شدند",
  "data": [
    {
      "id": 7,
      "installment_number": 1,
      "session_number": 1,
      "amount": "300000",
      "paid_count": 8,
      "pending_count": 4,
      "total_amount_paid": "2400000",
      "created_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": 8,
      "installment_number": 2,
      "session_number": 4,
      "amount": "300000",
      "paid_count": 5,
      "pending_count": 7,
      "total_amount_paid": "1500000",
      "created_at": "2024-01-15T11:45:00Z"
    }
  ]
}
```

---

## 7️⃣ بروزرسانی قسط

### 📤 درخواست
```http
PUT /api/teacher/packages/{package_id}/installments/{installment_id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_number": 5,
  "amount": "350000"
}
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "قسط با موفقیت بروزرسانی شد",
  "data": {
    "id": 8,
    "installment_number": 2,
    "session_number": 5,
    "amount": "350000",
    "paid_count": 5,
    "pending_count": 7,
    "total_amount_paid": "1500000"
  }
}
```

---

## 8️⃣ حذف قسط

### 📤 درخواست
```http
DELETE /api/teacher/packages/{package_id}/installments/{installment_id}/
Authorization: Bearer <token>
```

### ✅ پاسخ موفق (200)
```json
{
  "success": true,
  "message": "قسط با موفقیت حذف شد"
}
```

### 🚫 خطاهای ممکن
```json
// 400 - نمی‌توان حذف کرد (پرداخت‌های انجام شده وجود دارند)
{
  "success": false,
  "message": "نمی‌توان این قسط را حذف کرد. پرداخت‌های انجام شده وجود دارند",
  "code": "cannot_delete"
}
```

---

## 🔄 Workflow مثال

### سناریو: ایجاد کورس 12 جلسه‌ای با 4 قسط

```
1. معلم کورس را ایجاد می‌کند
   POST /api/teacher/packages/
   {
     "name": "Python Complete",
     "total_sessions": 12,
     "total_price": "1200000",
     "has_installment": true
   }
   ✅ قسط پیش‌فرض (جلسه 1، مبلغ 1200000) خودکار ایجاد می‌شود

2. معلم قسط‌های اضافی اضافه می‌کند
   POST /api/teacher/packages/5/installments/
   {"session_number": 4, "amount": "300000"}
   
   POST /api/teacher/packages/5/installments/
   {"session_number": 7, "amount": "300000"}
   
   POST /api/teacher/packages/5/installments/
   {"session_number": 10, "amount": "300000"}
   
   ✅ برای هر قسط، خودکار برای تمام دانش‌آموزان payment ایجاد می‌شود

3. معلم می‌تواند به‌هر‌زمان قسط‌ها را مدیریت کند
   PUT /api/teacher/packages/5/installments/8/
   {"session_number": 5, "amount": "350000"}
   
   DELETE /api/teacher/packages/5/installments/8/
   (فقط اگر پرداخت نشده باشد)
```

---

## 📊 Response Fields توضیح

### Package Response
| فیلد | توضیح |
|------|--------|
| `id` | شناسه‌ی یکتا |
| `name` | نام بسه |
| `total_sessions` | تعداد کل جلسات |
| `total_price` | قیمت کل |
| `total_students_enrolled` | تعداد دانش‌آموزان ثبت‌نام شده |
| `total_revenue` | مجموع درآمد دریافت شده |
| `total_paid_installments` | تعداد قسط‌های پرداخت شده |
| `created_at` | تاریخ ایجاد |

### Installment Response
| فیلد | توضیح |
|------|--------|
| `id` | شناسه‌ی یکتا |
| `installment_number` | شماره‌ی ترتیبی قسط |
| `session_number` | شماره‌ی جلسه |
| `amount` | مبلغ قسط |
| `paid_count` | تعداد پرداخت‌های انجام شده |
| `pending_count` | تعداد پرداخت‌های معلق |
| `total_amount_paid` | کل مبلغ پرداخت شده |

---

## 🛡️ قوانین و محدودیت‌ها

1. **مالکیت**: فقط سازنده‌ی بسه می‌تواند آن را مدیریت کند
2. **حذف بسه**: اگر دانش‌آموز ثبت‌نام شده باشد، نمی‌توان حذف کرد
3. **حذف قسط**: اگر پرداخت انجام شده باشد، نمی‌توان حذف کرد
4. **Session Number**: باید بین 1 تا total_sessions باشد
5. **عدم تکرار**: نمی‌توان برای یک جلسه دو قسط ایجاد کرد
6. **مبلغ مثبت**: تمام مبالغ باید بزرگتر از 0 باشند

---

## 🚀 نکات مهم

✅ **خودکار:**
- قسط پیش‌فرض هنگام ایجاد بسه (اگر `has_installment=true`)
- ایجاد StudentPackagePayment برای تمام دانش‌آموزان عند اضافه شدن قسط

✅ **امنیت:**
- تمام درخواست‌ها نیازمند احراز‌هویت هستند
- مالکیت بسه‌ها بررسی می‌شود

✅ **بازگشت:**
- تمام پاسخ‌ها شامل `success` و `message` هستند
- در صورت خطا، `errors` شامل جزئیات مشکل است
