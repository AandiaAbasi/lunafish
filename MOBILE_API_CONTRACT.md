# قرارداد ارتباط اپلیکیشن با بک‌اند
## خرید کلاس و پرداخت (Zibal)

**نسخه:** 1.0  
**تاریخ:** 1402-10-11  
**محیط:** Expo + TypeScript  
**زبان:** فارسی

---

## 1. پیش‌نیازها

### 1.1 احراز هویت
- **الزامی:** کاربر باید لاگین شده باشد
- **توکن:** توکن JWT در Header `Authorization: Bearer <token>` ارسال می‌شود
- **مدت اعتبار:** 24 ساعت (فرض کنید)

### 1.2 بیس URL
```typescript
const API_BASE_URL = "https://api.fofofish.com/api";
```

### 1.3 Timeout
```typescript
const REQUEST_TIMEOUT = 10000; // 10 seconds
```

### 1.4 Content-Type
```
Content-Type: application/json
```

---

## 2. Endpointها

### 2.1 رزرو کلاس (قبل از پرداخت)

**مقصد:** دانش‌آموز یک بازه زمانی را رزرو می‌کند

**Method:** `POST`

**URL:** `/class-booking/create/`

**Headers:**
```typescript
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

**Body (JSON):**
```typescript
{
  availability: number;      // Availability ID (الزامی)
  subject: number;           // Subject ID (الزامی)
}
```

**Response 201 (موفق):**
```json
{
  "data": {
    "id": 123,
    "availability": 5,
    "subject": 3,
    "teacher": {
      "id": 42,
      "name": "مرتضی"
    },
    "student": {
      "id": 99,
      "name": "علی"
    },
    "status": "reserved",
    "price": 100000,
    "discount_amount": 0,
    "final_price": 100000,
    "paid_amount": 0,
    "payment_status": "not_paid",
    "payment_ref": null,
    "paid_at": null,
    "created_at": "2026-01-01T10:30:00Z"
  },
  "message": "کلاس با موفقیت خریداری شد"
}
```

**Response 400 (خطای پارامتر):**
```json
{
  "error": "داده‌های نامعتبر",
  "details": {
    "availability": ["Availability ID invalid"]
  }
}
```

**Response 404 (بازه یا درس یافت نشد):**
```json
{
  "error": "بازه زمانی یا درس یافت نشد"
}
```

**Response 409 (بازه قبلاً رزرو شده):**
```json
{
  "error": "این بازه زمانی قبلاً رزرو شده است"
}
```

**Response 403 (فقط دانش‌آموز):**
```json
{
  "error": "تنها دانش‌آموزان می‌توانند کلاس خریداری کنند"
}
```

**TypeScript Interface:**
```typescript
interface CreateBookingRequest {
  availability: number;
  subject: number;
}

interface BookingResponse {
  id: number;
  availability: number;
  subject: number;
  teacher: {
    id: number;
    name: string;
  };
  student: {
    id: number;
    name: string;
  };
  status: BookingStatus;
  price: number;
  discount_amount: number;
  final_price: number;
  paid_amount: number;
  payment_status: PaymentStatus;
  payment_ref: string | null;
  paid_at: string | null;
  created_at: string;
}

interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  details?: Record<string, string[]>;
}
```

---

### 2.2 شروع پرداخت (Zibal)

**مقصد:** درخواست نشانی درگاه پرداخت

**Method:** `POST`

**URL:** `/class-booking/{booking_id}/initiate-payment/`

**URL Parameter:**
```typescript
booking_id: number;  // ID رزروی که در قدم 2.1 ایجاد شد
```

**Headers:**
```typescript
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

**Body:** (خالی - تنها booking_id در URL)
```json
{}
```

**Response 200 (موفق):**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "amount": "100000",
    "currency": "IRR",
    "payment_token": "temp_token_123_1234567890",
    "payment_url": "https://gateway.zibal.ir/pay/123abc456def"
  },
  "message": "پرداخت آغاز شد"
}
```

**Response 400 (قبلاً پرداخت شده):**
```json
{
  "error": "این رزرو قبلاً پرداخت شده است",
  "success": false
}
```

**Response 403 (دسترسی رد شد):**
```json
{
  "error": "شما دسترسی ندارید",
  "success": false
}
```

**Response 404 (رزرو یافت نشد):**
```json
{
  "error": "رزرو یافت نشد",
  "success": false
}
```

**TypeScript Interface:**
```typescript
interface InitiatePaymentRequest {
  // خالی
}

