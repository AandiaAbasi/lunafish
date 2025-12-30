# Exercise API - Technical Overview

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile App / Frontend                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────────┐
        │          API Endpoints (6 routes)        │
        ├──────────────────────────────────────────┤
        │ 1. POST /field/create/                   │
        │ 2. POST /exam/create/                    │
        │ 3. GET  /exam/{id}/                      │
        │ 4. POST /exam/{id}/submit/               │
        │ 5. GET  /results/                        │
        │ 6. GET  /results/{id}/                   │
        └──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                   ↓
    ┌────────┐      ┌─────────────┐    ┌──────────┐
    │  View  │      │ Serializer  │    │Permission│
    │ Classes│      │   Classes   │    │ Classes  │
    └────────┘      └─────────────┘    └──────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ↓
        ┌──────────────────────────────────────────┐
        │            Database Models               │
        ├──────────────────────────────────────────┤
        │ • Field (Questions)                      │
        │ • FieldDetail (Answer Options)           │
        │ • CategoryField (Exams)                  │
        │ • Order (Student Attempts)               │
        │ • OrderDetail (Student Answers)          │
        │ • TeachingSubject (Classes)              │
        │ • User (Students/Teachers)               │
        └──────────────────────────────────────────┘
```

---

## Data Flow

### Creating Exam Flow:
```
Teacher
  ↓
Create Field (Question) [POST /field/create/]
  ├─→ FieldCreateUpdateSerializer validates
  ├─→ Creates Field + FieldDetails
  └─→ Returns Question with ID
  
  ↓
Create Exam [POST /exam/create/]
  ├─→ Validates teacher owns subject
  ├─→ Links questions to subject
  ├─→ Creates CategoryField records
  └─→ Returns Exam structure with all questions
```

### Exam Submission Flow:
```
Student
  ↓
Get Exam [GET /exam/{id}/]
  ├─→ Validates access (active subject)
  ├─→ Returns all questions with options
  └─→ App displays exam UI
  
  ↓
Submit Answers [POST /exam/{id}/submit/]
  ├─→ OrderCreateSubmitSerializer validates
  ├─→ Creates Order (attempt record)
  ├─→ Processes each answer:
  │   ├─ For choice: Compare with is_correct
  │   ├─ For typing: Auto-score as 0
  │   └─ Create OrderDetail with score
  ├─→ Calculate totals:
  │   ├─ score = sum of correct answers
  │   ├─ correct = count of correct
  │   └─ incorrect = count of incorrect
  └─→ Returns result immediately
  
  ↓
View Results [GET /results/]
  ├─→ Filters by user role
  ├─→ Returns paginated list
  └─→ Shows score, percentage, date
  
  ↓
View Details [GET /results/{id}/]
  ├─→ OrderRetrieveSerializer
  ├─→ Returns full attempt with all answers
  └─→ Shows correctness for each answer
```

---

## Class Hierarchy

```
APIView (DRF Base Class)
│
├─ CreateFieldAPIView
│  └─ Creates new questions
│     Uses: FieldCreateUpdateSerializer
│
├─ CreateExamAPIView
│  └─ Links questions to subjects
│     Uses: CategoryField model
│
├─ GetExamAPIView
│  └─ Retrieves exam for students
│     Uses: FieldRetrieveSerializer
│
├─ SubmitExamAPIView
│  └─ Processes student answers
│     Uses: OrderCreateSubmitSerializer
│     Creates: Order, OrderDetail
│
├─ GetExamResultsAPIView
│  └─ Lists exam attempts with pagination
│     Uses: OrderListSerializer
│
└─ GetExamAttemptDetailAPIView
   └─ Shows single attempt details
      Uses: OrderRetrieveSerializer
```

---

## Serializer Hierarchy

```
Base Serializers:
├─ Field Serializers:
│  ├─ FieldDetailSerializer
│  ├─ FieldCreateUpdateSerializer (create/update)
│  └─ FieldRetrieveSerializer (read with details)
│
├─ Exam Serializers:
│  ├─ CategoryFieldCreateSerializer (create)
│  └─ CategoryFieldRetrieveSerializer (read)
│
└─ Result Serializers:
   ├─ OrderDetailSubmitSerializer (individual answer)
   ├─ OrderCreateSubmitSerializer (submit exam)
   ├─ OrderDetailRetrieveSerializer (view answer)
   ├─ OrderRetrieveSerializer (view attempt)
   └─ OrderListSerializer (list attempts)
