# Teacher Package Management APIs - راهنما و مثال‌ها

## 📋 خلاصه

معلمین می‌توانند:
1. **بسه‌های آموزشی** ایجاد، مشاهده، ویرایش و حذف کنند
2. **اقساط** برای بسه‌های خود تعریف کنند
3. **وضعیت پرداخت** دانش‌آموزان را مشاهده کنند

---

## 🔌 API Endpoints

### 1️⃣ مدیریت بسه‌ها

#### **GET /api/teacher/packages/**
لیست تمام بسه‌های معلم لاگین‌شده

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://domain.com/api/teacher/packages/
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Python پیشرفته",
      "description": "دوره کامل Python",
      "image": "https://...",
      "total_sessions": 12,
      "total_price": "1200000",
      "has_installment": true,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "teaching_subject_names": ["انگلیسی مبتدی", "ریاضی پایه"],
      "total_students_enrolled": 5,
      "total_revenue": "4500000",
      "total_paid_installments": 8
    }
  ],
  "count": 1
}
```

---

#### **POST /api/teacher/packages/**
ایجاد بسه جدید

```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python پیشرفته",
    "description": "دوره کامل Python",
    "total_sessions": 12,
    "total_price": "1200000",
    "teaching_subjects": [1, 2],
    "has_installment": true,
    "is_active": true
  }' \
  https://domain.com/api/teacher/packages/
```

**Request Body:**
```json
{
  "name": "string (required) - نام بسه",
  "description": "string (optional)",
  "image": "file (optional)",
  "total_sessions": "integer (required) - حداقل 1",
  "total_price": "decimal (required) - بزرگتر از 0",
  "teaching_subjects": "array of IDs",
  "has_installment": "boolean (default: false)",
  "is_active": "boolean (default: true)"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Package created successfully",
  "data": {
    "id": 1,
    "name": "Python پیشرفته",
    ...
  }
}
```

**خطاها:**
```json
// total_sessions < 1
{
  "success": false,
  "message": "Invalid input",
  "errors": {
    "total_sessions": ["تعداد جلسات باید حداقل 1 باشد"]
  }
} // 400

// total_price <= 0
{
  "success": false,
  "message": "Invalid input",
  "errors": {
    "total_price": ["قیمت باید بزرگتر از 0 باشد"]
  }
} // 400
```

---

#### **GET /api/teacher/packages/{id}/**
جزئیات یک بسه

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://domain.com/api/teacher/packages/1/
```

**Response (200):** نتیجه مشابه GET لیست

---

#### **PUT /api/teacher/packages/{id}/**
ویرایش بسه

```bash
curl -X PUT -H "Authorization: Bearer TOKEN" \
  -d '{"name": "Python پیشرفته (بهتر)"}' \
  https://domain.com/api/teacher/packages/1/
```

**Response (200):** اطلاعات به‌روز شده

---

#### **DELETE /api/teacher/packages/{id}/**
حذف بسه

```bash
curl -X DELETE -H "Authorization: Bearer TOKEN" \
  https://domain.com/api/teacher/packages/1/
```

**Response (200):**
```json
{
  "success": true,
  "message": "Package deleted successfully"
}
```

**خطا:**
```json
{
  "success": false,
  "message": "Cannot delete package with active enrollments"
} // 400
```

---

### 2️⃣ مدیریت اقساط

#### **GET /api/teacher/packages/{package_id}/installments/**
لیست اقساط یک بسه

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://domain.com/api/teacher/packages/1/installments/
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "installment_number": 1,
      "session_number": 1,
      "amount": "1200000",
      "paid_count": 3,
      "pending_count": 2,
      "total_amount_paid": "3600000"
    },
    {
      "id": 2,
      "installment_number": 2,
      "session_number": 4,
      "amount": "300000",
      "paid_count": 1,
      "pending_count": 4,
      "total_amount_paid": "300000"
    }
  ],
  "count": 2
}
```

---

#### **POST /api/teacher/packages/{package_id}/installments/**
اضافه کردن قسط جدید

```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -d '{
    "session_number": 7,
    "amount": "250000"
  }' \
  https://domain.com/api/teacher/packages/1/installments/
```

**Request Body:**
```json
{
  "session_number": "integer (1 الی total_sessions)",
  "amount": "decimal (> 0)"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Installment created successfully",
  "data": {
    "id": 3,
    "installment_number": 3,
    "session_number": 7,
    "amount": "250000",
    "paid_count": 0,
    "pending_count": 5,
    "total_amount_paid": "0"
  }
}
```

**خطاها:**
```json
// session_number خارج از محدوده
{
  "success": false,
  "errors": {
    "session_number": ["شماره جلسه باید بین 1 و 12 باشد"]
  }
} // 400

// session_number تکراری
{
  "success": false,
  "errors": {
    "non_field_errors": ["این شماره جلسه قبلاً برای این بسه تعریف شده است"]
  }
} // 400
```

---

#### **PUT /api/teacher/packages/{package_id}/installments/{installment_id}/**
ویرایش قسط

```bash
curl -X PUT -H "Authorization: Bearer TOKEN" \
  -d '{"amount": "350000"}' \
  https://domain.com/api/teacher/packages/1/installments/2/
```

**Response (200):** اطلاعات به‌روز شده

---

#### **DELETE /api/teacher/packages/{package_id}/installments/{installment_id}/**
حذف قسط

```bash
curl -X DELETE -H "Authorization: Bearer TOKEN" \
  https://domain.com/api/teacher/packages/1/installments/2/