interface InitiatePaymentResponse {
  booking_id: number;
  amount: string;           // مبلغ به صورت string
  currency: "IRR";
  payment_token: string;    // توکن موقت بک‌اند
  payment_url: string;      // نشانی درگاه Zibal
}

interface InitiatePaymentApiResponse {
  success: boolean;
  data?: InitiatePaymentResponse;
  error?: string;
  message?: string;
}
```

**رفتار اپلیکیشن:**
```typescript
// 1. درخواست payment_url
const response = await fetch(`${API_BASE_URL}/class-booking/${bookingId}/initiate-payment/`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});

// 2. باز کردن Zibal در WebView یا Linking
if (response.success) {
  const { payment_url } = response.data;
  
  // گزینه 1: WebView (توصیه‌شده برای Expo)
  // <WebView source={{ uri: payment_url }} />
  
  // گزینه 2: Linking (برای روز‌رسانی‌های بیرونی)
  // await Linking.openURL(payment_url);
}

// 3. پس از بازگشت از Zibal، بررسی وضعیت (بخش 2.4)
```

---

### 2.3 Callback پرداخت (برای درک تنها)

**توجه:** اپ مستقیماً این endpoint را صدا نمی‌زند.

**مقصد:** بک‌اند از Zibal بازخوری دریافت می‌کند و پرداخت را تأیید می‌کند.

**Method:** `POST` (فقط بک‌اند)

**URL:** `/payment/callback/` (webhook از Zibal)

**رفتار بک‌اند:**
- درخواست از Zibal دریافت می‌کند: `payment_ref`, `status`, `amount`, `booking_id`
- مبلغ را با `booking.final_price` تطابق می‌دهد
- اگر موفق: `payment_status = 'paid'`, `paid_amount` و `paid_at` آپدیت می‌شوند
- اگر ناموفق: `payment_status = 'failed'`

**اپ نیاز به اقدام خاصی ندارد - فقط وضعیت را بررسی کند (بخش 2.4)**

---

### 2.4 بررسی وضعیت پرداخت

**مقصد:** اپ وضعیت جاری پرداخت را بررسی می‌کند

**Method:** `GET`

**URL:** `/class-booking/{booking_id}/payment-status/`

**URL Parameter:**
```typescript
booking_id: number;  // ID رزرو
```

**Headers:**
```typescript
{
  "Authorization": "Bearer {token}"
}
```

**Response 200 (موفق):**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "payment_status": "paid",
    "final_price": "100000",
    "paid_amount": "100000",
    "payment_ref": "ref_xyz123",
    "paid_at": "2026-01-01T10:45:00Z",
    "is_paid": true
  }
}
```

**Response 200 (هنوز پرداخت نشده):**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "payment_status": "not_paid",
    "final_price": "100000",
    "paid_amount": "0",
    "payment_ref": null,
    "paid_at": null,
    "is_paid": false
  }
}
```

**Response 200 (پرداخت ناموفق):**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "payment_status": "failed",
    "final_price": "100000",
    "paid_amount": "0",
    "payment_ref": "ref_fail123",
    "paid_at": null,
    "is_paid": false
  }
}
```

**Response 403 (دسترسی رد شد):**
```json
{
  "error": "شما دسترسی ندارید",
  "success": false
}
```

**TypeScript Interface:**
```typescript
interface PaymentStatusResponse {
  booking_id: number;
  payment_status: PaymentStatus;
  final_price: string;
  paid_amount: string;
  payment_ref: string | null;
  paid_at: string | null;
  is_paid: boolean;
}

interface PaymentStatusApiResponse {
  success: boolean;
  data?: PaymentStatusResponse;
  error?: string;
}
```

**رفتار اپ در هر حالت:**

