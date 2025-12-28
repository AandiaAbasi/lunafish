# 📱 Student & Teacher Apps - API Documentation

## 🎯 Introduction

This document provides complete API specifications and requirements for:
- **Student App** - برای دانش‌آموزان
- **Teacher App** - برای معلمان

Each feature is clearly separated so you can ask Copilot to implement it step by step.

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
    // ... more avatars
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
    // ... more courses
  ]
}
```

**UI Required:**
- Course grid/list view
- Course card with:
  - Cover image
  - Title
  - Teacher name
  - Level
  - Lessons count
  - Price/rate
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
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-12-20T15:30:00Z"
}
```

**UI Required:**
- Header with course image
- Course title, teacher, level
- Description
- Schedule/lessons list link
- "Enroll" button
- Reviews/ratings (future)
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
    {
      "id": 1,
      "name": "Beginner",
      "description": "شروع برای مبتدیان",
      "order": 1
    },
    {
      "id": 2,
      "name": "Elementary",
      "order": 2
    },
    {
      "id": 3,
      "name": "Intermediate",
      "order": 3
    },
    {
      "id": 4,
      "name": "Advanced",
      "order": 4
    }
  ]
}
```

**UI Required:**
- Level selector dropdown/buttons
- Used in course filters

---

### 2.4 - List Languages
**Endpoint:** `GET /api/classroom/languages/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "English",
      "code": "en"
    },
    {
      "id": 2,
      "name": "Persian",
      "code": "fa"
    },
    {
      "id": 3,
      "name": "German",
      "code": "de"
    }
  ]
}
```

**UI Required:**
- Language selector
- Flag icons optional

---

## 📅 Section 3: Lessons & Enrollment

### 3.1 - List Upcoming Lessons
**Endpoint:** `GET /api/classroom/lessons/?course={id}`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `course=1` - Filter by course
- `status=scheduled,in_progress` - Filter by status
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
      "started_at": null,
      "ended_at": null,
      "is_recorded": true,
      "recording_url": null,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "course": 1,
      "course_title": "English for Kids",
      "teacher_name": "محمدحسن معلم",
      "title": "Lesson 2: Colors",
      "scheduled_at": "2025-12-30T15:00:00Z",
      "status": "scheduled",
      "started_at": null,
      "ended_at": null,
      "is_recorded": true,
      "recording_url": null
    }
    // ... more lessons
  ]
}
```

**UI Required:**
- Lesson list view
- Lesson card showing:
  - Title
  - Course name
  - Date & time
  - Teacher name
  - Status badge (Upcoming/Started/Completed)
  - Recording available icon
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
    "teacher": 5,
    "teacher_name": "محمدحسن معلم",
    "title": "English for Kids",
    "language": 1,
    "language_name": "English",
    "level": 1,
    "level_name": "Beginner",
    "max_students": 8,
    "duration_minutes": 60,
    "hourly_rate": "50.00",
    "cover_image": "https://api.com/media/courses/covers/course_1.jpg",
    "is_active": true
  },
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1",
  "status": "scheduled",
  "started_at": null,
  "ended_at": null,
  "duration_minutes": 60,
  "recording_url": null,
  "is_recorded": true,
  "teacher_notes": "سوالات رایج در این درس",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Course header
- Lesson title & description
- Time & date
- Status
- Teacher notes
- Materials section
- "Join Live Class" button
- Recording link (if available)

---

