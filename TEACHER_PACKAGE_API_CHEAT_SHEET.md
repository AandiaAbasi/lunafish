# Teacher Package API - Cheat Sheet

## 🔐 Authentication Setup

```bash
# 1. Get your token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher1", "password": "password123"}'

# Response
{
  "access": "eyJhbGciOiJIUzI1...",
  "refresh": "eyJhbGciOiJIUzI1..."
}

# 2. Save token
export TOKEN="your_token_here"

# 3. Use in requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/teacher/packages/
```

---

## 📦 Create Package

### Minimal
```bash
curl -X POST http://localhost:8000/api/teacher/packages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python 101",
    "total_sessions": 10,
    "total_price": "1000000",
    "has_installment": true
  }'
```

### Full
```bash
curl -X POST http://localhost:8000/api/teacher/packages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Advanced",
    "description": "Advanced Python Course",
    "total_sessions": 12,
    "total_price": "1200000",
    "teaching_subjects": [1, 2, 3],
    "has_installment": true,
    "is_active": true
  }'
```

**Response**: 201 Created with package details including `id`

---

## 📋 List Packages

```bash
curl -X GET http://localhost:8000/api/teacher/packages/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: 200 OK with array of packages

```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 5,
      "name": "Python Advanced",
      "total_sessions": 12,
      "total_price": "1200000",
      "total_students_enrolled": 25,
      "total_revenue": "600000",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

## 🔍 Get Package Details

```bash
curl -X GET http://localhost:8000/api/teacher/packages/5/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✏️ Update Package

```bash
curl -X PUT http://localhost:8000/api/teacher/packages/5/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Mastery",
    "total_sessions": 15,
    "total_price": "1500000",
    "is_active": true
  }'
```

---

## 🗑️ Delete Package

```bash
curl -X DELETE http://localhost:8000/api/teacher/packages/5/ \
  -H "Authorization: Bearer $TOKEN"
```

**Note**: Will fail if students are enrolled

---

## 💳 Add Installment

### First Installment (after default)
```bash
PACKAGE_ID=5
curl -X POST http://localhost:8000/api/teacher/packages/$PACKAGE_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_number": 4,
    "amount": "300000"
  }'
```

### Multiple Installments
```bash
PACKAGE_ID=5

# Add installment for session 4
curl -X POST http://localhost:8000/api/teacher/packages/$PACKAGE_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_number": 4, "amount": "400000"}'

# Add installment for session 8
curl -X POST http://localhost:8000/api/teacher/packages/$PACKAGE_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_number": 8, "amount": "400000"}'

# Add installment for session 12
curl -X POST http://localhost:8000/api/teacher/packages/$PACKAGE_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_number": 12, "amount": "400000"}'
```

---

## 📊 List Installments

```bash
curl -X GET http://localhost:8000/api/teacher/packages/5/installments/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 7,
      "installment_number": 1,
      "session_number": 1,
      "amount": "1200000",
      "paid_count": 15,
      "pending_count": 10,
      "total_amount_paid": "18000000",
      "created_at": "2024-01-15T10:05:00Z"
    }
  ]
}
```

---

## 📝 Update Installment

```bash
curl -X PUT http://localhost:8000/api/teacher/packages/5/installments/8/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_number": 5,
    "amount": "350000"
  }'
```

---

## ❌ Delete Installment

```bash
curl -X DELETE http://localhost:8000/api/teacher/packages/5/installments/8/ \
  -H "Authorization: Bearer $TOKEN"
```

**Note**: Will fail if payments are completed

---

## 🚨 Common Errors

### 400 Bad Request
```bash
# ❌ session_number out of range (1-12)
{
  "session_number": "شماره جلسه باید بین 1 تا 12 باشد"
}

# ❌ Duplicate session_number
{
  "session_number": "قسط برای این جلسه قبلا اضافه شده است"
}

# ❌ Invalid amount
{
  "amount": "مبلغ باید بزرگتر از 0 باشد"
}
```

### 401 Unauthorized
```bash
# ❌ Missing token
"Authorization header required"

