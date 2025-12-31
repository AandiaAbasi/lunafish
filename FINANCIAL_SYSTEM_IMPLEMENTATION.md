# Financial System Implementation - تکمیل سیستم مالی

## نمایش کلی | Overview

تمام APIهای سیستم مالی با موفقیت پیاده‌سازی شدند. سیستم شامل مدیریت کیف‌پول معلمان، درخواست‌های تسویه‌حساب، تراکنش‌ها و خلاصه‌های مالی می‌باشد.

---

## APIs پیاده‌سازی شده | Implemented APIs

### 1. TeacherWalletDetailAPIView
**نقطه انتهایی (Endpoint):** `GET /api/wallet/`

**توضیحات:**
- دریافت اطلاعات کامل کیف‌پول معلم
- معلمان تنها کیف‌پول خود را می‌بینند
- ادمین می‌تواند با `?teacher_id=X` کیف‌پول هر معلمی را ببیند

**پاسخ نمونه:**
```json
{
    "id": 1,
    "teacher": 42,
    "teacher_name": "علی محمدی",
    "balance": "150000.00",
    "available_balance": "100000.00",
    "pending_balance": "50000.00",
    "total_earned": "500000.00",
    "total_withdrawn": "350000.00",
    "bank_name": "بانک ملی",
    "is_verified": true
}
```

**کدهای خطا:**
- 403: کاربر معلم نیست یا به کیف‌پول دیگری دسترسی دارد
- 404: کیف‌پول یافت نشد

---

### 2. WithdrawalRequestCreateAPIView
**نقطه انتهایی (Endpoint):** `POST /api/withdrawal-requests/create/`

**توضیحات:**
- معلم درخواست تسویه‌حساب می‌کند
- خودکار موجودی و حداقل مبلغ را بررسی می‌کند
- تراکنش اتمی (atomic) برای ایمنی

**بدنه درخواست:**
```json
{
    "amount": "100000.00",
    "payment_method": "bank_transfer",
    "notes": "تقاضای کسب درآمد"
}
```

**نکات مهم:**
- `amount` باید کمتر از `available_balance` باشد
- `amount` باید بیشتر از `minimum_settlement_amount` باشد (معمولاً 50,000)
- تراکنش خودکار با `transaction.atomic()` محافظت می‌شود

---

### 3. WithdrawalRequestListAPIView
**نقطه انتهایی (Endpoint):** `GET /api/withdrawal-requests/`

**توضیحات:**
- لیست درخواست‌های تسویه‌حساب با فیلتر و صفحه‌بندی
- معلمان تنها درخواست‌های خود را می‌بینند
- ادمین تمام درخواست‌ها را می‌بیند

**پارامتر‌های فیلتر:**
- `status`: pending, processing, completed, failed, cancelled
- `teacher_id`: (فقط ادمین) ID معلم
- `date_from`, `date_to`: بازه تاریخی
- `page`, `page_size`: صفحه‌بندی

---

### 4. WalletTransactionListAPIView
**نقطه انتهایی (Endpoint):** `GET /api/transactions/`

**توضیحات:**
- تاریخچه تراکنش‌های کیف‌پول
- شامل تمام انواع: درآمد، تأیید، برداشت، بازگشت
- فیلتر و صفحه‌بندی

**انواع تراکنش:**
- `revenue`: درآمد از کلاس
- `confirmation`: تأیید درآمد
- `withdrawal`: برداشت از کیف‌پول
- `refund`: بازگشت پول
- `adjustment`: تعدیل دستی
- `bonus`: جایزه
- `penalty`: جریمه

---

### 5. FinancialSummaryAPIView
**نقطه انتهایی (Endpoint):** `GET /api/financial-summary/`

**توضیحات:**
- خلاصه مالی معلم یا دانش‌آموز
- شامل: موجودی، کلاس‌های انجام‌شده، تراکنش‌ها
- فیلتر بر اساس بازه تاریخی

