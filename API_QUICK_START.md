# Fofofish API Quick Start Guide

## 🚀 Getting Started

### Access the Interactive Documentation
- **Swagger UI:** https://fofofish.app/api/docs/swagger/
- **ReDoc:** https://fofofish.app/api/docs/redoc/
- **Schema (JSON):** https://fofofish.app/api/schema/

---

## 📱 Basic Authentication Flow

### Step 1: Send OTP (Phone)
```bash
curl -X POST https://fofofish.app/api/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "09xxxxxxxxxx",
    "purpose": "login"
  }'
```

### Step 2: Verify OTP
```bash
curl -X POST https://fofofish.app/api/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "09xxxxxxxxxx",
    "code": "123456"
  }'
```

Response includes:
- `access` token
- `refresh` token
- User profile data

### Step 3: Use Access Token
```bash
curl https://fofofish.app/api/fetch-user/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 👨‍🏫 Teacher Availability Management

### Create Time Slot
```bash
curl -X POST https://fofofish.app/api/teacher/availability/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-12-29",
    "start_time": "10:00",
    "end_time": "11:00",
    "price": 100000,
    "notes": "Available for all levels"
  }'
```

### Bulk Create Slots
```bash
curl -X POST https://fofofish.app/api/teacher/availability/bulk-create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "availabilities": [
      {
        "date": "2024-12-29",
        "start_time": "10:00",
        "end_time": "11:00",
        "price": 100000
      },
      {
        "date": "2024-12-30",
        "start_time": "14:00",
        "end_time": "15:00",
        "price": 100000
      }
    ]
  }'
```

### List Availability Slots
```bash
# All slots
curl https://fofofish.app/api/teacher/availability/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filtered by date
curl "https://fofofish.app/api/teacher/availability/?date=2024-12-29" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Only available slots
curl "https://fofofish.app/api/teacher/availability/?is_available=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Slot
```bash
curl -X PATCH https://fofofish.app/api/teacher/availability/1/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 120000,
    "notes": "Updated notes"
  }'
```

### Delete Slot
```bash
curl -X DELETE https://fofofish.app/api/teacher/availability/1/delete/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📝 Python Examples

### Login
```python
import requests

response = requests.post(
    'https://fofofish.app/api/login-password/',
    json={
        'username': 'user@example.com',
        'password': 'SecurePassword123'
    }
)

data = response.json()
access_token = data['tokens']['access']
user = data['user']

print(f"Logged in as: {user['username']}")
```

### Create Teacher Availability
```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

payload = {
    'date': '2024-12-29',
    'start_time': '10:00',
    'end_time': '11:00',
    'price': 100000,
    'notes': 'Available for intermediate level'
}

response = requests.post(
    'https://fofofish.app/api/teacher/availability/create/',
    json=payload,
    headers=headers
)

slot = response.json()['data']
print(f"Slot created: {slot['id']}")
```

### Get Current User
```python
response = requests.get(
    'https://fofofish.app/api/fetch-user/',
    headers={'Authorization': f'Bearer {access_token}'}
)

user = response.json()['user']
print(f"User: {user['name']} ({user['email']})")
```

---

## 🔐 JavaScript/React Examples

### Login
```javascript
async function login(username, password) {
  const response = await fetch('https://fofofish.app/api/login-password/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  
  const data = await response.json();
  localStorage.setItem('accessToken', data.tokens.access);
  localStorage.setItem('refreshToken', data.tokens.refresh);
  return data.user;
}

// Usage
const user = await login('user@example.com', 'password123');
```

### Create Availability Slot
```javascript
async function createSlot(date, startTime, endTime, price) {
  const token = localStorage.getItem('accessToken');
  
  const response = await fetch(
    'https://fofofish.app/api/teacher/availability/create/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        date,
        start_time: startTime,
        end_time: endTime,
        price
      })
    }
  );
  
  return await response.json();
}

