# Student API Documentation

## Overview
APIs available to student users (role: `student`)

---

## Teacher Discovery APIs

### 1. View All Teachers
Browse all available and verified teachers.

**Method:** `GET`  
**URL:** `/api/teachers/`  
**Permission:** `AllowAny` (Public - No authentication required)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Teachers per page (default: 10) |

**Response:** `200 OK`
```json
{
  "count": 25,
  "next": "http://api.example.com/api/teachers/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "علی محمدی",
      "qualifications": "دارای دیپلم تدریس و تجربه 10 سال",
      "languages_taught": "فارسی، انگلیسی",
      "profile_photo_path": "https://cdn.example.com/photos/user1.jpg",
      "hourly_rate": "150.00",
      "resume_summary": "معلم با تجربه زیاد در تدریس ریاضیات و فیزیک به دانش‌آموزان...",
      "experience_years": 10,
      "is_teacher_verified": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. View Teacher Profile
Get complete teacher profile with qualifications, teaching subjects, and available time slots.

**Method:** `GET`  
**URL:** `/api/teachers/{id}/`  
**Permission:** `AllowAny` (Public - No authentication required)

**Response fields (selected):**
- `name`: نام معلم
- `qualifications`: مدرک تحصیلی
- `languages_taught`: زبان‌های تدریس‌شده
- `introduction_video`: ویدئوی معرفی
- `resume_summary`: خلاصه رزومه
- `hourly_rate`: قیمت ساعتی پیشنهادی
- `availability_slots`: زمان‌های در دسترس

---

## Class Booking APIs

### 3. View Available Time Slots
Retrieve list of available teacher time slots for booking classes.

**Method:** `GET`  
**URL:** `/api/teacher/availability/`  
**Permission:** Authenticated (Any role, but filtered for students)  
**Authentication:** JWT Bearer Token

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| teacher | integer | No | Filter by teacher ID |
| start_date | string | No | Filter from date (YYYY/MM/DD Jalali format) |
| end_date | string | No | Filter to date (YYYY/MM/DD Jalali format) |
| is_available | boolean | No | Filter available slots only |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20) |

**Response:** `200 OK`
```json
{
  "count": 5,
  "next": "http://api.example.com/api/teacher/availability/?page=2",
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
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

### 4. Book/Purchase a Class
Student purchases/reserves a time slot from a teacher.

**Method:** `POST`  
**URL:** `/api/class-booking/create/`  
**Permission:** `IsAuthenticated` (Students only)  
**Role:** `student`

**Request Body:**
```json
{
  "availability": 1,
  "subject": 5,
  "discount_code": "CODE123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| availability | integer | Yes | ID of teacher availability slot |
| subject | integer | Yes | ID of teaching subject/class |
| discount_code | string | No | Discount code (if applicable) |

**Response:** `201 Created`
```json
{
  "data": {
    "id": 10,
    "teacher": 5,
    "student": 2,
    "availability": 1,
    "subject": 5,
    "status": "reserved",
    "price": 50000,
    "discount_amount": 0,
    "final_price": 40000,
    "created_at": "2025-01-05T14:30:00Z",
    "updated_at": "2025-01-05T14:30:00Z"
  },
  "message": "کلاس با موفقیت خریداری شد"
}
```

**Error Responses:**
- `400`: Invalid data or unavailable slot
- `403`: Only students can book classes
- `404`: Slot or subject not found

---

### 5. View My Bookings
Get list of all classes booked/purchased by student.

**Method:** `GET`  
**URL:** `/api/my-bookings/`  
**Permission:** `IsAuthenticated` (Students only)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter: `reserved`, `completed`, `cancelled`, `no_show` |
| teacher | integer | No | Filter by teacher ID |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20) |

**Response:** `200 OK`
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "teacher": 5,
      "student": 2,
      "availability": 1,
      "subject": 5,
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

**Error Responses:**
- `403`: Students can only view their own bookings

---

### 6. Cancel Booking
Cancel a reserved class booking (refund/cancellation).

**Method:** `POST`  
**URL:** `/api/class-booking/{id}/cancel/`  
**Permission:** `IsAuthenticated` (Student owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Booking ID to cancel |

**Request Body:** Empty

**Response:** `200 OK`
```json
{
  "data": {
    "id": 10,
    "teacher": 5,
    "student": 2,
    "availability": 1,
    "subject": 5,
    "status": "cancelled",
    "price": 50000,
    "discount_amount": 0,
    "final_price": 40000,
    "created_at": "2025-01-05T14:30:00Z",
    "updated_at": "2025-01-06T10:00:00Z"
  },
  "message": "رزرو با موفقیت لغو شد"
}
```

**Error Responses:**
- `403`: Permission denied or booking cannot be cancelled (only "reserved" status can be cancelled)
- `404`: Booking not found

---

## Teaching Subjects (Classes) APIs

### 7. View Available Teaching Subjects
Get list of active teaching subjects available to students.

**Method:** `GET`  
**URL:** `/api/teaching-subjects/`  
**Permission:** `IsAuthenticated` (Any role, filtered for active subjects for students)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| teacher | integer | No | Filter by teacher ID |
| level | string | No | Filter: `beginner`, `intermediate`, `advanced` |
| is_active | boolean | No | Filter active status |

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": 5,
      "teacher": 3,
      "title": "English Beginner - Alphabet",
      "description": "Learn English basics",
      "cover_image": "http://...",
      "demo_video": "http://...",
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

### 8. View Teaching Subject Details
Get full details of a specific teaching subject.

**Method:** `GET`  
**URL:** `/api/teaching-subjects/{id}/`  
**Permission:** `IsAuthenticated` (Students see active subjects only)

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
  "description": "Learn English basics",
  "cover_image": "http://...",
  "demo_video": "http://...",
  "min_age": 5,
  "max_age": 12,
  "level": "beginner",
  "is_active": true,
  "created_at": "2025-01-01T10:00:00Z"
}
```

**Error Responses:**
- `404`: Subject not found
- `403`: Subject not active (students can only view active subjects)

---

## Exercise/Exam APIs

### 9. Get Exam for a Subject
Retrieve all questions and answer options for an exam/subject.

**Method:** `GET`  
**URL:** `/api/exercise/exam/{subject_id}/`  
**Permission:** `IsAuthenticated` (Students can access active subjects only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| subject_id | integer | Teaching subject ID |

**Response:** `200 OK`
```json
{
  "id": 5,
  "subject_id": 5,
  "subject_title": "English Beginner - Alphabet",
  "questions": [
    {
      "id": 1,
      "title": "What is the first letter?",
      "type": "radioButton",
      "guide": "Choose from options",
      "des": "Description",
      "is_required": 1,
      "sort": 0,
      "correct_answer": null,
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "exam_question_id": 10,
      "step": 0,
      "sort": 0,
      "details": [
        {
          "id": 1,
          "title": "A",
          "second_title": null,
          "image_path": null,
          "is_correct": 1,
          "guide": "Correct!",
          "des": null,
          "sort": 0,
          "is_required": 0
        },
        {
          "id": 2,
          "title": "B",
          "second_title": null,
          "image_path": null,
          "is_correct": 0,
          "guide": "Wrong",
          "des": null,
          "sort": 1,
          "is_required": 0
        }
      ]
    },
    {
      "id": 2,
      "title": "Write the English word for this object",
      "type": "input",
      "guide": "Type your answer",
      "des": "Typing question",
      "is_required": 1,
      "sort": 1,
      "correct_answer": null,
      "image_path": "http://...",
      "audio_path": null,
      "video_path": null,
      "exam_question_id": 11,
      "step": 0,
      "sort": 1,
      "details": []
    }
  ],
  "total_questions": 2
}
```

**Error Responses:**
- `404`: Subject/exam not found
- `403`: Subject not accessible (not active for students)

---

### 10. Submit Exam Answers
Submit answers to exam questions. Server calculates score automatically.

**Method:** `POST`  
**URL:** `/api/exercise/exam/{subject_id}/submit/`  
**Permission:** `IsAuthenticated` (Students only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| subject_id | integer | Teaching subject ID |

**Request Body:**
```json
{
  "answers": [
    {
      "field_id": 1,
      "field_detail_id": 1
    },
    {
      "field_id": 2,
      "value": "apple"
    },
    {
      "field_id": 3,
      "field_detail_id": 5
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| field_id | integer | Question ID |
| field_detail_id | integer | For choice questions: selected option ID |
| value | string | For typing questions: text answer |

**Response:** `201 Created`
```json
{
  "data": {
    "id": 100,
    "user": 2,
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
        "order": 100,
        "field": 1,
        "field_detail": 1,
        "value": null,
        "score": 1
      },
      {
        "id": 201,
        "order": 100,
        "field": 2,
        "field_detail": null,
        "value": "apple",
        "score": 1
      },
      {
        "id": 202,
        "order": 100,
        "field": 3,
        "field_detail": 5,
        "value": null,
        "score": 0
      }
    ],
    "created_at": "2025-01-06T15:00:00Z"
  },
  "message": "پاسخ‌ها با موفقیت ثبت شدند"
}
```

**Error Responses:**
- `400`: Invalid answers or subject not found
- `404`: Subject not found

**Note:** For typing questions (input type):
- Server compares answer with `correct_answer` from Field model
- Comparison is case-insensitive and whitespace-trimmed
- If `correct_answer` is not defined, answer is marked incorrect

---

### 11. View All My Exam Results
Get list of all exam attempts by the student with scores.

**Method:** `GET`  
**URL:** `/api/exercise/results/`  
**Permission:** `IsAuthenticated` (Students see their results only)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| subject_id | integer | No | Filter by subject ID |
| page | integer | No | Page number |
| page_size | integer | No | Items per page |

**Response:** `200 OK`
```json
{
  "count": 5,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 100,
      "user": 2,
      "teachingsubject": 5,
      "subject_title": "English Beginner",
      "score": 2,
      "correct": 2,
      "incorrect": 1,
      "total_questions": 3,
      "percentage": 66.67,
      "created_at": "2025-01-06T15:00:00Z"
    }
  ]
}
```

---

### 12. View Specific Exam Attempt Details
Get detailed breakdown of a single exam attempt with all answers and feedback.

**Method:** `GET`  
**URL:** `/api/exercise/results/{attempt_id}/`  
**Permission:** `IsAuthenticated` (Student owner only)

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| attempt_id | integer | Exam attempt ID |

**Response:** `200 OK`
```json
{
  "id": 100,
  "user": 2,
  "user_name": "student_username",
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
      "field_title": "What is the first letter?",
      "student_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "score": 1
    },
    {
      "id": 201,
      "field_id": 2,
      "field_title": "Write the English word for this object",
      "student_answer": "apple",
      "correct_answer": "apple",
      "is_correct": true,
      "score": 1
    },
    {
      "id": 202,
      "field_id": 3,
      "field_title": "Choose the correct verb",
      "student_answer": "B",
      "correct_answer": "A",
      "is_correct": false,
      "score": 0
    }
  ],
  "created_at": "2025-01-06T15:00:00Z"
}
```

**Error Responses:**
- `404`: Attempt not found
- `403`: Student cannot view other students' results

---

## Profile & Account APIs

### 13. Fetch User Profile
Get current logged-in student's profile data.

**Method:** `GET`  
**URL:** `/api/fetch-user/`  
**Permission:** `IsAuthenticated`

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "student1",
  "email": "student@example.com",
  "phone": "09101234567",
  "first_name": "Ali",
  "last_name": "Hosseini",
  "display_name": "Ali",
  "role": "student",
  "bio": "I am a student",
  "gender": "m",
  "birth_date": "1403-05-15",
  "avatar": "http://...",
  "selected_avatar": 1,
  "is_phone_verified": true,
  "is_email_verified": true,
  "email_verified_at": "2025-01-01T10:00:00Z",
  "phone_verified_at": "2025-01-01T09:00:00Z",
  "is_teacher": false
}
```

