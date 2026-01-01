# Copilot Instruction Spec – Payment & Class Booking

**Version:** 1.0  
**Date:** 2026-01-01  
**Status:** ACTIVE  
**Binding:** MANDATORY

---

## 1. Scope

### ✅ Within Scope
- [api/views.py](api/views.py) – Payment & Booking endpoints
- [api/urls.py](api/urls.py) – Payment route configuration
- [classroom/models.py](classroom/models.py) – ClassBooking model fields
- [classroom/signals.py](classroom/signals.py) – Signal handling
- [classroom/admin.py](classroom/admin.py) – Admin interface updates (optional)
- Database migrations for new fields

### ❌ Out of Scope
- Architecture changes
- Model renames or deletions
- User authentication flow
- Exercise system
- Teacher wallet logic (except integration points)
- Business rules beyond payment flow
- New models or apps
- UI/Frontend changes

---

## 2. Current System State (Read-Only)

### 2.1 Payment & Booking Flow (WITHOUT actual payment)

```
دانش‌آموز → ClassBooking.create()
          ↓
        Signal fires → ClassRevenue.create()
                      ↓
                   pending_balance += teacher_share
                      ↓
        (NO PAYMENT VERIFICATION)
        payment_status = 'not_paid' (ALWAYS)
        
معلم نیاز به Admin Action برای تأیید کند
```

### 2.2 Models Involved

**ClassBooking** (classroom/models.py:108)
- `status`: 'reserved', 'completed', 'cancelled', 'no_show'
- `price`: Original price
- `discount_amount`: Discount (default 0)
- `final_price`: Calculated
- **NEW FIELDS NEEDED:**
  - `paid_amount` (default 0)
  - `payment_status` ('not_paid', 'partial', 'paid', 'failed')
  - `payment_ref` (nullable)
  - `paid_at` (nullable)

**ClassRevenue** (classroom/models.py:238)
- `is_confirmed`: False initially, True after admin approval
- Drives teacher earning

**TeacherWallet** (classroom/models.py:163)
- `pending_balance`: Waiting for revenue confirmation
- `available_balance`: Confirmed, can withdraw
- Must exist before ClassRevenue creation

**StudentTransaction** (classroom/models.py:462)
- Currently unused
- Must be created when payment_status = 'paid'

### 2.3 Signals (classroom/signals.py)

1. `@receiver(post_save, User)` – Creates TeacherWallet
2. `@receiver(post_save, ClassBooking)` – Creates ClassRevenue
3. `@receiver(pre_save, ClassRevenue)` – Handles confirmation
4. **NEW:** `@receiver(post_save, ClassBooking)` – Creates StudentTransaction (when paid)

### 2.4 Critical Issues (FIXED IN THIS SPEC)

| Issue | Current | After Fix |
|-------|---------|-----------|
| Race condition (double booking) | No select_for_update | ✅ select_for_update() |
| Non-atomic booking+availability | Separate saves | ✅ transaction.atomic() |
| Wallet missing = data loss | if wallet exists | ✅ get_or_create() |
| Inconsistent revenue+wallet | Separate operations | ✅ atomic transaction |
| Discount not calculated | discount_amount=0 | ✅ Computed correctly |
| No payment tracking | N/A | ✅ payment_status fields |
| No payment endpoints | N/A | ✅ 3 new endpoints |
| No error logging | Silent failures | ✅ logging added |
| StudentTransaction unused | N/A | ✅ Created on payment |

---

## 3. Allowed Actions

### 3.1 Code Modifications
- Add `try-except` blocks with logging
- Wrap existing operations in `transaction.atomic()`
- Add `select_for_update()` to queryset
- Add new model fields (ClassBooking only)
- Add new API endpoints
- Add new signals
- Refactor existing signal code (consolidate, simplify only)
- Update migrations
- Update admin.py to display new fields
- Add imports needed for above changes

### 3.2 Process Actions
- Create Django migrations
- Update routes in urls.py
- Update serializers if required by new fields
- Add error handling with logger

### 3.3 Testing (Allowed)
- Run migrations: `python manage.py migrate`
- Check for syntax errors
- Verify existing tests still pass