### 3.3 - Lesson Materials
**Endpoint:** `GET /api/classroom/lessons/{id}/materials/` OR `GET /api/classroom/lessons/{lesson_id}`

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
      "external_link": null,
      "description": "الفبای تلفظ",
      "order": 1,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "lesson": 1,
      "title": "Example Video",
      "material_type": "video",
      "file": null,
      "external_link": "https://youtube.com/watch?v=...",
      "description": "ویدیو مثال",
      "order": 2
    },
    {
      "id": 3,
      "lesson": 1,
      "title": "Exercise Image",
      "material_type": "image",
      "file": "https://api.com/media/lesson_materials/exercise.jpg",
      "external_link": null,
      "description": "تمرین برای درس",
      "order": 3
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
- Order based on `order` field

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
  "student_name": "محمد احمدی",
  "role": "student",
  "agora_uid": null,
  "joined_at": null,
  "left_at": null,
  "status": "registered",
  "paid": false,
  "notes": null,
  "attendance_duration": 0,
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
      "student": 10,
      "student_name": "محمد احمدی",
      "role": "student",
      "agora_uid": null,
      "joined_at": "2025-12-29T15:10:00Z",
      "left_at": "2025-12-29T16:05:00Z",
      "status": "present",
      "paid": true,
      "notes": "خوب شرکت کرد",
      "attendance_duration": 55,
      "created_at": "2025-12-28T10:30:00Z"
    }
    // ... more enrollments
  ]
}
```

**UI Required:**
- My lessons list
- Status indicator
- Attendance badge
- Notes display

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
  "lesson_title": "Lesson 1: Greeting",
  "user": 10,
  "user_name": "محمد احمدی",
  "token": "00750f8db7e542e8b7a7d80c98f4a93e19cAAgDHKzKM0qCjqxQFc2FS9nXJc0VJCg7YkzEkuNvzTQHnEpgKXAgAAAAAKEjJHwQEA3QEAAQHdAQABHx+DXwEA3QEAAQHdAQA=",
  "privilege": "publisher",
  "generated_at": "2025-12-29T15:05:00Z",
  "expires_at": "2025-12-29T16:05:00Z",
  "is_revoked": false,
  "is_valid": true,
  "created_at": "2025-12-29T15:05:00Z"
}
```

**UI Required:**
- Called automatically when joining class
- Loading indicator while generating

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
1. Get lesson details (3.2)
2. Check if lesson is started
3. Enroll if not enrolled (3.4)
4. Generate Agora token (4.1)
5. Initialize Agora SDK with token
6. Connect to channel
7. Start/stop audio & video

---

### 4.3 - Whiteboard Data
**Endpoint:** `GET /api/classroom/lessons/{id}/whiteboard/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "lesson": 1,
  "lesson_title": "Lesson 1: Greeting",
  "content": {
    "strokes": [
      {
        "points": [[10, 20], [11, 21], [12, 22]],
        "color": "#000000",
        "width": 2,
        "timestamp": 1640000000000
      }
    ],
    "shapes": [
      {
        "type": "rect",
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 150,
        "color": "#FF0000",
        "timestamp": 1640000010000
      }
    ]
  },
  "is_locked": false,
  "last_modified_by": 5,
  "last_modified_at": "2025-12-29T15:30:00Z"
}
```

**UI Required:**
- Canvas for drawing
- Drawing tools (pen, eraser, shapes)
- Color picker
- Line width selector
- Undo/Redo buttons
- Lock indicator (if locked)
- Real-time sync via WebSocket

**Note:** Implement WebSocket for real-time whiteboard updates

---

## 🎯 Section 5: Quiz & Assessment

