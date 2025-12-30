# Teacher API Documentation

## Overview
APIs available to teacher users (role: `teacher`)

---

## Time Slot Management APIs

### 1. Create Availability Slots (Single)
Create a single time slot for teaching availability.

**Method:** `POST`  
**URL:** `/api/teacher/availability/create/`  
**Permission:** `IsAuthenticated` (Teachers only)  
**Role:** `teacher`

**Request Body:**
```json
{
  "date": "1403/01/15",
  "start_time": "09:00",
  "end_time": "10:00",
  "price": 50000,
  "discount_price": 40000,
  "notes": "Online via Zoom - English Speaking"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date | string | Yes | Date in YYYY/MM/DD Jalali format |
| start_time | string | Yes | Start time in HH:MM format |
| end_time | string | Yes | End time in HH:MM format |
| price | number | Yes | Regular price per session |
| discount_price | number | No | Discounted price (optional) |
| notes | string | No | Additional notes |

**Response:** `201 Created`
```json
{
  "data": {
    "id": 1,
    "teacher": 5,
    "date": "1403/01/15",
    "start_time": "09:00",
    "end_time": "10:00",
    "price": 50000,
    "discount_price": 40000,
    "is_available": true,
    "is_booked": false,
    "notes": "Online via Zoom",
    "created_at": "2025-01-01T10:00:00Z"
  },
  "message": "بازه زمانی با موفقیت ایجاد شد"
}
```

**Error Responses:**
- `400`: Invalid date format or time values
- `403`: User is not a teacher

---

### 2. Create Availability Slots (Bulk with Date Range)
Create multiple time slots automatically for a date range.

**Method:** `POST`  
**URL:** `/api/teacher/availability/bulk-create/`  
**Permission:** `IsAuthenticated` (Teachers only)

**Request Body:**
```json
{
  "start_date": "1403/01/01",
  "end_date": "1403/01/10",
  "daily_start_time": "09:00",
  "daily_end_time": "17:00",
  "session_duration": 30,
  "break_duration": 10,
  "price": 50000,
  "discount_price": 40000,
  "notes": "Online classes via Zoom"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| start_date | string | Yes | Start date (YYYY/MM/DD Jalali) |
| end_date | string | Yes | End date (YYYY/MM/DD Jalali) |
| daily_start_time | string | Yes | Daily start time (HH:MM) |
| daily_end_time | string | Yes | Daily end time (HH:MM) |
| session_duration | integer | No | Session duration in minutes (default: 30, min: 5) |
| break_duration | integer | No | Break between sessions in minutes (default: 10, min: 0) |
| price | number | Yes | Price per session |
| discount_price | number | No | Discounted price |
| notes | string | No | Notes about slots |

**Response:** `201 Created`
```json
{
  "count": 20,
  "message": "بازه‌های زمانی با موفقیت ایجاد شدند"
}
```

**Example:** 
- start_date: 1403/01/01, end_date: 1403/01/03
- daily_start_time: 09:00, daily_end_time: 12:00
- session_duration: 30, break_duration: 10
- Creates: 9:00-9:30, 9:40-10:10, 10:20-10:50, 11:00-11:30, 11:40-12:10 for each day

---

### 3. View My Availability Slots
List all teacher's availability slots with filters.

**Method:** `GET`  
**URL:** `/api/teacher/availability/`  
**Permission:** `IsAuthenticated` (Teachers see own, students see all available)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| start_date | string | No | Filter from date (YYYY/MM/DD Jalali) |
| end_date | string | No | Filter to date (YYYY/MM/DD Jalali) |
| date | string | No | Filter by specific date |
| is_available | boolean | No | Filter available slots |
| is_booked | boolean | No | Filter booked slots |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20) |

**Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher": 5,
      "date": "1403/01/15",
      "start_time": "09:00",
      "end_time": "10:00",
      "price": 50000,
      "discount_price": 40000,
      "is_available": true,
      "is_booked": false,
      "notes": "Online via Zoom",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