# ❌ Invalid token
"Token is invalid or expired"
```

### 403 Forbidden
```bash
# ❌ Not the owner
{
  "detail": "شما مالک این بسه نیستید"
}
```

### 404 Not Found
```bash
# ❌ Package doesn't exist
{
  "detail": "بسه یافت نشد"
}

# ❌ Installment doesn't exist
{
  "detail": "قسط یافت نشد"
}
```

---

## 🔢 HTTP Status Codes Quick Reference

| Code | Meaning | Example |
|------|---------|---------|
| 200 | ✅ OK | GET, PUT, DELETE succeeded |
| 201 | ✅ Created | POST succeeded |
| 400 | ❌ Bad Request | Invalid input data |
| 401 | ❌ Unauthorized | Missing/invalid token |
| 403 | ❌ Forbidden | Not the owner |
| 404 | ❌ Not Found | Package/installment doesn't exist |
| 500 | ❌ Server Error | Unexpected server error |

---

## 🧪 Test Complete Workflow

```bash
#!/bin/bash

TOKEN="your_token"
BASE_URL="http://localhost:8000/api"

echo "1️⃣ Creating package..."
PKG=$(curl -s -X POST $BASE_URL/teacher/packages/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Course",
    "total_sessions": 10,
    "total_price": "1000000",
    "has_installment": true
  }')

PKG_ID=$(echo $PKG | grep -o '"id":[0-9]*' | cut -d: -f2)
echo "✅ Package created: $PKG_ID"

echo -e "\n2️⃣ Listing packages..."
curl -s -X GET $BASE_URL/teacher/packages/ \
  -H "Authorization: Bearer $TOKEN" | jq '.count'

echo -e "\n3️⃣ Adding installments..."
curl -s -X POST $BASE_URL/teacher/packages/$PKG_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_number": 5, "amount": "250000"}' > /dev/null

echo "✅ Installment added"

echo -e "\n4️⃣ Listing installments..."
curl -s -X GET $BASE_URL/teacher/packages/$PKG_ID/installments/ \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length'

echo -e "\n✅ Workflow complete!"
```

---

## 📱 JavaScript Quick Example

```javascript
const API = 'http://localhost:8000/api';
const TOKEN = localStorage.getItem('access_token');

// Create package
async function createPackage() {
  const res = await fetch(`${API}/teacher/packages/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'New Course',
      total_sessions: 10,
      total_price: '1000000',
      has_installment: true
    })
  });
  return res.json();
}

// List packages
async function listPackages() {
  const res = await fetch(`${API}/teacher/packages/`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` }
  });
  return res.json();
}

