# 📱 Student App - API Documentation

## 🎯 Introduction

Complete API specifications for the **Student App** with all endpoints and UI requirements.

Each section is independent and can be implemented separately. Just copy the section and ask Copilot!

---

# 🎓 STUDENT APP

## 📚 Section 1: Authentication & User Profile

### 1.1 - User Registration (Phone)
**Endpoint:** `POST /api/account/register/`

**Request:**
```json
{
  "phone": "+989123456789",
  "password": "SecurePass123!",
  "name": "محمد احمدی"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "user_9123456789",
  "phone": "+989123456789",
  "name": "محمد احمدی",
  "role": "user",
  "message": "OTP sent to your phone"
}
```

**UI Required:**
- Phone input field
- Password input field
- Name input field
- "Next" button
- OTP verification screen

---

### 1.2 - Verify OTP
**Endpoint:** `POST /api/account/verify-otp/`

**Request:**
```json
{
  "phone": "+989123456789",
  "code": "123456"
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user_9123456789",
    "phone": "+989123456789",
    "name": "محمد احمدی",
    "email_verified_at": null,
    "phone_verified_at": "2025-12-28T10:30:00Z"
  }
}
```

**UI Required:**
- OTP input (6-digit)
- "Verify" button
- "Resend OTP" link
- Timer for resend

---

### 1.3 - User Profile
**Endpoint:** `GET /api/account/profile/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "user_9123456789",
  "name": "محمد احمدی",
  "phone": "+989123456789",
  "email": "mohammad@example.com",
  "profile_photo_path": "https://api.com/media/avatars/user_1.jpg",
  "selected_avatar": {
    "id": 3,
    "image": "https://api.com/media/avatars/templates/cat_avatar.png"
  },
  "bio": "یک دانش‌آموز فعال",
  "gender": "male",
  "birth_date": "1410-05-24",
  "role": "user",
  "is_online": true,
  "last_seen": "2025-12-28T10:30:00Z"
}
```

**UI Required:**
- Profile picture with avatar selector
- Name, phone, email display
- Bio text area
- Gender selector
- Birth date picker
- Online status indicator

---

### 1.4 - Update Profile
**Endpoint:** `PUT /api/account/profile/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "name": "محمد احمدی",
  "email": "mohammad@example.com",
  "bio": "یک دانش‌آموز فعال",
  "gender": "male",
  "birth_date": "1410-05-24",
  "selected_avatar": 3
}
```

**Response:** `200 OK` - Same as 1.3

**UI Required:**
- Edit button
- Save/Cancel buttons
- Form validation

---

### 1.5 - Select Avatar
**Endpoint:** `GET /api/account/avatars/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "image": "https://api.com/media/avatars/templates/bear_avatar.png",
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "image": "https://api.com/media/avatars/templates/rabbit_avatar.png"
    }
  ]
}
```

**UI Required:**
- Grid of avatar images
- Select button for each
- Currently selected indicator
- Search/filter

---

## 📖 Section 2: Browse & Discover Courses

### 2.1 - List All Courses
**Endpoint:** `GET /api/classroom/courses/`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `language=en` - Filter by language
- `level=1` - Filter by level
- `search=english` - Search by title
- `page=1` - Pagination

**Response:** `200 OK`
```json
{
  "count": 45,
  "next": "https://api.com/api/classroom/courses/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "English for Kids",
      "description": "یادگیری زبان انگلیسی برای کودکان",
      "teacher": "teacher_1",
      "teacher_name": "محمدحسن معلم",
      "language": 1,
      "language_name": "English",
      "level": 1,
      "level_name": "Beginner",
      "max_students": 8,
      "duration_minutes": 60,
      "hourly_rate": "50.00",
      "cover_image": "https://api.com/media/courses/covers/course_1.jpg",
      "is_active": true,
      "lessons_count": 12,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

**UI Required:**
- Course grid/list view
- Course card with cover image, title, teacher name, level, lessons count, price
- Filter sidebar (language, level)
- Search bar
- Pagination

---

### 2.2 - Course Details
**Endpoint:** `GET /api/classroom/courses/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "teacher": 5,
  "teacher_name": "محمدحسن معلم",
  "title": "English for Kids",
  "description": "یادگیری زبان انگلیسی برای کودکان با روش‌های نوین",
  "language": 1,
  "language_name": "English",
  "level": 1,
  "level_name": "Beginner",
  "max_students": 8,
  "duration_minutes": 60,
  "hourly_rate": "50.00",
  "cover_image": "https://api.com/media/courses/covers/course_1.jpg",
  "is_active": true,
  "lessons_count": 12,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Header with course image
