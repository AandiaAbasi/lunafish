# Exercise API - Quick Reference for App Developers

## 🎯 Quick Summary

Teachers can create exercises for their classes. Students solve them and get instant scores.

**3 Question Types:**
- `input` - تایپی (Typing - student enters text)
- `checkbox` - چند گزینه‌ای (Multiple choice - select multiple)
- `radioButton` - تک گزینه‌ای (Single choice - select one)

---

## 🔑 API Endpoints

| Method | Endpoint | Purpose | Role |
|--------|----------|---------|------|
| POST | `/api/exercise/field/create/` | Create a question | Teacher |
| POST | `/api/exercise/exam/create/` | Create exam from questions | Teacher |
| GET | `/api/exercise/exam/{id}/` | Get exam questions | Student/Teacher |
| POST | `/api/exercise/exam/{id}/submit/` | Submit answers | Student |
| GET | `/api/exercise/results/` | View exam attempts | Student/Teacher |
| GET | `/api/exercise/results/{id}/` | View attempt details | Student/Teacher |

---

## 1️⃣ Create Question (Field)

```bash
POST /api/exercise/field/create/
```

### Single Choice (RadioButton) Example:
```json
{
  "title": "What is the capital of France?",
  "type": "radioButton",
  "is_required": 1,
  "guide": "Choose the correct answer",
  "details": [
    {"title": "London", "is_correct": 0},
    {"title": "Paris", "is_correct": 1},
    {"title": "Berlin", "is_correct": 0}
  ]
}
```

### Multiple Choice (Checkbox) Example:
```json
{
  "title": "Which of these are European countries?",
  "type": "checkbox",
  "details": [
    {"title": "France", "is_correct": 1},
    {"title": "Germany", "is_correct": 1},
    {"title": "Australia", "is_correct": 0}
  ]
}
```

### Typing Question (Input) Example:
```json
{
  "title": "What is your name?",
  "type": "input",
  "is_required": 1,
  "guide": "Enter your full name"
}
```

### Response:
```json
{
  "data": {
    "id": 1,
    "title": "...",
    "type": "radioButton",
    "details": [...]
  },
  "message": "سؤال با موفقیت ایجاد شد"
}
```

---

## 2️⃣ Create Exam

```bash
POST /api/exercise/exam/create/
```

**Link questions to a class/subject:**
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

**Understanding step and sort:**
- `step 0`: First section
- `step 1`: Second section
- `sort 0, 1, 2`: Order within section

---

## 3️⃣ Get Exam

```bash
GET /api/exercise/exam/5/
```

**Response:** Complete exam with all questions and answer options
- Use this to display exam to student
- Shows all fields needed to render the exam

---

## 4️⃣ Submit Answers

```bash
POST /api/exercise/exam/5/submit/
```

**For choice questions (radioButton, checkbox):**
```json
{
  "teachingsubject_id": 5,
  "answers": [
    {
      "field_id": 1,
      "field_detail_id": 2
    }
  ]
}
```

**For typing questions:**
```json
{
  "teachingsubject_id": 5,
  "answers": [
    {
      "field_id": 2,
      "value": "John Doe"
    }
  ]
}
```

**Response:** Includes instant score
```json
{
  "data": {
    "id": 42,
    "score": 2,
    "correct": 2,
    "incorrect": 1,
    "percentage": 66.67,
    "details": [...]
  },
  "message": "پاسخ‌ها با موفقیت ثبت شدند"
}
```

---

## 5️⃣ View Results

```bash
GET /api/exercise/results/
```

**Query params:**
- `subject_id=5` - Filter by subject
- `page=2` - Page number
- `page_size=20` - Items per page

**Response:** List of all exam attempts with scores

---

## 6️⃣ View Attempt Details

```bash
GET /api/exercise/results/42/
```

**Response:** Complete details of one exam attempt
- Shows all questions
- Shows student's answers
- Shows correctness of each answer
- Shows score for each answer

---

## 🎨 Frontend Implementation Guide

### Teacher View:
1. Show "Create Question" form
2. Show "Create Exam" form (selects questions)
3. Show results list with pagination

### Student View:
1. Display exam questions
2. Show answer options/input field
3. Handle submit
4. Show score immediately
5. Allow reviewing previous attempts

---

## 📊 Data Structures

### Question (Field):
```
{
  id: integer,
  title: string,
  type: "input" | "checkbox" | "radioButton",
  is_required: 0 | 1,
  guide: string,
  des: string,
  image_path: string,
  audio_path: string,
  video_path: string,
  details: FieldDetail[]
}
```

### Answer Option (FieldDetail):
```
{
  id: integer,
  title: string,
  is_correct: -1 | 0 | 1,
  image_path: string,
  guide: string,
  sort: integer
}
```

### Exam (CategoryField):
```
{
  id: integer,
  teachingsubject_id: integer,
  field_id: integer,
  step: integer,
  sort: integer,
  type: string,
  is_conditional: boolean
}
```

### Exam Attempt (Order):
```
{
  id: integer,
  user_id: integer,
  teachingsubject_id: integer,
  score: integer,
  correct: integer,
  incorrect: integer,
  created_at: datetime,
  details: OrderDetail[]
}
```

### Answer (OrderDetail):
```
{
  id: integer,
  field_id: integer,
  field_detail_id: integer | null,
  value: string | null,
  score: integer
}
```

---

## 🔐 Authentication

All requests need JWT token:
```bash
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Get token from:
- `/api/verify-otp/` - Student login
- `/api/teacher/verify-otp/` - Teacher login

---

## ⚠️ Error Handling

### 400 Bad Request
```json
{
  "error": "داده‌های نامعتبر",
  "details": {"field": ["error message"]}
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

## ✅ Checklist for Implementation

- [ ] Create question form for teachers
- [ ] Display created questions in list
- [ ] Create exam form with question selector
- [ ] Display exam to students
- [ ] Render questions based on type (input/choice)
- [ ] Handle answer submission
- [ ] Display score after submission
- [ ] Show results history
- [ ] Show detailed attempt results

---

## 💡 Tips

1. **Question Types:**
   - Show text input for `input` type
   - Show radio buttons for `radioButton` type
   - Show checkboxes for `checkbox` type

2. **Images/Media:**
   - Use `image_path`, `audio_path`, `video_path` from question
   - Also available in answer options

3. **Guides:**
   - Show as hint before submitting
   - Or show as feedback after submitting

4. **Scoring:**
   - Response score = number of correct answers
   - Percentage = (score / total_questions) × 100

5. **Typing Questions:**
   - Currently auto-scored as 0
   - Consider implementing answer key matching

---

## 📱 Mobile App Integration

```javascript
// Get exam
const exam = await fetch('api/exercise/exam/5/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Submit answers
const result = await fetch('api/exercise/exam/5/submit/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    teachingsubject_id: 5,
    answers: [
      { field_id: 1, field_detail_id: 2 },
      { field_id: 2, value: "Answer text" }
    ]
  })
}).then(r => r.json());

console.log(`Score: ${result.data.score}/${result.data.details.length}`);
```

---

## 🆘 Common Issues

**Q: Student can't see exam**
- A: Make sure teaching subject is active (`is_active: true`)

**Q: Score is 0 for typing questions**
- A: Current implementation doesn't auto-grade typing. Implement comparison logic.

**Q: Can't submit - 403 error**
- A: Check user role and subject permissions

**Q: Getting 404 on exam**
- A: Check subject_id is correct and subject exists

---

**For detailed documentation, see: EXERCISE_API_DOCUMENTATION.md**

