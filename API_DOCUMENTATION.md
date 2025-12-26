# Fofofish Skyroom API Documentation

## Overview

Complete REST API documentation for Skyroom Integration module in the Fofofish educational platform. This API enables full management of virtual meeting rooms, user accounts, room access, and direct login URLs.

**API Version**: 1.0.0  
**Base URL**: `https://fofofish.app/api/`  
**Authentication**: API Key in `X-API-Key` header

## Authentication

All API requests require authentication using an API key in the request header:

```http
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

### API Key Configuration

The API key is configured in Django settings and validates on every request:

```python
VALID_API_KEYS = {
    'apikey-39974696-1-e570445f94a95d2573d9922d04583008': 'skyroom_integration_key',
}
```

---

## Swagger/OpenAPI Documentation

Interactive API documentation is available via Swagger UI:

- **Swagger UI**: `https://fofofish.app/api/docs/swagger/`
- **ReDoc**: `https://fofofish.app/api/docs/redoc/`
- **OpenAPI Schema**: `https://fofofish.app/api/schema/`

## Response Format

All responses follow a consistent JSON format:

### Success Response (HTTP 200 or 201)
```json
{
  "id": 1,
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data
  }
}
```

### Paginated List Response
```json
{
  "count": 100,
  "next": "https://fofofish.app/api/endpoint/?page=2",
  "previous": null,
  "results": [
    // Array of items
  ]
}
```

### Error Response (HTTP 4xx or 5xx)
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

---

## API Endpoints

### 1. Services Management

Services represent Skyroom service plans with user and video limits.

#### List Services
```http
GET /skyroom/services/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Query Parameters:**
- `search`: Filter by title or skyroom_id
- `ordering`: Order by id, title, status, updated_at

**Example:**
```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  "https://fofofish.app/api/skyroom/services/?search=premium&ordering=-updated_at"
```

---

#### Get Service Details
```http
GET /skyroom/services/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Response:**
```json
{
  "id": 1,
  "skyroom_id": 1,
  "title": "Premium Service",
  "status": 1,
  "user_limit": 100,
  "video_limit": 8,
  "time_limit": 1000000,
  "time_usage": 50000,
  "start_time": 1609459200,
  "stop_time": 1640995200,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

---

#### Create Service
```http
POST /skyroom/services/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "skyroom_id": 1,
  "title": "Premium Service",
  "status": 1,
  "user_limit": 100,
  "video_limit": 8,
  "time_limit": 1000000,
  "time_usage": 0,
  "start_time": 1609459200,
  "stop_time": 1640995200
}
```

---

#### Update Service
```http
PUT /skyroom/services/{id}/
PATCH /skyroom/services/{id}/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

---

#### Delete Service
```http
DELETE /skyroom/services/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

---

### 2. Rooms Management

Manage virtual meeting rooms with access control and user management.

#### List Rooms
```http
GET /skyroom/rooms/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Query Parameters:**
- `service`: Filter by service ID
- `status`: Filter by status (0=Inactive, 1=Active)
- `guest_login`: Filter by guest_login (true/false)
- `search`: Filter by name, title, or skyroom_id
- `ordering`: Order by id, name, title, status, updated_at

**Example:**
```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  "https://fofofish.app/api/skyroom/rooms/?service=1&status=1&search=meeting"
```

---

#### Get Room Details
```http
GET /skyroom/rooms/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

---

#### Create Room
```http
POST /skyroom/rooms/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "skyroom_id": 1,
  "service": 1,
  "name": "meeting-room",
  "title": "Conference Room",
  "description": "Main meeting room",
  "status": 1,
  "guest_login": true,
  "guest_limit": 5,
  "op_login_first": true,
  "max_users": 50,
  "session_duration": 3600
}
```

---

#### Get Room Users
```http
GET /skyroom/rooms/{id}/users/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Returns all users with access to the room and their access levels.

---

#### Add Users to Room
```http
POST /skyroom/rooms/{id}/add_users/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "users": [
    {
      "user_id": 1,
      "access": 1
    },
    {
      "user_id": 2,
      "access": 2
    },
    {
      "user_id": 3,
      "access": 3
    }
  ]
}
```

**Access Levels:**
- `1` - Normal User (can join and view)
- `2` - Presenter (can present, share screen)
- `3` - Operator (full control, can manage other users)

**Response:**
```json
{
  "success": true,
  "message": "Users added successfully",
  "count": 3
}
```

---

#### Remove Users from Room
```http
POST /skyroom/rooms/{id}/remove_users/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "users": [1, 2, 3]
}
```

---

### 3. Users Management

Manage Skyroom user accounts with credentials, personal information, and room access.

#### List Users
```http
GET /skyroom/users/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Query Parameters:**
- `status`: Filter by status (0=Inactive, 1=Active)
- `is_public`: Filter by is_public (true/false)
- `gender`: Filter by gender (0=Unknown, 1=Male, 2=Female)
- `search`: Filter by username, nickname, email, skyroom_id
- `ordering`: Order by id, username, nickname, status, updated_at

---

#### Get User Details
```http
GET /skyroom/users/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Response:**
```json
{
  "id": 1,
  "skyroom_id": 1,
  "username": "testuser",
  "nickname": "Test User",
  "email": "test@example.com",
  "fname": "Test",
  "lname": "User",
  "gender": 1,
  "status": 1,
  "is_public": false,
  "concurrent": 0,
  "time_limit": null,
  "time_usage": 426466,
  "time_total": 8464516,
  "expiry_date": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

---

#### Create User
```http
POST /skyroom/users/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "skyroom_id": 1,
  "username": "testuser",
  "nickname": "Test User",
  "password": "securepassword123",
  "email": "test@example.com",
  "fname": "Test",
  "lname": "User",
  "gender": 1,
  "status": 1,
  "is_public": false
}
```

---

#### Get User Rooms
```http
GET /skyroom/users/{id}/rooms/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Returns all rooms that the user has access to with their access levels.

