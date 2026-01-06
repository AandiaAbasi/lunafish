"""
Teacher Package Management - Code Examples
نمونه کدهای مدیریت بسه توسط معلم
"""

# ============================================================================
# React Component Examples
# ============================================================================

REACT_EXAMPLES = """
// 1. لیست بسه‌های معلم

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const TeacherPackagesPage = () => {
  const [packages, setPackages] = useState([]);
  
  useEffect(() => {
    const fetchPackages = async () => {
      const res = await axios.get('/api/teacher/packages/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setPackages(res.data.data);
    };
    fetchPackages();
  }, []);
  
  return (
    <div>
      <h1>بسه‌های من</h1>
      {packages.map(pkg => (
        <div key={pkg.id} className="package-card">
          <h3>{pkg.name}</h3>
          <p>جلسات: {pkg.total_sessions}</p>
          <p>قیمت: {pkg.total_price} تومان</p>
          <p>دانش‌آموزان: {pkg.total_students_enrolled}</p>
          <p>درآمد: {pkg.total_revenue} تومان</p>
          <button onClick={() => editPackage(pkg.id)}>ویرایش</button>
          <button onClick={() => deletePackage(pkg.id)}>حذف</button>
          <button onClick={() => manageInstallments(pkg.id)}>مدیریت اقساط</button>
        </div>
      ))}
    </div>
  );
};
```

// 2. ایجاد بسه جدید

```javascript
const CreatePackageModal = () => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    total_sessions: 12,
    total_price: '',
    teaching_subjects: [],
    has_installment: true,
    is_active: true
  });
  
  const handleCreate = async () => {
    const res = await axios.post('/api/teacher/packages/', formData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (res.data.success) {
      alert('بسه ایجاد شد!');
      // قسط پیش‌فرض خودکار ایجاد شده است
      // اگر بخواهید اقساط بیشتری اضافه کنید...
      goToInstallments(res.data.data.id);
    }
  };
  
  return (
    <form onSubmit={handleCreate}>
      <input 
        value={formData.name}
        onChange={e => setFormData({...formData, name: e.target.value})}
        placeholder="نام بسه"
      />
      <input 
        type="number"
        value={formData.total_sessions}
        onChange={e => setFormData({...formData, total_sessions: e.target.value})}
        placeholder="تعداد جلسات"
      />
      <input 
        type="number"
        value={formData.total_price}
        onChange={e => setFormData({...formData, total_price: e.target.value})}
        placeholder="قیمت کل"
      />
      <button type="submit">ایجاد</button>
    </form>
  );
};
```

// 3. مدیریت اقساط

```javascript
const InstallmentManager = ({ packageId }) => {
  const [installments, setInstallments] = useState([]);
  const [newInstallment, setNewInstallment] = useState({
    session_number: '',
    amount: ''
  });
  
  // دریافت اقساط
  useEffect(() => {
    const fetch = async () => {
      const res = await axios.get(
        `/api/teacher/packages/${packageId}/installments/`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setInstallments(res.data.data);
    };
    fetch();
  }, [packageId]);
  
  // اضافه کردن قسط
  const handleAddInstallment = async () => {
    const res = await axios.post(
      `/api/teacher/packages/${packageId}/installments/`,
      newInstallment,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    if (res.data.success) {
      setInstallments([...installments, res.data.data]);
      setNewInstallment({ session_number: '', amount: '' });
      alert('قسط اضافه شد!');
    }
  };
  
  // حذف قسط
  const handleDeleteInstallment = async (installmentId) => {
    if (!confirm('آیا مطمئنید؟')) return;
    
    const res = await axios.delete(
      `/api/teacher/packages/${packageId}/installments/${installmentId}/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    if (res.data.success) {
      setInstallments(installments.filter(i => i.id !== installmentId));
      alert('قسط حذف شد!');
    }
  };
  
  return (
    <div>
      <h2>مدیریت اقساط</h2>
      
      {/* اقساط موجود */}
      <table>
        <thead>
          <tr>
            <th>قسط</th>
            <th>جلسه</th>
            <th>مبلغ</th>
            <th>پرداخت‌شده</th>
            <th>عملیات</th>
          </tr>
        </thead>
        <tbody>
          {installments.map(inst => (
            <tr key={inst.id}>
              <td>{inst.installment_number}</td>
              <td>{inst.session_number}</td>
              <td>{inst.amount}</td>
              <td>{inst.paid_count} / {inst.paid_count + inst.pending_count}</td>
              <td>
                <button onClick={() => handleDeleteInstallment(inst.id)}>حذف</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* اضافه کردن قسط جدید */}
      <h3>اضافه کردن قسط جدید</h3>
      <input
        type="number"
        value={newInstallment.session_number}
        onChange={e => setNewInstallment({...newInstallment, session_number: e.target.value})}
        placeholder="شماره جلسه"
      />
      <input
        type="number"
        value={newInstallment.amount}
        onChange={e => setNewInstallment({...newInstallment, amount: e.target.value})}
        placeholder="مبلغ"
      />
      <button onClick={handleAddInstallment}>اضافه کردن</button>
    </div>
  );
};
```

"""

