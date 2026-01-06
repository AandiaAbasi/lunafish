"""
Package Installment Payment - Integration Examples
نمونه‌های استفاده برای Classroom App (React/Vue Components)
"""

# ============================================================================
# 🎯 نمونه 1: دریافت بسه‌ها در صفحه اول
# ============================================================================

"""
REACT Component:

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const PackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPackages = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/packages/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.success) {
          setPackages(response.data.data);
        }
      } catch (error) {
        console.error('خطا در دریافت بسه‌ها:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPackages();
  }, []);

  return (
    <div className="packages-container">
      <h1>بسه‌های آموزشی</h1>
      
      {loading && <p>درحال بارگذاری...</p>}
      
      {packages.map((pkg) => (
        <div key={pkg.id} className="package-card">
          <h3>{pkg.name}</h3>
          <p>{pkg.description}</p>
          <p>معلم: {pkg.teacher_name}</p>
          <p>تعداد جلسات: {pkg.total_sessions}</p>
          <p>قیمت: {pkg.total_price} تومان</p>
          <button onClick={() => enrollPackage(pkg.id)}>
            ثبت‌نام
          </button>
        </div>
      ))}
    </div>
  );
};

export default PackagesPage;
"""


# ============================================================================
# 🎯 نمونه 2: نمایش ثبت‌نام‌ها و اقساط
# ============================================================================

"""
REACT Component:

const MyEnrollmentsPage = () => {
  const [enrollments, setEnrollments] = useState([]);

  useEffect(() => {
    const fetchEnrollments = async () => {
      const response = await axios.get('/api/student/enrollments/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.data.success) {
        setEnrollments(response.data.data);
      }
    };

    fetchEnrollments();
  }, []);

  return (
    <div>
      <h1>ثبت‌نام‌های من</h1>
      
      {enrollments.map((enrollment) => (
        <div key={enrollment.id} className="enrollment-card">
          <h3>{enrollment.package_name}</h3>
          <p>معلم: {enrollment.teacher_name}</p>
          
          {/* خلاصه پرداخت */}
          <div className="payment-summary">
            <h4>خلاصه پرداخت:</h4>
            <p>مبلغ کل: {enrollment.payment_summary.total_amount} تومان</p>
            <p>پرداخت شده: {enrollment.payment_summary.paid_amount} تومان</p>
            <p>باقی‌مانده: {enrollment.payment_summary.remaining_amount} تومان</p>
            
            {/* Progress Bar */}
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${enrollment.payment_summary.completion_percentage}%`
                }}
              />
            </div>
            <p>{enrollment.payment_summary.completion_percentage.toFixed(1)}% تکمیل</p>
          </div>
          
          {/* اقساط معلق */}
          {enrollment.pending_installments.length > 0 && (
            <div className="pending-installments">
              <h4>اقساط معلق:</h4>
              {enrollment.pending_installments.map((inst) => (
                <div key={inst.id} className="installment-item">
                  <p>قسط {inst.installment_number} - جلسه {inst.session_number}</p>
                  <p>مبلغ: {inst.amount_due} تومان</p>
                  <p>وضعیت: {inst.payment_status}</p>
                </div>
              ))}
            </div>
          )}
          
          {/* دکمه پرداخت */}
          {enrollment.next_due && (
            <button onClick={() => processPayment(enrollment.id)}>
              پرداخت قسط بعدی ({enrollment.next_due.amount_due} تومان)
            </button>
          )}
        </div>
      ))}
    </div>
  );
};
"""


# ============================================================================
# 🎯 نمونه 3: بررسی دسترسی قبل از شرکت در جلسه
# ============================================================================

"""
REACT Component:

const ClassroomPage = ({ enrollmentId, sessionNumber }) => {
  const [canAccess, setCanAccess] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const checkAccess = async () => {
      try {
        const response = await axios.post(
          '/api/packages/check-session-access/',
          {
            enrollment_id: enrollmentId,
            session_number: sessionNumber
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (response.data.success) {
          setCanAccess(response.data.can_access);
          setMessage(response.data.message);
          
          if (!response.data.can_access && response.data.next_due_installment) {
            // نمایش دکمه پرداخت
            console.log('قسط معلق:', response.data.next_due_installment);
          }
        }
      } catch (error) {
        console.error('خطا در بررسی دسترسی:', error);
      }
    };

    checkAccess();
  }, [enrollmentId, sessionNumber]);

  if (canAccess === null) {
    return <p>درحال بررسی دسترسی...</p>;
  }

  if (!canAccess) {
    return (
      <div className="access-denied">
        <h2>❌ دسترسی مجاز نیست</h2>
        <p>{message}</p>
        <button onClick={() => initiatePayment(enrollmentId)}>
          پرداخت و دریافت دسترسی
        </button>
      </div>
    );
  }

  return (
    <div className="classroom">
      <h1>✅ جلسه {sessionNumber}</h1>
      <p>{message}</p>
      {/* محتوای جلسه */}
    </div>
  );
};
"""