// Add installment
async function addInstallment(packageId, sessionNumber, amount) {
  const res = await fetch(`${API}/teacher/packages/${packageId}/installments/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_number: sessionNumber,
      amount: amount
    })
  });
  return res.json();
}

// Usage
const pkg = await createPackage();
const pkgId = pkg.data.id;
await addInstallment(pkgId, 5, '250000');
```

---

## 🐍 Python Quick Example

```python
import requests

TOKEN = "your_token"
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create package
def create_package():
    data = {
        "name": "Python Course",
        "total_sessions": 12,
        "total_price": "1200000",
        "has_installment": True
    }
    resp = requests.post(f"{BASE_URL}/teacher/packages/", json=data, headers=HEADERS)
    return resp.json()['data']['id']

# List packages
def list_packages():
    resp = requests.get(f"{BASE_URL}/teacher/packages/", headers=HEADERS)
    return resp.json()['data']

# Add installment
def add_installment(package_id, session_number, amount):
    data = {
        "session_number": session_number,
        "amount": amount
    }
    resp = requests.post(
        f"{BASE_URL}/teacher/packages/{package_id}/installments/",
        json=data,
        headers=HEADERS
    )
    return resp.json()

# Usage
pkg_id = create_package()
add_installment(pkg_id, 5, "300000")
```

---

## ⚡ Performance Tips

### Batch Operations
```bash
# Good: Sequential installments (ensures order)
for session in 4 8 12; do
  curl -X POST ... -d "{\"session_number\": $session, ...}"
  sleep 0.1
done

# Bad: Parallel (race conditions)
# Don't do: curl ... & curl ... & curl ...
```

### Pagination (Future)
```bash
# Get page 2 with 20 items per page
curl -X GET "http://localhost:8000/api/teacher/packages/?page=2&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtering (Future)
```bash
# Get active packages only
curl -X GET "http://localhost:8000/api/teacher/packages/?is_active=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔄 Field Value Ranges

| Field | Min | Max | Example |
|-------|-----|-----|---------|
| `total_sessions` | 1 | 100 | 12 |
| `total_price` | 0.01 | Unlimited | 1200000 |
| `session_number` | 1 | total_sessions | 5 |
| `amount` | 0.01 | Unlimited | 300000 |
| `name` | 3 chars | 100 chars | "Python Course" |

---

## 📌 Response Structure

Every response follows this structure:

```json
{
  "success": true/false,
  "message": "Human readable message",
  "data": {...},        // For single resource
  "data": [...],        // For list
  "count": 5,           // For list (total items)
  "errors": {...}       // Only on error
}
```

---

## 🎯 Quick Decision Tree

```
Need to...

├─ BROWSE PACKAGES?
│  └─ GET /api/packages/  (student API, public packages)

├─ CREATE YOUR OWN?
│  └─ POST /api/teacher/packages/

├─ MANAGE YOUR PACKAGES?
│  ├─ List: GET /api/teacher/packages/
│  ├─ Update: PUT /api/teacher/packages/{id}/
│  └─ Delete: DELETE /api/teacher/packages/{id}/

├─ MANAGE INSTALLMENTS?
│  ├─ List: GET /api/teacher/packages/{id}/installments/
│  ├─ Add: POST /api/teacher/packages/{id}/installments/
│  ├─ Update: PUT /api/teacher/packages/{id}/installments/{inst_id}/
│  └─ Delete: DELETE /api/teacher/packages/{id}/installments/{inst_id}/

├─ CHECK STATISTICS?
│  ├─ Package stats: GET /api/teacher/packages/
│  └─ Installment stats: GET /api/teacher/packages/{id}/installments/

├─ TROUBLESHOOT?
│  ├─ Check token validity: Verify Authorization header
│  ├─ Check ownership: GET /api/teacher/packages/ (see your packages)
│  ├─ Check session ranges: GET /api/teacher/packages/{id}/
│  └─ Check validation: Read error response carefully
```

---

## 🆘 Quick Troubleshooting

```bash
# Token expired?
curl -X POST http://localhost:8000/api/token/refresh/ \
  -d '{"refresh": "your_refresh_token"}'

# Not the owner?
# Make sure package_id is from GET /api/teacher/packages/

# Session number invalid?
# Check: 1 <= session_number <= total_sessions
curl -X GET http://localhost:8000/api/teacher/packages/5/ | grep total_sessions

# Session already exists?
curl -X GET http://localhost:8000/api/teacher/packages/5/installments/ | grep session_number

# Can't delete?
# Check if students enrolled (packages) or payments exist (installments)
# These are protected against deletion
```

---

## 📚 File References

| Need | File |
|------|------|
| Full API docs | TEACHER_PACKAGE_MANAGEMENT_API.md |
| Quick lookup | TEACHER_PACKAGE_API_QUICK_REFERENCE.md |
| Code examples | TEACHER_PACKAGE_MANAGEMENT_EXAMPLES.py |
| Best practices | TEACHER_PACKAGE_API_BEST_PRACTICES.md |
| Testing | TEACHER_PACKAGE_API_TEST_SUITE.json |
| Postman | TEACHER_PACKAGE_API_POSTMAN.json |

---

**Happy teaching! 🎓**