### 3.4 Documentation
- Add docstrings to new endpoints
- Update signal docstrings
- Mark BREAKING CHANGES in comments if any

---

## 4. Forbidden Actions

### ❌ Strictly Forbidden
- Design payment gateway integration (Zibal or other)
- Change ClassBooking or ClassRevenue fields beyond spec
- Modify User model
- Change signal behavior beyond what's specified
- Delete or rename any existing code
- Alter business logic (commission rates, etc.)
- Add new model types
- Merge or refactor unrelated code
- Suggest architectural improvements
- Propose new features
- Ask for clarification or opinion
- Make assumptions beyond this spec
- Add code comments not directly explaining the change
- Change any behavior not explicitly in Fix Definitions

---

## 5. Fix Execution Plan (Immutable)

### Phase 0: Immediate Safety (Before any payment integration)
1. **Fix #7** – Race Condition in TeacherAvailability
2. **Fix #1** – Double Booking Protection
3. **Fix #2** – Wallet Creation Fallback

### Phase 1: Data Consistency
4. **Fix #3** – Atomic Signal Operations
5. **Fix #5** – Discount Amount Calculation

### Phase 2: Payment Integration Framework
6. **Fix #6** – Payment Status Fields (requires migration)
7. **Fix #9** – Payment Endpoints (3 endpoints)

### Phase 3: Polish & Audit
8. **Fix #8** – Error Handling with Logging
9. **Fix #4** – StudentTransaction Activation

**Execution Order:** MANDATORY (cannot skip or reorder)

---

## 6. Fix Definitions

### Fix #7: Race Condition – select_for_update()

**Files:** api/views.py  
**Function:** CreateClassBookingAPIView.post()  
**Location:** Line ~2915 (availability = TeacherAvailability.objects.get(...))

**Change:**
```
OLD: availability = TeacherAvailability.objects.get(id=availability_id)
NEW: availability = TeacherAvailability.objects.select_for_update().get(id=availability_id)
```

**Why:** Prevents two concurrent requests from booking same slot.  
**When:** Before Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #1: Atomic Transaction – transaction.atomic()

**Files:** api/views.py  
**Function:** CreateClassBookingAPIView.post()  
**Location:** Line ~2940 (booking = ClassBooking.objects.create(...))

**Change:**
Wrap ClassBooking creation + availability update inside:
```python
from django.db import transaction
with transaction.atomic():
    booking = ClassBooking.objects.create(...)
    availability.is_booked = True
    availability.is_available = False
    availability.save()
```

**Why:** If exception occurs between create & update, prevents inconsistent state.  
**When:** Before Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #2: Wallet Fallback – get_or_create()

**Files:** classroom/signals.py  
**Function:** create_class_revenue()  
**Location:** Line ~100 (wallet = TeacherWallet.objects.filter(...).first())

**Change:**
```
OLD: wallet = TeacherWallet.objects.filter(teacher=instance.teacher).first()
     if wallet:
         wallet.pending_balance += teacher_share
         wallet.save()

NEW: wallet, _ = TeacherWallet.objects.get_or_create(
         teacher=instance.teacher,
         defaults={'account_holder_name': instance.teacher.get_full_name() or instance.teacher.username}
     )
     wallet.pending_balance += teacher_share
     wallet.save()
```

**Why:** If wallet doesn't exist, creates it; prevents lost revenue.  
**When:** Before Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #3: Atomic Signal – transaction.atomic()

**Files:** classroom/signals.py  
**Function:** create_class_revenue()  
**Location:** Lines ~85-120 (ClassRevenue.create + wallet update)

**Change:**
Wrap entire logic in `with transaction.atomic():` and add error handling:
```python
try:
    with transaction.atomic():
        ClassRevenue.objects.create(...)
        wallet, _ = TeacherWallet.objects.get_or_create(...)
        wallet.pending_balance += teacher_share
        wallet.save()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error creating ClassRevenue for booking {instance.id}: {str(e)}")
```

**Why:** Ensures ClassRevenue and wallet update both succeed or both fail.  
**When:** Before Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #5: Discount Amount Calculation