# ============================================================================
# 🎯 نمونه 4: فرآیند پرداخت (Zibal)
# ============================================================================

"""
REACT Component:

const PaymentPage = ({ enrollmentId }) => {
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');

  const handlePayment = async () => {
    if (!phone) {
      alert('لطفاً شماره موبایل خود را وارد کنید');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        '/api/packages/process-payment/',
        {
          enrollment_id: enrollmentId,
          phone: phone,
          description: 'پرداخت قسط بسته آموزشی'
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (response.data.success) {
        // نمایش اطلاعات پرداخت
        console.log('Track ID:', response.data.track_id);
        console.log('مبلغ:', response.data.amount);
        
        // ریدایرکت به درگاه Zibal
        window.location.href = response.data.payment_url;
        
        // یا
        // window.open(response.data.payment_url, '_blank');
      }
    } catch (error) {
      console.error('خطا در پرداخت:', error);
      alert('خطا در شروع پرداخت');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="payment-form">
      <h2>پرداخت قسط</h2>
      
      <div className="form-group">
        <label>شماره موبایل</label>
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="09123456789"
          disabled={loading}
        />
      </div>
      
      <button 
        onClick={handlePayment}
        disabled={loading}
      >
        {loading ? 'درحال پرداخت...' : 'پرداخت از طریق Zibal'}
      </button>
    </div>
  );
};
"""


# ============================================================================
# 🎯 نمونه 5: Django View - بررسی دسترسی
# ============================================================================

"""
Django (classroom/views.py):

from api.package_service import PackageInstallmentService
from classroom.models import StudentPackageEnrollment

class StudentClassroomView(View):
    def get(self, request, enrollment_id, session_number):
        try:
            enrollment = StudentPackageEnrollment.objects.get(
                id=enrollment_id,
                student=request.user
            )
            
            # بررسی دسترسی
            can_access, message = PackageInstallmentService.can_student_attend_session(
                enrollment,
                session_number
            )
            
            if not can_access:
                # بازگردان به صفحه پرداخت
                return redirect('payment', enrollment_id=enrollment_id)
            
            # کاربر می‌تواند وارد شود
            context = {
                'enrollment': enrollment,
                'session_number': session_number,
                'message': message
            }
            return render(request, 'classroom/session.html', context)
        
        except StudentPackageEnrollment.DoesNotExist:
            return HttpResponseForbidden('دسترسی رد شد')
"""


# ============================================================================
# 🎯 نمونه 6: JavaScript - Zibal Callback Handler
# ============================================================================

"""
JavaScript (صفحه‌ای که Zibal به آن بازمی‌گردد):

// URL: /payment/callback/?trackId=...&status=100&orderId=...&refNumber=...

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const trackId = urlParams.get('trackId');
  const status = urlParams.get('status');
  
  if (status === '100') {
    // پرداخت موفق
    console.log('✅ پرداخت موفق!');
    console.log('Track ID:', trackId);
    
    // Zibal خودکار backend را فراخوانی می‌کند
    // 2-3 ثانیه صبر کنید
    setTimeout(() => {
      // کاربر را به جلسه بازگردانید
      window.location.href = '/classroom/session/';
    }, 3000);
  } else {
    // پرداخت ناموفق
    console.error('❌ پرداخت ناموفق');
    console.error('Status:', status);
    
    // کاربر را به صفحه پرداخت بازگردانید
    window.location.href = '/payment/retry/';
  }
});
"""


# ============================================================================
# 🎯 نمونه 7: Python - Test from Postman/Thunder Client
# ============================================================================

