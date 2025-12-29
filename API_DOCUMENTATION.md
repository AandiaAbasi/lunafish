# Fofofish API Documentation

## Overview

This is the comprehensive API documentation for the Fofofish educational platform. The API is fully documented using **OpenAPI 3.0** (Swagger) specifications and can be accessed through interactive documentation interfaces.

## API Documentation Access

### Swagger UI (Interactive Documentation)
- **URL:** https://fofofish.app/api/docs/swagger/
- **Description:** Interactive API explorer with try-it-out capabilities
- **Features:** 
  - Test API endpoints directly in the browser
  - View request/response examples
  - See parameter descriptions and requirements

### ReDoc (Alternative Documentation)
- **URL:** https://fofofish.app/api/docs/redoc/
- **Description:** Clean, static API documentation view
- **Features:**
  - Better for reading documentation
  - Search functionality
  - Code examples

### OpenAPI Schema (JSON)
- **URL:** https://fofofish.app/api/schema/
- **Description:** Raw OpenAPI 3.0 specification in JSON format
- **Use:** Import into API clients (Postman, Insomnia, etc.)

---

## API Endpoints Organization

The API endpoints are organized into the following logical groups:

### 1. Authentication - OTP
User and teacher authentication using One-Time Passwords (SMS/Email)
- `POST /api/send-otp/` - Send OTP to phone or email
- `POST /api/verify-otp/` - Verify OTP code
- `POST /api/teacher/send-otp/` - Send OTP to teacher
- `POST /api/teacher/verify-otp/` - Verify teacher OTP

### 2. Authentication - Email OTP
Email-based authentication endpoints
- `POST /api/user/send-email-otp/` - Send email OTP
- `POST /api/user/verify-email-otp/` - Verify email OTP
- `POST /api/teacher/send-email-otp/` - Send teacher email OTP
- `POST /api/teacher/verify-email-otp/` - Verify teacher email OTP

### 3. Authentication - Registration
User registration completion
- `POST /api/complete-registration/` - Complete user registration
- `POST /api/teacher/complete-registration/` - Complete teacher registration

### 4. Authentication - Login
User and teacher login endpoints
- `POST /api/login-password/` - User login with password
- `POST /api/teacher/login-password/` - Teacher login with password

### 5. Profile Management
User profile operations
- `GET /api/fetch-user/` - Get current user profile
- `POST /api/profile/` - Update user/teacher profile
- `POST /api/teacher-profile/` - Legacy profile endpoint

### 6. Account Settings
Account management endpoints
- `POST /api/change-password/` - Change user password
- `POST /api/logout/` - Logout user
- `GET /api/check-username/` - Check username availability

### 7. Profile Completion
Complete user profile information
- `POST /api/complete-student-profile/` - Complete student profile
- `POST /api/complete-teacher-profile/` - Complete teacher profile
- `POST /api/promote-to-teacher/` - Promote user to teacher

### 8. Avatar Management
User avatar selection and templates
- `GET /api/avatars/` - List avatar templates
- `POST /api/select-avatar/` - Select avatar

### 9. Content
Educational content and information
- `GET /api/articles/` - List all articles
- `GET /api/articles/<id>/` - Get article details
- `GET /api/faqs/` - List FAQs
- `GET /api/about/` - Get about page
- `GET /api/terms/` - List terms and conditions
- `GET /api/privacy/` - List privacy policies
- `GET /api/contact/` - List contact information
- `GET /api/contact/phone/` - Get phone contact

### 10. Teacher Time Slots
Teacher availability and scheduling
- `GET /api/teacher/availability/` - List teacher availability slots
- `POST /api/teacher/availability/create/` - Create single availability slot
- `POST /api/teacher/availability/bulk-create/` - Create multiple slots
- `PATCH /api/teacher/availability/<id>/update/` - Update availability slot
- `DELETE /api/teacher/availability/<id>/delete/` - Delete availability slot

### 11. Home Page
Home page content
- `GET /api/home/` - Get home page content

---

## Authentication

Most endpoints require JWT (JSON Web Token) authentication. After login, you receive:

