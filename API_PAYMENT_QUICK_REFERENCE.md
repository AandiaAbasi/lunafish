# Payment API Reference - Quick Guide
# راهنمای سریع API پرداخت

## 📌 Three Main Endpoints

### 1️⃣ Initiate Payment (شروع پرداخت)
```
POST /api/class-booking/{booking_id}/initiate-payment/

Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

Body: {} (empty - booking_id in URL)
```

**Response 200 - Success:**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "amount": "100000",
    "currency": "IRR",
    "payment_url": "https://gateway.zibal.ir/start/5034399684ea1e2b",
    "message": "پرداخت آغاز شد"
  }
}
```

**Use payment_url in WebView/Browser to proceed to Zibal gateway**

---

### 2️⃣ Payment Callback (Webhook from Zibal)
```
POST /api/payment/callback/

Body:
{
  "trackId": "5034399684ea1e2b",
  "success": 1,
  "orderId": "123"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "پرداخت تأیید شد"
}
```

**Note:** This is called by Zibal, not by client

---

### 3️⃣ Check Payment Status (بررسی وضعیت)
```
GET /api/class-booking/{booking_id}/payment-status/

Authorization: Bearer <JWT_TOKEN>
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "payment_status": "paid",
    "final_price": "100000",
    "paid_amount": "100000",
    "payment_ref": "5034399684ea1e2b",
    "paid_at": "2026-01-01T10:30:00Z",
    "is_paid": true
  }
}
```

---

## 🔄 Complete Payment Flow

```
1. Create Booking
   POST /api/class-booking/create/
   ← booking_id=123

2. Start Payment
   POST /api/class-booking/123/initiate-payment/
   ← payment_url with trackId

3. Open Payment Gateway (Client/Browser)
   → User enters card details on Zibal

4. Zibal Callback (Automatic)
   POST /api/payment/callback/
   (No client action needed)

5. Check Status (Optional)
   GET /api/class-booking/123/payment-status/
   → Update UI based on is_paid status
```

---

## 📊 Response Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 400 | Bad request | Check parameters |
| 403 | Forbidden | Check authorization |
| 404 | Not found | Check booking_id |
| 500 | Server error | Retry or contact support |
| 503 | Gateway unavailable | Retry later |

---

## 🔐 Error Responses

**Already Paid:**
```json
{
  "error": "این رزرو قبلاً پرداخت شده است",
  "success": false
}
```

**Permission Denied:**
```json
{
  "error": "شما دسترسی ندارید",
  "success": false
}
```

**Gateway Error:**
```json
{
  "error": "خطا در اتصال به درگاه پرداخت",
  "success": false
}
```

---

## 💡 Key Points

- **Booking ID Required:** Must be from step 1 (create booking)
- **Authentication:** All endpoints (except callback) need JWT token
- **Amount:** Calculated automatically from booking.final_price
- **Currency:** Always IRR (Iranian Rial)
- **Fee Structure:** 30% platform, 70% teacher
- **Status Values:** not_paid, paid, failed
- **Payment Reference:** trackId from Zibal

---

## 🚀 Example Implementation (TypeScript/React)

```typescript
// 1. Start payment
const response = await fetch(
  `${API_URL}/class-booking/${bookingId}/initiate-payment/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
);

const { data } = await response.json();
const { payment_url } = data;

// 2. Open Zibal gateway
// Option A: WebView (Expo)
import { WebView } from 'react-native-webview';
<WebView source={{ uri: payment_url }} />

// Option B: Browser link
window.open(payment_url, '_blank');

// 3. Check status (after user returns)
const statusResponse = await fetch(
  `${API_URL}/class-booking/${bookingId}/payment-status/`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const { data: status } = await statusResponse.json();
if (status.is_paid) {
  // Payment successful
  showSuccess('پرداخت موفق بود');
} else {
  // Payment pending
  showPending('در انتظار تأیید پرداخت');
}
```

---

## 🔗 API Integration Checklist

- [ ] Create booking first
- [ ] Get booking_id from response
- [ ] POST to initiate-payment
- [ ] Extract payment_url
- [ ] Open payment_url in WebView/Browser
- [ ] Wait for user to complete payment (1-2 minutes)
- [ ] Poll GET payment-status (every 2 seconds for 5 minutes)
- [ ] On is_paid=true, show success and continue
- [ ] On timeout, show pending/retry message

---

## 🎯 Sandbox Testing

**Credentials:**
- Merchant ID: `zibal`
- Gateway: `https://gateway.zibal.ir/`
- Test Card: Any valid card (will succeed)
- Amount: Any amount in Rials

**Test Flow:**
1. Create booking with amount
2. Initiate payment
3. Enter test card on Zibal
4. Complete payment
5. Check status → should show is_paid=true

---

**Created:** January 1, 2026  
**Version:** 1.0  
**Status:** ✅ Ready