### 5.1 - List Quizzes
**Endpoint:** `GET /api/classroom/quizzes/?lesson={id}`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `lesson=1` - Filter by lesson

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
      "description": "کوییز سریع برای بررسی یادگیری",
      "difficulty": "easy",
      "time_limit_minutes": 5,
      "passing_score": 70,
      "show_before_lesson": false,
      "show_during_lesson": true,
      "show_after_lesson": true,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
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
    "course": 1,
    "course_title": "English for Kids",
    "teacher_name": "محمدحسن معلم",
    "title": "Lesson 1: Greeting",
    "scheduled_at": "2025-12-29T15:00:00Z",
    "status": "in_progress"
  },
  "title": "Quick Quiz - Greeting",
  "description": "کوییز سریع برای بررسی یادگیری",
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "show_before_lesson": false,
  "show_during_lesson": true,
  "show_after_lesson": true,
  "is_active": true,
  "questions": [
    {
      "id": 1,
      "quiz": 1,
      "question_text": "What is 'Hello' called in English?",
      "question_type": "multiple_choice",
      "points": 10,
      "order": 1,
      "explanation": "Hello is a greeting word used to say hi",
      "answers": [
        {
          "id": 1,
          "question": 1,
          "answer_text": "A greeting",
          "is_correct": true,
          "order": 1
        },
        {
          "id": 2,
          "question": 1,
          "answer_text": "A name",
          "is_correct": false,
          "order": 2
        },
        {
          "id": 3,
          "question": 1,
          "answer_text": "A verb",
          "is_correct": false,
          "order": 3
        }
      ]
    },
    {
      "id": 2,
      "quiz": 1,
      "question_text": "True or False: 'Hello' is informal",
      "question_type": "true_false",
      "points": 5,
      "order": 2,
      "explanation": "Hello can be both formal and informal",
      "answers": [
        {
          "id": 4,
          "question": 2,
          "answer_text": "True",
          "is_correct": true,
          "order": 1
        },
        {
          "id": 5,
          "question": 2,
          "answer_text": "False",
          "is_correct": false,
          "order": 2
        }
      ]
    }
  ],
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Quiz title & description
- Question display (one at a time or all)
- Answer options (radio for multiple choice, buttons for true/false)
- Navigation (previous/next question)
- Timer countdown
- Progress indicator
- Submit button
- Show/hide answers
- Answer explanation display

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
  "student_name": "محمد احمدی",
  "lesson_enrollment": 5,
  "started_at": "2025-12-29T15:15:00Z",
  "submitted_at": null,
  "score": null,
  "total_points": 0,
  "earned_points": 0,
  "passed": false,
  "created_at": "2025-12-29T15:15:00Z"
}
```

**UI Required:**
- Start timer
- Load quiz questions
- Disable question editing until submission

---

### 5.4 - Submit Quiz Answer
**Endpoint:** `POST /api/classroom/quiz-attempts/{attempt_id}/responses/`

**Headers:** `Authorization: Bearer {token}`

**Request (for multiple choice):**
```json
{
  "question_id": 1,
  "selected_answer_id": 1
}
```

**Request (for short answer):**
```json
{
  "question_id": 3,
  "text_response": "A greeting word used to say hi"
}
```

**Response:** `201 Created`
```json
{
  "id": 25,
  "attempt": 10,
  "question": 1,
  "question_text": "What is 'Hello' called in English?",
  "selected_answer": 1,
  "selected_answer_text": "A greeting",
  "text_response": null,
  "is_correct": true,
  "points_earned": 10,
  "answered_at": "2025-12-29T15:16:00Z"
}
```

**UI Required:**
- Answer submission
- Question mark/check indicators
- Save answer (auto-save optional)
- Navigation to next question

---

### 5.5 - Submit Quiz
**Endpoint:** `POST /api/classroom/quiz-attempts/{id}/submit/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 10,
  "quiz": 1,
  "student": 10,
  "student_name": "محمد احمدی",
  "lesson_enrollment": 5,
  "started_at": "2025-12-29T15:15:00Z",
  "submitted_at": "2025-12-29T15:20:00Z",
  "score": 85,
  "total_points": 15,
  "earned_points": 13,
  "passed": true,
  "created_at": "2025-12-29T15:15:00Z"
}
```

**UI Required:**
- Results summary:
  - Score (percentage)
  - Points earned/total
  - Pass/Fail badge
  - Time taken
- Answers review:
  - Question
  - User's answer
  - Correct answer
  - Explanation
- Options:
  - Review answers
  - Retake quiz
  - Share score

---

### 5.6 - Quiz Results
**Endpoint:** `GET /api/classroom/quiz-attempts/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 10,
  "quiz": {
    "id": 1,
    "lesson": 1,
    "lesson_title": "Lesson 1: Greeting",
    "title": "Quick Quiz - Greeting",
    "difficulty": "easy",
    "time_limit_minutes": 5,
    "passing_score": 70,
    "is_active": true
  },
  "student": 10,
  "student_name": "محمد احمدی",
  "lesson_enrollment": 5,
  "started_at": "2025-12-29T15:15:00Z",
  "submitted_at": "2025-12-29T15:20:00Z",
  "score": 85,
  "total_points": 15,
  "earned_points": 13,
  "passed": true,
  "responses": [
    {
      "id": 25,
      "attempt": 10,
      "question": 1,
      "question_text": "What is 'Hello' called in English?",
      "selected_answer": 1,
      "selected_answer_text": "A greeting",
      "text_response": null,
      "is_correct": true,
      "points_earned": 10,
      "answered_at": "2025-12-29T15:16:00Z"
    },
    {
      "id": 26,
      "attempt": 10,
      "question": 2,
      "question_text": "True or False: 'Hello' is informal",
      "selected_answer": 4,
      "selected_answer_text": "True",
      "text_response": null,
      "is_correct": true,
      "points_earned": 5,
      "answered_at": "2025-12-29T15:17:00Z"
    }
  ],
  "created_at": "2025-12-29T15:15:00Z"
}
```

**UI Required:**
- Same as 5.5 results screen

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
      "student_name": "محمد احمدی",
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
          "student": 10,
          "student_name": "محمد احمدی",
          "badge": {
            "id": 1,
            "name": "Perfect Attendance",
            "description": "شرکت در تمام کلاس‌ها",
            "icon": "https://api.com/media/badges/perfect_attendance.png",
            "color": "#FFD700"
          },
          "earned_at": "2025-12-28T10:30:00Z"
        },
        {
          "id": 6,
          "student": 10,
          "student_name": "محمد احمدی",
          "badge": {
            "id": 2,
            "name": "Quiz Master",
            "description": "کسب نمره بالاتر از 85 درصد",
            "icon": "https://api.com/media/badges/quiz_master.png",
            "color": "#4169E1"
          },
          "earned_at": "2025-12-27T10:30:00Z"
        }
      ],
      "last_updated": "2025-12-29T15:30:00Z",
      "created_at": "2025-12-01T00:00:00Z"
    }
  ]
}
```