**اگر `is_paid === true`:**
```typescript
// ✅ پرداخت موفق
// 1. پیام موفقیت نمایش بده
Alert.alert("موفق", "پرداخت تأیید شد!");

// 2. رزرو را دانش‌آموز خود قبول کند (Navigation)
navigation.navigate("BookingDetails", { bookingId });

// 3. بیلینگ را آپدیت کن (اگر صفحه قبل‌ترین وجود دارد)
refresh();
```

**اگر `payment_status === 'failed'`:**
```typescript
// ❌ پرداخت ناموفق
Alert.alert("خطا", "پرداخت ناموفق. لطفاً دوباره تلاش کنید.");

// دکمه "پرداخت دوباره" نمایش بده (برگشت به بخش 2.2)
```

**اگر `payment_status === 'not_paid'`:**
```typescript
// ⏳ هنوز پرداخت نشده
Alert.alert("در انتظار", "پرداخت هنوز تأیید نشده است. لطفاً چند ثانیه صبر کنید.");

// دکمه "بررسی دوباره" نمایش بده (Retry endpoint 2.4)
```

---

### 2.5 دریافت لیست رزروهای من

**مقصد:** دانش‌آموز تمام رزروهای خود را می‌بیند

**Method:** `GET`

**URL:** `/my-bookings/`

**Query Parameters (اختیاری):**
```typescript
status?: 'reserved' | 'completed' | 'cancelled' | 'no_show';
page?: number;        // صفحه‌بندی
page_size?: number;   // تعداد برای هر صفحه (پیش‌فرض: 20)
```

**Headers:**
```typescript
{
  "Authorization": "Bearer {token}"
}
```

**Response 200 (موفق):**
```json
{
  "count": 5,
  "next": "https://api.fofofish.com/api/my-bookings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "subject": {
        "id": 3,
        "title": "انگلیسی مبتدی",
        "teacher": {
          "id": 42,
          "name": "مرتضی"
        }
      },
      "status": "completed",
      "final_price": "100000",
      "paid_amount": "100000",
      "payment_status": "paid",
      "payment_ref": "ref_xyz123",
      "paid_at": "2026-01-01T10:45:00Z",
      "availability": {
        "date": "1402-10-15",
        "start_time": "14:00:00",
        "end_time": "15:00:00"
      }
    }
  ]
}
```

**TypeScript Interface:**
```typescript
interface BookingListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: BookingResponse[];
}
```

---

## 3. وضعیت‌ها (Enums)

### 3.1 وضعیت رزرو (BookingStatus)

```typescript
enum BookingStatus {
  RESERVED = 'reserved',      // رزرو شده (منتظر پرداخت)
  COMPLETED = 'completed',    // تکمیل شده (کلاس برگزار شد)
  CANCELLED = 'cancelled',    // لغو شده
  NO_SHOW = 'no_show'         // دانش‌آموز حاضر نشد
}
```

**معنی و Transition:**
```
RESERVED ──(پرداخت)──> (منتظر شروع کلاس)
         ──(لغو)──> CANCELLED
         
(پس از کلاس)
         ──(حاضر شد)──> COMPLETED
         ──(حاضر نشد)──> NO_SHOW
```

### 3.2 وضعیت پرداخت (PaymentStatus)

```typescript
enum PaymentStatus {
  NOT_PAID = 'not_paid',      // پرداخت نشده (رزرو اولیه)
  PAID = 'paid',              // پرداخت شده (موفق)
  FAILED = 'failed'           // ناموفق
}
```

**معنی:**
```
NOT_PAID  → دانش‌آموز هنوز درگاه را باز نکرده
PAID      → بک‌اند تأیید کرد، Zibal تراکنش را ثبت کرد
FAILED    → Zibal رد کرد یا زمان انقضا
```

---

## 4. سناریوهای کامل (Step-by-Step)

### سناریوی 1: پرداخت موفق

