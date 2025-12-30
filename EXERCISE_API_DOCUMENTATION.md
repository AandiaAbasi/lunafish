# Exercise API Documentation

## Overview

Complete API for managing exercises/exams in the FoFofish platform. Teachers can create questions and exams, while students can attempt exams and receive scores.

## Supported Question Types

- **input** (تایپی): Typing/text-based questions
- **checkbox** (چند گزینه‌ای): Multiple choice questions
- **radioButton** (تک گزینه‌ای): Single choice questions

## API Endpoints

### 1. Create Question (Field)
**Endpoint**: `POST /api/exercise/field/create/`

Teachers create reusable questions that can be used in multiple exams.

**Request:**
```json
{
  "title": "What is the capital of France?",
  "type": "radioButton",
  "is_required": 1,
  "guide": "Choose the correct answer",
  "des": "This is a geography question",
  "image_path": "https://example.com/image.jpg",
  "audio_path": null,
  "video_path": null,
  "sort": 0,
  "details": [
    {
      "title": "London",
      "is_correct": 0,
      "sort": 0
    },
    {
      "title": "Paris",
      "is_correct": 1,
      "sort": 1,
      "guide": "Correct! Paris is the capital of France"
    },
    {
      "title": "Berlin",
      "is_correct": 0,
      "sort": 2
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 1,
    "title": "What is the capital of France?",
    "type": "radioButton",
    "is_required": 1,
    "guide": "Choose the correct answer",
    "des": "This is a geography question",
    "image_path": "https://example.com/image.jpg",
    "audio_path": null,
    "video_path": null,
    "sort": 0,
    "details": [
      {
        "id": 1,
        "title": "London",
        "is_correct": 0,
        "sort": 0
      },
      {
        "id": 2,
        "title": "Paris",
        "is_correct": 1,
        "sort": 1,
        "guide": "Correct! Paris is the capital of France"
      },
      {
        "id": 3,
        "title": "Berlin",
        "is_correct": 0,
        "sort": 2
      }
    ]
  },
  "message": "سؤال با موفقیت ایجاد شد"
}
```

#### Question Type Examples

**Typing Question (input):**
```json
{
  "title": "What is your name?",
  "type": "input",
  "is_required": 1,
  "guide": "Enter your full name",
  "des": "Required for identification"
}
```

**Multiple Choice (checkbox):**
```json
{
  "title": "Select all correct answers",
  "type": "checkbox",
  "is_required": 1,
  "details": [
    {"title": "Option 1", "is_correct": 1},
    {"title": "Option 2", "is_correct": 1},
    {"title": "Option 3", "is_correct": 0}
  ]
}
```

**Single Choice (radioButton):**
```json
{
  "title": "Choose one answer",
  "type": "radioButton",
  "is_required": 1,
  "details": [
    {"title": "Option A", "is_correct": 0},
    {"title": "Option B", "is_correct": 1},
    {"title": "Option C", "is_correct": 0}
  ]
}
```

---

### 2. Create Exam
**Endpoint**: `POST /api/exercise/exam/create/`

Teachers create exams by linking questions to their teaching subjects.

**Request:**
```json
{
  "teachingsubject_id": 5,
  "questions": [
    {
      "field_id": 1,
      "step": 0,
      "sort": 0,
      "type": "radioButton",
      "is_conditional": false
    },
    {
      "field_id": 2,
      "step": 0,
      "sort": 1,
      "type": "input",
      "is_conditional": false
    },
    {
      "field_id": 3,
      "step": 1,
      "sort": 0,
      "type": "checkbox",
      "is_conditional": false
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 5,
    "subject_id": 5,
    "subject_title": "English 101",
    "questions": [
      {
        "id": 1,
        "field_id": 1,
        "field_title": "What is the capital of France?",
        "type": "radioButton",
        "step": 0,
        "sort": 0,
        "is_conditional": false,
        "details": [
          {
            "id": 1,
            "title": "London",
            "is_correct": 0
          },
          {
            "id": 2,
            "title": "Paris",
            "is_correct": 1
          }
        ]
      },
      {
        "id": 2,
        "field_id": 2,
        "field_title": "What is your name?",
        "type": "input",
        "step": 0,
        "sort": 1,
        "is_conditional": false,
        "details": []
      }
    ],
    "total_questions": 3
  },
  "message": "آزمون با موفقیت ایجاد شد"
}
```

#### Step and Sort Explanation

- **step**: Groups questions into sections (0 = Section 1, 1 = Section 2, etc.)
- **sort**: Order within each section (0 = first, 1 = second, etc.)