**UI Required:**
- Course card showing:
  - Course name
  - Lessons attended/total
  - Attendance percentage
  - Average quiz score
  - Points earned
  - Badges grid
- Progress bar for completion
- Detailed stats on tap

---

### 6.2 - Badges/Achievements
**Endpoint:** `GET /api/classroom/progress/{id}/badges/` OR from 6.1 response

**UI Required:**
- Badge grid
- Badge details on tap:
  - Badge icon
  - Name
  - Description
  - When earned
  - How to earn (criteria)
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
      "student": 10,
      "student_name": "محمد احمدی",
      "status": "present",
      "expected_at": "2025-12-29T15:00:00Z",
      "actual_joined_at": "2025-12-29T15:05:00Z",
      "left_at": "2025-12-29T16:00:00Z",
      "minutes_attended": 55,
      "notes": "خوب شرکت کرد",
      "created_at": "2025-12-29T15:00:00Z"
    },
    {
      "id": 2,
      "lesson": 2,
      "lesson_title": "Lesson 2: Colors",
      "student": 10,
      "student_name": "محمد احمدی",
      "status": "absent",
      "expected_at": "2025-12-30T15:00:00Z",
      "actual_joined_at": null,
      "left_at": null,
      "minutes_attended": 0,
      "notes": "غیبت معلوم",
      "created_at": "2025-12-30T15:00:00Z"
    }
  ]
}
```

**UI Required:**
- Attendance calendar/list
- Status indicator (present/absent/late/excused)
- Minutes attended
- Notes
- Attendance percentage
- Export/share attendance

---

## 💬 Section 8: Chat (OPTIONAL - Add Later)

### 8.1 - Class Chat Messages
**Endpoint:** `GET /api/classroom/lessons/{id}/messages/`

**Note:** This requires WebSocket implementation

**UI Required:**
- Message list
- Message input
- Timestamp
- User avatar
- Send button
- Emoji picker (optional)

---

---

# 👨‍🏫 TEACHER APP

## 📚 Section 1: Teacher Authentication & Profile

### 1.1 - Teacher Registration
**Endpoint:** `POST /api/account/register/`

**Request:**
```json
{
  "phone": "+989123456789",
  "password": "SecurePass123!",
  "name": "محمدحسن معلم",
  "role": "teacher"
}
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "username": "teacher_9123456789",
  "phone": "+989123456789",
  "name": "محمدحسن معلم",
  "role": "teacher",
  "message": "OTP sent to your phone"
}
```

---

### 1.2 - Teacher Profile
**Endpoint:** `GET /api/account/profile/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 5,
  "username": "teacher_9123456789",
  "name": "محمدحسن معلم",
  "phone": "+989123456789",
  "email": "teacher@example.com",
  "profile_photo_path": "https://api.com/media/avatars/teacher_5.jpg",
  "selected_avatar": null,
  "bio": "معلم انگلیسی با تجربه 5 سال",
  "gender": "male",
  "birth_date": "1390-05-24",
  "role": "teacher",
  "is_teacher_verified": true,
  "qualifications": "BA in English Language and Literature",
  "languages_taught": "English, German",
  "specialization": "Conversation and Grammar",
  "resume_summary": "5 years of teaching experience...",
  "introduction_video": "https://youtube.com/watch?v=...",
  "hourly_rate": "50.00",
  "experience_years": 5,
  "is_online": true,
  "last_seen": "2025-12-28T10:30:00Z"
}
```

**UI Required:**
- Profile picture
- Name, phone, email
- Qualifications
- Languages taught
- Specialization
- Experience years
- Hourly rate
- Introduction video
- Edit button

---

### 1.3 - Update Teacher Profile
**Endpoint:** `PUT /api/account/profile/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "name": "محمدحسن معلم",
  "email": "teacher@example.com",
  "bio": "معلم انگلیسی با تجربه 5 سال",
  "gender": "male",
  "birth_date": "1390-05-24",
  "qualifications": "BA in English Language and Literature",
  "languages_taught": "English, German",
  "specialization": "Conversation and Grammar",
  "resume_summary": "5 years of teaching experience...",
  "introduction_video": "https://youtube.com/watch?v=...",
  "hourly_rate": "50.00",
  "experience_years": 5
}
```

**Response:** `200 OK` - Same as 1.2

---

## 📖 Section 2: Manage Courses

### 2.1 - List My Courses
**Endpoint:** `GET /api/classroom/courses/`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `ordering=-created_at`

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "teacher": 5,
      "teacher_name": "محمدحسن معلم",
      "title": "English for Kids",
      "description": "یادگیری زبان انگلیسی برای کودکان",
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
- Course list view
- Edit button per course
- Delete button
- View students button
- Create course button

---

### 2.2 - Create Course
**Endpoint:** `POST /api/classroom/courses/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "title": "English for Kids",
  "description": "یادگیری زبان انگلیسی برای کودکان",
  "language": 1,
  "level": 1,
  "max_students": 8,
  "duration_minutes": 60,
  "hourly_rate": "50.00",
  "cover_image": "file_upload",
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "teacher": 5,
  "teacher_name": "محمدحسن معلم",
  "title": "English for Kids",
  "description": "یادگیری زبان انگلیسی برای کودکان",
  "language": 1,
  "language_name": "English",
  "level": 1,
  "level_name": "Beginner",
  "max_students": 8,
  "duration_minutes": 60,
  "hourly_rate": "50.00",
  "cover_image": "https://api.com/media/courses/covers/course_1.jpg",
  "is_active": true,
  "lessons_count": 0,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Form with all fields