### 4. View Availability Slot Details
Get full details of a specific time slot.

**Method:** `GET`  
**URL:** `/api/teacher/availability/{id}/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Availability slot ID |

**Response:** `200 OK`
```json
{
  "data": {
    "id": 1,
    "teacher": 5,
    "date": "1403/01/15",
    "start_time": "09:00",
    "end_time": "10:00",
    "price": 50000,
    "discount_price": 40000,
    "is_available": true,
    "is_booked": false,
    "notes": "Online via Zoom",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  },
  "message": "جزئیات بازه زمانی با موفقیت دریافت شد"
}
```

**Error Responses:**
- `403`: User is not slot owner
- `404`: Slot not found

---

### 5. Update Availability Slot
Modify an existing time slot (cannot update booked slots).

**Method:** `PATCH`  
**URL:** `/api/teacher/availability/{id}/update/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Availability slot ID |

**Request Body (all fields optional):**
```json
{
  "date": "1403/01/20",
  "start_time": "10:00",
  "end_time": "11:00",
  "price": 55000,
  "discount_price": 45000,
  "notes": "Updated: Online via Google Meet"
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "id": 1,
    "teacher": 5,
    "date": "1403/01/20",
    "start_time": "10:00",
    "end_time": "11:00",
    "price": 55000,
    "discount_price": 45000,
    "is_available": true,
    "is_booked": false,
    "notes": "Updated: Online via Google Meet",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-06T15:00:00Z"
  },
  "message": "بازه زمانی با موفقیت به‌روزرسانی شد"
}
```

**Error Responses:**
- `400`: Cannot update booked slot
- `403`: User is not slot owner
- `404`: Slot not found

---

### 6. Delete Availability Slot
Remove a time slot (cannot delete booked slots).

**Method:** `DELETE`  
**URL:** `/api/teacher/availability/{id}/delete/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Availability slot ID |

**Request Body:** Empty

**Response:** `204 No Content`
```json
{
  "message": "بازه زمانی با موفقیت حذف شد"
}
```

**Error Responses:**
- `400`: Cannot delete booked slot
- `403`: User is not slot owner
- `404`: Slot not found

---

## Class Booking Management APIs

### 7. View Bookings for My Classes
Get list of all student bookings for teacher's classes.

**Method:** `GET`  
**URL:** `/api/teacher/bookings/`  
**Permission:** `IsAuthenticated` (Teachers only)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter: `reserved`, `completed`, `cancelled`, `no_show` |
| subject | integer | No | Filter by subject ID |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20) |

**Response:** `200 OK`
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "teacher": 5,
      "student": 2,
      "student_name": "Ali Hosseini",
      "availability": 1,
      "subject": 5,
      "subject_title": "English Beginner",
      "status": "reserved",
      "price": 50000,
      "discount_amount": 0,
      "final_price": 40000,
      "created_at": "2025-01-05T14:30:00Z",
      "updated_at": "2025-01-05T14:30:00Z"
    }
  ]
}
```

---

### 8. Update Booking Status
Change status of a student booking (completed, cancelled, no_show).