---

### 14. Update Student Profile
Update profile information.

**Method:** `PATCH`  
**URL:** `/api/profile/`  
**Permission:** `IsAuthenticated`

**Request Body:**
```json
{
  "first_name": "Ali",
  "last_name": "Hosseini",
  "display_name": "Ali H",
  "bio": "Updated bio",
  "gender": "male",
  "birth_date": "1403-05-15",
  "selected_avatar": 2
}
```

| Field | Type | Description |
|-------|------|-------------|
| first_name | string | نام |
| last_name | string | نام خانوادگی |
| display_name | string | نام نمایشی |
| bio | string | شرح مختصر |
| gender | string | جنسیت: `male`, `female`, `custom`, `prefer_not_to_say` |
| birth_date | string | تاریخ تولد (YYYY-MM-DD فرمت جلالی) |
| selected_avatar | integer | انتخاب آواتار کارتونی |

**Response:** `200 OK` (same as fetch user)

---

### 15. Complete Student Profile
Fill in extended student profile information (optional).

**Method:** `POST`  
**URL:** `/api/complete-student-profile/`  
**Permission:** `IsAuthenticated` (Students only)

**Request Body:**
```json
{
  "first_name": "Ali",
  "last_name": "Hosseini",
  "display_name": "Ali",
  "bio": "I am interested in learning English",
  "gender": "male",
  "birth_date": "1403-05-15",
  "selected_avatar": 1
}
```