**پاسخ نمونه:**
```json
{
    "wallet": {
        "total_balance": "150000.00",
        "available_balance": "100000.00",
        "total_earned": "500000.00"
    },
    "statistics": {
        "total_bookings": 50,
        "completed_bookings": 48,
        "average_price_per_class": "10000.00"
    },
    "transactions": {
        "revenue_count": 50,
        "withdrawal_count": 7,
        "total_transactions": 60
    },
    "period": {
        "earned_this_period": "200000.00",
        "withdrawn_this_period": "100000.00"
    }
}
```

---

### 6. WithdrawalApproveAPIView
**نقطه انتهایی (Endpoint):** `POST /api/withdrawal-requests/<id>/approve/`

**توضیحات:**
- فقط ادمین درخواست‌ها را تأیید می‌کند
- وضعیت را از `pending` به `processing` تغییر می‌دهد
- transaction ID پرداخت را ثبت می‌کند

**بدنه درخواست:**
```json
{
    "transaction_id": "TXN123456789",
    "notes": "تأیید شده و در حال پردازش"
}
```

---

### 7. StudentTransactionListAPIView
**نقطه انتهایی (Endpoint):** `GET /api/student-transactions/`

**توضیحات:**
- تاریخچه پرداخت‌های دانش‌آموز
- شامل: درخواست کلاس، بازگشت
- دانش‌آموز تنها لیست خود را می‌بیند

**انواع تراکنش:**
- `class_payment`: پرداخت برای کلاس
- `refund`: بازگشت پول

**وضعیت‌های ممکن:**
- `pending`: در انتظار
- `completed`: تکمیل‌شده
- `failed`: ناموفق
- `refunded`: برگشت‌داده‌شده

---

## سیگنال‌های خودکار | Automatic Signals

### 1. create_teacher_wallet
**زمان فعال‌شدن:**
- هنگام ایجاد کاربر با `role='teacher'`
- هنگام تبدیل کاربر به معلم

**کار:**
- کیف‌پول جدید ایجاد می‌کند
- موجودی اولیه: 0

---

### 2. create_class_revenue
**زمانی فعال‌شدن:**
- هنگام رزرو کلاس (ClassBooking)

**کار:**
- ClassRevenue ایجاد می‌کند
- کارمزد (30%) محاسبه می‌کند
- سهم معلم (70%) محاسبه می‌کند
- `pending_balance` کیف‌پول را آپدیت می‌کند

---

### 3. handle_revenue_confirmation
**زمان فعال‌شدن:**
- هنگام تأیید درآمد (`is_confirmed = True`)

**کار:**
- مبلغ را از `pending_balance` به `available_balance` منتقل می‌کند
- WalletTransaction ثبت می‌کند
- با `transaction.atomic()` محافظت می‌شود

---

## نمودار جریان | Flow Diagrams

### درآمد کلاس | Class Revenue Flow
```
1. دانش‌آموز → کلاس رزرو می‌کند (ClassBooking)
   ↓
2. سیگنال create_class_revenue فعال می‌شود
   ↓
3. ClassRevenue ایجاد می‌شود (is_confirmed = False)
   ↓
4. pending_balance معلم افزایش می‌یابد
   ↓
5. معلم کلاس را تکمیل می‌کند
   ↓
6. درآمد تأیید می‌شود (is_confirmed = True)
   ↓
7. سیگنال handle_revenue_confirmation فعال می‌شود
   ↓
8. مبلغ از pending → available منتقل می‌شود
   ↓
9. WalletTransaction ثبت می‌شود
```

### درخواست تسویه‌حساب | Withdrawal Flow
```
1. معلم درخواست تسویه‌حساب می‌کند
   ↓
2. WithdrawalRequestCreateAPIView بررسی می‌کند:
   - available_balance >= amount
   - amount >= minimum_settlement_amount
   ↓
3. درخواست ایجاد می‌شود (status = pending)
   ↓
4. available_balance کم می‌شود (lock شده)
   ↓
5. WalletTransaction ثبت می‌شود (type = withdrawal)
   ↓
6. ادمین درخواست را تأیید می‌کند
   ↓
7. وضعیت به processing تغییر می‌یابد
   ↓
8. پول واقعی منتقل می‌شود (خارج سیستم)
```

---

## ایمنی و محافظت | Security Features

### 1. Atomic Transactions
```python
with transaction.atomic():
    wallet = TeacherWallet.objects.select_for_update().get(...)
    # تغییرات تضمین‌شده
```