- Image upload
- Level/Language dropdowns
- Save/Cancel buttons
- Validation messages

---

### 2.3 - Update Course
**Endpoint:** `PUT /api/classroom/courses/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Request:** Same as 2.2

**Response:** `200 OK` - Updated course object

---

### 2.4 - Delete Course
**Endpoint:** `DELETE /api/classroom/courses/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

**UI Required:**
- Confirmation dialog
- Check for active lessons

---

## 📅 Section 3: Manage Lessons

### 3.1 - List My Lessons
**Endpoint:** `GET /api/classroom/lessons/?course={id}`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `ordering=-scheduled_at`

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
      "started_at": null,
      "ended_at": null,
      "is_recorded": true,
      "recording_url": null,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

**UI Required:**
- Lesson list with cards
- Edit button per lesson
- Delete button
- Start/End lesson buttons (if upcoming/started)
- View details button
- Create lesson button

---

### 3.2 - Create Lesson
**Endpoint:** `POST /api/classroom/lessons/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "course": 1,
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "agora_channel_name": "english-kids-lesson-1",
  "agora_channel_id": "english-kids-lesson-1",
  "is_recorded": true,
  "teacher_notes": "سوالات رایج در این درس"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "course": 1,
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1",
  "status": "scheduled",
  "started_at": null,
  "ended_at": null,
  "duration_minutes": 60,
  "recording_url": null,
  "is_recorded": true,
  "teacher_notes": "سوالات رایج در این درس",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Form with all fields
- DateTime picker for scheduled_at
- Course dropdown
- Toggle for recording
- Save/Cancel buttons

---

### 3.3 - Update Lesson
**Endpoint:** `PUT /api/classroom/lessons/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Request:** Same as 3.2

