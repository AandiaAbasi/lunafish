# 👨‍🏫 Teacher App - API Documentation

## 🎯 Introduction

Complete API specifications for the **Teacher App** with all endpoints and UI requirements.

Each section is independent and can be implemented separately. Just copy the section and ask Copilot!

---

# 👨‍🏫 TEACHER APP

## 👤 Section 1: Teacher Profile & Setup

### 1.1 - Teacher Profile
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
  "profile_photo_path": "https://api.com/media/avatars/teacher_1.jpg",
  "selected_avatar": {
    "id": 3,
    "image": "https://api.com/media/avatars/templates/cat_avatar.png"
  },
  "bio": "معلم خصوصی زبان انگلیسی",
  "gender": "male",
  "birth_date": "1390-05-24",
  "role": "teacher",
  "is_online": true,
  "last_seen": "2025-12-28T10:30:00Z",
  "total_students": 45,
  "total_courses": 3,
  "rating": 4.8
}
```

**UI Required:**
- Profile picture with avatar selector
- Name, phone, email
- Bio
- Teacher rating/reviews count
- Total courses and students
- Online status

---

### 1.2 - Update Teacher Profile
**Endpoint:** `PUT /api/account/profile/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "name": "محمدحسن معلم",
  "email": "teacher@example.com",
  "bio": "معلم خصوصی زبان انگلیسی با 10 سال تجربه",
  "gender": "male",
  "birth_date": "1390-05-24",
  "selected_avatar": 3
}
```

**Response:** `200 OK` - Same as 1.1

**UI Required:**
- Edit profile form
- Save/Cancel buttons
- Photo upload

---

## 📖 Section 2: Create & Manage Courses

### 2.1 - Create Course
**Endpoint:** `POST /api/classroom/courses/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "title": "English for Kids",
  "description": "یادگیری زبان انگلیسی برای کودکان با روش‌های نوین",
  "language": 1,
  "level": 1,
  "max_students": 8,
  "duration_minutes": 60,
  "hourly_rate": "50.00",
  "cover_image": "<base64_image_data>"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "English for Kids",
  "description": "یادگیری زبان انگلیسی برای کودکان با روش‌های نوین",
  "teacher": 5,
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
  "lessons_count": 0,
  "created_at": "2025-12-28T10:30:00Z"
}
```

**UI Required:**
- Course form with:
  - Title input
  - Description textarea
  - Language dropdown
  - Level dropdown
  - Max students input
  - Duration input
  - Hourly rate input
  - Cover image upload
- Save/Cancel buttons
- Validation messages

---

### 2.2 - List My Courses
**Endpoint:** `GET /api/classroom/courses/?teacher=<my_id>`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `page=1` - Pagination
- `search=english` - Search

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "title": "English for Kids",
      "description": "یادگیری زبان انگلیسی برای کودکان",
      "teacher": 5,
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
      "created_at": "2025-12-01T00:00:00Z"
    }
  ]
}
```

**UI Required:**
- Course list/grid
- Search bar
- Create button
- Edit/Delete buttons for each
- View analytics button

---

### 2.3 - Update Course
**Endpoint:** `PUT /api/classroom/courses/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Request:** Same as 2.1

**Response:** `200 OK` - Same as 2.1

---

### 2.4 - Delete Course
**Endpoint:** `DELETE /api/classroom/courses/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

**UI Required:**
- Delete confirmation dialog
- Warning about deleting lessons

---

### 2.5 - Course Analytics
**Endpoint:** `GET /api/classroom/courses/{id}/analytics/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "course_id": 1,
  "course_title": "English for Kids",
  "total_enrollments": 45,
  "active_students": 42,
  "total_lessons": 12,
  "completed_lessons": 10,
  "average_attendance_rate": "92.50",
  "average_quiz_score": "87.30"
}
```

**UI Required:**
- Course stats cards
- Enrollment count
- Active students
- Attendance percentage
- Average quiz score

---

## 📅 Section 3: Create & Manage Lessons

### 3.1 - Create Lesson
**Endpoint:** `POST /api/classroom/lessons/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "course": 1,
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "teacher_notes": "سوالات رایج در این درس"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "course": 1,
  "course_title": "English for Kids",
  "teacher": 5,
  "teacher_name": "محمدحسن معلم",
  "title": "Lesson 1: Greeting",
  "description": "در این درس یادگیری سلام و علیک",
  "scheduled_at": "2025-12-29T15:00:00Z",
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1",
  "status": "scheduled",
  "teacher_notes": "سوالات رایج در این درس",
  "is_recorded": false
}
```

**UI Required:**
- Lesson form with:
  - Course dropdown
  - Title input
  - Description textarea
  - Date/time picker
  - Teacher notes textarea
- Save/Cancel buttons
- Validation

---

### 3.2 - List My Lessons
**Endpoint:** `GET /api/classroom/lessons/?teacher=<my_id>`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `status=scheduled,in_progress,completed`
- `ordering=-scheduled_at`
- `page=1`

**Response:** `200 OK`
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "course": 1,
      "course_title": "English for Kids",
      "teacher": 5,
      "teacher_name": "محمدحسن معلم",
      "title": "Lesson 1: Greeting",
      "scheduled_at": "2025-12-29T15:00:00Z",
      "status": "scheduled",
      "is_recorded": false,
      "recording_url": null,
      "enrolled_count": 7
    }
  ]
}
```

**UI Required:**
- Lesson list with status badges
- Date/time display
- Enrolled students count
- Edit/Delete/View buttons

---

### 3.3 - Update Lesson
**Endpoint:** `PUT /api/classroom/lessons/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Request:** Same as 3.1

**Response:** `200 OK` - Same as 3.1

---

### 3.4 - Add Lesson Material
**Endpoint:** `POST /api/classroom/lesson-materials/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "lesson": 1,
  "title": "Greeting PDF",
  "material_type": "pdf",
  "file": "<file_binary>",
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
  "description": "الفبای تلفظ",
  "order": 1
}
```

**UI Required:**
- Material upload form
- File type selector (PDF, Video, Image, Link)
- Title and description inputs
- Order/priority selector
- Upload progress indicator
- Save button

---

### 3.5 - List Lesson Materials
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
    }
  ]
}
```

---

### 3.6 - Delete Lesson Material
**Endpoint:** `DELETE /api/classroom/lesson-materials/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `204 No Content`

---

## 📺 Section 4: Teach Live Class

### 4.1 - Start Lesson
**Endpoint:** `POST /api/classroom/lessons/{id}/start/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "in_progress",
  "started_at": "2025-12-29T15:05:00Z",
  "agora_channel_id": "english-kids-lesson-1",
  "agora_channel_name": "english-kids-lesson-1"
}
```

---

### 4.2 - Live Class Interface
**Endpoint:** First call `/api/classroom/lessons/{id}/` to get details, then generate token

**UI Elements:**
- Main video grid (students + teacher self)
- Video on/off toggle
- Microphone on/off toggle
- Speaker list with names
- Mute individual students button
- Chat button
- Whiteboard button
- End class button
- Timer showing lesson duration
- Enrolled students count
- Connection quality indicator
- Recording status

**Flow:**
1. Start lesson (4.1)
2. Get Agora channel info
3. Generate token with "publisher" privilege
4. Initialize Agora SDK as publisher
5. Connect to channel
6. Display active students
7. Manage whiteboard & chat

---

### 4.3 - Get Agora Token
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
  "user": 5,
  "token": "00750f8db7e542e8b7a7d80c98f4a93e19cAAgDHKzKM0qCjqxQFc2FS9nXJc0VJCg7YkzEkuNvzTQHnEpgKXAgAAAAAKEjJHwQEA3QEAAQHdAQABHx+DXwEA3QEAAQHdAQA=",
  "privilege": "publisher",
  "expires_at": "2025-12-29T16:05:00Z",
  "is_valid": true
}
```

---

### 4.4 - Manage Whiteboard
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
- Canvas for drawing/writing
- Drawing tools (pen, eraser, shapes, text)
- Color picker
- Line width selector
- Clear/Delete button
- Undo/Redo buttons
- Lock button (prevent students from drawing)
- Real-time sync via WebSocket

---

### 4.5 - End Lesson
**Endpoint:** `POST /api/classroom/lessons/{id}/end/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "status": "completed",
  "started_at": "2025-12-29T15:05:00Z",
  "ended_at": "2025-12-29T16:05:00Z",
  "duration_minutes": 60,
  "attendance_marked": true
}
```

**UI Required:**
- End confirmation dialog
- Attendance summary
- Save recordings button
- Option to view student attendance

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
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "lesson": 1,
  "lesson_title": "Lesson 1: Greeting",
  "title": "Quick Quiz - Greeting",
  "difficulty": "easy",
  "time_limit_minutes": 5,
  "passing_score": 70,
  "is_active": true,
  "total_questions": 0
}
```

**UI Required:**
- Quiz form with:
  - Lesson selector
  - Title input
  - Difficulty dropdown
  - Time limit input
  - Passing score input
  - Active toggle
- Save/Cancel buttons

---

### 5.2 - Add Quiz Question
**Endpoint:** `POST /api/classroom/quiz-questions/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "quiz": 1,
  "question_text": "What is 'Hello' called in English?",
  "question_type": "multiple_choice",
  "points": 10,
  "explanation": "Hello is a greeting word"
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
  "explanation": "Hello is a greeting word",
  "order": 1
}
```

---

### 5.3 - Add Quiz Answer
**Endpoint:** `POST /api/classroom/quiz-answers/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "question": 1,
  "answer_text": "A greeting",
  "is_correct": true
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
- Question form with:
  - Quiz selector
  - Question text textarea
  - Question type dropdown
  - Points input
  - Explanation textarea
- Add answer form with:
  - Answer text input
  - Is correct toggle
  - Order input
- Save/Delete buttons for each

---

### 5.4 - List My Quizzes
**Endpoint:** `GET /api/classroom/quizzes/?lesson__course__teacher=<my_id>`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "lesson": 1,
      "lesson_title": "Lesson 1: Greeting",
      "title": "Quick Quiz - Greeting",
      "difficulty": "easy",
      "time_limit_minutes": 5,
      "passing_score": 70,
      "is_active": true,
      "total_questions": 5
    }
  ]
}
```

---

### 5.5 - Quiz Results
**Endpoint:** `GET /api/classroom/quizzes/{id}/attempts/`

**Headers:** `Authorization: Bearer {token}`

**Query Params:**
- `page=1` - Pagination

**Response:** `200 OK`
```json
{
  "count": 45,
  "results": [
    {
      "id": 10,
      "quiz": 1,
      "quiz_title": "Quick Quiz - Greeting",
      "student": 10,
      "student_name": "محمد احمدی",
      "score": 85,
      "total_points": 15,
      "earned_points": 13,
      "passed": true,
      "started_at": "2025-12-29T15:15:00Z",
      "submitted_at": "2025-12-29T15:20:00Z"
    }
  ]
}
```

**UI Required:**
- Results table with:
  - Student name
  - Score
  - Pass/Fail status
  - Date/time
- View details button for each
- Export to CSV button
- Filter by pass/fail

---

## 📊 Section 6: Analytics & Dashboard

### 6.1 - Teacher Dashboard
**Endpoint:** `GET /api/classroom/analytics/teacher-dashboard/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "total_students": 45,
  "total_courses": 3,
  "total_lessons": 12,
  "average_attendance_rate": "92.50",
  "average_quiz_score": "87.30",
  "upcoming_lessons": 5,
  "recent_enrollments": [
    {
      "id": 1,
      "student_name": "محمد احمدی",
      "course_title": "English for Kids",
      "enrolled_at": "2025-12-28T10:30:00Z"
    }
  ]
}
```

