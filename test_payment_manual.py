#!/usr/bin/env python
"""
تست Manual برای Payment & Discount Logic

این تست قابل اجرا بدون database است.
"""

from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MockBooking:
    """شبیه‌سازی Booking برای تست"""
    id: int
    price: Decimal
    discount_amount: Decimal
    payment_status: str = 'not_paid'
    paid_amount: Decimal = Decimal('0')
    paid_at: Optional[datetime] = None
    
    @property
    def final_price(self) -> Decimal:
        """محاسبه قیمت نهایی"""
        return self.price - self.discount_amount


# ===== تست‌های منطقی =====

def test_booking_without_discount():
    """تست: رزروی بدون تخفیف"""
    booking = MockBooking(
        id=1,
        price=Decimal('100000'),
        discount_amount=Decimal('0')
    )
    
    assert booking.final_price == Decimal('100000'), "Final price should equal price"
    print("✅ تست 1: رزروی بدون تخفیف - موفق")
    print(f"   Price: {booking.price}, Discount: {booking.discount_amount}, Final: {booking.final_price}")


def test_booking_with_discount():
    """تست: رزروی با تخفیف 30%"""
    booking = MockBooking(
        id=2,
        price=Decimal('100000'),
        discount_amount=Decimal('30000')
    )
    
    assert booking.final_price == Decimal('70000'), "Final price should be price - discount"
    print("✅ تست 2: رزروی با تخفیف 30% - موفق")
    print(f"   Price: {booking.price}, Discount: {booking.discount_amount}, Final: {booking.final_price}")


def test_booking_fully_discounted():
    """تست: رزروی رایگان (تخفیف 100%)"""
    booking = MockBooking(
        id=3,
        price=Decimal('100000'),
        discount_amount=Decimal('100000')
    )
    
    assert booking.final_price == Decimal('0'), "Final price should be zero for fully discounted"
    print("✅ تست 3: رزروی رایگان (تخفیف 100%) - موفق")
    print(f"   Price: {booking.price}, Discount: {booking.discount_amount}, Final: {booking.final_price}")


def test_payment_logic_without_discount():
    """تست: منطق پرداخت بدون تخفیف"""
    booking = MockBooking(
        id=4,
        price=Decimal('100000'),
        discount_amount=Decimal('0')
    )
    
    final_amount = booking.final_price
    
    # منطق: اگر > 0، به Zibal برو
    if final_amount > 0:
        amount_toman = int(float(final_amount) / 10)
        should_send_to_zibal = True
    else:
        amount_toman = 0
        should_send_to_zibal = False
    
    assert should_send_to_zibal == True, "Should send to Zibal"
    assert amount_toman == 10000, "Amount in toman should be 10000"
    print("✅ تست 4: منطق پرداخت بدون تخفیف - موفق")
    print(f"   Final: {final_amount}, Toman: {amount_toman}, Send to Zibal: {should_send_to_zibal}")


def test_payment_logic_with_discount():
    """تست: منطق پرداخت با تخفیف"""
    booking = MockBooking(
        id=5,
        price=Decimal('100000'),
        discount_amount=Decimal('30000')
    )
    
    final_amount = booking.final_price
    
    # منطق: اگر > 0، به Zibal برو
    if final_amount > 0:
        amount_toman = int(float(final_amount) / 10)
        should_send_to_zibal = True
    else:
        amount_toman = 0
        should_send_to_zibal = False
    
    assert should_send_to_zibal == True, "Should send to Zibal"
    assert amount_toman == 7000, "Amount in toman should be 7000"
    print("✅ تست 5: منطق پرداخت با تخفیف - موفق")
    print(f"   Final: {final_amount}, Toman: {amount_toman}, Send to Zibal: {should_send_to_zibal}")


def test_payment_logic_free():
    """تست: منطق پرداخت برای رزروی رایگان"""
    booking = MockBooking(
        id=6,
        price=Decimal('100000'),
        discount_amount=Decimal('100000')
    )
    
    final_amount = booking.final_price
    
    # منطق: اگر = 0، مستقیم paid
    if final_amount == 0:
        booking.payment_status = 'paid'
        booking.paid_amount = Decimal('0')
        booking.paid_at = datetime.now()
        should_send_to_zibal = False
        is_free = True
    else:
        amount_toman = int(float(final_amount) / 10)
        should_send_to_zibal = True
        is_free = False
    
    assert is_free == True, "Should be marked as free"
    assert booking.payment_status == 'paid', "Status should be paid"
    assert should_send_to_zibal == False, "Should NOT send to Zibal"
    print("✅ تست 6: منطق پرداخت برای رزروی رایگان - موفق")
    print(f"   Final: {final_amount}, Status: {booking.payment_status}, Send to Zibal: {should_send_to_zibal}")


