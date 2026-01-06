"""
Package Installment Payment API - Test Examples
تست کامل تمام endpoints قسط‌بندی
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token_here"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

HEADERS_NO_AUTH = {
    "Content-Type": "application/json"
}


def print_response(title, response):
    """نمایش پاسخ به شکل خوبی"""
    print(f"\n{'='*60}")
    print(f"🔹 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


# ============================================================================
# 1️⃣ Test: لیست بسه‌های آموزشی
# ============================================================================

def test_get_packages():
    """
    GET /api/packages/
    دریافت لیست بسه‌های فعال
    """
    print("\n" + "▶"*40)
    print("TEST 1: دریافت لیست بسه‌ها")
    print("▶"*40)
    
    response = requests.get(
        f"{BASE_URL}/packages/",
        headers=HEADERS
    )
    
    print_response("لیست بسه‌های آموزشی", response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            return data['data'][0]['id']  # برگردان ID اول
    return None


# ============================================================================
# 2️⃣ Test: لیست ثبت‌نام‌های دانش‌آموز
# ============================================================================

def test_get_enrollments():
    """
    GET /api/student/enrollments/
    دریافت ثبت‌نام‌های دانش‌آموز حاضر
    """
    print("\n" + "▶"*40)
    print("TEST 2: دریافت ثبت‌نام‌های دانش‌آموز")
    print("▶"*40)
    
    response = requests.get(
        f"{BASE_URL}/student/enrollments/",
        headers=HEADERS
    )
    
    print_response("ثبت‌نام‌های دانش‌آموز", response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            enrollment = data['data'][0]
            print(f"\n📊 خلاصه اول ثبت‌نام:")
            print(f"   - ID: {enrollment['id']}")
            print(f"   - نام بسه: {enrollment['package_name']}")
            print(f"   - وضعیت: {enrollment['status']}")
            print(f"   - درصد پرداخت: {enrollment['payment_summary']['completion_percentage']}%")
            return enrollment['id']
    return None


# ============================================================================
# 3️⃣ Test: بررسی دسترسی به جلسه (موفق)
# ============================================================================

def test_check_access_allowed(enrollment_id):
    """
    POST /api/packages/check-session-access/
    بررسی دسترسی (فرض: جلسه اول پرداخت شده)
    """
    print("\n" + "▶"*40)
    print("TEST 3: بررسی دسترسی به جلسه (انتظار: ✅ مجاز)")
    print("▶"*40)
    
    payload = {
        "enrollment_id": enrollment_id,
        "session_number": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/packages/check-session-access/",
        headers=HEADERS,
        json=payload
    )
    
    print_response("بررسی دسترسی - جلسه اول", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n{'✅' if data.get('can_access') else '❌'} نتیجه: {data.get('message')}")


# ============================================================================
# 4️⃣ Test: بررسی دسترسی به جلسه (رد)
# ============================================================================

def test_check_access_denied(enrollment_id):
    """
    POST /api/packages/check-session-access/
    بررسی دسترسی (فرض: جلسه بعدی پرداخت نشده)
    """
    print("\n" + "▶"*40)
    print("TEST 4: بررسی دسترسی به جلسه (انتظار: ❌ رد)")
    print("▶"*40)
    
    payload = {
        "enrollment_id": enrollment_id,
        "session_number": 5  # جلسه‌ای که احتمالاً قسط آن پرداخت نشده
    }
    
    response = requests.post(
        f"{BASE_URL}/packages/check-session-access/",
        headers=HEADERS,
        json=payload
    )
    
    print_response("بررسی دسترسی - جلسه بعدی", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n{'✅' if not data.get('can_access') else '❌'} نتیجه: {data.get('message')}")


# ============================================================================
# 5️⃣ Test: شروع فرآیند پرداخت
# ============================================================================

def test_process_payment(enrollment_id):
    """
    POST /api/packages/process-payment/
    شروع پرداخت قسط بعدی از طریق Zibal
    """
    print("\n" + "▶"*40)
    print("TEST 5: شروع فرآیند پرداخت (Zibal)")
    print("▶"*40)
    
    payload = {
        "enrollment_id": enrollment_id,
        "phone": "09123456789",
        "description": "پرداخت قسط دوم بسته آموزشی"
    }
    
    response = requests.post(
        f"{BASE_URL}/packages/process-payment/",
        headers=HEADERS,
        json=payload
    )
    
    print_response("درخواست پرداخت", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n💳 لینک پرداخت Zibal:")
        print(f"   {data.get('payment_url')}")
        print(f"\n📦 جزئیات:")
        print(f"   - مبلغ: {data.get('amount')} تومان")
        print(f"   - قسط: {data.get('installment_number')}")
        print(f"   - جلسه: {data.get('session_number')}")
        print(f"   - Track ID: {data.get('track_id')}")
        return data.get('track_id')
    return None


# ============================================================================
# 6️⃣ Test: تأیید پرداخت (Zibal Callback)
# ============================================================================

def test_verify_payment(track_id):
    """
    GET /api/packages/verify-payment/?trackId=...&status=100
    تأیید پرداخت (شبیه‌سازی callback از Zibal)
    
    توجه: این endpoint عادتاً توسط Zibal فراخوانی می‌شود
    """
    print("\n" + "▶"*40)
    print("TEST 6: تأیید پرداخت (Callback شبیه‌سازی)")
    print("▶"*40)
    
    if not track_id:
        print("❌ Track ID دریافت نشد، تست صرف نظر شد")
        return
    
    params = {
        'trackId': track_id,
        'status': '100',  # 100 = موفق
        'orderId': '5',
        'refNumber': '123456789'
    }
    
    response = requests.get(
        f"{BASE_URL}/packages/verify-payment/",
        headers=HEADERS_NO_AUTH,
        params=params
    )
    
    print_response("تأیید پرداخت", response)
    
    if response.status_code == 200:
        print("\n✅ پرداخت تأیید شد!")


# ============================================================================
# 7️⃣ Test: خطاها
# ============================================================================

def test_error_cases():
    """تست موارد خطا"""
    print("\n" + "▶"*40)
    print("TEST 7: موارد خطا")
    print("▶"*40)
    
    # خطا: بدون Token
    print("\n[1] بدون Token:")
    response = requests.get(f"{BASE_URL}/packages/")
    print(f"Status: {response.status_code} (انتظار: 401)")
    
    # خطا: Enrollment نامعتبر
    print("\n[2] Enrollment ID نامعتبر:")
    response = requests.post(
        f"{BASE_URL}/packages/check-session-access/",
        headers=HEADERS,
        json={"enrollment_id": 99999, "session_number": 1}
    )
    print(f"Status: {response.status_code} (انتظار: 404)")
    print(response.json().get('message'))
    
    # خطا: داده نقص
    print("\n[3] داده نقص (بدون session_number):")
    response = requests.post(
        f"{BASE_URL}/packages/check-session-access/",
        headers=HEADERS,
        json={"enrollment_id": 1}
    )
    print(f"Status: {response.status_code} (انتظار: 400)")
    print(response.json().get('message'))


# ============================================================================
# 🎯 اجرای کامل
# ============================================================================

def run_full_test():
    """
    اجرای کامل تمام تست‌ها
    """
    print("\n")
    print("🚀"*30)
    print("شروع تست‌های Package Payment API")
    print("🚀"*30)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. لیست بسه‌ها
    # package_id = test_get_packages()
    
    # 2. لیست ثبت‌نام‌های دانش‌آموز
    enrollment_id = test_get_enrollments()
    
    if not enrollment_id:
        print("\n❌ دریافت enrollment_id ناموفق")
        return
    
    # 3. بررسی دسترسی (موفق)
    test_check_access_allowed(enrollment_id)
    
    # 4. بررسی دسترسی (رد)
    test_check_access_denied(enrollment_id)
    
    # 5. شروع پرداخت
    track_id = test_process_payment(enrollment_id)
    
    # 6. تأیید پرداخت
    if track_id:
        test_verify_payment(track_id)
    
    # 7. خطاها
    test_error_cases()
    
    print("\n")
    print("✅"*30)
    print("پایان تست‌ها")
    print("✅"*30)


# ============================================================================
# مثال آزمایش جزئی
# ============================================================================

if __name__ == '__main__':
    # اجرای کامل:
    run_full_test()
    
    # یا جزئی (نمونه درخواست‌ها):
    # print("💡 نمونه درخواست‌ها:")
    print("\n1️⃣ GET /api/packages/")
    print("   (بدون داده)")
    
    print("\n2️⃣ GET /api/student/enrollments/")
    print("   (بدون داده)")
    
    print("\n3️⃣ POST /api/packages/check-session-access/")
    print(json.dumps({
        "enrollment_id": 5,
        "session_number": 3
    }, indent=2, ensure_ascii=False))
    
    print("\n4️⃣ POST /api/packages/process-payment/")
    print(json.dumps({
        "enrollment_id": 5,
        "phone": "09123456789",
        "description": "پرداخت قسط دوم"
    }, indent=2, ensure_ascii=False))
    
    print("\n5️⃣ GET /api/packages/verify-payment/")
    print("   ?trackId=5034399684ea1e2b&status=100&orderId=5&refNumber=123456")
    
    print("\n\n⚠️  برای اجرای کامل:")
    print("   python test_package_payment.py    (از command line)")
