# Package Installment Payment APIs - راهنمای استفاده

## 📋 خلاصه سیستم

سیستم **قسط‌بندی بسته‌های آموزشی** برای دانش‌آموزان که می‌خواهند پرداخت خود را تقسیم کنند و تنها هنگام رسیدن به جلسه مربوطه پرداخت کنند.

### ویژگی‌های کلیدی:
- ✅ لیست بسته‌های آموزشی با قسط‌بندی
- ✅ ثبت‌نام دانش‌آموز در بسه و اقساط خودکار
- ✅ بررسی دسترسی به جلسه (تنها اگر اقساط قبل از آن پرداخت شده)
- ✅ پرداخت از طریق درگاه Zibal
- ✅ تأیید خودکار پرداخت و بروزرسانی وضعیت

---

## 🔌 API Endpoints

### 1️⃣ **GET /api/packages/**
لیست بسه‌های آموزشی فعال که دارای قسط‌بندی هستند

#### درخواست:
```bash
curl -H "Authorization: Bearer <token>" \
  https://your-domain.com/api/packages/
```

#### پاسخ (۲۰۰):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "آموزش Python پیشرفته",
      "description": "کورس Python برای سطح پیشرفته",
      "teacher_name": "علی احمدی",
      "total_sessions": 12,
      "total_price": "1200000",
      "has_installment": true,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

---

### 2️⃣ **GET /api/student/enrollments/**
لیست ثبت‌نام‌های فعل دانش‌آموز در بسه‌ها

#### درخواست:
```bash
curl -H "Authorization: Bearer <token>" \
  https://your-domain.com/api/student/enrollments/
```

#### پاسخ (۲۰۰):
```json
{
  "success": true,
  "data": [
    {
      "id": 5,
      "package": 1,
      "package_name": "آموزش Python پیشرفته",
      "teacher_name": "علی احمدی",
      "total_sessions": "12",
      "status": "active",
      "enrolled_at": "2024-02-01T08:15:00Z",
      "payment_summary": {
        "total_amount": "1200000",
        "paid_amount": "400000",
        "remaining_amount": "800000",
        "total_installments": 4,
        "paid_installments": 1,
        "pending_installments": 3,
        "completion_percentage": 25.0
      },
      "pending_installments": [
        {
          "id": 2,
          "installment_number": 2,
          "session_number": 4,
          "amount_due": "300000",
          "amount_paid": "0",
          "remaining_amount": "300000",
          "payment_status": "pending"
        }
      ],
      "next_due": {
        "id": 2,
        "installment_number": 2,
        "session_number": 4,
        "amount_due": "300000",
        "amount_paid": "0",
        "remaining_amount": "300000"
      }
    }
  ],
  "count": 1
}
```

---

### 3️⃣ **POST /api/packages/check-session-access/**
بررسی آیا دانش‌آموز می‌تواند به یک جلسه دسترسی داشته باشد

#### درخواست:
```json
{
  "enrollment_id": 5,
  "session_number": 3
}
```

#### پاسخ - دسترسی مجاز (۲۰۰):
```json
{
  "success": true,
  "can_access": true,
  "message": "دسترسی مجاز است",
  "enrollment_id": 5,
  "session_number": 3,
  "payment_summary": {
    "total_amount": "1200000",
    "paid_amount": "400000",
    "remaining_amount": "800000",
    "completion_percentage": 33.33
  },
  "next_due_installment": {
    "id": 2,
    "installment_number": 2,
    "session_number": 4,
    "amount_due": "300000",
    "amount_paid": "0",
    "remaining_amount": "300000"
  }
}
```

#### پاسخ - دسترسی رد (۲۰۰):
```json
{
  "success": true,
  "can_access": false,
  "message": "قسط 2 (جلسه 4) پرداخت نشده",
  "enrollment_id": 5,
  "session_number": 5,
  "payment_summary": {...},
  "next_due_installment": {...}
}
```

---

### 4️⃣ **POST /api/packages/process-payment/**
شروع فرآیند پرداخت قسط بعدی از طریق Zibal

#### درخواست:
```json
{
  "enrollment_id": 5,
  "phone": "09123456789",
  "description": "پرداخت قسط دوم"
}
```

#### پاسخ (۲۰۰):
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "payment_url": "https://gateway.zibal.ir/start/5034399684ea1e2b",
  "track_id": "5034399684ea1e2b",
  "order_id": 5,
  "amount": "300000",
  "installment_number": 2,
  "session_number": 4
}
```

**توضیح:**
- کاربر را به `payment_url` برای پرداخت منتقل کنید
- Zibal پس از تکمیل پرداخت، خودکار `verify-payment` endpoint را فراخوانی می‌کند

#### خطاها:
```json
// ثبت‌نام یافت نشد
{
  "success": false,
  "message": "Enrollment not found or inactive"
} // 404

// هیچ قسط معلق وجود ندارد
{
  "success": false,
  "message": "No pending installment"
} // 400
```

---

### 5️⃣ **GET/POST /api/packages/verify-payment/**
تأیید پرداخت (Callback از Zibal)

**توجه:** این endpoint **خودکار** توسط Zibal فراخوانی می‌شود. آن را به‌طور دستی صدا نزنید.

#### درخواست (از Zibal):
```
GET /api/packages/verify-payment/?trackId=5034399684ea1e2b&status=100&orderId=5&refNumber=123456
```

#### پاسخ (۲۰۰):
```json
{
  "success": true,
  "message": "Payment verified successfully",
  "enrollment_id": 5,
  "installment_number": 2,
  "amount": "300000",
  "track_id": "5034399684ea1e2b",
  "ref_number": "123456"
}
```

#### خطاها:
```json
// پرداخت ناموفق (status != 100)
{
  "success": false,
  "message": "Payment failed",
  "status": 101
} // 400