| Field | Type | Description |
|-------|------|-------------|
| first_name | string | نام |
| last_name | string | نام خانوادگی |
| display_name | string | نام نمایشی |
| bio | string | شرح مختصر |
| gender | string | جنسیت: `male`, `female`, `custom`, `prefer_not_to_say` |
| birth_date | string | تاریخ تولد (YYYY-MM-DD فرمت جلالی) |
| selected_avatar | integer | انتخاب آواتار کارتونی |

**Response:** `200 OK`
```json
{
  "message": "پروفایل با موفقیت تکمیل شد",
  "data": {
    "id": 2,
    "username": "student1",
    "first_name": "Ali",
    "last_name": "Hosseini",
    "display_name": "Ali",
    "bio": "I am interested in learning English",
    "gender": "male",
    "birth_date": "1403-05-15",
    "selected_avatar": 1,
    "avatar": "http://...",
    "is_phone_verified": true,
    "is_email_verified": true
  }
}
```

---

### 16. Select Avatar
Choose an avatar from available templates.

**Method:** `POST`  
**URL:** `/api/select-avatar/`  
**Permission:** `IsAuthenticated`

**Request Body:**
```json
{
  "avatar_id": 1
}
```

**Response:** `200 OK`
```json
{
  "message": "آواتار با موفقیت انتخاب شد",
  "data": {
    "selected_avatar": 1,
    "avatar_image": "http://..."
  }
}
```