# ============================================================================
# JavaScript/Vanilla Examples
# ============================================================================

JAVASCRIPT_EXAMPLES = """
// Create Package
async function createPackage() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/teacher/packages/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Python Advanced',
      description: 'Complete Python Course',
      total_sessions: 12,
      total_price: '1200000',
      teaching_subjects: [1, 2],
      has_installment: true,
      is_active: true
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Package created:', data.data.id);
    return data.data.id;
  }
}

// List Packages
async function listPackages() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/teacher/packages/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  data.data.forEach(pkg => {
    console.log(`
      ${pkg.name}
      جلسات: ${pkg.total_sessions}
      قیمت: ${pkg.total_price}
      دانش‌آموزان: ${pkg.total_students_enrolled}
      درآمد: ${pkg.total_revenue}
    `);
  });
}

// Add Installment
async function addInstallment(packageId, sessionNumber, amount) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `/api/teacher/packages/${packageId}/installments/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_number: sessionNumber,
        amount: amount
      })
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Installment added:', data.data.id);
    return data.data.id;
  } else {
    console.error('Error:', data.errors);
  }
}

// List Installments
async function listInstallments(packageId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `/api/teacher/packages/${packageId}/installments/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  
  console.table(data.data);
}

// Delete Installment
async function deleteInstallment(packageId, installmentId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `/api/teacher/packages/${packageId}/installments/${installmentId}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Installment deleted');
  }
}
"""

# ============================================================================
# Python/Django Examples
# ============================================================================

PYTHON_EXAMPLES = """
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. ایجاد بسه جدید
def create_package():
    payload = {
        "name": "Python Advanced",
        "description": "Complete Python Course",
        "total_sessions": 12,
        "total_price": "1200000",
        "teaching_subjects": [1, 2],
        "has_installment": True,
        "is_active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/teacher/packages/",
        json=payload,
        headers=HEADERS
    )
    
    data = response.json()
    
    if data['success']:
        print(f"Package created: {data['data']['id']}")
        return data['data']['id']
    else:
        print(f"Error: {data['message']}")
        print(f"Details: {data.get('errors')}")

# 2. لیست بسه‌ها
def list_packages():
    response = requests.get(
        f"{BASE_URL}/teacher/packages/",
        headers=HEADERS
    )
    
    data = response.json()
    
    for pkg in data['data']:
        print(f"""
        {pkg['name']}
        Sessions: {pkg['total_sessions']}
        Price: {pkg['total_price']}
        Students: {pkg['total_students_enrolled']}
        Revenue: {pkg['total_revenue']}
        """)

# 3. اضافه کردن اقساط
def add_installments(package_id):
    # قسط 2: جلسه 4
    installment_2 = {
        "session_number": 4,
        "amount": "300000"
    }
    
    response = requests.post(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/",
        json=installment_2,
        headers=HEADERS
    )
    
    print(f"Installment 2: {response.json()['data']['id']}")
    
    # قسط 3: جلسه 7
    installment_3 = {
        "session_number": 7,
        "amount": "300000"
    }
    
    response = requests.post(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/",
        json=installment_3,
        headers=HEADERS
    )
    
    print(f"Installment 3: {response.json()['data']['id']}")
    
    # قسط 4: جلسه 10
    installment_4 = {
        "session_number": 10,
        "amount": "300000"
    }
    
    response = requests.post(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/",
        json=installment_4,
        headers=HEADERS
    )
    
    print(f"Installment 4: {response.json()['data']['id']}")

# 4. دریافت اقساط
def list_installments(package_id):
    response = requests.get(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/",
        headers=HEADERS
    )
    
    data = response.json()
    
    for inst in data['data']:
        print(f"""
        قسط {inst['installment_number']}:
        - جلسه: {inst['session_number']}
        - مبلغ: {inst['amount']}
        - پرداخت‌شده: {inst['paid_count']}
        - معلق: {inst['pending_count']}
        - درآمد: {inst['total_amount_paid']}
        """)

# 5. حذف قسط
def delete_installment(package_id, installment_id):
    response = requests.delete(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/{installment_id}/",
        headers=HEADERS
    )
    
    data = response.json()
    print(data['message'])

# استفاده:
if __name__ == '__main__':
    # 1. ایجاد بسه
    package_id = create_package()
    
    # 2. اضافه کردن اقساط
    add_installments(package_id)
    
    # 3. دریافت اقساط
    list_installments(package_id)
    
    # 4. لیست بسه‌ها
    list_packages()
"""