---

#### Add Rooms to User
```http
POST /skyroom/users/{id}/add_rooms/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "rooms": [
    {
      "room_id": 1,
      "access": 1
    },
    {
      "room_id": 2,
      "access": 2
    }
  ]
}
```

---

#### Remove Rooms from User
```http
POST /skyroom/users/{id}/remove_rooms/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "rooms": [1, 2, 3]
}
```

---

### 4. Login URLs Management

Generate and manage direct login URLs for quick access without credentials.

#### List Login URLs
```http
GET /skyroom/login-urls/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Query Parameters:**
- `room`: Filter by room ID
- `access`: Filter by access level
- `is_active`: Filter by active status (true/false)
- `ordering`: Order by id, created_at, expires_at

---

#### Get Login URL Details
```http
GET /skyroom/login-urls/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

---

#### Create Login URL
```http
POST /skyroom/login-urls/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "room": 1,
  "user": 1,
  "nickname": "Guest User",
  "access": 1,
  "concurrent": 1,
  "ttl": 3600
}
```

**Parameters:**
- `room` (required): Room ID
- `user` (required): Associated user ID
- `nickname`: Display name for this login
- `access`: Access level (1, 2, or 3)
- `concurrent`: Number of concurrent users allowed (default: 1)
- `ttl`: Time to live in seconds (default: 3600)

**Response:**
```json
{
  "id": 1,
  "room": 1,
  "user": 1,
  "nickname": "Guest User",
  "access": 1,
  "concurrent": 1,
  "url": "https://www.skyroom.online/ch/sample/room/t/eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "ttl": 3600,
  "is_active": true,
  "expires_at": "2024-01-15T11:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### Get Active Login URLs
```http
GET /skyroom/login-urls/active/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Returns all non-expired, active login URLs.

---

#### Get Expired Login URLs
```http
GET /skyroom/login-urls/expired/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Returns all expired login URLs.

---

#### Revoke Login URL
```http
POST /skyroom/login-urls/{id}/revoke/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Immediately deactivates a login URL preventing further use.

---

### 5. Access Management

Direct management of room-user access relationships.

#### List Access Records
```http
GET /skyroom/access/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Query Parameters:**
- `room`: Filter by room ID
- `user`: Filter by user ID
- `access`: Filter by access level (1, 2, or 3)

---

#### Get Access Details
```http
GET /skyroom/access/{id}/
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

---

#### Create Access Record
```http
POST /skyroom/access/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "room": 1,
  "user": 1,
  "access": 2
}
```

---

#### Update Access Level
```http
PUT /skyroom/access/{id}/
PATCH /skyroom/access/{id}/
Content-Type: application/json
X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

**Request Body:**
```json
{
  "room": 1,
  "user": 1,
  "access": 3
}
```

---

## Error Handling

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| `200` | OK - Request succeeded |
| `201` | Created - Resource created successfully |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Missing or invalid API key |
| `403` | Forbidden - Permission denied |
| `404` | Not Found - Resource not found |
| `500` | Server Error - Internal server error |

### Error Response Example

```json
{
  "success": false,
  "error": "Invalid API key",
  "code": "AUTHENTICATION_ERROR"
}
```

---

## Rate Limiting

API requests are rate limited to:
- **500 requests per minute** per API key

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 499
X-RateLimit-Reset: 1234567890
```

---

## Pagination

List endpoints return paginated results:

```http
GET /skyroom/users/?page=2&page_size=20
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 150,
  "next": "https://fofofish.app/api/skyroom/users/?page=3",
  "previous": "https://fofofish.app/api/skyroom/users/?page=1",
  "results": [
    // Array of items
  ]
}
```

---

## Internationalization (i18n)

All API responses support Persian (fa) and English (en) languages. Set the language via:

```http
Accept-Language: fa
```

or

```http
Accept-Language: en
```

---

## Example Usage

### Create a complete room setup

```bash
# 1. Create a service
curl -X POST "https://fofofish.app/api/skyroom/services/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "title": "Premium Service",
    "status": 1,
    "user_limit": 100,
    "video_limit": 8,
    "start_time": 1609459200,
    "stop_time": 1640995200
  }'

# 2. Create a room
curl -X POST "https://fofofish.app/api/skyroom/rooms/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "service": 1,
    "name": "meeting-room",
    "title": "Conference Room",
    "status": 1,
    "guest_login": true,
    "max_users": 50
  }'

# 3. Create a user
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "username": "john_doe",
    "nickname": "John Doe",
    "password": "securepassword",
    "email": "john@example.com",
    "status": 1
  }'

# 4. Add user to room
curl -X POST "https://fofofish.app/api/skyroom/rooms/1/add_users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [{"user_id": 1, "access": 2}]
  }'

# 5. Generate login URL
curl -X POST "https://fofofish.app/api/skyroom/login-urls/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "room": 1,
    "user": 1,
    "nickname": "Guest Access",
    "access": 1,
    "ttl": 3600
  }'
```

---

## Support

For API issues and support:
- **Documentation**: `https://fofofish.app/api/docs/swagger/`
- **Schema**: `https://fofofish.app/api/schema/`
- **Contact**: support@fofofish.app

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |

