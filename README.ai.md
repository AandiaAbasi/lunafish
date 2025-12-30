# CHAT SYSTEM — DJANGO (DO NOT GUESS)

This document defines the ONLY allowed chat system design.
Do NOT invent new models, fields, or flows.

---

## 1️⃣ Chat Types

There are EXACTLY two chat types:

### 1. Support Chat
- Participants:
  - Teacher
  - Admin (support)
- Scope: global (not tied to a class)
- One-to-one chat

### 2. Classroom Chat
- Participants:
  - Teacher
  - One or more Students
- Scope:
  - Bound to ONE TeachingSubject (class)
- Group chat

No other chat types exist.

---

## 2️⃣ Chat Core Models

### ChatRoom
Represents a single chat space.

Fields:
- id
- type: "support" | "classroom"
- teaching_subject (nullable, only for classroom chat)
- created_at

Rules:
- Support chat → teaching_subject = NULL
- Classroom chat → teaching_subject is REQUIRED

---

### ChatParticipant
Defines who is in a chat room.

Fields:
- id
- chat_room
- user
- role: "teacher" | "student" | "admin"
- joined_at

Rules:
- A user cannot join the same room twice
- Role is REQUIRED

---

### Message
Represents a single message.

Fields:
- id
- chat_room
- sender
- message_type:
  - text
  - image
  - video
  - audio
  - pdf
  - sticker
- text (nullable)
- file (nullable)
- created_at
- is_deleted (soft delete)

Rules:
- text messages → text REQUIRED
- file messages → file REQUIRED
- Do NOT mix text and file in the same message

---

### MessageReaction
Represents a reaction to a message.

Fields:
- id
- message
- user
- reaction_type:
  - like
  - dislike
  - heart
  - clap
  - star
- created_at

Rules:
- One reaction per user per message per reaction_type
- Reactions are NOT messages

---

## 3️⃣ Allowed Message Features

✅ Text  
✅ Emoji (Unicode only)  
✅ Stickers (as files)  
✅ Image  
✅ Audio (voice)  
✅ Video  
✅ PDF  

❌ No message editing  
❌ No message threading  
❌ No reactions as messages  

---

## 4️⃣ Permissions

- Only participants can:
  - Send messages
  - React to messages
- Only admins can:
  - Moderate support chats
- Teachers cannot delete student messages
- Soft delete only (no hard delete)

---

## 5️⃣ Realtime Rules

- Realtime delivery via:
  - Django Channels (WebSocket)
- HTTP APIs only for:
  - history
  - uploads
- No polling

---

## 6️⃣ Naming Rules (STRICT)

Model names:
- ChatRoom
- ChatParticipant
- Message
- MessageReaction

Do NOT rename models.

---

## 7️⃣ Forbidden (NEVER DO)

- ❌ Guess new chat types
- ❌ Guess reaction types
- ❌ Use JSON fields
- ❌ Store reactions inside Message
- ❌ Allow non-participants access
- ❌ Use generic "content" fields

---

## 8️⃣ If Something Is Missing

STOP.
ASK.
DO NOT GUESS.