- Course title, teacher, level
- Description
- Schedule/lessons list link
- "Enroll" button
- Share button

---

### 2.3 - List Class Levels
**Endpoint:** `GET /api/classroom/levels/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 4,
  "results": [
    {"id": 1, "name": "Beginner", "order": 1},
    {"id": 2, "name": "Elementary", "order": 2},
    {"id": 3, "name": "Intermediate", "order": 3},
    {"id": 4, "name": "Advanced", "order": 4}
  ]
}
```

---

### 2.4 - List Languages
**Endpoint:** `GET /api/classroom/languages/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {"id": 1, "name": "English", "code": "en"},
    {"id": 2, "name": "Persian", "code": "fa"},
    {"id": 3, "name": "German", "code": "de"}
  ]
}
```

---

## 📅 Section 3: Lessons & Enrollment

### 3.1 - List Upcoming Lessons
**Endpoint:** `GET /api/classroom/lessons/?course={id}`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `course=1` - Filter by course
- `status=scheduled,in_progress`
- `ordering=-scheduled_at` - Sort by time

**Response:** `200 OK`
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "course": 1,
      "course_title": "English for Kids",
      "teacher_name": "محمدحسن معلم",
      "title": "Lesson 1: Greeting",
      "scheduled_at": "2025-12-29T15:00:00Z",
      "status": "scheduled",
      "is_recorded": true,
      "recording_url": null
    }
  ]
}
```

**UI Required:**
- Lesson list view
- Lesson card with title, course name, date & time, teacher name, status badge
- "Join" button (if started)
- "Set Reminder" button
- Countdown timer (if upcoming)

---

### 3.2 - Lesson Details
**Endpoint:** `GET /api/classroom/lessons/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "course": {
    "id": 1,
    "title": "English for Kids",
    "teacher_name": "محمدحسن معلم"
  },
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1",
  "status": "scheduled",
  "teacher_notes": "سوالات رایج در این درس"
}
```

**UI Required:**
- Course header
- Lesson title & description
- Time & date
- Materials section
- "Join Live Class" button
- Recording link (if available)

---

### 3.3 - Lesson Materials
**Endpoint:** `GET /api/classroom/lessons/{id}/materials/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "lesson": 1,
      "title": "Greeting PDF",
      "material_type": "pdf",
      "file": "https://api.com/media/lesson_materials/greeting.pdf",
      "description": "الفبای تلفظ",
      "order": 1
    },
    {
      "id": 2,
      "lesson": 1,
      "title": "Example Video",
      "material_type": "video",
      "external_link": "https://youtube.com/watch?v=...",
      "description": "ویدیو مثال",
      "order": 2
    }
  ]
}
```

**UI Required:**
- Materials list
- Download button for files
- Preview for images
- Video player for videos
- Link preview for external links

---

### 3.4 - Enroll in Lesson
**Endpoint:** `POST /api/classroom/enrollments/enroll/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "lesson_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "lesson": 1,
  "lesson_title": "Lesson 1: Greeting",
  "student": 10,
  "status": "registered",
  "created_at": "2025-12-28T10:30:00Z"
}
```

**UI Required:**
- "Enroll" button
- Confirmation dialog
- Success message
- Button changes to "Enrolled"

---

### 3.5 - My Enrollments
**Endpoint:** `GET /api/classroom/enrollments/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": 5,
      "lesson": 1,
      "lesson_title": "Lesson 1: Greeting",
      "status": "present",
      "joined_at": "2025-12-29T15:10:00Z",
      "left_at": "2025-12-29T16:05:00Z",
      "attendance_duration": 55
    }
  ]
}
```

**UI Required:**
- My lessons list
- Status indicator
- Attendance badge
- Duration display

---

## 🎥 Section 4: Live Class

### 4.1 - Generate Agora Token
**Endpoint:** `POST /api/classroom/agora-tokens/generate_token/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "lesson_id": 1,
  "privilege": "publisher"
}
```

**Response:** `201 Created`
```json
{
  "id": 12,
  "lesson": 1,
  "user": 10,
  "token": "00750f8db7e542e8b7a7d80c98f4a93e19cAAgDHKzKM0qCjqxQFc2FS9nXJc0VJCg7YkzEkuNvzTQHnEpgKXAgAAAAAKEjJHwQEA3QEAAQHdAQABHx+DXwEA3QEAAQHdAQA=",
  "privilege": "publisher",
  "expires_at": "2025-12-29T16:05:00Z",
  "is_valid": true
}
```

---

### 4.2 - Join Live Class
**Screen Elements:**
- Agora video view (grid layout)
- Self video preview
- Mute/unmute audio toggle
- Turn on/off video toggle
- Speaker list
- Chat button
- Whiteboard button
- Leave button
- Timer showing lesson duration
- Connection quality indicator

**Flow:**
1. Get lesson details
2. Check if lesson is started
3. Enroll if not enrolled
4. Generate Agora token
5. Initialize Agora SDK
6. Connect to channel

---

### 4.3 - Whiteboard Data
**Endpoint:** `GET /api/classroom/lessons/{id}/whiteboard/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "lesson": 1,
  "content": {
    "strokes": [
      {
        "points": [[10, 20], [11, 21], [12, 22]],
        "color": "#000000",
        "width": 2,
        "timestamp": 1640000000000
      }
    ]
  },
  "is_locked": false,
  "last_modified_at": "2025-12-29T15:30:00Z"
}
```

**UI Required:**
- Canvas for drawing
- Drawing tools (pen, eraser, shapes)
- Color picker
- Line width selector
- Undo/Redo buttons
- Real-time sync via WebSocket

---

## 🎯 Section 5: Quiz & Assessment

### 5.1 - List Quizzes
**Endpoint:** `GET /api/classroom/quizzes/?lesson={id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "lesson": 1,
      "lesson_title": "Lesson 1: Greeting",
      "title": "Quick Quiz - Greeting",
      "difficulty": "easy",
      "time_limit_minutes": 5,
      "passing_score": 70,
      "is_active": true
    }
  ]
}
```

**UI Required:**
- Quiz card with title
- Difficulty badge
- Time limit info
- "Start Quiz" button
- "View Results" button (if completed)

---

### 5.2 - Quiz Details
**Endpoint:** `GET /api/classroom/quizzes/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "lesson": {
    "id": 1,
    "title": "Lesson 1: Greeting"
  },
  "title": "Quick Quiz - Greeting",
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "questions": [
    {
      "id": 1,
      "question_text": "What is 'Hello' called in English?",
      "question_type": "multiple_choice",
      "points": 10,
      "explanation": "Hello is a greeting word",
      "answers": [
        {
          "id": 1,
          "answer_text": "A greeting",
          "is_correct": true
        },
        {
          "id": 2,
          "answer_text": "A name",
          "is_correct": false
        }
      ]
    }
  ]
}
```

**UI Required:**
- Quiz title & description
- Question display
- Answer options
- Navigation (previous/next)
- Timer countdown
- Progress indicator
- Submit button

---

### 5.3 - Start Quiz Attempt
**Endpoint:** `POST /api/classroom/quiz-attempts/start_attempt/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "quiz_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 10,
  "quiz": 1,
  "student": 10,
  "started_at": "2025-12-29T15:15:00Z"
}
```

---

### 5.4 - Submit Quiz Answer
**Endpoint:** `POST /api/classroom/quiz-attempts/{attempt_id}/responses/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "question_id": 1,
  "selected_answer_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 25,
  "attempt": 10,
  "question": 1,
  "selected_answer": 1,
  "is_correct": true,
  "points_earned": 10
}
```

---

### 5.5 - Submit Quiz
**Endpoint:** `POST /api/classroom/quiz-attempts/{id}/submit/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 10,
  "quiz": 1,
  "score": 85,
  "total_points": 15,
  "earned_points": 13,
  "passed": true
}
```

**UI Required:**
- Results summary (score %, points, pass/fail)
- Time taken
- Answers review with explanations
- Share/retry options

---

### 5.6 - Quiz Results
**Endpoint:** `GET /api/classroom/quiz-attempts/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** Complete attempt with all responses