**Response:** `200 OK` - Updated lesson object

---

### 3.4 - Delete Lesson
**Endpoint:** `DELETE /api/classroom/lessons/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

**UI Required:**
- Confirmation dialog
- Check if lesson started

---

### 3.5 - Add Lesson Materials
**Endpoint:** `POST /api/classroom/lessons/{id}/materials/`

**Headers:** `Authorization: Bearer {token}`

**Request (multipart/form-data):**
```
{
  "lesson": 1,
  "title": "Greeting PDF",
  "material_type": "pdf",
  "file": <binary>,
  "description": "الفبای تلفظ",
  "order": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "lesson": 1,
  "title": "Greeting PDF",
  "material_type": "pdf",
  "file": "https://api.com/media/lesson_materials/greeting.pdf",
  "external_link": null,
  "description": "الفبای تلفظ",
  "order": 1,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- File upload area
- Material type selector
- Title input
- Description textarea
- Order input
- Upload button
- Material list with delete buttons

---

### 3.6 - Update Material
**Endpoint:** `PUT /api/classroom/lessons/{lesson_id}/materials/{material_id}/`

**Response:** `200 OK` - Updated material

---

### 3.7 - Delete Material
**Endpoint:** `DELETE /api/classroom/lessons/{lesson_id}/materials/{material_id}/`

**Response:** `204 No Content`

---

## 🎥 Section 4: Teach Live Class

### 4.1 - Start Lesson
**Endpoint:** `POST /api/classroom/lessons/{id}/start_lesson/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "status": "started",
  "lesson_id": 1,
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1"
}
```

**UI Required:**
- Called when teacher clicks "Start Lesson"
- Loading state
- Success message

---

### 4.2 - End Lesson
**Endpoint:** `POST /api/classroom/lessons/{id}/end_lesson/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "status": "completed",
  "duration_minutes": 65
}
```

**UI Required:**
- Confirmation dialog
- Loading state
- Success message
- Redirect to lesson summary

---

### 4.3 - Lesson Control Screen
**Screen Elements:**
- Video grid (all participants)
- Participant list with:
  - Name
  - Status (online/offline)
  - Mute button
  - Remove button
  - Hand raise indicator
- Teacher controls:
  - Mute all button
  - Record button
  - Whiteboard button
  - Chat button
  - Timer
  - End lesson button
- Whiteboard canvas (same as student 4.3)
- Connection quality indicator

**Flow:**
1. Get lesson details
2. Start lesson (4.1)
3. Generate Agora token
4. Initialize Agora SDK
5. Show control panel
6. Monitor participants
7. End lesson (4.2)

---

### 4.4 - Participant Management
**Features:**
- View all students enrolled
- See who's online
- Mute/unmute individual
- Mute all
- Remove student (temporary or permanent)
- Hand raise notifications

**UI Required:**
- Participant list
- Status icons
- Action buttons per participant
- Hand raise badge with count

---

## 🎯 Section 5: Create & Manage Quizzes

### 5.1 - Create Quiz
**Endpoint:** `POST /api/classroom/quizzes/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "lesson": 1,
  "title": "Quick Quiz - Greeting",
  "description": "کوییز سریع برای بررسی یادگیری",
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "show_before_lesson": false,
  "show_during_lesson": true,
  "show_after_lesson": true,
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "lesson": 1,
  "title": "Quick Quiz - Greeting",
  "description": "کوییز سریع برای بررسی یادگیری",
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "show_before_lesson": false,
  "show_during_lesson": true,
  "show_after_lesson": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Form with all fields
- Difficulty dropdown
- Time limit input
- Passing score slider
- Toggle for show options
- Save button

---

### 5.2 - Add Quiz Questions
**Endpoint:** `POST /api/classroom/quizzes/{quiz_id}/questions/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "question_text": "What is 'Hello' called in English?",
  "question_type": "multiple_choice",
  "points": 10,
  "order": 1,
  "explanation": "Hello is a greeting word used to say hi"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "quiz": 1,
  "question_text": "What is 'Hello' called in English?",
  "question_type": "multiple_choice",
  "points": 10,
  "order": 1,
  "explanation": "Hello is a greeting word used to say hi",
  "answers": [],
  "created_at": "2025-01-01T00:00:00Z"
}
```

**UI Required:**
- Question text input
- Question type selector
- Points input
- Order input
- Explanation textarea
- Add button

---

### 5.3 - Add Answer Options
**Endpoint:** `POST /api/classroom/quizzes/{quiz_id}/questions/{question_id}/answers/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "answer_text": "A greeting",
  "is_correct": true,
  "order": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "question": 1,
  "answer_text": "A greeting",
  "is_correct": true,
  "order": 1
}
```

**UI Required:**
- Answer text input
- Correct/Incorrect toggle
- Order input
- Add button
- List of answers

---

### 5.4 - Edit Quiz & Questions
**Endpoints:** `PUT` versions of 5.1, 5.2, 5.3

**UI Required:**
- Edit buttons per question/answer
- Delete buttons
- Reorder questions (drag & drop)

---

### 5.5 - View Student Quiz Attempts
**Endpoint:** `GET /api/classroom/quiz-attempts/?quiz={id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 8,
  "results": [
    {
      "id": 10,
      "quiz": 1,
      "quiz_title": "Quick Quiz - Greeting",
      "student": 10,
      "student_name": "محمد احمدی",
      "started_at": "2025-12-29T15:15:00Z",
      "submitted_at": "2025-12-29T15:20:00Z",
      "score": 85,
      "earned_points": 13,
      "total_points": 15,
      "passed": true,
      "created_at": "2025-12-29T15:15:00Z"
    }
  ]
}
```

**UI Required:**
- Student quiz results table
- Columns: Student, Score, Points, Passed, Time
- View details button per attempt
- Export results button

---

### 5.6 - View Student Response Details
**Endpoint:** `GET /api/classroom/quiz-attempts/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** Full attempt with responses (same as student 5.6)