# ============================================================================
# Test Cases
# ============================================================================

TEST_CASES = """
import pytest
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from classroom.models import Package, PackageInstallment, TeachingSubject

User = get_user_model()

class TeacherPackageAPITestCase(APITestCase):
    
    def setUp(self):
        self.client = APIClient()
        
        # ایجاد معلم
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='pass123'
        )
        self.teacher.role = 'teacher'
        self.teacher.save()
        
        # ایجاد کلاس آموزشی
        self.subject = TeachingSubject.objects.create(
            title='Python',
            teacher=self.teacher
        )
    
    def test_create_package(self):
        '''معلم می‌تواند بسه ایجاد کند'''
        self.client.force_authenticate(user=self.teacher)
        
        response = self.client.post('/api/teacher/packages/', {
            'name': 'Python 101',
            'total_sessions': 10,
            'total_price': '1000000',
            'teaching_subjects': [self.subject.id],
            'has_installment': True,
            'is_active': True
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
        
        # بررسی اینکه قسط پیش‌فرض ایجاد شد
        package = Package.objects.get(id=response.data['data']['id'])
        self.assertEqual(package.installments.count(), 1)
    
    def test_list_teacher_packages(self):
        '''معلم می‌تواند بسه‌های خود را ببیند'''
        package = Package.objects.create(
            name='Python',
            teacher=self.teacher,
            total_sessions=10,
            total_price=1000000
        )
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/teacher/packages/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
    
    def test_add_installment(self):
        '''معلم می‌تواند قسط اضافه کند'''
        package = Package.objects.create(
            name='Python',
            teacher=self.teacher,
            total_sessions=12,
            total_price=1200000,
            has_installment=True
        )
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            f'/api/teacher/packages/{package.id}/installments/',
            {
                'session_number': 4,
                'amount': '300000'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(package.installments.count(), 2)
    
    def test_cannot_add_duplicate_installment(self):
        '''نمی‌توان قسط تکراری اضافه کرد'''
        package = Package.objects.create(
            name='Python',
            teacher=self.teacher,
            total_sessions=10,
            total_price=1000000
        )
        
        PackageInstallment.objects.create(
            package=package,
            installment_number=1,
            session_number=1,
            amount=1000000
        )
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            f'/api/teacher/packages/{package.id}/installments/',
            {
                'session_number': 1,  # تکراری!
                'amount': '500000'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
"""

# ============================================================================
# Print Examples
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("REACT EXAMPLES")
    print("=" * 80)
    print(REACT_EXAMPLES)
    
    print("\n" + "=" * 80)
    print("JAVASCRIPT EXAMPLES")
    print("=" * 80)
    print(JAVASCRIPT_EXAMPLES)
    
    print("\n" + "=" * 80)
    print("PYTHON EXAMPLES")
    print("=" * 80)
    print(PYTHON_EXAMPLES)
    
    print("\n" + "=" * 80)
    print("TEST CASES")
    print("=" * 80)
    print(TEST_CASES)