### 2. Row Locking
- `select_for_update()` برای قفل کردن ردیف
- جلوگیری از race conditions
- اطمینان از بی‌تفاوتی (consistency)

### 3. Role-Based Access
- معلمان: تنها کیف‌پول خود
- ادمین: تمام کیف‌پول‌ها
- دانش‌آموزان: تنها تراکنش‌های خود

### 4. Decimal Field
- همه مبالغ Decimal هستند
- جلوگیری از خطاهای floating-point
- دقت مالی تضمین‌شده

---

## مثال‌های استفاده | Usage Examples

### 1. دریافت موجودی کیف‌پول
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/wallet/"
```

### 2. درخواست تسویه‌حساب
```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100000.00",
    "payment_method": "bank_transfer",
    "notes": "تقاضای کسب درآمد"
  }' \
  "http://localhost:8000/api/withdrawal-requests/create/"
```

### 3. لیست درخواست‌های معلق
```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  "http://localhost:8000/api/withdrawal-requests/?status=pending&page=1"
```

### 4. تأیید درخواست (ادمین)
```bash
curl -X POST -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN123456789",
    "notes": "تأیید و پردازش شد"
  }' \
  "http://localhost:8000/api/withdrawal-requests/5/approve/"
```

### 5. خلاصه مالی
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/financial-summary/?date_from=2024-01-01&date_to=2024-12-31"
```

---

## فیلدهای پایگاه‌داده | Database Fields

### TeacherWallet
- `balance`: موجودی کل
- `available_balance`: موجودی برای برداشت
- `pending_balance`: موجودی در انتظار تأیید
- `total_earned`: درآمد کل
- `total_withdrawn`: برداشت کل
- `is_verified`: آیا اطلاعات بانکی تأیید شده است

### ClassRevenue
- `teacher_share`: سهم معلم
- `platform_fee`: کارمزد پلتفرم (30%)
- `is_confirmed`: آیا درآمد تأیید شده است

### WithdrawalRequest
- `status`: pending, processing, completed, failed
- `amount`: مبلغ درخواستی
- `payment_method`: روش پرداخت

### WalletTransaction
- `transaction_type`: نوع تراکنش
- `amount`: مبلغ
- `balance_before`: موجودی قبل
- `balance_after`: موجودی بعد

---

## آزمایش | Testing

### 1. تست سیگنال‌ها
```python
# ایجاد کاربر معلم
teacher = User.objects.create(username='test', role='teacher')

# بررسی کیف‌پول خودکار
wallet = TeacherWallet.objects.get(teacher=teacher)
assert wallet.balance == 0
```

### 2. تست درخواست تسویه‌حساب
```python
# درخواست تسویه‌حساب
response = client.post('/api/withdrawal-requests/create/', {
    'amount': '100000',
    'payment_method': 'bank_transfer'
})

assert response.status_code == 201
assert response.data['status'] == 'pending'
```

### 3. تست فیلتر‌ها
```bash
# فیلتر بر اساس وضعیت
curl "http://localhost:8000/api/withdrawal-requests/?status=completed"

# فیلتر بر اساس تاریخ
curl "http://localhost:8000/api/transactions/?date_from=2024-01-01&date_to=2024-12-31"
```

---

## خلاصه | Summary

✅ **Implemented:**
- 7 API views
- 3 automatic signals
- Role-based access control
- Atomic transactions with row locking
- Comprehensive filtering and pagination
- Error handling and validation

✅ **Security:**
- select_for_update() for row locking
- transaction.atomic() for data consistency
- Decimal fields for financial precision
- Role-based access control

✅ **Features:**
- Wallet management
- Withdrawal requests
- Transaction history
- Financial summaries
- Admin approval workflow

---

## نکات نهایی | Final Notes

1. تمام APIها با `IsAuthenticated` محافظت می‌شوند
2. موجودی اتمی محافظت می‌شود (atomic + locked)
3. سیگنال‌ها خودکار هستند (بدون نیاز به کال دستی)
4. تمام اعداد Decimal برای دقت مالی
5. فیلتر و صفحه‌بندی برای سهولت جستجو