---

## Content/Info APIs (Read-Only)

### 17. Get Articles
Get list of published articles.

**Method:** `GET`  
**URL:** `/api/articles/`  
**Permission:** `AllowAny` (No authentication required)

**Response:** `200 OK`
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "title": "Article Title",
      "content": "Article content",
      "author": "Admin",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

### 18. Get FAQs
Get frequently asked questions.

**Method:** `GET`  
**URL:** `/api/faqs/`  
**Permission:** `AllowAny`

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "question": "How to book a class?",
      "answer": "You can book...",
      "is_active": true,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

---

### 19. Get Home Page Data
Get home page banners and content.

**Method:** `GET`  
**URL:** `/api/home/`  
**Permission:** `AllowAny`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "type": "banners",
      "data": [...]
    }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Success with no response body |
| 400 | Bad Request - Invalid data or parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Permission denied (role check) |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

---

## Authentication

All protected endpoints require JWT Bearer token in header:

```
Authorization: Bearer <access_token>
```

Obtain tokens via:
- `/api/send-otp/` → `/api/verify-otp/` → `/api/complete-registration/`
- `/api/login-password/`

---

## Pagination

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

## Notes

- **Typing Question Grading:** Comparison is case-insensitive. Spaces are trimmed.
- **Choice Questions:** Must select an option from provided details.
- **Exam Access:** Students can only take exams for active teaching subjects.
- **Booking Cancellation:** Only "reserved" bookings can be cancelled.