**UI Required:**
- All questions and student responses
- Correct/incorrect indicators
- Student vs correct answer comparison
- Points earned per question
- Time taken per question

---

## 📊 Section 6: Monitor & Analytics

### 6.1 - Class Analytics
**Endpoint:** `GET /api/classroom/lessons/{id}/analytics/` (NEW - Optional)

**Headers:** `Authorization: Bearer {token}`

**Would include:**
- Total students enrolled
- Students present
- Students absent
- Attendance rate
- Average quiz score
- Quiz completion rate
- Time spent
- Engagement metrics

**UI Required:**
- Dashboard with charts
- KPI cards
- Attendance chart
- Performance chart

---

### 6.2 - Student Attendance
**Endpoint:** `GET /api/classroom/attendance/?lesson={id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "lesson": 1,
      "lesson_title": "Lesson 1: Greeting",
      "student": 10,
      "student_name": "محمد احمدی",
      "status": "present",
      "expected_at": "2025-12-29T15:00:00Z",
      "actual_joined_at": "2025-12-29T15:05:00Z",
      "left_at": "2025-12-29T16:00:00Z",
      "minutes_attended": 55,
      "notes": "خوب شرکت کرد",
      "created_at": "2025-12-29T15:00:00Z"
    }
  ]
}
```

