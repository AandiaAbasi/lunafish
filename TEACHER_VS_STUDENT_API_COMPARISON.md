# Teacher vs Student Package APIs - Complete Comparison

## 🎯 Overview

```
STUDENT APIs (Existing)          TEACHER APIs (New)
└── آب برداشت انجام             └── آب منبع تعریف
    (درخواست خدمات)                  (ارائه خدمات)
```

---

## 📊 Side-by-Side Comparison

### 1. Package Management

#### STUDENT API: List Available Packages
```http
GET /api/packages/
Authorization: Bearer {token}

Response (200):
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Python 101",
      "total_sessions": 10,
      "total_price": "1000000",
      "description": "...",
      "image": "...",
      "teaching_subjects": [1, 2],
      "is_active": true
    }
  ]
}
```

#### TEACHER API: Create & List Own Packages
```http
POST /api/teacher/packages/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Python 101",
  "total_sessions": 10,
  "total_price": "1000000",
  "teaching_subjects": [1, 2],
  "has_installment": true,
  "is_active": true
}

Response (201):
{
  "success": true,
  "data": {
    "id": 5,
    "name": "Python 101",
    "total_sessions": 10,
    "total_price": "1000000",
    "total_students_enrolled": 0,
    "total_revenue": "0"
  }
}
```

| جنبه | Student | Teacher |
|------|---------|---------|
| متد | GET (فقط خواندن) | POST (ایجاد), GET (لیست), PUT (ویرایش), DELETE (حذف) |
| صاحب | دیگری | خود (شما) |
| حق | خواندن | کل CRUD |
| نمایش | عمومی | خصوصی |
| عمل | پیدا کردن | ایجاد و مدیریت |

---

### 2. Enrollment & Installments

#### STUDENT API: Enroll & Check Session Access
```http
POST /api/packages/{id}/enroll/
Authorization: Bearer {token}

Response (201):
{
  "success": true,
  "message": "ثبت‌نام موفق",
  "data": {
    "enrollment_id": 42,
    "package_id": 5,
    "enrolled_at": "2024-01-15T10:00:00Z"
  }
}

---

GET /api/packages/{id}/check-session/{session_number}/
Authorization: Bearer {token}

Response (200):
{
  "success": true,
  "has_access": true,
  "session_number": 4,
  "installment_paid": true
}
```

#### TEACHER API: Create & Manage Installments
```http
POST /api/teacher/packages/{id}/installments/
Authorization: Bearer {token}

{
  "session_number": 4,
  "amount": "300000"
}

Response (201):
{
  "success": true,
  "data": {
    "id": 8,
    "installment_number": 2,
    "session_number": 4,
    "amount": "300000",
    "paid_count": 5,
    "pending_count": 7,
    "total_amount_paid": "1500000"
  }
}
```

| جنبه | Student | Teacher |
|------|---------|---------|
| عمل | ثبت‌نام در دوره | تعریف قسط‌های دوره |
| صاحب | دانش‌آموز | معلم |
| مقصد | دریافت خدمات | ارائه خدمات |
| نتیجه | Enrollment ایجاد | Installment ایجاد + Payment شناسائی |

---

### 3. Payment Processing

#### STUDENT API: Process Payment
```http
POST /api/payments/process/
Authorization: Bearer {token}

{
  "enrollment_id": 42,
  "installment_id": 8,
  "amount": "300000",
  "payment_method": "credit_card"
}

Response (200):
{
  "success": true,
  "message": "پرداخت موفق",
  "data": {
    "payment_id": 125,
    "status": "completed",
    "amount": "300000"
  }
}
```

#### TEACHER API: Monitor Payments
```http
GET /api/teacher/packages/{id}/installments/
Authorization: Bearer {token}

Response (200):
{
  "success": true,
  "data": [
    {
      "id": 8,
      "installment_number": 2,
      "session_number": 4,
      "amount": "300000",
      "paid_count": 5,          ← تعداد پرداخت‌شده
      "pending_count": 7,       ← تعداد معلق
      "total_amount_paid": "1500000"
    }
  ]
}
```

| جنبه | Student | Teacher |
|------|---------|---------|
| عمل | پرداخت پول | مراقبت درآمد |
| سیاق | معاملات | تحلیل |
| نتیجه | رسید | آمار |

---

## 🔄 Complete Workflow: Student + Teacher Perspective