**UI Required:**
- Dashboard cards with KPIs
- Charts for attendance trends
- Recent enrollments list
- Upcoming lessons list
- Quick action buttons

---

### 6.2 - Course Analytics Detailed
**Endpoint:** `GET /api/classroom/courses/{id}/analytics/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "course_id": 1,
  "course_title": "English for Kids",
  "total_enrollments": 45,
  "active_students": 42,
  "total_lessons": 12,
  "completed_lessons": 10,
  "average_attendance_rate": "92.50",
  "average_quiz_score": "87.30",
  "lesson_wise_attendance": [
    {
      "lesson_id": 1,
      "lesson_title": "Lesson 1: Greeting",
      "attendance_rate": "95.00",
      "students_present": 42,
      "students_absent": 3
    }
  ]
}
```

**UI Required:**
- Course overview stats
- Attendance percentage chart
- Quiz scores distribution
- Lesson-by-lesson breakdown
- Student progress list

---

### 6.3 - Student Progress Report
**Endpoint:** `GET /api/classroom/progress/?course={id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 45,
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
      "badges_earned": 2
    }
  ]
}
```

**UI Required:**
- Student list with progress
- Attendance percentage for each
- Quiz scores
- Points earned
- Badges earned
- Click for detailed student report

---

## 🎖️ Section 7: Badges & Achievements

### 7.1 - List Available Badges
**Endpoint:** `GET /api/classroom/badges/`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "name": "Perfect Attendance",
      "description": "حاضری 100 درصد",
      "icon": "https://api.com/media/badges/perfect_attendance.png",
      "criteria": "attendance_rate_100",
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Quiz Master",
      "description": "تمام تست‌ها را با نمره 100 پاس کردن",
      "icon": "https://api.com/media/badges/quiz_master.png",
      "criteria": "perfect_quiz_score",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### 7.2 - Award Badge to Student
**Endpoint:** `POST /api/classroom/student-badges/`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "student": 10,
  "badge": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "student": 10,
  "student_name": "محمد احمدی",
  "badge": {
    "id": 1,
    "name": "Perfect Attendance",
    "icon": "https://api.com/media/badges/perfect_attendance.png"
  },
  "earned_at": "2025-12-28T10:30:00Z"
}
```

**UI Required:**
- Badges list
- Award badge button for each
- Student selector
- Confirmation dialog
- Student badges history view

---

### 7.3 - Student Badges
**Endpoint:** `GET /api/classroom/progress/{id}/`

**Headers:** `Authorization: Bearer {token}`

**Response:** See Section 6.3 - includes badges array

---

# 🚀 Implementation Priority

## Phase 1: Core (Must Have)
- [ ] Section 1: Teacher Profile
- [ ] Section 2: Create & Manage Courses
- [ ] Section 3: Create & Manage Lessons
- [ ] Section 5: Create Quizzes
- [ ] Section 6: Analytics Dashboard

## Phase 2: Enhanced
- [ ] Section 4: Live Class (Agora)
- [ ] Whiteboard (WebSocket)
- [ ] Quiz result analytics

## Phase 3: Advanced
- [ ] Advanced analytics
- [ ] Badge system
- [ ] Student communication

---

# 📝 NOTES

- All timestamps in UTC (ISO 8601)
- Phone numbers in E.164 format (+98...)
- Prices in default currency (decimal)
- Jalali date format for birth_date (YYYY-MM-DD)
- JWT token for authorization
- Only teachers can see their own courses/lessons
- Pagination with default 20 items per page
- File uploads use form-data encoding

---

# How to Use

1. **Open this file:** TEACHER_APP_API_SPECS.md
2. **Choose a section:** e.g., "Section 2: Create & Manage Courses"
3. **Copy entire section**
4. **Ask Copilot:** "Implement Teacher App Section 2 with this API spec: [paste]"
5. **Get working code!** ✅

---

**Ready to build? 🚀**

Start with: **"Implement TEACHER APP - Section 1: Teacher Profile & Setup"**