```json
{
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Using JWT Token

Include the token in request headers:

```
Authorization: Bearer <access_token>
```

### Token Expiration

- **Access Token:** 24 hours
- **Refresh Token:** 7 days
- Use refresh token to get a new access token when expired

---

## Common Request/Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Error message"]
  }
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "https://fofofish.app/api/articles/?page=2",
  "previous": null,
  "results": [
    // Array of results
  ]
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful deletion |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - User doesn't have permission |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Server Error - Internal server error |

---

## Common Query Parameters

### Pagination
```
?page=1&page_size=20
```

### Search
```
?search=keyword
```

### Filtering
```
?teacher_id=1
?date=2024-12-29
?is_available=true
```

### Ordering
```
?ordering=-created_at
?ordering=name
```

---

## Authentication Flow

### OTP-Based Login (Phone)

1. **Send OTP**
   ```
   POST /api/send-otp/
   {
     "identifier": "09xxxxxxxxxx",
     "purpose": "login"
   }
   ```

2. **Verify OTP**
   ```
   POST /api/verify-otp/
   {
     "identifier": "09xxxxxxxxxx",
     "code": "123456"
   }
   ```
   Returns: `user` and `tokens`

### Password-Based Login

```
POST /api/login-password/
{
  "username": "user@example.com",
  "password": "password123"
}
```
Returns: `user` and `tokens`

### OTP-Based Registration

1. **Send OTP**
   ```
   POST /api/send-otp/
   {
     "identifier": "09xxxxxxxxxx",
     "purpose": "registration"
   }
   ```

2. **Verify OTP** → Get `verification_token`
   ```
   POST /api/verify-otp/
   {
     "identifier": "09xxxxxxxxxx",
     "code": "123456",
     "purpose": "registration"
   }
   ```

3. **Complete Registration**
   ```
   POST /api/complete-registration/
   {
     "verification_token": "token_from_verify",
     "username": "newuser",
     "password": "StrongPassword123",
     "name": "User Name"
   }
   ```

---

## Teacher Availability Management

### Create Single Slot
```
POST /api/teacher/availability/create/
{
  "date": "2024-12-29",
  "start_time": "10:00",
  "end_time": "11:00",
  "price": 100000,
  "notes": "Available for all levels"
}
```

### Bulk Create Multiple Slots
```
POST /api/teacher/availability/bulk-create/
{
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
}
```

### Update Slot
```
PATCH /api/teacher/availability/<id>/update/
{
  "price": 120000,
  "notes": "Updated notes"
}
```

### Delete Slot
```
DELETE /api/teacher/availability/<id>/delete/
```

### List Slots with Filters
```
GET /api/teacher/availability/?date=2024-12-29&is_available=true
```

---

## Error Handling

### Common Error Scenarios

1. **Invalid OTP**
   ```json
   {
     "success": false,
     "message": "Invalid or expired OTP"
   }
   ```

2. **Username Already Exists**
   ```json
   {
     "success": false,
     "message": "This username has already been taken"
   }
   ```

3. **Insufficient Permissions**
   ```json
   {
     "success": false,
     "message": "You do not have permission to access this resource"
   }
   ```

4. **Rate Limit Exceeded**
   ```json
   {
     "success": false,
     "message": "Please wait 2 minutes"
   }
   ```

---

## Best Practices

### 1. Token Management
- Store refresh token securely (HttpOnly cookie for web)
- Use access token for API requests
- Refresh token before expiration

### 2. Error Handling
- Always check `success` field
- Display user-friendly error messages
- Log errors for debugging

### 3. Rate Limiting
- Respect 429 Too Many Requests responses
- Implement exponential backoff for retries
- Cache responses when possible

### 4. Security
- Always use HTTPS
- Never expose tokens in logs
- Validate all user input
- Use strong passwords (min 8 characters)

### 5. Performance
- Use pagination for list endpoints
- Filter results when possible
- Cache static content (FAQs, Terms)
- Use appropriate timeout values

---

## API Client Examples

### Using cURL
```bash
# Get home page
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://fofofish.app/api/home/

# Login with password
curl -X POST https://fofofish.app/api/login-password/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

### Using Python Requests
```python
import requests

# Login
response = requests.post(
    'https://fofofish.app/api/login-password/',
    json={'username': 'user', 'password': 'pass'}
)
data = response.json()
token = data['tokens']['access']

# Authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'https://fofofish.app/api/fetch-user/',
    headers=headers
)
user = response.json()
```

### Using JavaScript/Fetch
```javascript
// Login
const response = await fetch('https://fofofish.app/api/login-password/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'user', password: 'pass'})
});
const data = await response.json();
const token = data.tokens.access;

// Authenticated request
const userResponse = await fetch('https://fofofish.app/api/fetch-user/', {
  headers: {'Authorization': `Bearer ${token}`}
});
const user = await userResponse.json();
```

---

## Support and Contact

For API support and issues:
- **Email:** api-support@fofofish.app
- **Documentation:** https://fofofish.app/api/docs/swagger/
- **ReDoc:** https://fofofish.app/api/docs/redoc/

---

## Version History

### Version 1.0.0 (Current)
- OTP-based authentication (SMS/Email)
- Password-based login
- User and teacher registration
- Profile management
- Teacher availability scheduling
- Content delivery (Articles, FAQs, Terms, Privacy)
- Home page personalization

---

## Last Updated
December 29, 2024