**Method:** `PATCH`  
**URL:** `/api/class-booking/{id}/status/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Booking ID |

**Request Body:**
```json
{
  "status": "completed"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | Yes | One of: `reserved`, `completed`, `cancelled`, `no_show` |

**Response:** `200 OK`
```json
{
  "data": {
    "id": 10,
    "teacher": 5,
    "student": 2,
    "availability": 1,
    "subject": 5,
    "status": "completed",
    "price": 50000,
    "discount_amount": 0,
    "final_price": 40000,
    "created_at": "2025-01-05T14:30:00Z",
    "updated_at": "2025-01-06T16:00:00Z"
  },
  "message": "وضعیت رزرو با موفقیت به‌روزرسانی شد"
}
```

**Error Responses:**
- `400`: Invalid status
- `403`: Permission denied (not booking owner)
- `404`: Booking not found

---

## Teaching Subject (Class) Management APIs

### 9. Create Teaching Subject
Create a new class/subject.

**Method:** `POST`  
**URL:** `/api/teaching-subjects/create/`  
**Permission:** `IsAuthenticated` (Teachers only)

**Request Body (multipart/form-data):**
```json
{
  "title": "English Beginner - Alphabet",
  "description": "Learn basic English alphabet and sounds",
  "cover_image": "<binary image data>",
  "demo_video": "https://youtube.com/watch?v=...",
  "min_age": 5,
  "max_age": 12,
  "level": "beginner",
  "is_active": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Subject title (max 255 chars) |
| description | string | No | Description of subject |
| cover_image | file | No | Image file (JPG/PNG) |
| demo_video | string | No | YouTube/video URL |
| min_age | integer | No | Minimum age requirement |
| max_age | integer | No | Maximum age requirement |
| level | string | No | One of: `beginner`, `intermediate`, `advanced` |
| is_active | boolean | No | Whether subject is published (default: true) |

**Response:** `201 Created`
```json
{
  "id": 5,
  "teacher": 3,
  "title": "English Beginner - Alphabet",
  "description": "Learn basic English...",
  "cover_image": "http://...",
  "demo_video": "https://...",
  "min_age": 5,
  "max_age": 12,
  "level": "beginner",
  "is_active": true,
  "created_at": "2025-01-01T10:00:00Z"
}
```

**Error Responses:**
- `400`: Invalid data
- `403`: Only teachers can create subjects

---

### 10. View My Teaching Subjects
Get list of all teacher's classes/subjects.

**Method:** `GET`  
**URL:** `/api/teaching-subjects/`  
**Permission:** `IsAuthenticated` (Teachers see own, filtered by role)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| level | string | No | Filter: `beginner`, `intermediate`, `advanced` |
| is_active | boolean | No | Filter by active status |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20) |

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": 5,
      "teacher": 3,
      "title": "English Beginner - Alphabet",
      "description": "Learn basic English...",
      "cover_image": "http://...",
      "demo_video": "https://...",
      "min_age": 5,
      "max_age": 12,
      "level": "beginner",
      "is_active": true,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

### 11. View Teaching Subject Details
Get full details of a specific subject.

**Method:** `GET`  
**URL:** `/api/teaching-subjects/{id}/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Subject ID |

**Response:** `200 OK`
```json
{
  "id": 5,
  "teacher": 3,
  "title": "English Beginner - Alphabet",
  "description": "Learn basic English...",
  "cover_image": "http://...",
  "demo_video": "https://...",
  "min_age": 5,
  "max_age": 12,
  "level": "beginner",
  "is_active": true,
  "created_at": "2025-01-01T10:00:00Z"
}
```

**Error Responses:**
- `404`: Subject not found

---

### 12. Update Teaching Subject
Edit an existing subject.

**Method:** `POST`  
**URL:** `/api/teaching-subjects/{id}/update/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Subject ID |

**Request Body (all fields optional, multipart/form-data):**
```json
{
  "title": "English Intermediate - Grammar",
  "description": "Learn English grammar rules",
  "cover_image": "<binary image data>",
  "demo_video": "https://youtube.com/watch?v=...",
  "min_age": 10,
  "max_age": 18,
  "level": "intermediate",
  "is_active": true
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "id": 5,
    "teacher": 3,
    "title": "English Intermediate - Grammar",
    "description": "Learn English grammar rules",
    "cover_image": "http://...",
    "demo_video": "https://...",
    "min_age": 10,
    "max_age": 18,
    "level": "intermediate",
    "is_active": true,
    "created_at": "2025-01-01T10:00:00Z"
  },
  "message": "موضوع تدریسی با موفقیت ویرایش شد"
}
```

**Error Responses:**
- `400`: Invalid data
- `403`: Permission denied (not subject owner)
- `404`: Subject not found

---

### 13. Delete Teaching Subject
Remove a subject.

**Method:** `POST`  
**URL:** `/api/teaching-subjects/{id}/delete/`  
**Permission:** `IsAuthenticated` (Teacher owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Subject ID |

**Request Body:** Empty

**Response:** `204 No Content`
```json
{
  "message": "موضوع تدریسی با موفقیت حذف شد"
}
```

**Error Responses:**
- `403`: Permission denied
- `404`: Subject not found

---

## Exam/Question Management APIs

### 14. Create Question (Field)
Create a new exam question. Supports three types: input (typing), checkbox, radioButton.

**Method:** `POST`  
**URL:** `/api/exercise/field/create/`  
**Permission:** `IsAuthenticated` (Teachers only)

**Request Body:**
```json
{
  "title": "What is the capital of France?",
  "type": "radioButton",
  "is_required": 1,
  "guide": "Choose the correct answer",
  "des": "This is about European capitals",
  "sort": 0,
  "correct_answer": "Paris",
  "details": [
    {
      "title": "London",
      "is_correct": 0,
      "guide": "No, this is UK"
    },
    {
      "title": "Paris",
      "is_correct": 1,
      "guide": "Correct!"
    },
    {
      "title": "Berlin",
      "is_correct": 0,
      "guide": "No, this is Germany"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Question text |
| type | string | Yes | One of: `input`, `checkbox`, `radioButton` |
| is_required | integer | No | 0 or 1 - Whether answer required |
| guide | string | No | Question hint/guide |
| des | string | No | Question description |
| sort | integer | No | Sort order (default: 0) |
| image_path | string | No | URL to question image |
| audio_path | string | No | URL to question audio |
| video_path | string | No | URL to question video |
| correct_answer | string | No | For typing (input) questions: correct answer text |
| details | array | No | For choice questions: answer options |
| - title | string | Yes | Option text |
| - is_correct | integer | Yes | 1 if correct, 0 if incorrect |
| - image_path | string | No | Option image URL |
| - guide | string | No | Explanation for this option |

**Response:** `201 Created`
```json
{
  "data": {
    "id": 1,
    "title": "What is the capital of France?",
    "type": "radioButton",
    "is_required": 1,
    "guide": "Choose the correct answer",
    "des": "This is about European capitals",
    "sort": 0,
    "correct_answer": "Paris",
    "image_path": null,
    "audio_path": null,
    "video_path": null,
    "details": [
      {
        "id": 1,
        "title": "London",
        "is_correct": 0,
        "guide": "No, this is UK",
        "sort": 0
      },
      {
        "id": 2,
        "title": "Paris",
        "is_correct": 1,
        "guide": "Correct!",
        "sort": 1
      },
      {
        "id": 3,
        "title": "Berlin",
        "is_correct": 0,
        "guide": "No, this is Germany",
        "sort": 2
      }
    ]
  },
  "message": "سؤال با موفقیت ایجاد شد"
}
```

**For Typing Question Example:**
```json
{
  "title": "Write the English word for the image",
  "type": "input",
  "is_required": 1,
  "guide": "Type the English word",
  "correct_answer": "apple",
  "image_path": "http://example.com/apple.jpg"
}
```

**Error Responses:**
- `400`: Invalid data
- `403`: Only teachers can create questions

---

### 15. Create Exam (Add Questions to Subject)
Link questions to a teaching subject to create an exam.

**Method:** `POST`  
**URL:** `/api/exercise/exam/create/`  
**Permission:** `IsAuthenticated` (Teachers of the subject only)

**Request Body:**
```json
{
  "teachingsubject_id": 5,
  "questions": [
    {
      "field_id": 1,
      "step": 0,
      "sort": 0,
      "type": "radioButton"
    },
    {
      "field_id": 2,
      "step": 0,
      "sort": 1,
      "type": "input"
    },
    {
      "field_id": 3,
      "step": 1,
      "sort": 0,
      "type": "checkbox"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| teachingsubject_id | integer | Yes | ID of class/subject |
| questions | array | Yes | List of questions to add |
| - field_id | integer | Yes | Question ID |
| - step | integer | Yes | Question stage/group (0, 1, 2, ...) |
| - sort | integer | Yes | Order within step (0, 1, 2, ...) |
| - type | string | No | Question type (from Field model) |
| - is_conditional | boolean | No | Is this conditional question |

**Response:** `201 Created`
```json
{
  "id": 5,
  "subject": {
    "id": 5,
    "title": "English Beginner - Alphabet"
  },
  "questions": [
    {
      "id": 10,
      "field_id": 1,
      "field_title": "What is the capital of France?",
      "step": 0,
      "sort": 0
    },
    {
      "id": 11,
      "field_id": 2,
      "field_title": "Write the English word for...",
      "step": 0,
      "sort": 1
    },
    {
      "id": 12,
      "field_id": 3,
      "field_title": "Choose all correct options",
      "step": 1,
      "sort": 0
    }
  ],
  "total_questions": 3,
  "message": "آزمون با موفقیت ایجاد شد"
}
```

**Error Responses:**
- `400`: Invalid data or non-existent subject
- `403`: Can only create exam for own subject
- `404`: Subject not found

---

## Exam Results & Student Answers APIs

### 16. View Exam Results for My Subjects
Get list of all exam attempts from students in teacher's subjects.

**Method:** `GET`  
**URL:** `/api/exercise/results/`  
**Permission:** `IsAuthenticated` (Teachers see their subject results only)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| subject_id | integer | No | Filter by subject ID |
| page | integer | No | Page number |
| page_size | integer | No | Items per page |

**Response:** `200 OK`
```json
{
  "count": 15,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 100,
      "user": 2,
      "user_name": "Ali Hosseini",
      "teachingsubject": 5,
      "subject_title": "English Beginner",
      "score": 2,
      "correct": 2,
      "incorrect": 1,
      "total_questions": 3,
      "percentage": 66.67,
      "created_at": "2025-01-06T15:00:00Z"
    },
    {
      "id": 101,
      "user": 3,
      "user_name": "Fatima Ahmadi",
      "teachingsubject": 5,
      "subject_title": "English Beginner",
      "score": 3,
      "correct": 3,
      "incorrect": 0,
      "total_questions": 3,
      "percentage": 100.0,
      "created_at": "2025-01-06T16:30:00Z"
    }
  ]
}
```

---

### 17. View Student's Specific Exam Attempt
Get detailed results of a student's exam attempt with all answers and grading.

**Method:** `GET`  
**URL:** `/api/exercise/results/{attempt_id}/`  
**Permission:** `IsAuthenticated` (Teacher of subject only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| attempt_id | integer | Exam attempt ID |

**Response:** `200 OK`
```json
{
  "id": 100,
  "user": 2,
  "user_name": "Ali Hosseini",
  "teachingsubject": 5,
  "subject_title": "English Beginner",
  "score": 2,
  "correct": 2,
  "incorrect": 1,
  "total_questions": 3,
  "percentage": 66.67,
  "details": [
    {
      "id": 200,
      "field_id": 1,
      "field_title": "What is the capital of France?",
      "student_answer": "London",
      "correct_answer": "Paris",
      "is_correct": false,
      "score": 0
    },
    {
      "id": 201,
      "field_id": 2,
      "field_title": "Write the English word",
      "student_answer": "apple",
      "correct_answer": "apple",
      "is_correct": true,
      "score": 1
    },
    {
      "id": 202,
      "field_id": 3,
      "field_title": "Choose all correct options",
      "student_answer": "Option B, Option C",
      "correct_answer": "Option B, Option C, Option D",
      "is_correct": true,
      "score": 1
    }
  ],
  "created_at": "2025-01-06T15:00:00Z"
}
```

**Error Responses:**
- `403`: Teacher cannot view this attempt (not their subject)
- `404`: Attempt not found

---

## Profile & Account APIs

### 18. Fetch Teacher Profile
Get current logged-in teacher's profile data.

**Method:** `GET`  
**URL:** `/api/fetch-user/`  
**Permission:** `IsAuthenticated`

**Response:** `200 OK`
```json
{
  "id": 3,
  "username": "teacher1",
  "email": "teacher@example.com",
  "phone": "09101234567",
  "first_name": "Mohammad",
  "last_name": "Ahmadi",
  "display_name": "Mohammad",
  "role": "teacher",
  "bio": "English teacher with 5 years experience",
  "gender": "m",
  "birth_date": "1380-05-15",
  "avatar": "http://...",
  "selected_avatar": 1,
  "is_phone_verified": true,
  "is_email_verified": true,
  "email_verified_at": "2025-01-01T10:00:00Z",
  "phone_verified_at": "2025-01-01T09:00:00Z",
  "is_teacher": true,
  "teacher_verified": true,
  "educational_qualifications": "BA in English",
  "languages_taught": "English, Persian",
  "specialization": "Grammar and Conversation",
  "resume_summary": "5 years teaching experience",
  "introduction_video_url": "https://youtube.com/...",
  "hourly_rate": 50000,
  "available_times": {...},
  "years_of_experience": 5
}
```

---

### 19. Complete/Update Teacher Profile
Set up or update teacher profile with professional information.

**Method:** `POST`  
**URL:** `/api/complete-teacher-profile/`  
**Permission:** `IsAuthenticated` (Teachers only)

**Request Body:**
```json
{
  "first_name": "Mohammad",
  "last_name": "Ahmadi",
  "display_name": "Mohammad",
  "bio": "English teacher with 5 years experience",
  "gender": "m",
  "birth_date": "1380-05-15",
  "educational_qualifications": "BA in English from Tehran University",
  "languages_taught": "English, Persian",
  "specialization": "Grammar and Conversation",
  "resume_summary": "I have 5 years of teaching experience in English language.",
  "introduction_video_url": "https://youtube.com/watch?v=...",
  "hourly_rate": 50000,
  "years_of_experience": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| first_name | string | No | First name |
| last_name | string | No | Last name |
| display_name | string | No | Display name |
| bio | string | No | Biography |
| gender | string | No | One of: `m`, `f`, `prefer_not_to_say` |
| birth_date | string | No | Date in YYYY-MM-DD Jalali format |
| educational_qualifications | string | No | Degrees/certifications |
| languages_taught | string | No | Languages (comma-separated) |
| specialization | string | No | Area of expertise |
| resume_summary | string | No | Professional summary |
| introduction_video_url | string | No | YouTube/video URL |
| hourly_rate | number | No | Suggested hourly teaching rate |
| years_of_experience | integer | No | Years of teaching experience |

**Response:** `200 OK`
```json
{
  "message": "پروفایل معلم با موفقیت تکمیل شد",
  "data": {
    "id": 3,
    "username": "teacher1",
    "first_name": "Mohammad",
    "last_name": "Ahmadi",
    "role": "teacher",
    ...
  }
}
```

---

### 20. Update Teacher Profile
Alias for complete teacher profile (PATCH).

**Method:** `PATCH`  
**URL:** `/api/profile/`  
**Permission:** `IsAuthenticated`

**Request Body:** Same as complete profile (all fields optional)

**Response:** `200 OK` (same structure as complete profile)

---

### 21. Select Avatar
Choose an avatar from available templates.

**Method:** `POST`  
**URL:** `/api/select-avatar/`  
**Permission:** `IsAuthenticated`

**Request Body:**
```json
{
  "avatar_id": 2
}
```

**Response:** `200 OK`
```json
{
  "message": "آواتار با موفقیت انتخاب شد",
  "data": {
    "selected_avatar": 2,
    "avatar_image": "http://..."
  }
}
```

---

## Shared/Mixed Access APIs

### 22. View Teaching Subjects (Mixed Access)
Get list of teaching subjects with role-based filtering.

**Method:** `GET`  
**URL:** `/api/teaching-subjects/`  
**Permission:** `IsAuthenticated`

**Role-Based Behavior:**
- **Teacher:** See only their own subjects
- **Admin:** See all subjects
- **Student:** See only active subjects

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| teacher | integer | No | Filter by teacher ID |
| level | string | No | Filter: `beginner`, `intermediate`, `advanced` |
| is_active | boolean | No | Filter by active status |
| page | integer | No | Page number |
| page_size | integer | No | Items per page |

---

### 23. Get Exam Questions (Mixed Access)
Retrieve exam questions and options.

**Method:** `GET`  
**URL:** `/api/exercise/exam/{subject_id}/`  
**Permission:** `IsAuthenticated`

**Role-Based Behavior:**
- **Teacher:** Can access their own subjects only
- **Student:** Can access active subjects only
- **Admin:** Can access all subjects

**Access Rules:**
- Teachers see `correct_answer` field
- Students do NOT see `correct_answer` field (to prevent cheating)

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Success with no response body |
| 400 | Bad Request - Invalid data or parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Permission denied (role/ownership check) |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

---

## Authentication

All protected endpoints require JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Obtain tokens via:
- `/api/teacher/send-otp/` → `/api/teacher/verify-otp/` → `/api/teacher/complete-registration/`
- `/api/teacher/login-password/`
- `/api/teacher/send-email-otp/` → `/api/teacher/verify-email-otp/`

---

## Important Notes

### Exam Question Types

1. **input (تایپی) - Typing Questions**
   - Students type text answer
   - No `details` array (no options)
   - Uses `correct_answer` field for automatic grading
   - Case-insensitive comparison
   - Whitespace is trimmed

2. **radioButton (تک گزینه‌ای) - Single Choice**
   - Students select ONE option
   - Has `details` array with options
   - Option with `is_correct: 1` is marked correct
   - Scored automatically

3. **checkbox (چند گزینه‌ای) - Multiple Choice**
   - Students select MULTIPLE options
   - Has `details` array with options
   - Options with `is_correct: 1` are correct
   - Scored automatically

### Availability Slot Status

- **is_available: true** - Slot is available for students to book
- **is_booked: true** - Slot is already booked by a student
- Teachers cannot delete or significantly modify booked slots

### Booking Workflow

1. Student views availability slots
2. Student books/purchases a slot → creates ClassBooking with status "reserved"
3. Teacher marks as "completed" when class is done
4. OR student cancels → status becomes "cancelled" (only from "reserved")

### Exam Submission & Grading

- Students submit answers via SubmitExamAPIView
- Automatic grading happens on submission
- For choice questions: compares `field_detail.is_correct`
- For typing questions: compares with `field.correct_answer` (case-insensitive)
- Results stored in Order and OrderDetail models
- Teachers can review student answers immediately

### Pagination

List endpoints support pagination:

| Parameter | Type | Default |
|-----------|------|---------|
| page | integer | 1 |
| page_size | integer | 20 |

Response format:
```json
{
  "count": 100,
  "next": "http://api.../endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Teacher-Only Operations

- Create/update/delete availability slots
- Create teaching subjects
- Create and manage exam questions
- Add questions to subjects (create exams)
- View student exam results and answers
- Mark class bookings as completed/cancelled/no_show

---

## Admin Capabilities

- Teachers see their own data; admins see all teachers' data
- In exam results: Teachers see their subject results; admins see all results

