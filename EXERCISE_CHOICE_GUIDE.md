# Exercise Choice System Guide
# راهنمای سیستم انتخاب تمرین‌های اختیاری

## Overview
The Exercise Choice System allows teachers to create groups of exercises where students can select from multiple options. This is useful for:
- Optional exercises within assignments
- Variant exercises (easy/medium/hard versions)
- Choice-based learning experiences
- Differentiated instruction

---

## Models

### ExerciseChoice
Groups of exercises that students can choose from.

**Fields:**
- `title` (str, max 255): Title of the choice group
- `description` (text, optional): Detailed description
- `teacher` (FK to User): Teacher who created the group
- `subject` (FK to TeachingSubject): Associated teaching subject
- `choice_type` (choices): Type of choice group
  - `difficulty`: Easy/Medium/Hard variations
  - `variant`: Different versions of the same exercise
  - `language`: Different language options
  - `topic`: Different topic variations
  - `style`: Different exercise style options
- `exercises` (M2M to Exercise): Available exercises to choose from
- `required_choices` (int, default=1): How many exercises student must select
- `is_published` (bool, default=False): Whether group is visible to students
- `created_at`, `updated_at`: Timestamps

**Example:**
```python
# Create a difficulty choice group
ExerciseChoice.objects.create(
    title="Select Your Difficulty Level",
    teacher=teacher_obj,
    subject=subject_obj,
    choice_type='difficulty',
    required_choices=1,
    is_published=True
)
# Then add exercises with different difficulties via many-to-many
```

### StudentExerciseChoice
Tracks which exercises students selected from choice groups.

**Fields:**
- `student` (FK to User): Student making the choice
- `exercise_choice_group` (FK to ExerciseChoice): The choice group
- `selected_exercises` (M2M to Exercise): Exercises student selected
- `confirmed_at` (datetime, auto_now_add): When selection was confirmed
- `created_at`, `updated_at`: Timestamps

**Constraints:**
- Unique together: (student, exercise_choice_group) - each student can select only once per group

**Example:**
```python
# Student selects exercises from a choice group
choice = StudentExerciseChoice.objects.create(
    student=student_obj,
    exercise_choice_group=choice_group_obj
)
choice.selected_exercises.set([exercise1, exercise2])
```

---

## API Endpoints

### Exercise Choice Endpoints

#### 1. List/Create Exercise Choices
**Endpoint:** `POST /api/exercises/choices/`
**Endpoint:** `GET /api/exercises/choices/`

**Query Parameters:**
- `subject` (int): Filter by subject ID
- `teacher` (int): Filter by teacher ID
- `is_published` (bool): Filter by published status

**Request Body (POST):**
```json
{
  "title": "Select Exercise Difficulty",
  "description": "Choose your preferred difficulty level",
  "subject": 1,
  "choice_type": "difficulty",
  "exercises": [1, 2, 3],
  "required_choices": 1,
  "is_published": true
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Select Exercise Difficulty",
  "description": "Choose your preferred difficulty level",
  "teacher": 1,
  "teacher_name": "علی محمدی",
  "subject": 1,
  "subject_title": "ریاضیات",
  "choice_type": "difficulty",
  "choice_type_display": "سطح دشواری",
  "exercises_detail": [
    {
      "id": 1,
      "title": "Exercise 1 (Easy)",
      "difficulty": "easy"
    }
  ],
  "required_choices": 1,
  "exercise_count": 3,
  "is_published": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Retrieve Exercise Choice
**Endpoint:** `GET /api/exercises/choices/{id}/`

**Response:** Same as list response

#### 3. Update Exercise Choice
**Endpoint:** `POST /api/exercises/choices/{id}/update/`

**Permissions:**
- Only the teacher who created the choice group can update

**Request Body:**
```json
{
  "title": "Updated Title",
  "is_published": false
}
```

#### 4. Delete Exercise Choice
**Endpoint:** `POST /api/exercises/choices/{id}/delete/`

**Permissions:**
- Only the teacher who created the choice group can delete

**Response:**
```json
{
  "message": "دسته تمرین حذف شد"
}
```

---

### Student Exercise Choice Endpoints

#### 1. List/Create Student Choices
**Endpoint:** `POST /api/exercises/student-choices/`
**Endpoint:** `GET /api/exercises/student-choices/`

**Query Parameters:**
- `student` (int): Filter by student ID (teachers only)
- `exercise_choice_group` (int): Filter by choice group

**Permissions:**
- Students see only their own choices
- Teachers see all students' choices

**Request Body (POST):**
```json
{
  "exercise_choice_group": 1,
  "selected_exercises": [1, 2]
}
```

**Response:**
```json
{
  "id": 1,
  "student": 1,
  "student_name": "فاطمه احمدی",
  "exercise_choice_group": 1,
  "choice_group_title": "Select Exercise Difficulty",
  "selected_exercises_detail": [
    {
      "id": 1,
      "title": "Exercise 1 (Easy)",
      "difficulty": "easy"
    },
    {
      "id": 2,
      "title": "Exercise 2 (Medium)",
      "difficulty": "medium"
    }
  ],
  "confirmed_at": "2024-01-15T10:35:00Z",
  "created_at": "2024-01-15T10:35:00Z"
}
```

#### 2. Retrieve Student Choice
**Endpoint:** `GET /api/exercises/student-choices/{id}/`

**Permissions:**
- Student can see only their own choice
- Teachers can see all

**Response:** Same as list response

#### 3. Update Student Choice
**Endpoint:** `POST /api/exercises/student-choices/{id}/update/`

**Permissions:**
- Student can update only their own choice

**Request Body:**
```json
{
  "selected_exercises": [1, 3]
}
```

---

## Choice Types

### 1. Difficulty (سطح دشواری)
Students select their preferred difficulty level:
```python
ExerciseChoice.objects.create(
    choice_type='difficulty',
    exercises=[easy_exercise, medium_exercise, hard_exercise],
    required_choices=1  # Select one difficulty
)
```

### 2. Variant (نسخه متفاوت)
Students choose between different versions:
```python
ExerciseChoice.objects.create(
    choice_type='variant',
    exercises=[exercise_v1, exercise_v2, exercise_v3],
    required_choices=1
)
```

### 3. Language (زبان)
Students choose exercise language:
```python
ExerciseChoice.objects.create(
    choice_type='language',
    exercises=[english_exercise, persian_exercise],
    required_choices=1
)
```

### 4. Topic (موضوع)
Students choose topics to practice:
```python
ExerciseChoice.objects.create(
    choice_type='topic',
    exercises=[topic1_exercise, topic2_exercise, topic3_exercise],
    required_choices=2  # Select two topics
)
```

### 5. Style (سبک)
Students choose exercise style (essay, multiple choice, etc.):
```python
ExerciseChoice.objects.create(
    choice_type='style',
    exercises=[essay_exercise, multiple_choice_exercise],
    required_choices=1
)
```

---

## Usage Examples

### Example 1: Create a Difficulty Choice Group

```bash
curl -X POST http://localhost:8000/api/exercises/choices/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Math Practice - Select Difficulty",
    "description": "Choose the difficulty level you prefer",
    "subject": 1,
    "choice_type": "difficulty",
    "exercises": [10, 11, 12],
    "required_choices": 1,
    "is_published": true
  }'