**Files:** api/views.py  
**Function:** CreateClassBookingAPIView.post()  
**Location:** Line ~2943 (final_price calculation)

**Change:**
```
OLD: final_price = availability.discount_price if availability.discount_price else availability.price
     booking = ClassBooking.objects.create(
         ...
         price=availability.price,
         discount_amount=0,
         final_price=final_price
     )

NEW: original_price = availability.price
     final_price = availability.discount_price if availability.discount_price else original_price
     discount_amount = original_price - final_price
     
     booking = ClassBooking.objects.create(
         ...
         price=original_price,
         discount_amount=discount_amount,
         final_price=final_price
     )
```

**Why:** Ensures ClassRevenue calculates correct teacher share.  
**When:** Before Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #6: Payment Status Fields

**Files:** classroom/models.py  
**Model:** ClassBooking (Line ~118, after final_price field)

**Change:** Add 4 fields to ClassBooking model:

```python
paid_amount = models.DecimalField(
    max_digits=10, decimal_places=2, default=0,
    verbose_name=_("مبلغ پرداختی")
)
payment_status = models.CharField(
    max_length=20,
    choices=[
        ('not_paid', _("پرداخت نشده")),
        ('partial', _("جزئی")),
        ('paid', _("پرداخت شده")),
        ('failed', _("ناموفق"))
    ],
    default='not_paid',
    verbose_name=_("وضعیت پرداخت")
)
payment_ref = models.CharField(
    max_length=255, blank=True, null=True,
    verbose_name=_("شناسه تراکنش")
)
paid_at = models.DateTimeField(
    blank=True, null=True,
    verbose_name=_("تاریخ پرداخت")
)
```

**Post-Action:** Run migrations:
```bash
python manage.py makemigrations classroom
python manage.py migrate classroom
```

**Why:** Tracks payment state separately from booking status.  
**When:** During Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Migration created & applied

---

### Fix #9: Payment Endpoints

**Files:** api/views.py (add 3 new classes)  
**Location:** After CancelBookingAPIView (Line ~3210)

**Endpoint 1: InitiatePaymentAPIView**
```
POST /api/class-booking/<booking_id>/initiate-payment/
Input: booking_id (in URL)
Output: { payment_token, amount, currency }
Logic:
  - Check payment_status != 'paid'
  - Generate temp token
  - Return token
```

**Endpoint 2: PaymentCallbackAPIView**
```
POST /api/payment/callback/
Input: { payment_ref, status, amount, booking_id }
Output: { success: bool, message: str }
Logic:
  - Verify payment_ref exists
  - Match amount == booking.final_price (exact)
  - If status='success': payment_status='paid', paid_amount=amount, paid_at=now()
  - If status='failed': payment_status='failed'
  - Create ClassRevenue if not exists
  - Atomic transaction
```

**Endpoint 3: PaymentStatusAPIView**
```
GET /api/class-booking/<booking_id>/payment-status/
Output: { payment_status, paid_amount, final_price, is_paid: bool }
Logic:
  - Return current payment state
  - Only student can view own booking
```

**Files to Update:**
- api/views.py: Add 3 new APIView classes
- api/urls.py: Add 3 new paths

**Why:** Enables actual payment flow.  
**When:** During Payment Integration  
**Criticality:** 🔴 CRITICAL

**Status After Completion:** Merged to main ✅

---

### Fix #8: Error Handling with Logging

**Files:** classroom/signals.py  
**Locations:** 
1. create_class_revenue() – wrap in try-except with logger
2. handle_revenue_confirmation() – add try-except with logger

**Change:** Add error handling:
```python
try:
    with transaction.atomic():
        # existing code
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error in signal XYZ for instance {instance.id}: {str(e)}")
    raise  # Re-raise to prevent silent failures
```

**Why:** Makes failures visible in logs instead of silent.  
**When:** After Payment Integration  
**Criticality:** ⚠️ IMPROVEMENT

**Status After Completion:** Merged to main ✅

---

### Fix #4: StudentTransaction Activation

**Files:** classroom/signals.py  
**Location:** End of file (new signal)