"""
Postman Collection (JSON):

{
  "info": {
    "name": "Package Payment API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Packages",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/packages/",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    },
    {
      "name": "Get Enrollments",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/student/enrollments/",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    },
    {
      "name": "Check Session Access",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/packages/check-session-access/",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\\"enrollment_id\\": 5, \\"session_number\\": 3}"
        }
      }
    },
    {
      "name": "Process Payment",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/packages/process-payment/",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\\"enrollment_id\\": 5, \\"phone\\": \\"09123456789\\", \\"description\\": \\"پرداخت قسط\\"}"
        }
      }
    },
    {
      "name": "Verify Payment",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/packages/verify-payment/?trackId=ABC123&status=100&orderId=5&refNumber=XYZ"
      }
    }
  ]
}
"""


# ============================================================================
# 🎯 نمونه 8: React Hook - Custom Hook
# ============================================================================

"""
React Hook:

import { useCallback, useState } from 'react';
import axios from 'axios';

export const usePackagePayment = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getPackages = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get('/api/packages/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      return data.data;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkAccess = useCallback(async (enrollmentId, sessionNumber) => {
    try {
      const { data } = await axios.post(
        '/api/packages/check-session-access/',
        { enrollment_id: enrollmentId, session_number: sessionNumber },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      return data;
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const processPayment = useCallback(async (enrollmentId, phone) => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        '/api/packages/process-payment/',
        { enrollment_id: enrollmentId, phone },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      return data;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, getPackages, checkAccess, processPayment };
};

// استفاده:
// const { loading, error, checkAccess } = usePackagePayment();
// await checkAccess(enrollmentId, sessionNumber);
"""


# ============================================================================
# 🎯 نمونه 9: Vue.js Component
# ============================================================================

"""
Vue Component:

<template>
  <div class="payment-container">
    <h1>{{ enrollment.package_name }}</h1>
    
    <!-- خلاصه پرداخت -->
    <div class="summary">
      <p>مبلغ کل: {{ summary.total_amount }}</p>
      <p>پرداخت شده: {{ summary.paid_amount }}</p>
      <p>درصد: {{ summary.completion_percentage }}%</p>
    </div>
    
    <!-- اقساط معلق -->
    <div v-if="nextDue" class="next-installment">
      <h3>قسط بعدی</h3>
      <p>مبلغ: {{ nextDue.amount_due }} تومان</p>
      <input v-model="phone" placeholder="شماره موبایل" />
      <button @click="handlePayment" :disabled="loading">
        {{ loading ? 'درحال پرداخت...' : 'پرداخت' }}
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      enrollment: null,
      phone: '',
      loading: false
    }
  },
  computed: {
    summary() {
      return this.enrollment?.payment_summary || {};
    },
    nextDue() {
      return this.enrollment?.next_due || null;
    }
  },
  methods: {
    async handlePayment() {
      this.loading = true;
      try {
        const { data } = await axios.post(
          '/api/packages/process-payment/',
          {
            enrollment_id: this.enrollment.id,
            phone: this.phone
          }
        );
        
        window.location.href = data.payment_url;
      } catch (error) {
        console.error(error);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
"""


# ============================================================================
# 🎯 نمونه 10: Unit Tests (Pytest)
# ============================================================================

"""
Pytest Tests:

import pytest
from django.test import Client
from rest_framework.test import APITestCase, APIClient
from classroom.models import Package, StudentPackageEnrollment

@pytest.mark.django_db
class TestPackagePaymentAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # ایجاد test data
        
    def test_get_packages(self):
        response = self.client.get('/api/packages/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('success'))
    
    def test_check_access_allowed(self):
        response = self.client.post(
            '/api/packages/check-session-access/',
            {'enrollment_id': 1, 'session_number': 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('can_access'))
    
    def test_check_access_denied(self):
        response = self.client.post(
            '/api/packages/check-session-access/',
            {'enrollment_id': 1, 'session_number': 99}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data.get('can_access'))
"""


print("""
✅ Integration Examples Complete!

نمونه‌های ارائه شده:
1. ✅ React Component - صفحه بسه‌ها
2. ✅ React Component - نمایش ثبت‌نام‌ها
3. ✅ React Component - بررسی دسترسی
4. ✅ React Component - فرآیند پرداخت
5. ✅ Django View - بررسی دسترسی
6. ✅ JavaScript - Zibal Callback
7. ✅ Postman Collection
8. ✅ React Hook - Custom
9. ✅ Vue Component
10. ✅ Pytest Tests

برای استفاده:
1. کد مربوطه را کاپی کنید
2. به پروژه خود اضافه کنید
3. تست کنید!
""")
