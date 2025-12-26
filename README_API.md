# 📚 Fofofish API Documentation Index

## 🎯 Start Here

Choose what you need:

### 🚀 **I want to use the API right now**
→ Read: [API_KEY_AND_DOCUMENTATION.md](./API_KEY_AND_DOCUMENTATION.md)
- Quick reference
- Copy-paste ready examples
- 5 minute setup

### 📖 **I want complete API documentation**
→ Read: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Every endpoint explained
- Request/response examples
- All parameters documented
- 30 minute read

### 🔧 **I want to understand the setup**
→ Read: [API_SETUP_SUMMARY.md](./API_SETUP_SUMMARY.md)
- What was created/changed
- Configuration details
- File modifications
- 10 minute read

### 📋 **I want to see what files changed**
→ Read: [FILES_CREATED_SUMMARY.md](./FILES_CREATED_SUMMARY.md)
- File-by-file breakdown
- Code changes
- New files created
- 15 minute read

### 🔐 **I want to test with Postman**
→ Import: [Fofofish_Skyroom_API.postman_collection.json](./Fofofish_Skyroom_API.postman_collection.json)
- 27 pre-configured requests
- API key pre-filled
- Ready to test
- 2 minute setup

---

## 📚 Documentation Files

| File | Purpose | Read Time | Audience |
|------|---------|-----------|----------|
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | Complete API reference | 30 min | Developers |
| [API_KEY_AND_DOCUMENTATION.md](./API_KEY_AND_DOCUMENTATION.md) | Quick reference guide | 5 min | Everyone |
| [API_SETUP_SUMMARY.md](./API_SETUP_SUMMARY.md) | Setup documentation | 10 min | Project managers |
| [FILES_CREATED_SUMMARY.md](./FILES_CREATED_SUMMARY.md) | File breakdown | 15 min | Developers |
| [Fofofish_Skyroom_API.postman_collection.json](./Fofofish_Skyroom_API.postman_collection.json) | Postman import | 2 min | QA/Testers |

---

## 🔑 API Key

```
apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

Use this in the `X-API-Key` header for all API requests.

---

## 🌐 Documentation URLs

### Interactive (Live Testing)
- **Swagger UI**: https://fofofish.app/api/docs/swagger/
- **ReDoc**: https://fofofish.app/api/docs/redoc/
- **OpenAPI Schema**: https://fofofish.app/api/schema/

### Local Development
- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## 🚀 Quick Start (5 minutes)

### Option 1: Swagger UI (Browser)
```
1. Go to: https://fofofish.app/api/docs/swagger/
2. Scroll to any endpoint
3. Click "Try it out"
4. API key is auto-filled
5. Click "Execute"
```

### Option 2: Postman
```
1. Open Postman
2. Click File → Import
3. Select: Fofofish_Skyroom_API.postman_collection.json
4. Select any request
5. Click Send
```

### Option 3: cURL
```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/services/
```

---

## 📊 API Overview

### Total Endpoints: 27

```
Services       : 5 endpoints
Rooms          : 6 endpoints (+ 2 custom actions)
Users          : 6 endpoints (+ 2 custom actions)
Login URLs     : 6 endpoints (+ 2 custom actions)
Access         : 4 endpoints
```

### HTTP Methods
- GET: 14 endpoints
- POST: 9 endpoints
- PUT: 2 endpoints
- PATCH: 2 endpoints
- DELETE: 5 endpoints

---

## 🔐 Authentication

### How it works
```
Every request needs the API key in the header:

X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008
```

### Example with cURL
```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/rooms/
```

### Example with Python
```python
import requests

headers = {
    "X-API-Key": "apikey-39974696-1-e570445f94a95d2573d9922d04583008"
}

response = requests.get(
    "https://fofofish.app/api/skyroom/rooms/",
    headers=headers
)
print(response.json())
```

### Example with JavaScript
```javascript
const headers = {
  "X-API-Key": "apikey-39974696-1-e570445f94a95d2573d9922d04583008"
};

fetch("https://fofofish.app/api/skyroom/rooms/", { headers })
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## 📚 API Endpoints (Quick Reference)