```

### Example 2: Student Selects Exercises

```bash
curl -X POST http://localhost:8000/api/exercises/student-choices/ \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_choice_group": 1,
    "selected_exercises": [10]
  }'
```

### Example 3: List Student's Choices

```bash
curl -X GET http://localhost:8000/api/exercises/student-choices/ \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

### Example 4: Update Student's Selection

```bash
curl -X POST http://localhost:8000/api/exercises/student-choices/1/update/ \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_exercises": [11]
  }'
```

---

## Admin Interface

### ExerciseChoice Admin
- List view shows: Title, Teacher, Subject, Choice Type, Exercise Count
- Filters by: Teacher, Subject, Choice Type, Published Status
- Search by: Title, Teacher Name, Subject Title
- Bulk action: Set exercises via filter_horizontal widget

### StudentExerciseChoice Admin
- List view shows: Student Name, Choice Group, Exercise Count, Confirmation Time
- Filters by: Exercise Choice Group, Confirmation Date
- Search by: Student Name/Username, Choice Group Title
- Bulk action: Set exercises via filter_horizontal widget
- Read-only fields: Confirmed At, Created/Updated timestamps

---

## Business Rules

1. **One Selection Per Group**: Each student can select exercises from a choice group only once
2. **Required Choices**: Student must select at least `required_choices` number of exercises
3. **Teacher Only**: Only the teacher who created the choice group can modify or delete it
4. **Student Privacy**: Students can only see and update their own choices
5. **Publication Control**: Choice groups must be published to be visible to students
6. **Exercise Association**: All exercises in a choice group must belong to the same subject

---

## Integration with Exercises

Exercise choices work seamlessly with the existing exercise system:

```python
# When student selects exercises from choice group:
student_choice = StudentExerciseChoice.objects.get(id=1)

# Get all their selected exercises
selected_exercises = student_choice.selected_exercises.all()

# Create attempts for each selected exercise
for exercise in selected_exercises:
    attempt = StudentExerciseAttempt.objects.create(
        student=student_choice.student,
        exercise=exercise,
        status='in_progress'
    )
```

---

## Technical Notes

### Performance
- `ExerciseChoice` has indexes on: teacher, subject, created_at
- `StudentExerciseChoice` has indexes on: student, exercise_choice_group
- Filter by published status for faster student queries

### Permissions
```python
# Teacher permission check
if exercise_choice.teacher_id != request.user.id:
    return 403 Forbidden

# Student permission check (for own choices)
if student_choice.student_id != request.user.id:
    return 403 Forbidden
```

### Many-to-Many Management
```python
# Add exercises
choice_group.exercises.add(exercise1, exercise2, exercise3)

# Remove exercise
choice_group.exercises.remove(exercise1)

# Clear and set
choice_group.exercises.set([exercise1, exercise2])

# Similar for student selections
student_choice.selected_exercises.set([exercise1, exercise2])
```

---

## Troubleshooting

### Error: "شما قبلاً برای این گروه انتخاب کرده‌اید"
**Cause:** Student already made a selection for this choice group
**Solution:** Update existing choice instead of creating new one

### Error: "دسترسی محدود است"
**Cause:** Insufficient permissions
**Solution:** 
- Teacher: Only owners can update/delete
- Student: Can only access own choices

### Missing Exercises in Choice Group
**Cause:** Exercises not added to M2M relationship
**Solution:** Add via admin or API with exercises array

---

## Future Enhancements

- [ ] Deadline for student selections
- [ ] Grade/points for choice selection
- [ ] Auto-assignment if no selection made
- [ ] Analytics on choice distribution
- [ ] Time tracking per selected exercise
- [ ] Batch selection APIs for bulk operations
