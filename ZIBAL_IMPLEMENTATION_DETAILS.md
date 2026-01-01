# Zibal Integration - Implementation Details (Matching sedamix Pattern)
# تفاصیل پیاده‌سازی Zibal (مطابق الگوی sedamix)

---

## 🔍 How It Works (Step by Step)

### Step 1: User Creates Booking
```python
# POST /api/class-booking/create/

ClassBooking.objects.create(
    teacher=teacher,
    student=student,
    subject=subject,
    price=100000,
    discount_amount=0,
    final_price=100000,
    payment_status='not_paid',  # ← Initial state
    status='reserved'
)
```

---

### Step 2: User Initiates Payment
```python
# POST /api/class-booking/{booking_id}/initiate-payment/

# Check permissions & status
assert booking.student_id == request.user.id
assert booking.payment_status != 'paid'

# Prepare Zibal request
payload = {
    'merchant': 'zibal',              # Sandbox merchant ID
    'amount': 100000,                 # Amount in Rials
    'callbackUrl': ZIBAL_CALLBACK_URL,
    'description': 'کلاس ریاضی با علی',
    'orderId': '123'                  # Booking ID
}

# Send request to Zibal
response = requests.post(
    'https://gateway.zibal.ir/v1/request',
    json=payload
)

# Get response
{
    'result': 100,                           # Success code
    'trackId': '5034399684ea1e2b'           # Payment ID
}

# Generate payment URL
payment_url = f'https://gateway.zibal.ir/start/{trackId}'

# Return to client
return {
    'success': True,
    'data': {
        'payment_url': payment_url,
        'booking_id': 123,
        'amount': 100000
    }
}
```

---

### Step 3: User Pays on Zibal Gateway
```
Frontend opens: https://gateway.zibal.ir/start/5034399684ea1e2b

User:
1. Enters card number
2. Enters CVV
3. Clicks Pay
4. Completes verification (OTP, etc.)
5. Zibal confirms payment
6. Zibal calls backend webhook
```

---

### Step 4: Backend Verifies Payment (Webhook)
```python
# POST /api/payment/callback/ (called by Zibal automatically)

# Receive from Zibal
{
    'trackId': '5034399684ea1e2b',
    'success': 1,              # 1 = success, 0 = failed
    'orderId': '123'
}

# Find booking
booking = ClassBooking.objects.get(id=order_id)

# If payment failed
if success != 1:
    booking.payment_status = 'failed'
    booking.payment_ref = track_id
    booking.save()
    return {'success': False}

# Verify with Zibal
verify_payload = {
    'merchant': 'zibal',
    'trackId': '5034399684ea1e2b'
}

response = requests.post(
    'https://gateway.zibal.ir/v1/verify',
    json=verify_payload
)

# Get verification response
{
    'result': 100,            # 100 = verified
    'status': 1,              # Settled
    'orderId': '123',
    'amount': 100000
}

# Verify success
if response_data.get('result') != 100:
    booking.payment_status = 'failed'
    booking.save()
    return {'success': False}

# Mark as paid (in atomic transaction)
with transaction.atomic():
    booking.payment_status = 'paid'           # ← Status change
    booking.payment_ref = track_id            # ← Store Zibal trackId
    booking.paid_amount = 100000
    booking.paid_at = timezone.now()
    booking.save()
    
    # Create revenue tracking
    ClassRevenue.objects.create(
        teacher=booking.teacher,
        booking=booking,
        original_price=100000,
        total_amount=100000,
        platform_fee_percentage=30,
        platform_fee=30000,      # 30% of total
        teacher_share=70000,     # 70% of total
        is_confirmed=False
    )

# Signal triggered here automatically
# Signal: @receiver(post_save, sender=ClassBooking)
# Action: Create StudentTransaction for audit trail

return {'success': True, 'message': 'پرداخت تأیید شد'}
```

---

### Step 5: Frontend Checks Status
```python
# GET /api/class-booking/{booking_id}/payment-status/

booking = ClassBooking.objects.get(id=booking_id)

# Return current status
{
    'success': True,
    'data': {
        'booking_id': 123,
        'payment_status': 'paid',      # ← Updated status
        'paid_amount': 100000,
        'paid_at': '2026-01-01T10:30:00Z',
        'is_paid': True                # ← Boolean for easy checking
    }
}

# Frontend updates UI based on is_paid
if is_paid:
    showSuccess('کلاس رزرو شد و پرداخت موفق بود')
    navigateToClassPage()
else:
    showPending('درحال انتظار تأیید پرداخت...')
```

---

## 🔐 Security Implementation

### 1. Permission Check
```python
# Only the student who created booking can pay
if request.user.role != 'user' or booking.student_id != request.user.id:
    return Response({'error': 'شما دسترسی ندارید'}, status=403)
```

### 2. Status Validation
```python
# Can't pay if already paid
if booking.payment_status in ['paid', 'partial']:
    return Response({'error': 'قبلاً پرداخت شده است'}, status=400)
```

### 3. Amount Verification
```python
# Verify Zibal amount matches booking price
amount_from_zibal = verify_data.get('amount')  # 100000
if amount_from_zibal != booking.final_price:
    payment_status = 'failed'  # Reject mismatch
```

### 4. Transaction Atomicity
```python
# All or nothing - if anything fails, everything rolls back
with transaction.atomic():
    booking.payment_status = 'paid'
    booking.save()
    revenue = ClassRevenue.objects.create(...)  # Must succeed
    # If creation fails, entire transaction rolled back
```

---

## 🔄 State Diagram