---

## 📊 Section 6: Progress & Achievements

### 6.1 - Student Progress
**Endpoint:** `GET /api/classroom/progress/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 2,
  "results": [
    {
      "id": 3,
      "student": 10,
      "course": 1,
      "course_title": "English for Kids",
      "total_lessons": 12,
      "lessons_completed": 5,
      "lessons_attended": 5,
      "attendance_percentage": "100.00",
      "average_quiz_score": "87.50",
      "total_points": 45,
      "badges_earned": 2,
      "badges": [
        {
          "id": 5,
          "badge": {
            "id": 1,
            "name": "Perfect Attendance",
            "icon": "https://api.com/media/badges/perfect_attendance.png"
          },
          "earned_at": "2025-12-28T10:30:00Z"
        }
      ]
    }
  ]
}
```

**UI Required:**
- Course card with stats
- Lessons attended/total
- Attendance percentage
- Average quiz score
- Points earned
- Badges grid

---

### 6.2 - Badges/Achievements
**From 6.1 response**

**UI Required:**
- Badge grid
- Badge details on tap
- Locked badges with requirements

---

## 📝 Section 7: Attendance & History

### 7.1 - Attendance Records
**Endpoint:** `GET /api/classroom/attendance/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "lesson": 1,
      "lesson_title": "Lesson 1: Greeting",
      "status": "present",
      "expected_at": "2025-12-29T15:00:00Z",
      "actual_joined_at": "2025-12-29T15:05:00Z",
      "left_at": "2025-12-29T16:00:00Z",
      "minutes_attended": 55,
      "notes": "خوب شرکت کرد"
    }
  ]
}
```