```

---

## Database Schema

```sql
-- Questions (Field)
Field
├─ id (PK)
├─ title (question text)
├─ type (input, checkbox, radioButton)
├─ is_required (0/1)
├─ image_path, audio_path, video_path
├─ guide, des (description)
└─ sort

-- Answer Options (FieldDetail)
FieldDetail
├─ id (PK)
├─ field_id (FK → Field)
├─ title (option text)
├─ second_title
├─ is_correct (-1, 0, 1)
├─ image_path
├─ guide, des
└─ sort

-- Exams (CategoryField)
CategoryField
├─ id (PK)
├─ teachingsubject_id (FK → TeachingSubject)
├─ field_id (FK → Field)
├─ step (section number)
├─ sort (order in section)
├─ type (question type)
└─ is_conditional (boolean)

-- Exam Attempts (Order)
Order
├─ id (PK)
├─ user_id (FK → User/Student)
├─ teachingsubject_id (FK → TeachingSubject)
├─ score (number correct)
├─ correct (count)
├─ incorrect (count)
└─ created_at

-- Student Answers (OrderDetail)
OrderDetail
├─ id (PK)
├─ order_id (FK → Order)
├─ field_id (FK → Field)
├─ field_detail_id (FK → FieldDetail, nullable)
├─ value (typed answer, nullable)
└─ score (0 or 1)
```

---

## File Structure

```
fofofish/
├── api/
│   ├── exercise_serializers.py    [NEW] 425 lines
│   │   └─ All exercise serializers
│   ├── views.py                   [MODIFIED] +900 lines
│   │   └─ 6 new exercise API classes
│   ├── urls.py                    [MODIFIED] +6 lines
│   │   └─ 6 new exercise routes
│   ├── classroom_serializers.py   [EXISTING]
│   ├── models.py
│   └─ ...
│
├── exercise/
│   ├── models.py                  [EXISTING]
│   │   ├─ Field
│   │   ├─ FieldDetail
│   │   ├─ CategoryField
│   │   ├─ Order
│   │   └─ OrderDetail
│   ├── admin.py                   [EXISTING]
│   ├── views.py
│   └─ ...
│
├── classroom/
│   ├── models.py                  [EXISTING]
│   │   └─ TeachingSubject
│   └─ ...
│
├── account/
│   ├── models.py                  [EXISTING]
│   │   └─ User
│   └─ ...
│
├── EXERCISE_API_DOCUMENTATION.md  [NEW] 500 lines
├── EXERCISE_API_QUICK_REFERENCE.md [NEW] 300 lines
└─ ...
```

---

## Request/Response Examples

### 1. Create Question
```
POST /api/exercise/field/create/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Question text",
  "type": "radioButton",
  "is_required": 1,
  "details": [
    {"title": "Option 1", "is_correct": 1}
  ]
}

→ 201 Created
{
  "data": {
    "id": 1,
    "title": "...",
    "details": [...]
  }
}
```

### 2. Create Exam
```
POST /api/exercise/exam/create/
Authorization: Bearer <token>

{
  "teachingsubject_id": 5,
  "questions": [
    {"field_id": 1, "step": 0, "sort": 0, "type": "radioButton"}
  ]
}

→ 201 Created
{
  "data": {
    "id": 5,
    "subject_title": "...",
    "questions": [...],
    "total_questions": 1
  }
}
```

### 3. Get Exam
```
GET /api/exercise/exam/5/
Authorization: Bearer <token>

→ 200 OK
{
  "id": 5,
  "subject_title": "...",
  "questions": [
    {
      "id": 1,
      "title": "...",
      "type": "radioButton",
      "details": [...]
    }
  ]
}
```

### 4. Submit Exam
```
POST /api/exercise/exam/5/submit/
Authorization: Bearer <token>