Example:
```
Step 0 (Section 1):
  - Sort 0: Question 1
  - Sort 1: Question 2
  - Sort 2: Question 3

Step 1 (Section 2):
  - Sort 0: Question 4
  - Sort 1: Question 5
```

---

### 3. Get Exam
**Endpoint**: `GET /api/exercise/exam/{subject_id}/`

Retrieve complete exam with all questions and options for students and teachers.

**Query Parameters:**
- `subject_id` (required, path): Teaching subject ID

**Response (200 OK):**
```json
{
  "id": 5,
  "subject_id": 5,
  "subject_title": "English 101",
  "questions": [
    {
      "id": 1,
      "title": "What is the capital of France?",
      "type": "radioButton",
      "is_required": 1,
      "guide": "Choose the correct answer",
      "des": "This is a geography question",
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "sort": 0,
      "details": [
        {
          "id": 1,
          "title": "London",
          "second_title": null,
          "image_path": null,
          "is_correct": 0,
          "guide": null,
          "des": null,
          "sort": 0,
          "is_required": 0
        },
        {
          "id": 2,
          "title": "Paris",
          "second_title": null,
          "image_path": null,
          "is_correct": 1,
          "guide": "Correct! Paris is the capital of France",
          "des": null,
          "sort": 1,
          "is_required": 0
        }
      ]
    },
    {
      "id": 2,
      "title": "What is your name?",
      "type": "input",
      "is_required": 1,
      "guide": "Enter your full name",
      "des": "Required for identification",
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "sort": 0,
      "details": []
    }
  ],
  "total_questions": 2
}
```

---

### 4. Submit Exam
**Endpoint**: `POST /api/exercise/exam/{subject_id}/submit/`

Student submits exam answers. System automatically scores the answers.

**Request:**
```json
{
  "teachingsubject_id": 5,
  "answers": [
    {
      "field_id": 1,
      "field_detail_id": 2
    },
    {
      "field_id": 2,
      "value": "John Doe"
    },
    {
      "field_id": 3,
      "field_detail_id": 10
    },
    {
      "field_id": 3,
      "field_detail_id": 11
    }
  ]
}
```

**Request Explanation:**
- For **choice questions** (radioButton, checkbox): Use `field_detail_id` from the options
- For **text questions** (input): Use `value` with the text answer
- For **multiple choice (checkbox)**: Include one entry per selected option

**Response (201 Created):**
```json
{
  "data": {
    "id": 42,
    "user": 123,
    "user_name": "Ali Hosseini",
    "teachingsubject": 5,
    "subject_title": "English 101",
    "score": 2,
    "correct": 2,
    "incorrect": 1,
    "created_at": "2025-12-30T14:30:00Z",
    "details": [
      {
        "id": 1,
        "field": 1,
        "field_title": "What is the capital of France?",
        "field_type": "radioButton",
        "field_detail": 2,
        "option_title": "Paris",
        "value": null,
        "score": 1
      },
      {
        "id": 2,
        "field": 2,
        "field_title": "What is your name?",
        "field_type": "input",
        "field_detail": null,
        "option_title": null,
        "value": "John Doe",
        "score": 0
      },
      {
        "id": 3,
        "field": 3,
        "field_title": "Select all correct answers",
        "field_type": "checkbox",
        "field_detail": 10,
        "option_title": "Option 1",
        "value": null,
        "score": 1
      }
    ]
  },
  "message": "پاسخ‌ها با موفقیت ثبت شدند"
}
```

**Scoring Rules:**
- **Correct answer**: score = 1, added to `correct` count
- **Incorrect answer**: score = 0, added to `incorrect` count
- **Typing (input)**: Currently auto-scored as 0. You can implement fuzzy matching later.

---

### 5. Get Exam Results List
**Endpoint**: `GET /api/exercise/results/`

Get all exam attempts with pagination.

**Query Parameters:**
- `subject_id` (optional): Filter by specific subject
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20): Items per page (max 100)

**Response (200 OK):**
```json
{
  "count": 15,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 42,
      "teachingsubject": 5,
      "subject_title": "English 101",
      "score": 2,
      "correct": 2,
      "incorrect": 1,
      "total_questions": 3,
      "percentage": 66.67,
      "created_at": "2025-12-30T14:30:00Z"
    },
    {
      "id": 41,
      "teachingsubject": 5,
      "subject_title": "English 101",
      "score": 3,
      "correct": 3,
      "incorrect": 0,
      "total_questions": 3,
      "percentage": 100.0,
      "created_at": "2025-12-29T10:15:00Z"
    }
  ]
}
```

**Access Control:**
- **Students**: See only their own results
- **Teachers**: See results of all students in their subjects
- **Admins**: See all results

---

### 6. Get Exam Attempt Details
**Endpoint**: `GET /api/exercise/results/{attempt_id}/`

