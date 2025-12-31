# تحلیل سیستم مالی پروژه Fofofish

## 📊 وضعیت موجود

### ✅ موجود (Implemented)

#### 1. **مدل‌ها** (classroom/models.py)
- `TeacherWallet` ✅
  - balance, available_balance, pending_balance
  - اطلاعات بانکی (bank_name, iban, card_number, etc)
  - متدهای: add_revenue(), confirm_revenue(), withdraw(), can_request_settlement()
  
- `ClassRevenue` ✅
  - درآمد معلم از کلاس‌های تدریس شده
  - محاسبه خودکار platform_fee و teacher_share
  - متدهای: confirm()
  
- `WithdrawalRequest` ✅
  - درخواست برداشت درآمد
  - status choices: pending, processing, completed, failed, cancelled
  - متدهای: complete_withdrawal(), cancel_withdrawal()
  
- `WalletTransaction` ✅
  - ثبت تمام تراکنش‌های کیف پول معلم
  - types: revenue, confirmation, withdrawal, refund, adjustment, bonus, penalty
  
- `StudentTransaction` ✅
  - ثبت پرداخت‌های دانش‌آموز برای کلاس‌ها
  - status: pending, completed, failed, refunded
  
- `PlatformSettings` ✅
  - تنظیمات کمیسیون (commission_rate_class = 30% by default)
  
- `Attendance` ✅
  - ثبت حضور/غیاب دانش‌آموزان

#### 2. **Serializers** (api/classroom_serializers.py)
- `TeacherWalletSerializer` ✅
- `ClassRevenueSerializer` ✅
- `WithdrawalRequestSerializer` ✅
- `WalletTransactionSerializer` ✅
- `StudentTransactionSerializer` ✅
- `PlatformSettingsSerializer` ✅

#### 3. **Admin Interface** (classroom/admin.py)
- `TeacherWalletAdmin` ✅ - رنگین, نمایش موجودی، تایید بانکی
- `ClassRevenueAdmin` ✅ - مدیریت درآمدها
- `WithdrawalRequestAdmin` ✅ - مدیریت درخواست‌های برداشت
- `WalletTransactionAdmin` ✅ - نمایش تراکنش‌ها
- `StudentTransactionAdmin` ✅ - نمایش پرداخت‌های دانش‌آموز
- `PlatformSettingsAdmin` ✅ - مدیریت تنظیمات

---

## ❌ ناقص یا وجود ندارد

### 1. **API Views** (api/views.py)
**وضعیت:** هیچ API برای مالی وجود ندارد ❌

**نیاز:**
- `TeacherWalletDetailAPIView` - دریافت اطلاعات کیف پول معلم
- `StudentWalletDetailAPIView` - دریافت اطلاعات حساب دانش‌آموز
- `WithdrawalRequestCreateAPIView` - ثبت درخواست برداشت
- `WithdrawalRequestListAPIView` - لیست درخواست‌های برداشت
- `WithdrawalRequestApproveAPIView` - تایید درخواست (Admin)
- `WithdrawalRequestRejectAPIView` - رد درخواست (Admin)
- `TransactionListAPIView` - لیست تراکنش‌های معلم (فیلتر بر اساس نوع، تاریخ)
- `StudentTransactionListAPIView` - لیست تراکنش‌های دانش‌آموز
- `FinancialSummaryAPIView` - خلاصه مالی معلم (درآمد، کمیسیون، برداشت)
- `AdminFinancialReportAPIView` - گزارش مالی کل (Admin)

### 2. **URLs** (api/urls.py)
**وضعیت:** هیچ URL برای مالی وجود ندارد ❌

**نیاز:**
```
/api/wallet/                           - دریافت کیف پول
/api/wallet/update/                    - بروزرسانی اطلاعات بانکی
/api/withdrawal-requests/              - لیست درخواست‌ها
/api/withdrawal-requests/create/       - ثبت درخواست جدید
/api/withdrawal-requests/<id>/approve/ - تایید (Admin)
/api/withdrawal-requests/<id>/reject/  - رد (Admin)
/api/transactions/                     - لیست تراکنش‌ها
/api/financial-summary/                - خلاصه مالی
/api/admin/financial-report/           - گزارش مالی (Admin)
```