### From Teacher Side
```
1. Create Package
   Teacher: POST /api/teacher/packages/
   → Package created with default installment

2. Wait for Enrollments
   [Students enroll via POST /api/packages/{id}/enroll/]
   → StudentPackageEnrollment created
   → StudentPackagePayment auto-created for default installment

3. Add Installments
   Teacher: POST /api/teacher/packages/{id}/installments/
   → Installment created
   → StudentPackagePayment auto-created for all enrolled students

4. Monitor Payments
   Teacher: GET /api/teacher/packages/{id}/installments/
   → View paid_count, pending_count, total_amount_paid
```

### From Student Side
```
1. Browse Packages
   Student: GET /api/packages/
   → List of active packages

2. Enroll in Package
   Student: POST /api/packages/{id}/enroll/
   → StudentPackageEnrollment created
   → Can now access sessions

3. Check Session Access
   Student: GET /api/packages/{id}/check-session/{session}/
   → View which installments are required

4. Process Payments
   Student: POST /api/payments/process/
   → Pay for installments
   → Update StudentPackagePayment status to 'paid'
```

### Database Impact
```
Student Action: Enroll
  ├─ StudentPackageEnrollment created
  └─ StudentPackagePayment created for each existing installment

Teacher Action: Add Installment
  └─ StudentPackagePayment created for each enrolled student

Both Working Together:
  ├─ Student can only enroll in active packages
  ├─ Student can only access paid sessions
  ├─ Teacher controls prices and installments
  └─ System ensures fairness
```

---

## 👥 Permission Matrix

### Student Permissions
```
Student can:
  ✅ GET /api/packages/                    (list all public)
  ✅ POST /api/packages/{id}/enroll/       (enroll)
  ✅ GET /api/packages/{id}/check-session/ (check access)
  ✅ POST /api/payments/process/           (pay)
  ✅ GET /api/payments/{id}/verify/        (verify)

Student CANNOT:
  ❌ POST /api/teacher/packages/
  ❌ PUT /api/teacher/packages/{id}/
  ❌ DELETE /api/teacher/packages/{id}/
  ❌ POST /api/teacher/packages/{id}/installments/
  ❌ PUT /api/teacher/packages/{id}/installments/{id}/
  ❌ DELETE /api/teacher/packages/{id}/installments/{id}/
```

### Teacher Permissions
```
Teacher can:
  ✅ GET /api/packages/                    (view for reference)
  ✅ POST /api/teacher/packages/           (create)
  ✅ GET /api/teacher/packages/            (list own)
  ✅ PUT /api/teacher/packages/{id}/       (update own)
  ✅ DELETE /api/teacher/packages/{id}/    (delete own)
  ✅ GET /api/teacher/packages/{id}/installments/
  ✅ POST /api/teacher/packages/{id}/installments/ (add)
  ✅ PUT /api/teacher/packages/{id}/installments/{id}/ (update)
  ✅ DELETE /api/teacher/packages/{id}/installments/{id}/ (delete)

Teacher CANNOT:
  ❌ Modify other teacher's packages
  ❌ Delete package with enrolled students
  ❌ Delete installment with paid payments
  ❌ POST /api/payments/process/ (student only)
```

### Admin Permissions (Future)
```
Admin can:
  ✅ View all packages (any teacher)
  ✅ View all installments
  ✅ View all payments
  ✅ Modify system settings
  ✅ Generate reports
  ✅ Manage disputes
```

---

## 📈 Data Relationships

### Student Perspective
```
Student (User)
  ↓
StudentPackageEnrollment
  ├─ Package (what I enrolled in)
  └─ StudentPackagePayment (what I need to pay)
```

### Teacher Perspective
```
Teacher (User)
  ↓
Package (created by me)
  ├─ StudentPackageEnrollment (who enrolled)
  ├─ PackageInstallment (payment plan I created)
  │   └─ StudentPackagePayment (payment tracking)
  └─ TeachingSubject (subjects I teach)
```

### Complete Relationship
```
Teacher (User)
  │
  └─ Package (owns)
      │
      ├─ StudentPackageEnrollment
      │   │   (Student enrolls in Package)
      │   └─ StudentPackagePayment
      │       │   (Payment for each installment)
      │       └─ Installment
      │           (Defined by Teacher)
      │
      └─ PackageInstallment
          │   (Created by Teacher)
          └─ StudentPackagePayment
              (Auto-created for all enrolled students)
```

---

## 🔄 Auto-Creation Rules

### When Student Enrolls
```
POST /api/packages/{id}/enroll/
  ↓
StudentPackageEnrollment created
  ↓
For each existing PackageInstallment:
  └─ StudentPackagePayment auto-created (status='pending')
```

### When Teacher Creates Package with has_installment=true
```
POST /api/teacher/packages/
{
  "has_installment": true,
  ...
}
  ↓
Package created
  ↓
DEFAULT PackageInstallment auto-created:
  └─ installment_number=1, session_number=1, amount=total_price
```