**Change:** Add new signal:
```python
@receiver(post_save, sender=ClassBooking)
def create_student_transaction(sender, instance, created, **kwargs):
    from .models import StudentTransaction
    
    if instance.payment_status == 'paid':
        if not StudentTransaction.objects.filter(
            booking=instance,
            transaction_type='class_payment'
        ).exists():
            try:
                StudentTransaction.objects.create(
                    student=instance.student,
                    transaction_type='class_payment',
                    amount=instance.paid_amount,
                    booking=instance,
                    status='completed',
                    description=f'Payment for class {instance.subject.title}'
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating StudentTransaction for booking {instance.id}: {str(e)}")
```

**Why:** Creates audit trail of student payments.  
**When:** After Payment Integration  
**Criticality:** ⚠️ IMPROVEMENT

**Status After Completion:** Merged to main ✅

---

## 7. Payment Integration Constraints

### 7.1 Gateway Agnostic
- Endpoints do NOT implement actual Zibal (or any) integration
- Endpoints accept generic payment_ref and status from webhook
- Gateway integration is OUTSIDE this spec
- These endpoints are framework-ready for any gateway

### 7.2 Amount Matching (MANDATORY)
- PaymentCallbackAPIView MUST verify: `amount == booking.final_price`
- Allow 0.01 tolerance (rounding)
- REJECT if mismatch
- Set payment_status = 'failed' if mismatch

### 7.3 No Partial Payment
- payment_status only: 'not_paid', 'paid', 'failed'
- NO 'partial' state (reserved for future)
- Single payment per booking

### 7.4 Transaction Safety
- Callback MUST use `transaction.atomic()`
- ClassRevenue creation inside atomic block
- If ClassRevenue creation fails, entire callback fails

### 7.5 Idempotency
- PaymentCallbackAPIView must handle duplicate calls
- Check if booking.payment_status already 'paid'
- Return success if already processed

---

## 8. Completion Rules

### After Each Fix

**Report Format:**
```
✅ Done

OR

⛔ Blocked – [reason]
```

**If Blocked:** Stop and wait for clarification. Never proceed beyond blocker.

**If Done:** Continue to next Fix in sequence immediately.

**No Optional Actions:** Do not add tests, refactor, optimize, or improve beyond spec.

---

## 9. Termination Condition

### Work Complete When:
1. All 9 Fixes merged to main
2. All migrations created and applied
3. No errors from `python manage.py check`
4. No failing existing tests

### Final Report:
```
# COMPLETION REPORT

✅ Fix #7: Done
✅ Fix #1: Done
✅ Fix #2: Done
✅ Fix #3: Done
✅ Fix #5: Done
✅ Fix #6: Done + Migration
✅ Fix #9: Done
✅ Fix #8: Done
✅ Fix #4: Done

System Status: Development → Staging (Production-Ready)
All Critical Fixes: IMPLEMENTED
Next Step: Integration Testing (Outside this spec)
```

### After Completion:
**STOP.** No further work permitted under this spec.

---

## 10. Escape Hatch (For Blocker Resolution)

**IF work cannot proceed:**

1. Identify exact blocker
2. Report: `⛔ BLOCKED – [specific technical reason]`
3. Provide evidence (error message, line number, etc.)
4. Wait for specification update

**Do NOT:**
- Deviate from spec
- Assume or guess
- Proceed with workaround
- Request opinion on fix approach

---

## Appendix A: File Changes Summary

| File | Lines | Change Type | Fix |
|------|-------|-------------|-----|
| api/views.py | 2915 | Modify | #7 |
| api/views.py | 2940 | Wrap | #1 |
| api/views.py | 3210+ | Add 3 classes | #9 |
| api/urls.py | 80-90 | Add 3 paths | #9 |
| classroom/models.py | 118+ | Add 4 fields | #6 |
| classroom/signals.py | ~100 | Modify | #2 |
| classroom/signals.py | ~85 | Wrap | #3 |
| classroom/signals.py | ~160 | Add try-except | #8 |
| classroom/signals.py | ~end | Add signal | #4 |
| (migration) | new | Create | #6 |

---

**END OF SPECIFICATION**

This document is binding and immutable. Deviations require signed amendment.