**UI Required:**
- Attendance calendar/list
- Status indicator
- Minutes attended
- Notes
- Attendance percentage

---

# 🚀 Implementation Priority

## Phase 1: Core (Must Have)
- [ ] Section 1: Authentication
- [ ] Section 2: Course Discovery
- [ ] Section 3: Lessons & Enroll
- [ ] Section 5: Quiz System
- [ ] Section 7: Attendance

## Phase 2: Enhanced
- [ ] Section 4: Live Classes (Agora)
- [ ] Whiteboard (WebSocket)
- [ ] Section 6: Progress & Badges

## Phase 3: Advanced
- [ ] Chat system
- [ ] Notifications
- [ ] Analytics dashboard

---

# 📝 NOTES

- All timestamps in UTC (ISO 8601)
- Phone numbers in E.164 format (+98...)
- Prices in default currency (decimal)
- Jalali date format for birth_date (YYYY-MM-DD)
- JWT token for authorization
- Pagination with default 20 items per page

---

# How to Use

1. **Open this file:** STUDENT_APP_API_SPECS.md
2. **Choose a section:** e.g., "Section 1: Authentication"
3. **Copy entire section**
4. **Ask Copilot:** "Implement Student App Section 1 with this API spec: [paste]"
5. **Get working code!** ✅

---

**Ready to build? 🚀**

Start with: **"Implement STUDENT APP - Section 1: Authentication & User Profile"**