Get detailed results of a single exam attempt with all answers.

**Path Parameters:**
- `attempt_id` (required): Exam attempt ID

**Response (200 OK):**
```json
{
  "id": 42,
  "user": 123,
  "user_name": "Ali Hosseini",
  "teachingsubject": 5,
  "subject_title": "English 101",
  "score": 2,
  "correct": 2,
  "incorrect": 1,
  "created_at": "2025-12-30T14:30:00Z",
  "details": [
    {
      "id": 1,
      "field": 1,
      "field_title": "What is the capital of France?",
      "field_type": "radioButton",
      "field_detail": 2,
      "option_title": "Paris",
      "value": null,
      "score": 1
    },
    {
      "id": 2,
      "field": 2,
      "field_title": "What is your name?",
      "field_type": "input",
      "field_detail": null,
      "option_title": null,
      "value": "John Doe",
      "score": 0
    },
    {
      "id": 3,
      "field": 3,
      "field_title": "Select all correct answers",
      "field_type": "checkbox",
      "field_detail": 10,
      "option_title": "Option 1",
      "value": null,
      "score": 1
    }
  ]
}
```

---

## Authentication

All endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.example.com/api/exercise/exam/5/
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "داده‌های نامعتبر",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 403 Forbidden
```json
{
  "error": "شما دسترسی ندارید"
}
```

### 404 Not Found
```json
{
  "error": "موضوع تدریسی یافت نشد"
}
```

---

## Usage Flow

### For Teachers:

1. **Create Questions:**
   ```
   POST /api/exercise/field/create/
   ```
   Create reusable questions of different types

2. **Create Exam:**
   ```
   POST /api/exercise/exam/create/
   ```
   Link questions to your teaching subject

3. **View Results:**
   ```
   GET /api/exercise/results/?subject_id=5
   ```
   See all student results for the exam

4. **View Attempt Details:**
   ```
   GET /api/exercise/results/42/
   ```
   See detailed answers for a specific attempt

### For Students:

1. **Get Exam:**
   ```
   GET /api/exercise/exam/5/
   ```
   Retrieve exam questions and options

2. **Submit Answers:**
   ```
   POST /api/exercise/exam/5/submit/
   ```
   Submit exam and receive score

3. **View Results:**
   ```
   GET /api/exercise/results/
   ```
   See all their exam attempts

4. **View Attempt Details:**
   ```
   GET /api/exercise/results/42/
   ```
   See detailed feedback for an attempt

---

## Important Notes

### Question Type Usage:
- **input**: No options needed, student types answer
- **checkbox**: Multiple options can be correct, multiple selections allowed
- **radioButton**: Only one correct option, single selection required

### Scoring:
- Currently, typing (input) answers are scored as 0 by default
- Implement fuzzy string matching or answer keys for better typing question scoring
- Choice questions are auto-scored by comparing with `is_correct` field

### Field Attributes:
- `is_required`: 0 = optional, 1 = required (for UI validation)
- `is_correct`: -1 = N/A, 0 = incorrect, 1 = correct
- `is_conditional`: For future conditional logic (skip if...)

### Images and Media:
- `image_path`: Store full URLs or relative paths
- `audio_path`: For audio-based questions
- `video_path`: For video instructions or content
- `guide`: Shows when answer is correct/incorrect (feedback)

---

## Database Models Summary

### Field (Question)
- Stores question content and metadata
- Related to FieldDetail through `details` relation

### FieldDetail (Answer Option)
- Stores options for choice questions
- Each option has correctness indicator

### CategoryField (Exam)
- Links Field to TeachingSubject
- Orders questions with step and sort
- Creates the exam/assignment structure

### Order (Exam Attempt)
- Stores student's exam attempt
- Calculates score, correct, incorrect counts

### OrderDetail (Answer)
- Individual student answer to a question
- Stores submitted value and calculated score

---

## Future Enhancements

1. **Typing Answer Evaluation:**
   - Implement fuzzy string matching
   - Support multiple correct answers
   - Case-insensitive comparison

2. **Conditional Questions:**
   - Show/hide questions based on previous answers
   - Branching logic support

3. **Partial Scoring:**
   - Weight questions differently
   - Partial credit for partially correct answers

4. **Time Limit:**
   - Add time constraints to exams
   - Track time spent per question

5. **Analytics:**
   - Student performance statistics
   - Question difficulty analysis
   - Common mistakes identification

---

## Code Files

- **Serializers**: `api/exercise_serializers.py`
- **Views/Endpoints**: `api/views.py` (Exercise API section)
- **Models**: `exercise/models.py`
- **URLs**: `api/urls.py`
- **Admin**: `exercise/admin.py`

