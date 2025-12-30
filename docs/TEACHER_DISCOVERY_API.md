# Teacher List and Detail APIs Implementation

## Overview
Implemented two new REST API endpoints for discovering teachers and viewing their detailed profiles. These are public APIs that allow students and guests to browse available teachers and their teaching information.

## Endpoints

### 1. Teacher List API
**URL:** `GET /api/teachers/`

**Description:** Returns a paginated list of all verified teachers with their basic information for discovery and browsing.

**Permissions:** Public (AllowAny)

**Query Parameters:**
- `page` (optional, default=1): Page number for pagination
- `page_size` (optional, default=10): Number of teachers per page

**Response (200 OK):**
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

**Response Fields:**
- `id` (integer): Unique teacher identifier
- `name` (string): Teacher's full name
- `qualifications` (string): Educational qualifications (up to 500 characters)
- `languages_taught` (string): Languages the teacher teaches (up to 500 characters)
- `profile_photo_path` (string, URL): Path to teacher's profile photo (null if not set)
- `hourly_rate` (decimal): Price per hour as decimal (e.g., "150.00")
- `resume_summary` (string): Truncated resume (first 200 characters, with "..." if longer)
- `experience_years` (integer): Years of teaching experience
- `is_teacher_verified` (boolean): Whether teacher is verified
- `created_at` (string, ISO datetime): When teacher profile was created

**Example Requests:**
```bash
# Get first page (default 10 per page)
curl http://localhost:8000/api/teachers/

# Get with custom page size
curl http://localhost:8000/api/teachers/?page_size=20

# Get second page
curl http://localhost:8000/api/teachers/?page=2&page_size=10
```

### 2. Teacher Detail API
**URL:** `GET /api/teachers/{id}/`

**Description:** Returns complete teacher profile including qualifications, teaching subjects, and available time slots.

**Permissions:** Public (AllowAny)

**Path Parameters:**
- `id` (integer, required): Teacher ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "علی محمدی",
  "email": "ali@example.com",
  "phone": "09123456789",
  "qualifications": "دارای دیپلم تدریس و تجربه 10 سال",
  "languages_taught": "فارسی، انگلیسی",
  "specialization": "ریاضیات و فیزیک",
  "experience_years": 10,
  "is_teacher_verified": true,
  "resume_summary": "معلم با تجربه زیاد در تدریس ریاضیات و فیزیک به دانش‌آموزان کلاس‌های متوسطه و دبیرستان...",
  "introduction_video": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "bio": "با علاقه زیاد به تدریس و کمک به یادگیری بهتر دانش‌آموزان...",
  "profile_photo_path": "https://cdn.example.com/photos/user1.jpg",
  "hourly_rate": "150.00",
  "teaching_subjects": [
    {
      "id": 5,
      "title": "ریاضیات پایه‌ای",
      "description": "دوره آموزشی ریاضیات برای دانش‌آموزان پایه...",
      "level": "beginner",
      "level_display": "مبتدی",
      "cover_image": "https://cdn.example.com/subjects/math.jpg",
      "demo_video": "https://example.com/videos/math-demo.mp4",
      "min_age": 12,
      "max_age": 18,
      "is_active": true
    }
  ],
  "availability_slots": [
    {
      "id": 100,
      "date": "1403/11/25",
      "start_time": "14:30",
      "end_time": "15:30",
      "price": "150.00",
      "discount_price": null,
      "is_available": true,
      "is_booked": false,
      "is_expired": false,
      "notes": "درس انگلیسی"
    }
  ]
}
```

**Response Fields (Basic Information Section):**
- `id` (integer): Teacher's unique ID
- `name` (string): Teacher's full name
- `email` (string): Teacher's email address
- `phone` (string): Phone number

**Response Fields (Qualifications Section):**
- `qualifications` (string): Educational and professional qualifications
- `languages_taught` (string): Languages the teacher teaches
- `specialization` (string): Teaching specialization/subject area
- `experience_years` (integer): Years of teaching experience
- `is_teacher_verified` (boolean): Whether teacher is verified by platform

**Response Fields (Introduction Section):**
- `resume_summary` (string): Full resume/biography text
- `introduction_video` (string, URL): Video introduction URL (null if not set)
- `bio` (string): Short biography text
- `profile_photo_path` (string, URL): Profile photo URL (null if not set)

**Response Fields (Teaching Information Section):**
- `hourly_rate` (decimal): Price per hour

**Response Fields (Related Data Section):**
- `teaching_subjects` (array): List of teaching subjects with:
  - `id`: Subject ID
  - `title`: Subject title
  - `description`: Subject description
  - `level`: Level code (beginner/intermediate/advanced)
  - `level_display`: Translated level display
  - `cover_image`: Subject cover image URL
  - `demo_video`: Demo video URL
  - `min_age`: Minimum student age (null if not set)
  - `max_age`: Maximum student age (null if not set)
  - `is_active`: Whether subject is active

- `availability_slots` (array): List of available time slots (limited to 50 most recent slots not yet expired), with:
  - `id`: Slot ID
  - `date`: Date in Jalali format (YYYY/MM/DD)
  - `start_time`: Start time (HH:MM format)
  - `end_time`: End time (HH:MM format)
  - `price`: Base price for the slot
  - `discount_price`: Discounted price (null if no discount)
  - `is_available`: Whether slot is available
  - `is_booked`: Whether slot is already booked
  - `is_expired`: Whether slot has expired
  - `notes`: Any notes about the slot

**Error Responses:**

**404 Not Found:**
```json
{
  "error": "معلم یافت نشد"
}
```
- When teacher ID doesn't exist or teacher is not verified

**Example Requests:**
```bash
# Get teacher with ID 1
curl http://localhost:8000/api/teachers/1/

