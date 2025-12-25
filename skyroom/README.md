# Skyroom Integration App

This Django app provides a complete integration with the Skyroom web conferencing API.

## Overview

The Skyroom integration app includes models for managing:
- **Services**: Skyroom service plans with limits and usage
- **Rooms**: Virtual meeting/classroom rooms
- **Users**: Skyroom user accounts
- **Access Control**: Room user permissions and access levels
- **Login URLs**: Direct access links without login

## Models

### Service Model
Represents a Skyroom service plan.

**Fields:**
- `skyroom_id` (Integer): Unique Skyroom service ID
- `title` (String): Service title (max 128 chars)
- `status` (Integer): 0=Inactive, 1=Active
- `user_limit` (Integer): Maximum concurrent users
- `video_limit` (Integer): Maximum concurrent videos per room
- `time_limit` (BigInteger): Person-second time limit
- `time_usage` (BigInteger): Person-second time used
- `start_time` (BigInteger): Service start time (Unix timestamp)
- `stop_time` (BigInteger): Service stop time (Unix timestamp)

### Room Model
Represents a virtual room for meetings/classes.

**Fields:**
- `skyroom_id` (Integer): Unique Skyroom room ID
- `service` (ForeignKey): Associated service
- `name` (String): Room name in Latin (max 128 chars) - must be unique
- `title` (String): Room display title (max 128 chars)
- `description` (Text): Room description (optional)
- `status` (Integer): 0=Inactive, 1=Active
- `guest_login` (Boolean): Allow guest access
- `guest_limit` (Integer): Maximum guests (0=unlimited)
- `op_login_first` (Boolean): Require operator login first
- `max_users` (Integer): Maximum concurrent users
- `session_duration` (Integer): Max session duration in seconds
- `time_limit` (BigInteger): Person-second time limit
- `time_usage` (BigInteger): Current session time usage
- `time_total` (BigInteger): Total time usage

### SkyroomUser Model
Represents a user account in Skyroom.

**Fields:**
- `skyroom_id` (Integer): Unique Skyroom user ID
- `username` (String): Username in Latin (max 32 chars) - must be unique
- `nickname` (String): Display name (max 128 chars)
- `password` (String): Password hash
- `email` (Email): User email (optional, max 128 chars)
- `fname` (String): First name (optional)
- `lname` (String): Last name (optional)
- `gender` (Integer): 0=Unknown, 1=Male, 2=Female
- `status` (Integer): 0=Inactive, 1=Active
- `is_public` (Boolean): Public/shared account
- `concurrent` (Integer): Concurrent usage limit (0=unlimited)
- `time_limit` (BigInteger): Maximum time allowed (seconds)
- `time_usage` (BigInteger): Current time used (seconds)
- `time_total` (BigInteger): Total time used (seconds)
- `expiry_date` (BigInteger): Account expiry date (Unix timestamp, optional)

### RoomUserAccess Model
Manages access levels for users to rooms.

**Fields:**
- `room` (ForeignKey): Associated room
- `user` (ForeignKey): Associated user
- `access` (Integer): 1=Normal User, 2=Presenter, 3=Operator

**Unique Constraint:** (room, user) pair is unique

### LoginUrl Model
Generates direct login links without username/password.

**Fields:**
- `room` (ForeignKey): Associated room
- `user_id` (String): User identifier (number or string)
- `nickname` (String): Display name for this login (optional)
- `access` (Integer): Access level (1=User, 2=Presenter, 3=Operator)
- `concurrent` (Integer): Allowed concurrent users (default 1)
- `url` (Text): Generated login URL
- `ttl` (Integer): Time to live in seconds (default 3600)
- `is_active` (Boolean): Whether the URL is active
- `expires_at` (DateTime): Expiration timestamp

## API Endpoints

### Services
- `GET /api/skyroom/services/` - List all services
- `POST /api/skyroom/services/` - Create new service
- `GET /api/skyroom/services/{id}/` - Get service details
- `PUT /api/skyroom/services/{id}/` - Update service
- `DELETE /api/skyroom/services/{id}/` - Delete service

### Rooms
- `GET /api/skyroom/rooms/` - List all rooms
- `POST /api/skyroom/rooms/` - Create new room
- `GET /api/skyroom/rooms/{id}/` - Get room details
- `PUT /api/skyroom/rooms/{id}/` - Update room
- `DELETE /api/skyroom/rooms/{id}/` - Delete room
- `GET /api/skyroom/rooms/{id}/users/` - Get room users
- `POST /api/skyroom/rooms/{id}/add_users/` - Add users to room
- `POST /api/skyroom/rooms/{id}/remove_users/` - Remove users from room

### Users
- `GET /api/skyroom/users/` - List all users
- `POST /api/skyroom/users/` - Create new user
- `GET /api/skyroom/users/{id}/` - Get user details
- `PUT /api/skyroom/users/{id}/` - Update user
- `DELETE /api/skyroom/users/{id}/` - Delete user
- `GET /api/skyroom/users/{id}/rooms/` - Get user's rooms
- `POST /api/skyroom/users/{id}/add_rooms/` - Add rooms to user
- `POST /api/skyroom/users/{id}/remove_rooms/` - Remove rooms from user

### Room User Access
- `GET /api/skyroom/access/` - List all access records
- `POST /api/skyroom/access/` - Create access record
- `GET /api/skyroom/access/{id}/` - Get access details
- `PUT /api/skyroom/access/{id}/` - Update access
- `DELETE /api/skyroom/access/{id}/` - Delete access

### Login URLs
- `GET /api/skyroom/login-urls/` - List all login URLs
- `POST /api/skyroom/login-urls/` - Create new login URL
- `GET /api/skyroom/login-urls/{id}/` - Get login URL details
- `DELETE /api/skyroom/login-urls/{id}/` - Delete login URL
- `GET /api/skyroom/login-urls/expired/` - Get expired URLs
- `GET /api/skyroom/login-urls/active/` - Get active URLs
- `POST /api/skyroom/login-urls/{id}/revoke/` - Revoke a login URL

## Access Codes

### Status Codes
- `0` - Inactive
- `1` - Active

### Access Levels
- `1` - Normal User
- `2` - Presenter
- `3` - Operator

### Gender Codes
- `0` - Unknown
- `1` - Male
- `2` - Female

## Setup

1. Add `skyroom` to `INSTALLED_APPS` in settings.py:
```python
INSTALLED_APPS = [
    ...
    'skyroom',
    ...
]
```

2. Include skyroom URLs in your main urls.py:
```python
urlpatterns = [
    ...
    path('api/skyroom/', include('skyroom.urls')),
    ...
]
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Filtering and Searching

All endpoints support filtering, searching, and ordering:

**Rooms:**
- Filter: `service`, `status`, `guest_login`
- Search: `name`, `title`, `skyroom_id`
- Order: `id`, `name`, `title`, `status`, `updated_at`

**Users:**
- Filter: `status`, `is_public`, `gender`
- Search: `username`, `nickname`, `email`, `skyroom_id`
- Order: `id`, `username`, `nickname`, `status`, `updated_at`

**Example:**
```
GET /api/skyroom/rooms/?service=1&status=1&search=test&ordering=-updated_at
```

## Authentication

All endpoints require admin authentication. Update permissions as needed in settings.

## Notes

- All timestamps from Skyroom API are stored as Unix timestamps
- Database timestamps (created_at, updated_at) are stored as DateTimeField
- Room names must be unique and in Latin characters
- Username must be unique
- The LoginUrl model includes a helper method `is_expired()` to check expiration