```
┌─────────────────┐
│ اپ          │
│ (Expo TypeScript)
└────────┬────────┘

1️⃣ کاربر درس را انتخاب کرد
   ↓
   POST /class-booking/create/
   Body: { availability: 5, subject: 3 }
   
2️⃣ بک‌اند رزرو ایجاد کرد
   ← 201 Created
   ← data: { id: 123, status: 'reserved', payment_status: 'not_paid', final_price: 100000 }
   
3️⃣ دکمه "پرداخت" رو زد
   ↓
   POST /class-booking/123/initiate-payment/
   
4️⃣ بک‌اند درگاه Zibal را دیده‌بان کرد
   ← 200 OK
   ← data: { payment_url: 'https://gateway.zibal.ir/...', payment_token: '...' }
   
5️⃣ اپ درگاه در WebView باز کرد
   → User redirects to Zibal
   → User enters card info
   → Zibal redirects back to app
   
6️⃣ اپ وضعیت را بررسی کرد (1 ثانیه تأخیر)
   ↓
   GET /class-booking/123/payment-status/
   
7️⃣ بک‌اند تأیید کرد (Zibal callback دریافت شده)
   ← 200 OK
   ← data: { payment_status: 'paid', paid_amount: '100000', is_paid: true }
   
8️⃣ اپ موفقیت نمایش داد
   ✅ "پرداخت تأیید شد!"
   ← رزرو در لیست رزروها نمایش داده می‌شود
```

---

### سناریوی 2: پرداخت ناموفق (کارت رد شد)

```
1️⃣ تا مرحله 5️⃣ مانند سناریو 1
   
5️⃣ کاربر در Zibal کارت‌ اشتباهی وارد کرد
   → Zibal: "پرداخت رد شد"
   → Redirect: app://booking/123?status=failed
   
6️⃣ اپ وضعیت را بررسی کرد
   ↓
   GET /class-booking/123/payment-status/
   
7️⃣ بک‌اند ناموفقی را نشان داد
   ← data: { payment_status: 'failed', is_paid: false }
   
8️⃣ اپ خطا نمایش داد
   ❌ "پرداخت ناموفق. کارت رد شد."
   → دکمه "پرداخت دوباره" (مراحل 3️⃣-8️⃣)
```

---

### سناریوی 3: کاربر پرداخت را نیمه‌کاره رها می‌کند

```
1️⃣ تا مرحله 5️⃣ مانند سناریو 1
   
5️⃣ کاربر درگاه Zibal را بسته (دکمه "بازگشت" یا بستن تب)
   → Redirect: app://booking/123 (بدون ?status)
   
6️⃣ اپ به صفحه رزرو بازگشت
   
7️⃣ کاربر دکمه "بررسی وضعیت" را فشرد (optional)
   ↓
   GET /class-booking/123/payment-status/
   
8️⃣ بک‌اند تأیید نکرده را نشان داد
   ← data: { payment_status: 'not_paid', is_paid: false }
   
9️⃣ اپ دریافت کرد
   ⏳ "پرداخت هنوز تأیید نشده است."
   → دکمه "پرداخت دوباره" دسترسی است
```

---

### سناریوی 4: رزرو منقضی می‌شود (بعد از 30 دقیقه)

```
1️⃣ کاربر رزرو کرد (booking_id: 123)
   
2️⃣ 30 دقیقه صبر کرد بدون پرداخت
   
3️⃣ بک‌اند scheduled task اجرا کرد
   → بررسی: payment_status === 'not_paid' && created_at > 30min
   → availability.is_available = True (آزاد کردن بازه)
   
4️⃣ کاربر اپ را باز کرد
   
5️⃣ سعی کرد پرداخت کند
   ↓
   POST /class-booking/123/initiate-payment/
   
6️⃣ بک‌اند رد کرد
   ← 400 Bad Request
   ← error: "این رزرو منقضی شده است"
   
7️⃣ اپ خطا نمایش داد
   ❌ "رزرو منقضی شده است. لطفاً دوباره رزرو کنید."
```

---

## 5. خطاهای رایج و واکنش اپ

### 5.1 خطای شبکه

**علت:** اینترنت قطع است یا تأخیر زیاد است

**HTTP Status:** Connection timeout / Network error

**TypeScript:**
```typescript
try {
  const response = await fetch(url, {
    timeout: REQUEST_TIMEOUT
  });
} catch (error) {
  if (error.message.includes('timeout')) {
    Alert.alert("خطای شبکه", "اتصال بیش‌از حد کند است. لطفاً دوباره تلاش کنید.");
  } else {
    Alert.alert("خطای شبکه", "اتصال اینترنتی ندارید.");
  }
  // Retry button available
}
```

**واکنش اپ:**
- ✅ دکمه "تلاش دوباره" نمایش بده
- ✅ لاگ خطا در console (development فقط)
- ❌ رزرو را حذف نکن
- ❌ صحفه را refresh نکن خودکار

---

### 5.2 خطای احراز هویت

**علت:** توکن منقضی شده یا نامعتبر است

**HTTP Status:** 401 Unauthorized

**Response:**
```json
{
  "error": "Unauthorized",
  "detail": "Invalid token"
}
```

**TypeScript:**
```typescript
if (response.status === 401) {
  // صفحه لاگین را نمایش بده
  navigation.navigate("Login");
  Alert.alert("جلسه پایان‌یافته", "لطفاً دوباره لاگین کنید.");
}
```

**واکنش اپ:**
- ✅ صفحه لاگین نمایش بده
- ✅ توکن قدیم را پاک کن
- ❌ رزرو را حذف نکن (بک‌اند محفوظ است)

---

### 5.3 خطای پرداخت (Zibal)

**علت:** درگاه Zibal در دسترس نیست یا بازه اختیار به پایان رسید

**HTTP Status:** 503 Service Unavailable

**Response:**
```json
{
  "error": "درگاه پرداخت در دسترس نیست. لطفاً بعداً تلاش کنید."
}
```

**TypeScript:**
```typescript
if (response.status === 503) {
  Alert.alert("خطای درگاه", "درگاه پرداخت در دسترس نیست. بعداً تلاش کنید.");
}
```

**واکنش اپ:**
- ✅ دکمه "تلاش بعداً" نمایش بده
- ✅ رزرو باقی می‌ماند (منقضی نمی‌شود)
- ❌ رزرو را حذف نکن

---

### 5.4 رزرو نامعتبر

**علت:** بازه قبلاً رزرو شده یا منقضی شده است

**HTTP Status:** 409 Conflict یا 400 Bad Request

**Response:**
```json
{
  "error": "این بازه زمانی قبلاً رزرو شده است"
}
```

**TypeScript:**
```typescript
if (response.status === 409 || response.status === 400) {
  const error = await response.json();
  Alert.alert("رزرو نامعتبر", error.error);
  
  // صفحه معلمان را دوباره بارگذاری کن
  navigation.navigate("Teachers");
}
```

**واکنش اپ:**
- ✅ پیام خطای مفصل نمایش بده
- ✅ کاربر را به صفحه انتخاب معلم برگردان
- ❌ رزرو را خودکار حذف نکن

---

### 5.5 خطای مبلغ

**علت:** مبلغ رزرو تغییر کرده است (نادر)

**HTTP Status:** 400 Bad Request

**Response:**
```json
{
  "error": "مبلغ تطابق ندارد. لطفاً دوباره رزرو کنید."
}
```

**واکنش اپ:**
- ✅ رزرو را حذف کن
- ✅ پیام "لطفاً دوباره سعی کنید" نمایش بده
- ✅ کاربر را به انتخاب درس برگردان

---

## 6. نکات مهم برای Expo / TypeScript

### 6.1 استفاده از Fetch

**بهترین روش:**
```typescript
import { API_BASE_URL, REQUEST_TIMEOUT } from './config';

interface FetchOptions extends RequestInit {
  timeout?: number;
}

async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = REQUEST_TIMEOUT, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// استفاده
async function createBooking(availability: number, subject: number) {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/class-booking/create/`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ availability, subject }),
        timeout: 10000,
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Booking error:", error);
    throw error;
  }
}
```

### 6.2 مدیریت توکن

**نگهداری توکن:**
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// ذخیره
await AsyncStorage.setItem('authToken', token);

// بازیابی
const token = await AsyncStorage.getItem('authToken');

// حذف (logout)
await AsyncStorage.removeItem('authToken');
```

### 6.3 مدیریت درگاه Zibal

