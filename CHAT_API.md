# Chat System API Documentation

**Platform:** FoFoFish  
**Version:** 1.0  
**Last Updated:** 2025-01-01  
**Language:** English / Persian (دوزبانه)

---

## Table of Contents

1. [Overview](#overview)
2. [Chat Types](#chat-types)
3. [Models](#models)
4. [Authentication](#authentication)
5. [API Endpoints](#api-endpoints)
6. [Message Types](#message-types)
7. [Reactions](#reactions)
8. [Code Examples](#code-examples)
9. [Error Handling](#error-handling)
10. [WebSocket (Real-time)](#websocket-real-time)

---

## Overview

The Chat System provides real-time messaging between users in two contexts:

### **Support Chat** (1:1)
- One-to-one communication between a **Teacher** and **Admin**
- Global scope (not tied to any specific class)
- Asynchronous support requests and responses

### **Classroom Chat** (1:Many)
- Teacher-to-Students communication within a specific **TeachingSubject** (class)
- Multiple participants (teacher + students)
- Tied to a specific class/teaching subject
- Group discussion and announcements

---

## Chat Types

### Support Chat
```
Type: 'support'
Participants: Teacher + Admin
Scope: Global (teaching_subject = NULL)
Use Case: Support requests, technical issues, account help
```

### Classroom Chat
```
Type: 'classroom'
Participants: Teacher + Students (enrolled in class)
Scope: Class-specific (teaching_subject = REQUIRED)
Use Case: Class announcements, assignment discussions, Q&A
```

---

## Models

### **ChatRoom**

Represents a conversation space.

**Fields:**
- `id` (Integer, Primary Key)
- `type` (CharField: 'support' | 'classroom')
  - Determines who can participate
- `teaching_subject` (OneToOneField → TeachingSubject, nullable)
  - **NULL** for Support Chat
  - **REQUIRED** for Classroom Chat
- `created_at` (DateTime, auto-created)
- `updated_at` (DateTime, auto-updated)

**Constraints:**
- Support Chat: `teaching_subject` MUST be NULL
- Classroom Chat: `teaching_subject` MUST NOT be NULL

---

### **ChatParticipant**

Defines who is in a chat room and their role.

**Fields:**
- `id` (Integer, Primary Key)
- `chat_room` (ForeignKey → ChatRoom)
- `user` (ForeignKey → User)
- `role` (CharField: 'teacher' | 'student' | 'admin')
- `joined_at` (DateTime, auto-created)
- `updated_at` (DateTime, auto-updated)

**Constraints:**
- Unique: `(chat_room, user)` - A user can only be in a chat room once

---

### **Message**

Represents a message in a chat room.

**Fields:**
- `id` (Integer, Primary Key)
- `chat_room` (ForeignKey → ChatRoom)
- `sender` (ForeignKey → User, nullable)
  - NULL if user is deleted
- `message_type` (CharField: 'text' | 'image' | 'video' | 'audio' | 'pdf' | 'sticker')
- `text` (TextField, nullable)
  - Required for `message_type='text'`
- `file` (FileField, nullable)
  - Required for other message types
  - Uploaded to: `chat/files/%Y/%m/%d/`
- `is_deleted` (BooleanField, default=False)
  - Soft delete only (logical deletion)
- `created_at` (DateTime, auto-created)
- `updated_at` (DateTime, auto-updated)

**Constraints:**
- No hard delete - use soft delete only
- No message editing allowed (immutable after creation)
- No message threading/replies

---

### **MessageReaction**

Represents an emoji reaction to a message.

**Fields:**
- `id` (Integer, Primary Key)
- `message` (ForeignKey → Message)
- `user` (ForeignKey → User)
- `reaction_type` (CharField: 'like' | 'dislike' | 'heart' | 'clap' | 'star')
- `created_at` (DateTime, auto-created)
- `updated_at` (DateTime, auto-updated)

**Constraints:**
- Unique: `(message, user, reaction_type)` - User can add each reaction type once per message
- Reactions are separate from messages (not stored inside Message)

---

## Authentication

All chat endpoints require **JWT Authentication**.

**Header:**
```
Authorization: Bearer <access_token>
```

**User Roles:**
- `teacher` - Can create support chats, send messages
- `student` - Can only participate in classroom chats
- `admin` - Can join support chats, moderate messages

---

## API Endpoints

### 1. Get Chat History

**Endpoint:**
```
GET /api/chat/<chat_room_id>/
```

**Authentication:** Required (IsAuthenticated)

**Parameters:**
- `chat_room_id` (Path, Integer, Required)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "chat_room": 5,
    "sender": 10,
    "sender_name": "علی",
    "sender_avatar": "https://cdn.example.com/avatars/10.png",
    "message_type": "text",
    "text": "سلام، چطور می‌تونم کمک کنم؟",
    "file": null,
    "reactions": [
      {
        "id": 1,
        "user": 11,
        "user_name": "فاطمه",
        "reaction_type": "like",
        "created_at": "2025-01-01T10:30:00Z"
      }
    ],
    "reactions_count": 1,
    "is_deleted": false,
    "created_at": "2025-01-01T10:00:00Z"
  }
]
```

**Errors:**
- `403 Forbidden` - User is not a participant in this chat
- `404 Not Found` - Chat room does not exist

---

### 2. Send Message

**Endpoint:**
```
POST /api/chat/<chat_room_id>/send/
```

**Authentication:** Required (IsAuthenticated)

**Parameters:**
- `chat_room_id` (Path, Integer, Required)

**Request Body (Form-Data or JSON):**

**For Text Messages:**
```json
{
  "message_type": "text",
  "text": "سلام، این یک پیام متنی است"
}
```

**For Media Messages:**
```
message_type: image
file: <binary_file_data>
```

**Supported File Types:**
- `image` - Image files (JPG, PNG, etc.)
- `video` - Video files (MP4, etc.)
- `audio` - Audio files (MP3, M4A, etc.)
- `pdf` - PDF documents
- `sticker` - Sticker image

**Response (201 Created):**
```json
{
  "id": 2,
  "chat_room": 5,
  "sender": 10,
  "sender_name": "علی",
  "sender_avatar": "https://cdn.example.com/avatars/10.png",
  "message_type": "text",
  "text": "سلام، این یک پیام متنی است",
  "file": null,
  "reactions": [],
  "reactions_count": 0,
  "is_deleted": false,
  "created_at": "2025-01-01T10:15:00Z"
}
```

**Errors:**
- `400 Bad Request` - Missing required fields or invalid message_type
- `403 Forbidden` - User is not a participant
- `404 Not Found` - Chat room does not exist

---

### 3. Add Reaction to Message

**Endpoint:**
```
POST /api/chat/message/<message_id>/react/
```

**Authentication:** Required (IsAuthenticated)

**Parameters:**
- `message_id` (Path, Integer, Required)

**Request Body:**
```json
{
  "reaction_type": "like"
}
```

**Reaction Types:**
- `like` (👍)
- `dislike` (👎)
- `heart` (❤️)
- `clap` (👏)
- `star` (⭐)

**Response (201 Created):**
```json
{
  "id": 1,
  "user": 11,
  "user_name": "فاطمه",
  "reaction_type": "like",
  "created_at": "2025-01-01T10:30:00Z"
}
```

**Special Behavior (Toggle):**
- If the user already added this reaction type to this message, the reaction is **removed** (deleted)
- Returns `204 No Content` when toggling off

**Errors:**
- `400 Bad Request` - Missing reaction_type
- `403 Forbidden` - User is not a participant in the chat room
- `404 Not Found` - Message does not exist

---

### 4. List Chat Participants

**Endpoint:**
```
GET /api/chat/<chat_room_id>/participants/
```

**Authentication:** Required (IsAuthenticated)

**Parameters:**
- `chat_room_id` (Path, Integer, Required)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": 10,
    "user_name": "علی",
    "user_avatar": "https://cdn.example.com/avatars/10.png",
    "role": "teacher",
    "joined_at": "2025-01-01T08:00:00Z"
  },
  {
    "id": 2,
    "user": 11,
    "user_name": "فاطمه",
    "user_avatar": "https://cdn.example.com/avatars/11.png",
    "role": "student",
    "joined_at": "2025-01-01T09:00:00Z"
  }
]
```

**Errors:**
- `403 Forbidden` - User is not a participant
- `404 Not Found` - Chat room does not exist

---

## Message Types

### Text
```json
{
  "message_type": "text",
  "text": "متن پیام",
  "file": null
}
```

### Image
```json
{
  "message_type": "image",
  "text": null,
  "file": <image_file>
}
```

### Video
```json
{
  "message_type": "video",
  "text": null,
  "file": <video_file>
}
```

### Audio
```json
{
  "message_type": "audio",
  "text": null,
  "file": <audio_file>
}
```

### PDF
```json
{
  "message_type": "pdf",
  "text": null,
  "file": <pdf_file>
}
```

### Sticker
```json
{
  "message_type": "sticker",
  "text": null,
  "file": <sticker_image>
}
```

---

## Reactions

### Reaction Types

| Type | Emoji | Database Value |
|------|-------|-----------------|
| Like | 👍 | `like` |
| Dislike | 👎 | `dislike` |
| Heart | ❤️ | `heart` |
| Clap | 👏 | `clap` |
| Star | ⭐ | `star` |

### Reaction Constraints

- **One per type per user:** A user can only add one `like` reaction to a message
- **Toggle behavior:** Sending the same reaction twice removes it (toggle)
- **Participants only:** Only users in the chat can react
- **Independent from message:** Reactions are stored in a separate model

### Get Reactions for a Message

Reactions are included in the message response:

```json
{
  "id": 1,
  "text": "سلام",
  "reactions": [
    {
      "id": 1,
      "user": 11,
      "user_name": "فاطمه",
      "reaction_type": "like",
      "created_at": "2025-01-01T10:30:00Z"
    },
    {
      "id": 2,
      "user": 12,
      "user_name": "محمد",
      "reaction_type": "heart",
      "created_at": "2025-01-01T10:35:00Z"
    }
  ],
  "reactions_count": 2
}
```

---

## Code Examples

### Python/Django

```python
import requests

# Get chat history
response = requests.get(
    'https://api.fofofish.com/api/chat/5/',
    headers={'Authorization': f'Bearer {access_token}'}
)
messages = response.json()

# Send a text message
response = requests.post(
    'https://api.fofofish.com/api/chat/5/send/',
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        'message_type': 'text',
        'text': 'سلام'
    }
)
message = response.json()

# Send an image message
with open('photo.jpg', 'rb') as f:
    files = {'file': f}
    data = {'message_type': 'image'}
    response = requests.post(
        'https://api.fofofish.com/api/chat/5/send/',
        headers={'Authorization': f'Bearer {access_token}'},
        files=files,
        data=data
    )

# Add reaction
response = requests.post(
    'https://api.fofofish.com/api/chat/message/1/react/',
    headers={'Authorization': f'Bearer {access_token}'},
    json={'reaction_type': 'like'}
)
```

### JavaScript/React Native

```javascript
// Get chat history
const response = await fetch('https://api.fofofish.com/api/chat/5/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const messages = await response.json();

// Send text message
const sendResponse = await fetch('https://api.fofofish.com/api/chat/5/send/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message_type: 'text',
    text: 'سلام'
  })
});
const message = await sendResponse.json();

// Send image message
const formData = new FormData();
formData.append('message_type', 'image');
formData.append('file', imageFile);

const imageResponse = await fetch('https://api.fofofish.com/api/chat/5/send/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

// Add reaction
const reactionResponse = await fetch(
  'https://api.fofofish.com/api/chat/message/1/react/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ reaction_type: 'like' })
  }
);
```

### cURL

```bash
# Get chat history
curl -X GET https://api.fofofish.com/api/chat/5/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Send text message
curl -X POST https://api.fofofish.com/api/chat/5/send/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_type": "text",
    "text": "سلام"
  }'

# Send image
curl -X POST https://api.fofofish.com/api/chat/5/send/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "message_type=image" \
  -F "file=@/path/to/image.jpg"

# Add reaction
curl -X POST https://api.fofofish.com/api/chat/message/1/react/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reaction_type": "like"}'
```

---

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "error": "message_type الزامی است"
}
```

#### 403 Forbidden
```json
{
  "error": "شما دسترسی به این چت ندارید"
}
```

#### 404 Not Found
```json
{
  "error": "اتاق چت یافت نشد"
}
```

### Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful, data returned |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful, no content to return (e.g., reaction toggled off) |
| 400 | Bad Request | Invalid request data |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

---

## WebSocket (Real-time)

For real-time messaging, the application uses **Django Channels** with WebSocket.

### WebSocket Connection

```javascript
// Connect to WebSocket
const socket = new WebSocket(
  `wss://api.fofofish.com/ws/chat/5/?token=${accessToken}`
);

// Listen for messages
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data contains the new message or reaction
};

// Send message via WebSocket (optional - HTTP is primary)
socket.send(JSON.stringify({
  type: 'message',
  data: {
    message_type: 'text',
    text: 'سلام'
  }
}));
```

### WebSocket Message Format

**New Message Event:**
```json
{
  "type": "message",
  "data": {
    "id": 2,
    "chat_room": 5,
    "sender": 10,
    "sender_name": "علی",
    "message_type": "text",
    "text": "سلام",
    "created_at": "2025-01-01T10:15:00Z"
  }
}
```

**New Reaction Event:**
```json
{
  "type": "reaction",
  "data": {
    "id": 1,
    "message_id": 1,
    "user": 11,
    "user_name": "فاطمه",
    "reaction_type": "like",
    "created_at": "2025-01-01T10:30:00Z"
  }
}
```

**User Joined Event:**
```json
{
  "type": "user_joined",
  "data": {
    "user_id": 12,
    "user_name": "محمد",
    "role": "student"
  }
}
```

---

## Permissions

### Support Chat
- **Teacher** can initiate support chat
- **Admin** can join support chats
- Only participants can send messages

### Classroom Chat
- **Teacher** (who created the class) can create chat
- **Students** (enrolled in the class) automatically participate
- Only participants can send messages
- Admins can moderate (soft delete messages)

### Message Deletion
- Soft delete only (is_deleted = True)
- Deleted messages are hidden from the UI
- Reactions to deleted messages are also hidden
- Only admins or the message sender can delete

### Reactions
- Any participant can add/remove reactions
- Cannot react to deleted messages

---

## Best Practices

1. **Load History Gradually:** Use pagination/pagination for large chat histories
2. **Soft Delete Only:** Never hard delete messages
3. **Validate Input:** Check message_type and file size before uploading
4. **Cache Reactions:** Store reaction counts client-side to reduce API calls
5. **Handle Errors:** Implement proper error handling for network failures
6. **Use WebSocket:** Implement real-time updates via Django Channels
7. **Throttle Uploads:** Limit file upload size (recommended max: 50MB)

---

## Database Schema

```sql
-- Chat Rooms
CREATE TABLE classroom_chatroom (
    id INTEGER PRIMARY KEY,
    type VARCHAR(20) NOT NULL,  -- 'support' or 'classroom'
    teaching_subject_id INTEGER UNIQUE NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Participants
CREATE TABLE classroom_chatparticipant (
    id INTEGER PRIMARY KEY,
    chat_room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'teacher', 'student', 'admin'
    joined_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE(chat_room_id, user_id)
);

-- Messages
CREATE TABLE classroom_message (
    id INTEGER PRIMARY KEY,
    chat_room_id INTEGER NOT NULL,
    sender_id INTEGER NULL,
    message_type VARCHAR(20) NOT NULL,  -- 'text', 'image', etc.
    text TEXT NULL,
    file VARCHAR(255) NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Reactions
CREATE TABLE classroom_messagereaction (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reaction_type VARCHAR(20) NOT NULL,  -- 'like', 'heart', etc.
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE(message_id, user_id, reaction_type)
);
```

---

## Changelog

### Version 1.0 (2025-01-01)
- ✅ Initial implementation
- ✅ Support and Classroom chat types
- ✅ Text and media messages
- ✅ Emoji reactions
- ✅ Soft delete
- ✅ WebSocket real-time updates
- ✅ Complete API documentation