### Services
```
GET    /skyroom/services/        List all services
GET    /skyroom/services/{id}/   Get service details
POST   /skyroom/services/        Create service
PUT    /skyroom/services/{id}/   Update service
DELETE /skyroom/services/{id}/   Delete service
```

### Rooms
```
GET    /skyroom/rooms/                     List rooms
GET    /skyroom/rooms/{id}/                Get room details
POST   /skyroom/rooms/                     Create room
PUT    /skyroom/rooms/{id}/                Update room
DELETE /skyroom/rooms/{id}/                Delete room
GET    /skyroom/rooms/{id}/users/          Get room users
POST   /skyroom/rooms/{id}/add_users/      Add users to room
POST   /skyroom/rooms/{id}/remove_users/   Remove users from room
```

### Users
```
GET    /skyroom/users/                     List users
GET    /skyroom/users/{id}/                Get user details
POST   /skyroom/users/                     Create user
PUT    /skyroom/users/{id}/                Update user
DELETE /skyroom/users/{id}/                Delete user
GET    /skyroom/users/{id}/rooms/          Get user rooms
POST   /skyroom/users/{id}/add_rooms/      Add rooms to user
POST   /skyroom/users/{id}/remove_rooms/   Remove rooms from user
```

### Login URLs
```
GET    /skyroom/login-urls/                List login URLs
GET    /skyroom/login-urls/{id}/           Get login URL
POST   /skyroom/login-urls/                Create login URL
DELETE /skyroom/login-urls/{id}/           Delete login URL
GET    /skyroom/login-urls/active/         Get active URLs
GET    /skyroom/login-urls/expired/        Get expired URLs
POST   /skyroom/login-urls/{id}/revoke/    Revoke login URL
```

### Access Management
```
GET    /skyroom/access/                    List access records
GET    /skyroom/access/{id}/               Get access details
POST   /skyroom/access/                    Create access record
PUT    /skyroom/access/{id}/               Update access level
DELETE /skyroom/access/{id}/               Delete access record
```

---

## 📖 Complete Documentation

For complete details on:
- All parameters
- Request/response formats
- Error codes
- Filtering options
- Pagination
- Rate limiting

→ See: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

## 💾 Local Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run migrations
```bash
python manage.py migrate
```

### 3. Start server
```bash
python manage.py runserver
```

### 4. Access documentation
- Swagger: http://localhost:8000/api/docs/swagger/
- ReDoc: http://localhost:8000/api/docs/redoc/
- Schema: http://localhost:8000/api/schema/

---

## 🔍 Find What You Need

### "How do I create a room?"
1. Open [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
2. Find "2. Rooms Management"
3. Find "Create Room" section
4. Copy the request example
5. Try in Swagger or Postman

### "What parameters does the user endpoint accept?"
1. Open [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
2. Find "3. Users Management"
3. Find "Create User" section
4. See all required parameters

### "How do I test the API?"
1. Go to: https://fofofish.app/api/docs/swagger/
2. Click any endpoint
3. Click "Try it out"
4. Modify parameters
5. Click "Execute"

### "How do I use this in my code?"
1. Open [API_KEY_AND_DOCUMENTATION.md](./API_KEY_AND_DOCUMENTATION.md)
2. Find code examples (Python, JavaScript, cURL)
3. Copy and adapt to your needs

---

## 📞 Support Resources

| Need | Solution |
|------|----------|
| API testing | Swagger UI: /api/docs/swagger/ |
| Reference docs | API_DOCUMENTATION.md |
| Quick examples | API_KEY_AND_DOCUMENTATION.md |
| Setup info | API_SETUP_SUMMARY.md |
| File details | FILES_CREATED_SUMMARY.md |
| Postman setup | Import the .json collection file |

---

## ✅ Everything You Need

- ✅ API key ready to use
- ✅ Interactive documentation (Swagger)
- ✅ Organized documentation (ReDoc)
- ✅ Postman collection
- ✅ Markdown documentation
- ✅ Code examples
- ✅ Quick reference guide
- ✅ Setup instructions

**You're all set!** Start with [API_KEY_AND_DOCUMENTATION.md](./API_KEY_AND_DOCUMENTATION.md)

---

**API Key**: `apikey-39974696-1-e570445f94a95d2573d9922d04583008`

**Documentation**: https://fofofish.app/api/docs/swagger/

**Ready for production!** 🚀