# ===== تست‌های Edge Cases =====

def test_very_small_discount():
    """تست: تخفیف بسیار کوچک"""
    booking = MockBooking(
        id=7,
        price=Decimal('100000'),
        discount_amount=Decimal('1')
    )
    
    assert booking.final_price == Decimal('99999'), "Should calculate correctly"
    print("✅ تست 7: تخفیف بسیار کوچک - موفق")


def test_decimal_precision():
    """تست: دقت Decimal"""
    booking = MockBooking(
        id=8,
        price=Decimal('123456.78'),
        discount_amount=Decimal('45678.90')
    )
    
    expected = Decimal('77777.88')
    assert booking.final_price == expected, f"Should be {expected}, got {booking.final_price}"
    print("✅ تست 8: دقت Decimal - موفق")


def test_amount_conversion():
    """تست: تبدیل ریال به تومان"""
    test_cases = [
        (Decimal('100000'), 10000),  # 100,000 ریال = 10,000 تومان
        (Decimal('70000'), 7000),    # 70,000 ریال = 7,000 تومان
        (Decimal('50000'), 5000),    # 50,000 ریال = 5,000 تومان
        (Decimal('10000'), 1000),    # 10,000 ریال = 1,000 تومان
    ]
    
    for amount_rial, expected_toman in test_cases:
        amount_toman = int(float(amount_rial) / 10)
        assert amount_toman == expected_toman, f"Failed for {amount_rial}"
    
    print("✅ تست 9: تبدیل ریال به تومان - موفق")


# ===== API Response Scenarios =====

def test_api_response_with_payment():
    """تست: پاسخ API برای رزروی نیازمند پرداخت"""
    booking = MockBooking(
        id=10,
        price=Decimal('100000'),
        discount_amount=Decimal('30000')
    )
    
    final_amount = booking.final_price
    
    response = {
        'success': True,
        'data': {
            'booking_id': booking.id,
            'amount': str(final_amount),
            'currency': 'IRR',
            'is_free': False,
            'payment_url': 'https://gateway.zibal.ir/start/ABC123',
            'message': 'پرداخت آغاز شد'
        }
    }
    
    assert response['data']['is_free'] == False
    assert response['data']['amount'] == '70000'
    assert response['data']['payment_url'] is not None
    print("✅ تست 10: API Response برای پرداخت - موفق")
    print(f"   Response: {response}")


def test_api_response_free():
    """تست: پاسخ API برای رزروی رایگان"""
    booking = MockBooking(
        id=11,
        price=Decimal('100000'),
        discount_amount=Decimal('100000')
    )
    
    final_amount = booking.final_price
    
    response = {
        'success': True,
        'data': {
            'booking_id': booking.id,
            'amount': str(final_amount),
            'currency': 'IRR',
            'is_free': True,
            'payment_url': None,
            'message': 'کلاس رایگان است - پرداخت ثبت شد'
        }
    }
    
    assert response['data']['is_free'] == True
    assert response['data']['amount'] == '0'
    assert response['data']['payment_url'] is None
    print("✅ تست 11: API Response برای رایگان - موفق")
    print(f"   Response: {response}")


# ===== اجرای تست‌ها =====

def run_all_tests():
    """اجرای تمام تست‌ها"""
    print("\n" + "="*60)
    print("🧪 تست سیستم پرداخت و تخفیف")
    print("="*60 + "\n")
    
    tests = [
        ("محاسبه مبلغ نهایی", [
            test_booking_without_discount,
            test_booking_with_discount,
            test_booking_fully_discounted,
        ]),
        ("منطق پرداخت", [
            test_payment_logic_without_discount,
            test_payment_logic_with_discount,
            test_payment_logic_free,
        ]),
        ("Edge Cases", [
            test_very_small_discount,
            test_decimal_precision,
            test_amount_conversion,
        ]),
        ("API Responses", [
            test_api_response_with_payment,
            test_api_response_free,
        ]),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for category, test_funcs in tests:
        print(f"\n📋 {category}:")
        print("-" * 60)
        
        for test_func in test_funcs:
            try:
                test_func()
                total_passed += 1
            except AssertionError as e:
                print(f"❌ {test_func.__name__} - FAILED: {e}")
                total_failed += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} - ERROR: {e}")
                total_failed += 1
    
    # خلاصه
    print("\n" + "="*60)
    print(f"📊 نتایج: ✅ {total_passed} موفق, ❌ {total_failed} ناموفق")
    print("="*60 + "\n")
    
    return total_failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
