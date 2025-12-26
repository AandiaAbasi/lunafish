# API Authentication & Documentation Quick Reference

## 🔐 API Key

```
apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

## 📚 Documentation Access

### Interactive Swagger UI
```
https://fofofish.app/api/docs/swagger/
```
- Full interactive API testing
- Try endpoints directly in browser
- Real-time request/response examples

### ReDoc Documentation
```
https://fofofish.app/api/docs/redoc/
```
- Organized API documentation
- Better for reading
- Mobile-friendly

### OpenAPI Schema
```
https://fofofish.app/api/schema/
```
- Raw OpenAPI 3.0 specification
- Import into tools (Postman, Insomnia, etc.)

## 📥 Postman Import

1. Open Postman
2. Click **File** → **Import**
3. Select **Fofofish_Skyroom_API.postman_collection.json**
4. All requests pre-configured with API key

**File Location:**
```
./Fofofish_Skyroom_API.postman_collection.json
```

## 🚀 Quick API Calls

### Using cURL with API Key

```bash
# List all services
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/services/

# List all rooms
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/rooms/

# List all users
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/users/

# List login URLs
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/login-urls/
```

### Using Python

```python
import requests

API_KEY = "apikey-39974696-1-e570445f94a95d2573d9922d04583008"
BASE_URL = "https://fofofish.app/api"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get all services
response = requests.get(f"{BASE_URL}/skyroom/services/", headers=headers)
print(response.json())

# Get all rooms
response = requests.get(f"{BASE_URL}/skyroom/rooms/", headers=headers)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
const API_KEY = "apikey-39974696-1-e570445f94a95d2573d9922d04583008";
const BASE_URL = "https://fofofish.app/api";

const headers = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json"
};

// Get all services
fetch(`${BASE_URL}/skyroom/services/`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));
```

## 📊 API Endpoints Summary

### Services
```
GET    /skyroom/services/           # List all services
GET    /skyroom/services/{id}/      # Get service details
POST   /skyroom/services/           # Create service
PUT    /skyroom/services/{id}/      # Update service
DELETE /skyroom/services/{id}/      # Delete service
```

### Rooms
```
GET    /skyroom/rooms/              # List all rooms
GET    /skyroom/rooms/{id}/         # Get room details
POST   /skyroom/rooms/              # Create room
PUT    /skyroom/rooms/{id}/         # Update room
DELETE /skyroom/rooms/{id}/         # Delete room
GET    /skyroom/rooms/{id}/users/   # Get room users
POST   /skyroom/rooms/{id}/add_users/       # Add users to room
POST   /skyroom/rooms/{id}/remove_users/    # Remove users from room
```

### Users
```
GET    /skyroom/users/              # List all users
GET    /skyroom/users/{id}/         # Get user details
POST   /skyroom/users/              # Create user
PUT    /skyroom/users/{id}/         # Update user
DELETE /skyroom/users/{id}/         # Delete user
GET    /skyroom/users/{id}/rooms/   # Get user rooms
POST   /skyroom/users/{id}/add_rooms/       # Add rooms to user
POST   /skyroom/users/{id}/remove_rooms/    # Remove rooms from user
```

### Login URLs
```
GET    /skyroom/login-urls/         # List login URLs
GET    /skyroom/login-urls/{id}/    # Get login URL
POST   /skyroom/login-urls/         # Create login URL
DELETE /skyroom/login-urls/{id}/    # Delete login URL
GET    /skyroom/login-urls/active/  # Get active URLs
GET    /skyroom/login-urls/expired/ # Get expired URLs
POST   /skyroom/login-urls/{id}/revoke/    # Revoke login URL
```

### Access Management
```
GET    /skyroom/access/             # List access records
GET    /skyroom/access/{id}/        # Get access details
POST   /skyroom/access/             # Create access record
PUT    /skyroom/access/{id}/        # Update access level
DELETE /skyroom/access/{id}/        # Delete access record
```

## 🔍 Filtering & Searching

### Services
```
?search=premium          # Search by title or skyroom_id
?ordering=-updated_at    # Order by field (prefix - for desc)
```

### Rooms
```
?service=1              # Filter by service ID
?status=1               # Filter by status (0/1)
?guest_login=true       # Filter by guest login
?search=meeting         # Search by name/title/skyroom_id
?ordering=-updated_at
```

### Users
```
?status=1               # Filter by status
?is_public=false        # Filter by public flag
?gender=1               # Filter by gender (0/1/2)
?search=username        # Search by username/nickname/email
```

### Login URLs
```
?room=1                 # Filter by room
?access=2               # Filter by access level
?is_active=true         # Filter by active status
```

## 🔐 Access Levels

```
1 = Normal User    (can join and view)
2 = Presenter      (can present, share screen)
3 = Operator       (full control, manage users)
```

## 👥 Gender Codes

```
0 = Unknown
1 = Male
2 = Female
```

## 📝 Status Codes

### Service Status
```
0 = Inactive
1 = Active
```

### Room Status
```
0 = Inactive
1 = Active
```

### User Status
```
0 = Inactive
1 = Active
```

## 📋 Full Documentation

For complete API documentation with examples:
- **Markdown Guide**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Interactive Swagger**: https://fofofish.app/api/docs/swagger/
- **Organized ReDoc**: https://fofofish.app/api/docs/redoc/

## ✅ Configuration in Django

API key authentication is configured in `fofofish/settings.py`:

```python
# Valid API Keys
VALID_API_KEYS = {
    'apikey-39974696-1-e570445f94a95d2573d9922d04583008': 'skyroom_integration_key',
}

# drf-spectacular Swagger/OpenAPI Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Fofofish API',
    'VERSION': '1.0.0',
    # ... more settings
}
```

## 🛠️ Tools Used

- **DRF**: Django REST Framework for API development
- **drf-spectacular**: For Swagger/OpenAPI documentation
- **Postman**: For API testing and documentation

## 📞 Support

- Swagger UI: https://fofofish.app/api/docs/swagger/
- Documentation: API_DOCUMENTATION.md
- Questions: Check the full documentation above