// درخواست بدی
{
  "success": false,
  "message": "Missing required parameters"
} // 400
```

---

## 🔄 جریان مکمل پرداخت

```
1. دانش‌آموز درخواست GET /api/packages/ → لیست بسه‌ها
   
2. دانش‌آموز انتخاب می‌کند و ثبت‌نام می‌شود → StudentPackageEnrollment
   
3. Installments خودکار ایجاد می‌شوند

4. بررسی دسترسی قبل از شرکت:
   POST /api/packages/check-session-access/
   
5. اگر دسترسی نداشت:
   POST /api/packages/process-payment/
   ↓ (کاربر به Zibal رفته)
   
6. پس از پرداخت، Zibal callback:
   GET /api/packages/verify-payment/?trackId=...&status=100
   
7. وضعیت Payment Record = 'paid'
   
8. دانش‌آموز می‌تواند وارد جلسه شود ✅
```

---

## 🛡️ قوانین دسترسی

| وضعیت | توضیح |
|------|--------|
| **active** | ثبت‌نام فعل، دانش‌آموز می‌تواند جلسات را دید |
| **completed** | همه اقساط پرداخت شد، دسترسی کامل |
| **cancelled** | ثبت‌نام لغو شد، بدون دسترسی |

### منطق دسترسی به جلسه N:
```
✅ ALLOW if: تمام اقساط با session_number ≤ N پرداخت شده

❌ DENY if: حداقل یک قسط با session_number ≤ N پرداخت نشده
```

مثال:
- جلسه 1 و 2: قسط 1 (session_number=1) پرداخت شده → ✅ دسترسی
- جلسه 3 و 4: قسط 1 و 2 (session_number=4) پرداخت شده → ✅ دسترسی
- جلسه 5: قسط 3 (session_number=5) پرداخت نشده → ❌ بدون دسترسی

---

## 📊 نمودار وضعیت‌ها

```
StudentPackagePayment States:

pending → (پرداخت شروع) → Zibal → (تأیید) → paid ✅
  ↓
  └─→ failed ❌

partial → (پرداخت جزئی) → (پرداخت مجدد) → paid ✅
```

---

## 🔐 احراز هویت و صلاحیت‌ها

- **Required:** JWT Token in `Authorization: Bearer <token>`
- **Scope:** کاربر فقط اطلاعات خود را می‌بیند
- **Exception:** `/api/packages/verify-payment/` - بدون احراز (Zibal نیاز دارد)

---

## ⚠️ خطاهای رایج

| کد | پیام | دلیل |
|-----|------|-------|
| 400 | No pending installment | همه اقساط پرداخت شده |
| 400 | Enrollment not found | ID غلط یا متعلق به شخص دیگر |
| 404 | Enrollment not found or inactive | ثبت‌نام لغو شد |
| 500 | Payment gateway error | خطا در ارتباط با Zibal |

---

## 📝 مثال پیاده‌سازی (Frontend)

```javascript
// 1. لیست بسه‌ها
async function getPackages() {
  const res = await fetch('/api/packages/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return res.json();
}

// 2. ثبت‌نام
async function enrollPackage(packageId) {
  // (در classroom app - API الگو)
}

// 3. بررسی دسترسی
async function checkAccess(enrollmentId, sessionNumber) {
  const res = await fetch('/api/packages/check-session-access/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ enrollment_id: enrollmentId, session_number: sessionNumber })
  });
  const data = await res.json();
  
  if (!data.can_access) {
    alert(`دسترسی رد: ${data.message}`);
    return false;
  }
  return true;
}

// 4. پرداخت
async function initiatePayment(enrollmentId, phone) {
  const res = await fetch('/api/packages/process-payment/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      enrollment_id: enrollmentId,
      phone: phone,
      description: 'پرداخت قسط'
    })
  });
  const data = await res.json();
  
  if (data.success) {
    // کاربر را به Zibal منتقل کنید
    window.location.href = data.payment_url;
  }
}

// 5. Zibal بعد از پرداخت، خودکار verify می‌کند ✅
```

---

## 🚀 استقرار

1. فایل‌ها:
   - `api/package_service.py` ✅
   - `api/classroom_serializers.py` (اضافه شد) ✅
   - `api/views.py` (اضافه شد) ✅
   - `api/urls.py` (اضافه شد) ✅

2. Migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Settings:
   - `ZIBAL_MERCHANT_ID` موجود است
   - `ZIBAL_REQUEST_URL` موجود است
   - `ZIBAL_VERIFY_URL` موجود است
   - `ZIBAL_CALLBACK_URL` موجود است

4. Test:
   ```bash
   curl -H "Authorization: Bearer <token>" https://your-domain.com/api/packages/
   ```

---

## ✨ خصوصیات پیشرفته

### Auto-Create Default Installment
اگر Package ایجاد شود بدون اقساط مشخص، یک قسط پیش‌فرض ایجاد می‌شود:
- `session_number = 1`
- `amount = total_price`

### Partial Payments
اگر دانش‌آموز جزئی پرداخت کند:
- `payment_status = 'partial'`
- `amount_paid = X`
- می‌تواند دوباره پرداخت کند

### Automatic Status Updates
- اگر **تمام اقساط** پرداخت شوند → `enrollment.status = 'completed'`
- دسترسی دائم به **تمام جلسات**

---

**آخرین بروزرسانی:** ۲۰۲۴
**نسخه:** ۱.۰