{
  "teachingsubject_id": 5,
  "answers": [
    {"field_id": 1, "field_detail_id": 2}
  ]
}

→ 201 Created
{
  "data": {
    "id": 42,
    "score": 1,
    "correct": 1,
    "incorrect": 0,
    "percentage": 100.0,
    "details": [...]
  }
}
```

### 5. View Results
```
GET /api/exercise/results/?page=1
Authorization: Bearer <token>

→ 200 OK
{
  "count": 15,
  "results": [
    {
      "id": 42,
      "subject_title": "...",
      "score": 1,
      "percentage": 100.0,
      "created_at": "2025-12-30T14:30:00Z"
    }
  ]
}
```

### 6. View Attempt Details
```
GET /api/exercise/results/42/
Authorization: Bearer <token>

→ 200 OK
{
  "id": 42,
  "subject_title": "...",
  "score": 1,
  "details": [
    {
      "field_id": 1,
      "field_title": "...",
      "field_type": "radioButton",
      "value": null,
      "option_title": "Paris",
      "score": 1
    }
  ]
}
```

---

## Permission Matrix

```
                    Create   Read   Update   Delete
                    Question Exam   Exam     Exam
Teacher (own)       ✓        ✓      ✓        ✓
Teacher (other)     ✓        ✗      ✗        ✗
Student             ✗        ✓      ✗        ✗
Admin               ✓        ✓      ✓        ✓

Results View
                    Own      Other Student's
Student             ✓        ✗              ✗
Teacher             ✓        ✗              ✓ (own subject)
Admin               ✓        ✓              ✓
```

---

## Performance Considerations

### Database Queries
- `GetExamAPIView`: Uses `select_related('field')` to optimize joins
- `SubmitExamAPIView`: Bulk creates for efficiency
- `GetExamResultsAPIView`: Uses pagination to limit data
- Result filtering done at database level (filter queries)

### Pagination
- Default: 20 items per page
- Maximum: 100 items per page
- Configurable via `page_size` parameter

### Indexing Recommendations
```sql
-- Add these indexes for performance:
CREATE INDEX idx_categoryfield_subject ON exercise_categoryfield(teachingsubject_id);
CREATE INDEX idx_categoryfield_field ON exercise_categoryfield(field_id);
CREATE INDEX idx_order_user ON exercise_order(user_id);
CREATE INDEX idx_order_subject ON exercise_order(teachingsubject_id);
CREATE INDEX idx_orderdetail_order ON exercise_orderdetail(order_id);
CREATE INDEX idx_orderdetail_field ON exercise_orderdetail(field_id);
```

---

## Error Handling Strategy

```
Error Type              Status   Response
──────────────────────────────────────────────
Invalid data            400      {"error": "...", "details": {...}}
Unauthorized            401      {"error": "Not authenticated"}
Forbidden (permissions) 403      {"error": "No access"}
Not found               404      {"error": "Not found"}
Validation error        400      {"error": "...", "details": {...}}
Server error            500      {"error": "Server error occurred"}
```

---

## Testing Checklist

```
✓ Create question with each type (input, checkbox, radioButton)
✓ Create exam from multiple questions
✓ Retrieve exam with all questions
✓ Submit exam with correct answers
✓ Submit exam with incorrect answers
✓ Submit exam with mixed answers
✓ Verify scoring calculation
✓ Access control - teacher can't see other's subjects
✓ Access control - student can only submit for active subjects
✓ Pagination on results list
✓ Detailed result view shows correct answers
✓ Multiple attempt support
✓ Typing question scoring (currently 0)
✓ Choice question scoring
✓ Percentage calculation
```

---

## Future Enhancements

### Phase 2:
- [ ] Answer key matching for typing questions
- [ ] Conditional question logic (skip if...)
- [ ] Time limit enforcement
- [ ] Question images from file upload
- [ ] PDF result export
- [ ] Analytics dashboard

### Phase 3:
- [ ] Weighted scoring
- [ ] Partial credit
- [ ] Question randomization
- [ ] Answer shuffling
- [ ] Question bank management
- [ ] Template exams

---

**Generated**: December 30, 2025  
**Version**: 1.0  
**Status**: Production Ready