**UI Required:**
- Attendance table
- Student name
- Status (Present/Absent/Late)
- Time joined/left
- Minutes attended
- Notes
- Edit notes button
- Export attendance

---

### 6.3 - Update Attendance Notes
**Endpoint:** `PATCH /api/classroom/attendance/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "notes": "خوب شرکت کرد"
}
```

**Response:** `200 OK` - Updated attendance

---

## 📋 Section 7: Dashboard & Navigation

### 7.1 - Teacher Dashboard
**Elements:**
- Welcome message
- Quick stats:
  - Total courses
  - Total students
  - Upcoming lessons
  - Pending student requests
- Recent activities:
  - Upcoming lessons (next 7 days)
  - Latest quiz results
  - Recent attendance
- Quick actions:
  - Create course
  - Create lesson
  - View all courses
  - View all lessons

**UI Required:**
- Card-based layout
- Charts/graphs optional
- Navigation menu

---

---

# 🚀 IMPLEMENTATION PRIORITY

## Phase 1: Core Features (Must Have)
1. ✅ User authentication (phone/OTP)
2. ✅ Profile management
3. ✅ Course browse & creation
4. ✅ Lesson creation & management
5. ✅ Agora integration (live class)
6. ✅ Quiz system
7. ✅ Attendance tracking

## Phase 2: Enhanced Features
1. ⏳ Whiteboard (real-time with WebSocket)
2. ⏳ Lesson materials (upload)
3. ⏳ Chat system
4. ⏳ Notifications
5. ⏳ Analytics dashboard

## Phase 3: Advanced Features
1. ⏸️ Payment integration
2. ⏸️ Certificate generation
3. ⏸️ Advanced analytics
4. ⏸️ Mobile app push notifications

---

# 📝 NOTES

- All timestamps in UTC (ISO 8601)
- Phone numbers in E.164 format (+98...)
- Prices in default currency (decimal)
- Jalali date format for birth_date (YYYY-MM-DD)
- JWT token for authorization
- Pagination with default 20 items per page
- All text in both Persian & English where applicable
- Images uploaded as multipart/form-data
- WebSocket for real-time whiteboard & chat (implement later)

---

## How to Use This Document

For each feature, follow this format when asking Copilot:

**Example 1:**
> "Implement Section 1.1 - User Registration in the Student App. Follow the API spec for endpoint, request format, response format, and UI requirements."

**Example 2:**
> "Complete Section 2.2 - Create Course in Teacher App. Include form validation, image upload handling, and error messages."

**Example 3:**
> "Build Section 4 - Teach Live Class. Set up Agora integration, participant management, and teacher controls."

Each section is independent and can be implemented separately!
