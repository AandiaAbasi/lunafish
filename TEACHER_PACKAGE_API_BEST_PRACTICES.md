# Teacher Package Management API - Best Practices Guide

## 📚 Table of Contents
1. [Authentication Best Practices](#authentication)
2. [API Usage Patterns](#patterns)
3. [Error Handling](#errors)
4. [Performance Tips](#performance)
5. [Common Workflows](#workflows)
6. [Troubleshooting](#troubleshooting)

---

## 🔐 Authentication Best Practices {#authentication}

### Token Management

```python
# ✅ GOOD: Store token securely
localStorage.setItem('access_token', response.data.access)
localStorage.setItem('refresh_token', response.data.refresh)

# ❌ BAD: Hardcoding token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Refresh

```javascript
// ✅ GOOD: Auto-refresh expired tokens
async function apiCall(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  // If 401, try refreshing token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    if (refreshResponse.ok) {
      const newToken = (await refreshResponse.json()).access;
      localStorage.setItem('access_token', newToken);
      
      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`
        }
      });
    }
  }
  
  return response;
}
```

### Security Headers

```python
# ✅ GOOD: Always use HTTPS in production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ✅ GOOD: Set proper CORS headers
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]
```

---

## 🔄 API Usage Patterns {#patterns}

### 1. Create & List Pattern

```javascript
// ✅ GOOD: Separation of concerns
class PackageService {
  constructor(token) {
    this.token = token;
    this.baseURL = '/api';
  }
  
  async createPackage(packageData) {
    return this.request('POST', '/teacher/packages/', packageData);
  }
  
  async listPackages() {
    return this.request('GET', '/teacher/packages/');
  }
  
  async request(method, endpoint, data = null) {
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    };
    
    if (data) options.body = JSON.stringify(data);
    
    const response = await fetch(`${this.baseURL}${endpoint}`, options);
    return response.json();
  }
}

// Usage
const service = new PackageService(token);
const newPackage = await service.createPackage({
  name: 'Python',
  total_sessions: 12,
  total_price: '1200000'
});

const packages = await service.listPackages();
```

### 2. Error Handling Pattern

```javascript
// ✅ GOOD: Comprehensive error handling
async function createPackageWithErrorHandling(packageData) {
  try {
    const response = await fetch('/api/teacher/packages/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(packageData)
    });
    
    const data = await response.json();
    
    // Check success field
    if (!data.success) {
      // Handle validation errors
      if (data.errors) {
        Object.entries(data.errors).forEach(([field, error]) => {
          console.error(`Field ${field}: ${error}`);
        });
      }
      throw new Error(data.message);
    }
    
    return data.data;
  } catch (error) {
    if (error instanceof TypeError) {
      console.error('Network error:', error);
    } else if (error instanceof SyntaxError) {
      console.error('Invalid JSON response:', error);
    } else {
      console.error('API error:', error.message);
    }
    throw error;
  }
}
```

### 3. Batch Operations Pattern

```javascript
// ✅ GOOD: Create installments sequentially
async function createPackageWithInstallments(packageData, installments) {
  // 1. Create package
  const createResp = await fetch('/api/teacher/packages/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(packageData)
  });
  
  const { data: package } = await createResp.json();
  
  // 2. Add installments sequentially (important for order)
  for (const installment of installments) {
    await fetch(`/api/teacher/packages/${package.id}/installments/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(installment)
    });
  }
  
  return package;
}

// ❌ BAD: Parallel installment creation (race conditions)
async function badCreateInstallments(packageId, installments) {
  // DON'T DO THIS - order not guaranteed
  return Promise.all(
    installments.map(inst =>
      fetch(`/api/teacher/packages/${packageId}/installments/`, {
        method: 'POST',
        body: JSON.stringify(inst)
      })
    )
  );
}
```

### 4. Caching Pattern

```javascript
// ✅ GOOD: Cache package data
class CachedPackageService {
  constructor(token) {
    this.token = token;
    this.cache = {};
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }
  
  async listPackages(forceRefresh = false) {
    const cacheKey = 'packages_list';
    const now = Date.now();
    
    if (!forceRefresh && this.cache[cacheKey]) {
      const { data, timestamp } = this.cache[cacheKey];
      if (now - timestamp < this.cacheTimeout) {
        return data; // Return cached data
      }
    }
    
    // Fetch fresh data
    const response = await fetch('/api/teacher/packages/', {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    const data = await response.json();
    
    // Store in cache
    this.cache[cacheKey] = {
      data: data.data,
      timestamp: now
    };
    
    return data.data;
  }
  
  // Invalidate cache when data changes
  invalidateCache(key) {
    delete this.cache[key];
  }
}
```

---

## ⚠️ Error Handling {#errors}

### Common HTTP Status Codes

```python
# 200 OK - Request successful
# 201 Created - Resource created
# 400 Bad Request - Validation error
#   - Invalid session_number
#   - Duplicate session_number
#   - Missing required fields

# 401 Unauthorized - Token missing/expired
# 403 Forbidden - User not authorized (not owner)
# 404 Not Found - Package/installment not found
# 500 Server Error - Unexpected server error
```

### Error Response Handling

```javascript
// ✅ GOOD: Handle all response codes
function handleError(response) {
  switch(response.status) {
    case 400:
      return handleValidationError(response.data.errors);
    case 401:
      return redirectToLogin();
    case 403:
      return showPermissionError();
    case 404:
      return showNotFoundError();
    case 500:
      return showServerError();
    default:
      return showGenericError(response.status);
  }
}

// ✅ GOOD: Display validation errors to user
async function createPackageWithValidation(data) {
  const response = await fetch('/api/teacher/packages/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(data)
  });
  
  const result = await response.json();
  
  if (!result.success) {
    // Show field-specific errors
    if (result.errors) {
      result.errors.forEach((error, field) => {
        showFieldError(field, error);
      });
    } else {
      showMessage(result.message); // Generic error
    }
    return null;
  }
  
  return result.data;
}
```

### Retry Logic

```python
# ✅ GOOD: Retry failed requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,  # Maximum retries
        backoff_factor=1,  # Wait 1, 2, 4 seconds
        status_forcelist=[429, 500, 502, 503, 504]  # Retry on these codes
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

# Usage
session = create_session_with_retries()
response = session.post(
    'http://localhost:8000/api/teacher/packages/',
    json=package_data,
    headers={'Authorization': f'Bearer {token}'}
)
```

---

## 🚀 Performance Tips {#performance}

### 1. Request Optimization

```javascript
// ❌ BAD: Multiple separate requests
async function getBadPackageStats(packageId) {
  const pkg = await fetch(`/api/teacher/packages/${packageId}/`);
  const installments = await fetch(`/api/teacher/packages/${packageId}/installments/`);
  
  return {
    package: await pkg.json(),
    installments: await installments.json()
  };
}

// ✅ GOOD: Single batched request
async function getGoodPackageStats(packageId) {
  // Response includes both package and installment data
  const response = await fetch(`/api/teacher/packages/${packageId}/`);
  const data = await response.json();
  
  // installments included in response
  return data;
}
```

### 2. Pagination Usage

```javascript
// ✅ GOOD: Implement pagination for large lists
async function listPackagesWithPagination(page = 1, pageSize = 20) {
  const response = await fetch(
    `/api/teacher/packages/?page=${page}&page_size=${pageSize}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  
  const data = await response.json();
  
  return {
    packages: data.data,
    totalCount: data.count,
    nextPage: data.next ? page + 1 : null,
    prevPage: data.previous ? page - 1 : null
  };
}
```

### 3. Lazy Loading

```javascript
// ✅ GOOD: Load installments only when needed
async function lazyLoadInstallments(packageId) {
  // Initially just get package
  const package = await fetch(`/api/teacher/packages/${packageId}/`);
  
  // Later, load installments on demand
  const installmentsButton = document.querySelector('.load-installments');
  installmentsButton.addEventListener('click', async () => {
    const installments = await fetch(
      `/api/teacher/packages/${packageId}/installments/`
    );
    renderInstallments(await installments.json());
  });
}
```

---

## 🔄 Common Workflows {#workflows}

### Workflow 1: Create Complete Course with Installments

```javascript
async function createCompletePackage() {
  try {
    // Step 1: Create package
    console.log('Creating package...');
    const pkgResponse = await fetch('/api/teacher/packages/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        name: 'Python Complete',
        total_sessions: 12,
        total_price: '1200000',
        has_installment: true
      })
    });
    
    const { success, data: pkg } = await pkgResponse.json();
    if (!success) throw new Error('Failed to create package');
    console.log(`✅ Package created: ${pkg.id}`);
    
    // Step 2: Add additional installments
    const installments = [
      { session_number: 4, amount: '300000' },
      { session_number: 7, amount: '300000' },
      { session_number: 10, amount: '300000' }
    ];
    
    for (let i = 0; i < installments.length; i++) {
      console.log(`Adding installment ${i + 2}/4...`);
      
      const instResponse = await fetch(
        `/api/teacher/packages/${pkg.id}/installments/`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: JSON.stringify(installments[i])
        }
      );
      
      const { success, data: inst } = await instResponse.json();
      if (!success) throw new Error(`Failed to add installment ${i + 2}`);
      console.log(`✅ Installment ${i + 2} added: ${inst.id}`);
    }
    
    console.log('✅ Complete package created successfully!');
    return pkg;
  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  }
}
```

### Workflow 2: Update Package and Adjust Installments

```javascript
async function updatePackageAndInstallments(packageId, updates) {
  try {
    // Step 1: Update package
    const pkgResponse = await fetch(`/api/teacher/packages/${packageId}/`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(updates)
    });
    
    if (!pkgResponse.ok) throw new Error('Failed to update package');
    console.log('✅ Package updated');
    
    // Step 2: If total_sessions changed, might need to adjust installments
    // Get current installments
    const instResponse = await fetch(
      `/api/teacher/packages/${packageId}/installments/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const { data: installments } = await instResponse.json();
    
    // Check if any installments are now out of range
    const newTotalSessions = updates.total_sessions;
    
    for (const inst of installments) {
      if (inst.session_number > newTotalSessions) {
        console.log(`Deleting installment ${inst.id} (out of range)`);
        
        await fetch(
          `/api/teacher/packages/${packageId}/installments/${inst.id}/`,
          { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } }
        );
      }
    }
    
    console.log('✅ Package and installments updated');
  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  }
}
```

### Workflow 3: View Package Analytics

```javascript
async function getPackageAnalytics(packageId) {
  try {
    // Get package details (includes aggregate stats)
    const pkgResponse = await fetch(`/api/teacher/packages/${packageId}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const { data: pkg } = await pkgResponse.json();
    
    // Get installment details
    const instResponse = await fetch(
      `/api/teacher/packages/${packageId}/installments/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const { data: installments } = await instResponse.json();
    
    // Calculate analytics
    const analytics = {
      packageName: pkg.name,
      totalStudents: pkg.total_students_enrolled,
      totalRevenue: pkg.total_revenue,
      coursePrice: pkg.total_price,
      conversationRate: (pkg.total_students_enrolled / 100 * 100).toFixed(2),
      
      installments: installments.map(inst => ({
        number: inst.installment_number,
        session: inst.session_number,
        amount: inst.amount,
        paidCount: inst.paid_count,
        pendingCount: inst.pending_count,
        completionRate: (inst.paid_count / (inst.paid_count + inst.pending_count) * 100).toFixed(2)
      }))
    };
    
    return analytics;
  } catch (error) {
    console.error('Error fetching analytics:', error);
    throw error;
  }
}
```

---

## 🔧 Troubleshooting {#troubleshooting}

### Issue: "401 Unauthorized"

```
원인: Token 만료되었거나 잘못됨

해결책:
1. Token 유효성 확인
   const payload = decodeToken(token);
   console.log(payload.exp); // Expiration time
   
2. Token 새로고침
   POST /api/token/refresh/
   { "refresh": "your_refresh_token" }
   
3. 새로 로그인
   POST /api/token/
   { "username": "...", "password": "..." }
```

### Issue: "403 Forbidden - You are not the owner"

```
원인: 다른 사람의 패키지를 수정/삭제하려고 함

해결책:
1. 올바른 패키지 ID 확인
   GET /api/teacher/packages/
   // 자신의 패키지만 표시됨
   
2. 패키지 소유권 확인
   GET /api/teacher/packages/{id}/
   // Response에 teacher 필드 확인
```

### Issue: "400 Bad Request - session_number out of range"

```
원인: session_number가 1보다 작거나 total_sessions보다 큼

해결책:
1. 패키지의 total_sessions 확인
   GET /api/teacher/packages/{id}/
   
2. 유효한 범위 내에서 session_number 설정
   POST /api/teacher/packages/{id}/installments/
   { "session_number": 1, "amount": "..." } // 1 to 12
```

### Issue: "400 Bad Request - duplicate session_number"

```
원인: 같은 jlsه에 여러 회사팍 추가하려고 함

해결책:
1. 현재 설정된 session_numbers 확인
   GET /api/teacher/packages/{id}/installments/
   
2. 사용되지 않은 session_number 사용
   POST /api/teacher/packages/{id}/installments/
   { "session_number": 4, "amount": "..." } // Use different number
```

### Issue: "400 Bad Request - Cannot delete package"

```
원인: 학생이 등록된 패키지를 삭제하려고 함

해결책:
1. 먼저 모든 학생이 패키지를 포기하도록 해야함
2. 또는 패키지를 비활성화만 하기
   PUT /api/teacher/packages/{id}/
   { "is_active": false }
```

### Issue: Slow API Response

```
원인: 네트워크 지연 또는 서버 과부하

해결책:
1. 캐싱 사용
   service.listPackages() // 캐시 활용
   
2. Pagination 사용
   GET /api/teacher/packages/?page=1&page_size=20
   
3. 불필요한 데이터 제외
   // 필요한 필드만 요청
```

---

## 📋 Checklists

### Before Going to Production
- [ ] All endpoints tested
- [ ] Error handling implemented
- [ ] Token refresh working
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Rate limiting implemented
- [ ] Monitoring/logging setup
- [ ] Database backups configured
- [ ] User documentation ready

### When Deploying New Version
- [ ] Database migrations run
- [ ] Previous version still supported (backward compatibility)
- [ ] API versioning considered
- [ ] Documentation updated
- [ ] Changelog published
- [ ] Users notified about changes

---

**Happy coding! 🚀**