### 3. **Signals** (classroom/signals.py)
**وضعیت:** فایل خالی است ❌

**نیاز:**
- Signal برای ایجاد `TeacherWallet` خودکار هنگام ثبت‌نام معلم
- Signal برای کسر هزینه از حساب دانش‌آموز هنگام ثبت‌نام کلاس

### 4. **Business Logic Issues**

#### Issue #1: ClassBooking → ClassRevenue → WalletTransaction
**وضعیت:** جریان کامل ندارد

**نیاز:**
```
1. دانش‌آموز کلاس را رزرو می‌کند (ClassBooking)
2. پول از حساب دانش‌آموز کسر می‌شود (StudentTransaction)
3. ClassRevenue ایجاد می‌شود (بصورت pending)
4. Wallet میخانی (pending_balance اضافه)
5. ادمین تایید می‌کند
6. درآمد تایید شده (confirm_revenue)
7. WalletTransaction ثبت می‌شود
8. معلم می‌تواند درخواست برداشت دهد
```

#### Issue #2: Atomicity و Security
**وضعیت:** متدهای Wallet از transaction.atomic استفاده نمی‌کنند ❌

**نیاز:**
```python
from django.db import transaction

# استفاده از select_for_update
with transaction.atomic():
    wallet = TeacherWallet.objects.select_for_update().get(...)
    # تغییر موجودی
```

#### Issue #3: Student Wallet
**وضعیت:** مدل StudentWallet وجود ندارد ❌

**نیاز:**
- `StudentWallet` model برای مدیریت اعتبار دانش‌آموز

---

## 📋 خلاصه کار مورد نیاز

| بخش | وضعیت | اولویت | کار |
|-----|--------|--------|-----|
| Models | ✅ | - | تکمیل شده |
| Serializers | ✅ | - | تکمیل شده |
| Admin | ✅ | - | تکمیل شده |
| API Views | ❌ | 🔴 بالا | ایجاد 10 APIView |
| URLs | ❌ | 🔴 بالا | ایجاد 10 URL pattern |
| Signals | ❌ | 🟡 متوسط | ایجاد 2 Signal |
| Transaction Safety | ❌ | 🔴 بالا | اضافه کردن atomic و select_for_update |
| Student Wallet | ❌ | 🟡 متوسط | ایجاد StudentWallet model |
| ClassBooking Logic | ⚠️ | 🔴 بالا | اتصال ClassBooking → ClassRevenue → Transaction |

---

## 🔄 جریان مالی (Flow)

### 1. معلم ثبت‌نام می‌کند
```
Signal: User(role=teacher) → TeacherWallet.create()
```

### 2. دانش‌آموز کلاس را رزرو می‌کند
```
ClassBooking.create()
↓
StudentTransaction.create(type=class_payment, status=pending)
↓
StudentWallet.balance -= amount
↓
ClassRevenue.create(status=pending)
↓
TeacherWallet.pending_balance += teacher_share
```

### 3. ادمین درآمد را تایید می‌کند
```
ClassRevenue.confirm()
↓
TeacherWallet.pending_balance -= teacher_share
↓
TeacherWallet.available_balance += teacher_share
↓
WalletTransaction.create(type=confirmation)
```

### 4. معلم درخواست برداشت می‌دهد
```
WithdrawalRequest.create(amount=X, status=pending)
```

### 5. ادمین درخواست را تایید می‌کند
```
WithdrawalRequest.complete_withdrawal()
↓
TeacherWallet.available_balance -= amount
↓
WalletTransaction.create(type=withdrawal)
↓
WithdrawalRequest.status = completed
```

---

## 🎯 بعدی: ایجاد API ها

ترتیب ایجاد:
1. `TeacherWalletDetailAPIView` - آسان‌ترین
2. `WithdrawalRequestCreateAPIView`
3. `WithdrawalRequestListAPIView`
4. `TransactionListAPIView`
5. بقیه...