// Usage
const slot = await createSlot('2024-12-29', '10:00', '11:00', 100000);
console.log(`Slot ${slot.data.id} created`);
```

### Get Current User
```javascript
async function getCurrentUser() {
  const token = localStorage.getItem('accessToken');
  
  const response = await fetch('https://fofofish.app/api/fetch-user/', {
    headers: {'Authorization': `Bearer ${token}`}
  });
  
  return (await response.json()).user;
}

// Usage
const user = await getCurrentUser();
console.log(`Logged in as: ${user.name}`);
```

---

## 🛠️ API Client Setup

### Postman Import
1. Open Postman
2. Click "Import"
3. Paste URL: `https://fofofish.app/api/schema/`
4. Click "Continue"
5. Collection auto-generates with all endpoints

### Insomnia Import
1. Open Insomnia
2. Create → Request Collection
3. Import from URL: `https://fofofish.app/api/schema/`
4. All endpoints ready to test

### VS Code REST Client
```http
### Variables
@baseUrl = https://fofofish.app
@token = YOUR_ACCESS_TOKEN

### Login
POST {{baseUrl}}/api/login-password/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

### Get Current User
GET {{baseUrl}}/api/fetch-user/
Authorization: Bearer {{token}}

### Create Availability Slot
POST {{baseUrl}}/api/teacher/availability/create/
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "date": "2024-12-29",
  "start_time": "10:00",
  "end_time": "11:00",
  "price": 100000
}
```

---

## 📊 Common API Patterns

### Pagination
```bash
# Get page 1 with 20 items per page
curl "https://fofofish.app/api/articles/?page=1&page_size=20"
```

### Filtering
```bash
# Get availability for specific date
curl "https://fofofish.app/api/teacher/availability/?date=2024-12-29"
```

### Search
```bash
# Search articles
curl "https://fofofish.app/api/articles/?search=python"
```

### Ordering
```bash
# Order by creation date (descending)
curl "https://fofofish.app/api/articles/?ordering=-created_at"
```

---

## ⚠️ Error Handling

### Invalid Credentials
```json
{
  "success": false,
  "message": "Username or password is incorrect"
}
```

### Token Expired
```json
{
  "success": false,
  "message": "Token is invalid or expired"
}
```

### Rate Limited
```json
{
  "success": false,
  "message": "Please wait 2 minutes"
}
```

### Validation Error
```json
{
  "success": false,
  "errors": {
    "username": ["This field may not be blank"],
    "password": ["Ensure this field has at least 8 characters"]
  }
}
```

---

## 🔄 Token Refresh

When access token expires:

```bash
curl -X POST https://fofofish.app/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

Response:
```json
{
  "access": "NEW_ACCESS_TOKEN"
}
```

---

## 🚪 Logout

```bash
curl -X POST https://fofofish.app/api/logout/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## 📚 Additional Resources

- **Full Documentation:** https://fofofish.app/api/docs/swagger/
- **ReDoc View:** https://fofofish.app/api/docs/redoc/
- **OpenAPI Schema:** https://fofofish.app/api/schema/
- **Documentation File:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Implementation Details:** [SWAGGER_IMPLEMENTATION.md](./SWAGGER_IMPLEMENTATION.md)

---

## 💡 Tips

1. **Always use HTTPS** - Never send credentials over HTTP
2. **Store tokens securely** - Use HttpOnly cookies for web apps
3. **Implement retry logic** - Handle network timeouts gracefully
4. **Cache responses** - Reduce API calls for static content
5. **Monitor rate limits** - Respect 429 responses
6. **Log errors** - Keep logs for debugging
7. **Test in Swagger** - Use interactive docs before coding

---

## 🆘 Support

For API issues:
- Check the [complete documentation](./API_DOCUMENTATION.md)
- Review [implementation details](./SWAGGER_IMPLEMENTATION.md)
- Test in Swagger UI: https://fofofish.app/api/docs/swagger/
- Contact: api-support@fofofish.app

---

**Last Updated:** December 29, 2024
**API Version:** 1.0.0