```

**Response (200):**
```json
{
  "success": true,
  "message": "Installment deleted successfully"
}
```

**خطا:**
```json
{
  "success": false,
  "message": "Cannot delete installment with paid payments"
} // 400
```

---

## 🎯 فرآیند ایجاد بسه

### مثال عملی: ایجاد بسه Python به 4 قسط

#### Step 1: ایجاد بسه
```javascript
const createPackage = async () => {
  const response = await fetch('/api/teacher/packages/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      name: 'Python پیشرفته',
      description: 'دوره ۱۲ جلسه‌ای Python',
      total_sessions: 12,
      total_price: '1200000',
      teaching_subjects: [1, 2],
      has_installment: true,
      is_active: true
    })
  });
  
  const data = await response.json();
  const packageId = data.data.id;
  console.log('Package created:', packageId);
  
  // اطلاعات:
  // - یک قسط پیش‌فرض برای session_number=1 و amount=1200000 ایجاد شد
  return packageId;
};
```

#### Step 2: اضافه کردن 3 قسط دیگر
```javascript
const createInstallments = async (packageId) => {
  const installments = [
    { session_number: 4, amount: '300000' },
    { session_number: 7, amount: '300000' },
    { session_number: 10, amount: '300000' }
  ];
  
  for (const inst of installments) {
    const response = await fetch(`/api/teacher/packages/${packageId}/installments/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(inst)
    });
    
    const data = await response.json();
    console.log(`Installment ${inst.session_number} created:`, data.data.id);
  }
};
```

#### Step 3: مشاهده اقساط
```javascript
const viewInstallments = async (packageId) => {
  const response = await fetch(`/api/teacher/packages/${packageId}/installments/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  data.data.forEach(inst => {
    console.log(`
      قسط ${inst.installment_number}:
      - جلسه ${inst.session_number}
      - مبلغ: ${inst.amount}
      - پرداخت‌شده: ${inst.paid_count}
      - معلق: ${inst.pending_count}
    `);
  });
};
```

---

## 📊 نمودار وضعیت‌ها

```
معلم:
└─ ایجاد بسه (POST /teacher/packages/)
   └─ قسط پیش‌فرض ایجاد می‌شود
   └─ معلم اقساط بیشتر اضافه می‌کند
   └─ دانش‌آموزان ثبت‌نام می‌کنند
   └─ StudentPackagePayment برای هر دانش‌آموز + قسط

دانش‌آموز:
└─ ثبت‌نام در بسه
   └─ StudentPackagePayment برای تمام اقساط ایجاد می‌شوند
   └─ check-session-access قبل از هر جلسه
   └─ اگر قسط معلق → پرداخت
   └─ بعد از پرداخت → دسترسی ✅

معلم:
└─ مشاهده وضعیت پرداخت‌ها
   └─ برای هر قسط:
      - paid_count: چند نفر پرداخت کردند
      - pending_count: چند نفر معلق دارند
      - total_amount_paid: کل درآمد
```

---

## 🔐 قوانین Authorization

| Action | شرط |
|--------|-----|
| **لیست بسه‌ها** | معلم لاگین‌شده (تنها خود را می‌بیند) |
| **ایجاد بسه** | معلم لاگین‌شده |
| **ویرایش بسه** | فقط سازنده |
| **حذف بسه** | فقط سازنده + بدون enrollment فعل |
| **اضافه قسط** | فقط سازنده بسه |
| **ویرایش قسط** | فقط سازنده بسه |
| **حذف قسط** | فقط سازنده بسه + بدون paid payment |

---

## ⚠️ خطاهای رایج

### خطا: "Package not found"
```python
# معایر:
1. Package ID اشتباه است
2. معلم دیگر صاحب آن نیست
```

### خطا: "Cannot delete package with active enrollments"
```python
# حل:
# Package را مقدار is_active=false کنید
# یا دانش‌آموزان را حذف کنید
PUT /api/teacher/packages/1/
{"is_active": false}
```

### خطا: "Cannot delete installment with paid payments"
```python
# نمی‌توان قسط را حذف کرد اگر کسی آن را پرداخت کرده
# راهکار: اقساط را ویرایش کنید، نه حذف
```

---

## 💡 نکات مهم

### 1. قسط پیش‌فرض
اگر `has_installment=true` باشد:
- قسط خودکار برای session_number=1 ایجاد می‌شود
- مبلغ = کل قیمت بسه

### 2. StudentPackagePayment خودکار
زمانی که:
- دانش‌آموز ثبت‌نام می‌کند → StudentPackagePayment برای تمام اقساط
- معلم قسط جدید اضافه می‌کند → StudentPackagePayment برای تمام دانش‌آموزان

### 3. installment_number
خودکار محاسبه می‌شود (نمی‌توانید آن را تغییر دهید)

---

## 🧪 Test Examples

### Postman Collection:

```json
{
  "info": {
    "name": "Teacher Package Management"
  },
  "item": [
    {
      "name": "Create Package",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/teacher/packages/",
        "body": {
          "raw": "{\"name\": \"Python\", \"total_sessions\": 12, ...}"
        }
      }
    },
    {
      "name": "List Packages",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/teacher/packages/"
      }
    },
    {
      "name": "Add Installment",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/teacher/packages/1/installments/",
        "body": {
          "raw": "{\"session_number\": 4, \"amount\": \"300000\"}"
        }
      }
    }
  ]
}
```

---

## 📚 رابطه با APIهای دیگر

```
Teacher Package Management
├─ لیست بسه‌ها (معلم) → /api/teacher/packages/
│
├─ دانش‌آموز می‌بیند → /api/packages/
│
└─ Student enrollment
   └─ check-session-access
   └─ process-payment
   └─ verify-payment
```

---

**نسخه:** ۱.۰  
**تاریخ:** ۱ اسفند ۱۴۰۲  