### When Teacher Adds Installment
```
POST /api/teacher/packages/{id}/installments/
  ↓
PackageInstallment created
  ↓
For each StudentPackageEnrollment in this package:
  └─ StudentPackagePayment auto-created (status='pending')
```

### When Student Pays Installment
```
POST /api/payments/process/
  ↓
StudentPackagePayment status = 'paid'
  ↓
StudentPackageEnrollment can access that session
  ↓
GET /api/packages/{id}/check-session/{session}/
  └─ Returns has_access=true
```

---

## 📊 Statistics & Analytics

### From Student API (Not yet available)
```
GET /api/student/my-packages/
  └─ Returns: List of enrolled packages with progress

GET /api/student/my-payments/
  └─ Returns: Payment history and status
```

### From Teacher API (Available)
```
GET /api/teacher/packages/
  Returns for each package:
  - total_students_enrolled: Count of unique enrollments
  - total_revenue: Sum of paid installments
  - total_paid_installments: Count of installations with any payment

GET /api/teacher/packages/{id}/installments/
  Returns for each installment:
  - paid_count: Count of completed payments
  - pending_count: Count of pending payments
  - total_amount_paid: Sum of completed payment amounts
```

### Future Admin APIs
```
GET /api/admin/reports/payments/
  └─ System-wide payment statistics

GET /api/admin/reports/packages/
  └─ All packages performance metrics

GET /api/admin/disputes/
  └─ Payment disputes and issues
```

---

## 🔐 Security Comparison

### Student API Security
```
✓ JWT Token required
✓ Can only access own enrollments
✓ Cannot modify other students' data
✓ Cannot access other packages' payments
```

### Teacher API Security
```
✓ JWT Token required
✓ Can only manage own packages
✓ Cannot access other teachers' packages
✓ Cannot delete if students enrolled
✓ Cannot delete if payments completed
✓ Ownership verified on every operation
```

### Data Isolation
```
Student:
  - Can see: All public packages, own enrollments
  - Cannot see: Other students' data, payment details

Teacher:
  - Can see: Own packages, own installments, own payments
  - Cannot see: Other teachers' packages, student payments
```

---

## 🚀 Integration Points

### Student → Teacher Flow
```
1. Student enrolls in Package
   └─ StudentPackageEnrollment created

2. Teacher checks enrollment statistics
   └─ GET /api/teacher/packages/ returns total_students_enrolled

3. Student pays installment
   └─ StudentPackagePayment.status = 'paid'

4. Teacher views revenue
   └─ GET /api/teacher/packages/{id}/installments/ returns paid_count
```

### Teacher → Student Flow
```
1. Teacher creates package with has_installment=true
   └─ Default installment created

2. Student enrolls
   └─ StudentPackagePayment auto-created for default installment

3. Teacher adds new installment
   └─ StudentPackagePayment auto-created for all enrolled students

4. Student pays all installments
   └─ Can access all sessions
```

---

## 📚 Documentation Cross-Reference

| Requirement | Student Doc | Teacher Doc | Implementation |
|-------------|------------|-------------|-----------------|
| List packages | STUDENT_GUIDE | TEACHER_QUICK_REFERENCE | ✅ Both |
| Enroll/Create | STUDENT_GUIDE | TEACHER_API_QUICK_REFERENCE | ✅ Both |
| Manage payments | STUDENT_GUIDE | TEACHER_API_DOCS | ✅ Both |
| Examples | PACKAGE_PAYMENT_INTEGRATION_EXAMPLES | TEACHER_PACKAGE_MANAGEMENT_EXAMPLES | ✅ Both |
| Best practices | - | TEACHER_PACKAGE_API_BEST_PRACTICES | ✅ Teacher |

---

## 🎯 Summary

### Student APIs Purpose
- Allow students to discover and enroll in courses
- Process payments for installments
- Access course content based on payments

### Teacher APIs Purpose
- Create and manage courses
- Define payment installment plans
- Monitor enrollment and payment statistics

### Relationship
```
Student APIs ←→ Shared Data Models ←→ Teacher APIs
  (Client)         (Database)          (Server)
```

### Success Criteria
- ✅ Students can enroll in any active package
- ✅ Students can pay for installments
- ✅ Students can only access paid sessions
- ✅ Teachers can create packages
- ✅ Teachers can define installments
- ✅ Teachers can monitor payments
- ✅ No data leaks between students/teachers
- ✅ Ownership respected for modifications

---

**Both Student and Teacher APIs working together create a complete payment system! 🎉**