**بدون WebView (استفاده از Linking):**
```typescript
import * as Linking from 'expo-linking';

async function openPaymentGateway(paymentUrl: string) {
  try {
    const supported = await Linking.canOpenURL(paymentUrl);
    if (supported) {
      await Linking.openURL(paymentUrl);
    } else {
      Alert.alert("خطا", "درگاه پرداخت قابل باز کردن نیست.");
    }
  } catch (error) {
    Alert.alert("خطا", "خطای باز کردن درگاه");
  }
}
```

**با WebView (توصیه‌شده برای کنترل بیشتر):**
```typescript
import { WebView } from 'react-native-webview';

<WebView
  source={{ uri: paymentUrl }}
  onNavigationStateChange={(navState) => {
    if (navState.url.includes('booking')) {
      // بازگشت از Zibal
      checkPaymentStatus(bookingId);
      navigation.goBack();
    }
  }}
/>
```

### 6.4 مدیریت Deep Links

**برای Deep Link پس از پرداخت:**
```typescript
import * as Linking from 'expo-linking';

const prefix = Linking.createURL('/');

const linking = {
  prefixes: [prefix, 'fofofish://'],
  config: {
    screens: {
      BookingDetails: 'booking/:id',
      PaymentReturn: 'booking/:id/payment/return',
    },
  },
};

// استفاده در Navigation
<NavigationContainer linking={linking}>
  {/* screens */}
</NavigationContainer>
```

### 6.5 Retry Strategy

**خطا فقط یک بار، پس از نمایش:**
```typescript
async function fetchWithRetry(
  url: string,
  options: FetchOptions,
  retries = 1
): Promise<Response> {
  try {
    return await fetchWithTimeout(url, options);
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 ثانیه تأخیر
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}

// استفاده
try {
  const response = await fetchWithRetry(url, options, retries = 2);
} catch (error) {
  // نمایش خطا
}
```

---

### 6.6 عدم ذخیره payment_url

**⚠️ IMPORTANT:**
```typescript
// ❌ WRONG
const savedPaymentUrl = paymentUrl; // در state ذخیره نکنید
localStorage.setItem('paymentUrl', paymentUrl); // یا AsyncStorage

// ✅ CORRECT
// فقط هنگام استفاده
function handlePayment(paymentUrl: string) {
  openPaymentGateway(paymentUrl); // فوری باز کنید
}

// بعد از استفاده: فراموش کنید
paymentUrl = null;
```

**دلیل:** payment_url محدود‌المدت است (~15 دقیقه). اگر ذخیره شود و بعداً استفاده شود، معتبر نخواهد بود.

### 6.7 Timeout Settings

**بهترین مقادیر برای Fofofish:**
```typescript
const TIMEOUTS = {
  BOOKING_CREATE: 10000,        // 10s
  PAYMENT_INITIATE: 15000,      // 15s (درگاه بخش‌تر است)
  PAYMENT_STATUS_CHECK: 8000,   // 8s
  LIST_FETCH: 10000,            // 10s
};
```

---

## 7. خلاصه API Endpoints

| فعل | URL | عنوان | Authentication |
|-----|-----|-------|---|
| POST | `/class-booking/create/` | رزرو کلاس | ✅ |
| POST | `/class-booking/{id}/initiate-payment/` | شروع پرداخت | ✅ |
| GET | `/class-booking/{id}/payment-status/` | بررسی وضعیت | ✅ |
| GET | `/my-bookings/` | لیست رزروها | ✅ |

---

## 8. نکات نهایی

### ✅ بهترین‌های
- توکن را همیشه در Header ارسال کن
- بعد از پرداخت 1-2 ثانیه صبر کن پیش از بررسی وضعیت
- Deep Links برای پرداخت استفاده کن
- خطاهای شبکه را مشترکانه مدیریت کن
- Loading UI نمایش بده حین درخواست‌ها

### ❌ اشتباهات رایج
- استفاده از `fetch` بدون timeout
- ذخیره payment_url برای استفاده‌های آینده
- خودکار refresh صفحه پس از خطا
- حذف رزرو بدون تأیید بک‌اند
- نمایش raw error messages از بک‌اند (ترجمه کن)

---

**نسخه:** 1.0  
**آخرین بروزرسانی:** 1402-10-11  
**Binding:** MANDATORY برای Copilot اپ موبایل