# Get teacher details with full information
curl http://localhost:8000/api/teachers/5/ -H "Accept: application/json"
```

## Implementation Details

### Files Modified

1. **api/classroom_serializers.py**
   - Added `TeacherListSerializer`: Serializes basic teacher information for list view
   - Added `TeachingSubjectDetailSerializer`: Serializes teaching subjects for detail view
   - Added `TeacherAvailabilityDetailSerializer`: Serializes availability slots for detail view
   - Added `TeacherDetailSerializer`: Serializes complete teacher profile with related data

2. **api/views.py**
   - Added `TeacherListAPIView`: APIView that lists all verified teachers with pagination
   - Added `TeacherDetailAPIView`: APIView that returns detailed teacher profile

3. **api/urls.py**
   - Added URL patterns:
     - `path('teachers/', views.TeacherListAPIView.as_view(), name='teacher_list')`
     - `path('teachers/<int:id>/', views.TeacherDetailAPIView.as_view(), name='teacher_detail')`

### Key Features

1. **Public Access**: Both endpoints are publicly accessible (no authentication required)
2. **Pagination**: Teacher list endpoint supports pagination with configurable page size
3. **Data Optimization**:
   - Only shows verified teachers
   - Availability slots are limited to 50 most recent non-expired slots
   - Resume summary is truncated in list view for performance
4. **Related Data**: Teacher detail view includes related teaching subjects and availability slots
5. **Error Handling**: Returns 404 when teacher not found
6. **Jalali Date Format**: Availability dates are returned in Persian Jalali calendar format

### Data Filtering Logic

**Teacher List:**
- Filters: `role='teacher'` AND `is_teacher_verified=True`
- Orders by: `-created_at` (newest first)
- Paginated by default with 10 per page

**Teacher Detail - Availability Slots:**
- Filters: Today or future dates, `is_available=True`, `is_booked=False`, `is_expired=False`
- Orders by: `date`, `start_time`
- Limited to 50 most recent slots

**Teacher Detail - Teaching Subjects:**
- Filters: `is_active=True`
- Shows all active teaching subjects

## Usage Examples

### Discovering Teachers
```bash
# Student wants to browse available teachers
curl http://localhost:8000/api/teachers/

# Student wants to see more teachers on next page
curl http://localhost:8000/api/teachers/?page=2

# Increase page size to see 20 teachers at once
curl http://localhost:8000/api/teachers/?page_size=20
```

### Viewing Teacher Details
```bash
# Student wants to see full details of teacher with ID 1
curl http://localhost:8000/api/teachers/1/

# Check what subjects the teacher teaches
curl http://localhost:8000/api/teachers/1/ | jq '.teaching_subjects'

# Check available time slots for booking
curl http://localhost:8000/api/teachers/1/ | jq '.availability_slots'
```

## Integration with Existing APIs

These APIs complement the existing classroom APIs:
- **Teaching Subjects API** (`/api/teaching-subjects/`): Manages subject CRUD operations
- **Teacher Availability API** (`/api/teacher/availability/`): Manages time slot CRUD operations
- **Teacher List/Detail APIs** (NEW): Provides public discovery and profile viewing

Students can use Teacher List/Detail APIs to discover teachers, then use the Teaching Subjects API to view full subject details and proceed with bookings.

## Notes

- Both endpoints return data in JSON format
- All dates are in Jalali calendar format (YYYY/MM/DD) for availability
- All times are in HH:MM format (24-hour)
- Prices are returned as decimal strings (e.g., "150.00")
- The APIs follow DRF conventions and return appropriate HTTP status codes