```
┌──────────────┐
│  not_paid    │  Initial state after booking
└──────┬───────┘
       │
       │ POST initiate-payment
       │ ↓
┌──────────────────────────────┐
│ Payment in Progress          │  Waiting for user payment
│ (No state change yet)        │
└──────┬───────────────────────┘
       │
       │ Zibal webhook callback
       │ ↓
   ┌───┴────────────────┬─────────────┐
   │                    │             │
   ▼                    ▼             ▼
┌────────┐         ┌─────────┐   ┌──────────┐
│ paid   │         │ failed  │   │ partial  │
│ (100%) │         │ (0%)    │   │ (50-99%) │
└────────┘         └─────────┘   └──────────┘
Final state        Error state   Reserved for
Payment OK         Payment error future use
```

---

## 📝 Database Changes

### ClassBooking Table Changes (On Payment)
```sql
UPDATE classroom_classbooking SET
    payment_status = 'paid',         -- Changed from 'not_paid'
    payment_ref = 'trackId_123',     -- Store Zibal trackId
    paid_amount = 100000,            -- Amount received
    paid_at = '2026-01-01 10:30'     -- Payment timestamp
WHERE id = 123;
```

### ClassRevenue Auto-Created
```sql
INSERT INTO classroom_classrevenue (
    teacher_id,
    booking_id,
    original_price,
    total_amount,
    platform_fee,
    teacher_share,
    is_confirmed
) VALUES (
    45,
    123,
    100000,
    100000,
    30000,
    70000,
    FALSE
);
```

### StudentTransaction Auto-Created (Signal)
```sql
INSERT INTO classroom_studenttransaction (
    student_id,
    transaction_type,
    amount,
    booking_id,
    status
) VALUES (
    12,
    'class_payment',
    100000,
    123,
    'completed'
);
```

---

## 🔗 API Endpoints Summary

| Endpoint | Method | Purpose | Who Calls |
|----------|--------|---------|-----------|
| `/api/class-booking/{id}/initiate-payment/` | POST | Start payment | Client |
| `/api/payment/callback/` | POST | Verify payment | Zibal (webhook) |
| `/api/class-booking/{id}/payment-status/` | GET | Check status | Client (poll) |

---

## ⚙️ Configuration

**Settings (fofofish/settings.py):**
```python
ZIBAL_MERCHANT_ID = "zibal"              # Sandbox
ZIBAL_REQUEST_URL = "https://gateway.zibal.ir/v1/request"
ZIBAL_VERIFY_URL = "https://gateway.zibal.ir/v1/verify"
ZIBAL_START_PAY_URL = "https://gateway.zibal.ir/start/{trackId}"
ZIBAL_CALLBACK_URL = "https://fofofish.app/api/payment/callback/"
```

**Environment Variables (.env):**
```bash
USE_SANDBOX=True
ZIBAL_MERCHANT_ID=zibal
ZIBAL_CALLBACK_URL=https://fofofish.app/api/payment/callback/
```

---

## 🧪 Test Scenario

### Successful Payment Flow
```
1. Student creates booking
   → ClassBooking(payment_status='not_paid')

2. Student clicks "Pay Now"
   → POST /initiate-payment
   ← payment_url from Zibal

3. Student opens payment_url
   → Opens Zibal gateway
   → Enters card details
   → Zibal confirms payment

4. Zibal calls webhook
   → POST /payment/callback/
   ← Backend verifies with Zibal (/v1/verify)
   → Updates: payment_status='paid'
   → Creates: ClassRevenue, StudentTransaction

5. Frontend polls status
   → GET /payment-status
   ← payment_status='paid', is_paid=true
   → Shows success, navigates to class

Result:
✅ ClassBooking.payment_status = 'paid'
✅ ClassRevenue created with 30% platform fee
✅ StudentTransaction created for audit
```

---

## 🎯 Key Implementation Details (Matching sedamix)

| Component | Implementation | Notes |
|-----------|---|---|
| **Payment Gateway** | Zibal | `/v1/request` and `/v1/verify` |
| **Callback Handler** | Webhook | POST `/api/payment/callback/` |
| **Payment Reference** | trackId | From Zibal response |
| **Status Fields** | payment_status | not_paid, paid, failed |
| **Timestamp** | paid_at | When payment confirmed |
| **Reference Storage** | payment_ref | Store trackId for support |
| **Revenue Tracking** | ClassRevenue | Automatic on payment success |
| **Fee Split** | 30% / 70% | Platform / Teacher |
| **Atomicity** | transaction.atomic() | All or nothing |
| **Signal Integration** | post_save | StudentTransaction creation |

---

## 📊 Request/Response Examples

### Zibal Request (Backend → Zibal)
```json
POST https://gateway.zibal.ir/v1/request
{
  "merchant": "zibal",
  "amount": 100000,
  "callbackUrl": "https://fofofish.app/api/payment/callback/",
  "description": "کلاس ریاضی با معلم علی",
  "orderId": "123"
}
```

**Response:**
```json
{
  "result": 100,
  "trackId": "5034399684ea1e2b",
  "message": "درخواست موفق"
}
```

### Zibal Verify (Backend → Zibal)
```json
POST https://gateway.zibal.ir/v1/verify
{
  "merchant": "zibal",
  "trackId": "5034399684ea1e2b"
}
```

**Response:**
```json
{
  "result": 100,
  "status": 1,
  "orderId": "123",
  "amount": 100000,
  "message": "تأیید موفق"
}
```

### Zibal Callback (Zibal → Backend)
```json
POST https://fofofish.app/api/payment/callback/
{
  "trackId": "5034399684ea1e2b",
  "success": 1,
  "orderId": "123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "پرداخت تأیید شد"
}
```

---

**Implementation:** ✅ Complete  
**Verified Against:** sedamix track purchase pattern  
**Status:** 🟢 Ready for production
