# Quick Start: Optional & Choice-Based Exercises
# شروع سریع: تمرین‌های اختیاری و انتخاب‌گزینه‌ای

## What You Can Do Now

✅ **Create optional exercises** - Mark exercises as optional or required
✅ **Create exercise variants** - Easy/Medium/Hard versions of same exercise  
✅ **Create choice groups** - Let students choose which exercises to do
✅ **Track student selections** - See which exercises students selected
✅ **Admin management** - Visual interface with badges and filters

---

## 5-Minute Setup

### 1. Create Database Tables

```bash
cd c:\Users\mobila\Desktop\fatemeh\fofofish
python manage.py makemigrations exercise
python manage.py migrate
```

### 2. Go to Admin Panel

```
http://localhost:8000/admin/
Login with your teacher account
Navigate to "Exercise Choices" section
```

### 3. Create Your First Choice Group

1. Go to Admin → Exercise → Exercise Choices
2. Click "Add Exercise Choice"
3. Fill in:
   - Title: "Select Your Exercise Difficulty"
   - Subject: Your subject
   - Choice Type: "difficulty" (سطح دشواری)
   - Exercises: Check 3 exercises (easy, medium, hard)
   - Required Choices: 1
   - Publish: ✓ Yes
4. Save

### 4. Check Student Side

Students will see in API:
```bash
GET /api/exercises/student-choices/
# Returns: Empty list (no choices made yet)

POST /api/exercises/student-choices/
# Request body:
{
  "exercise_choice_group": 1,
  "selected_exercises": [5]
}
# Returns: Their selection with timestamp
```

---

## Common Tasks

### Task 1: Make an Exercise Optional

**Old Way (Manual):**
```
Admin → Exercises → Edit Exercise
Set "اختیاری" (is_optional) = ✓
```

**Now Shows:**
- Orange badge "● اختیاری"
- Count of optional vs required questions
- Parent exercise field if it's a variant

### Task 2: Create Exercise Variants

**Step 1:** Create 3 exercises
- Easy version
- Medium version  
- Hard version

**Step 2:** In Easy exercise, set:
- Parent Exercise: (leave blank - it's the parent)
- Variant Order: 1

**Step 3:** In Medium exercise:
- Parent Exercise: Easy version
- Variant Order: 2

**Step 4:** In Hard exercise:
- Parent Exercise: Easy version
- Variant Order: 3

**Result:**
```
Easy (parent)
├── Medium (variant)
└── Hard (variant)
```

### Task 3: Let Students Choose Difficulty

**Step 1:** Create 3 exercises with difficulties:
- Easy exercise (id: 10)
- Medium exercise (id: 11)
- Hard exercise (id: 12)

**Step 2:** Create choice group in admin or API:

```bash
POST /api/exercises/choices/
{
  "title": "Select Difficulty Level",
  "subject": 1,
  "choice_type": "difficulty",
  "exercises": [10, 11, 12],
  "required_choices": 1,
  "is_published": true
}
```

**Step 3:** Students select via API:

```bash
POST /api/exercises/student-choices/
{
  "exercise_choice_group": 1,
  "selected_exercises": [11]
}
```

**Step 4:** View student selections:

```bash
GET /api/exercises/student-choices/
# Shows all their selections with timestamps
```

---

## API Quick Reference

### Create Choice Group (Teacher)
```bash
curl -X POST http://localhost:8000/api/exercises/choices/ \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Select Your Exercises",
    "subject": 1,
    "choice_type": "difficulty",
    "exercises": [1, 2, 3],
    "required_choices": 1,
    "is_published": true
  }'
```

### List Available Choices (Student)
```bash
curl http://localhost:8000/api/exercises/choices/ \
  -H "Authorization: Bearer STUDENT_TOKEN"
```

### Student Selects Exercises
```bash
curl -X POST http://localhost:8000/api/exercises/student-choices/ \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_choice_group": 1,
    "selected_exercises": [1]
  }'
```

### Update Student Selection
```bash
curl -X POST http://localhost:8000/api/exercises/student-choices/1/update/ \
  -H "Authorization: Bearer STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_exercises": [2]
  }'
```

### Delete Choice Group (Teacher)
```bash
curl -X POST http://localhost:8000/api/exercises/choices/1/delete/ \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

---

## Admin Features

### Exercise Admin (Updated)
**List shows:**
- Title
- Teacher
- Subject
- Exercise Type (practice, homework, quiz, exam)
- Optional Badge (blue "● الزامی" or orange "● اختیاری")
- Published Status
- Question Count

**Filters available:**
- By Exercise Type
- By Optional/Required
- By Published Status
- By Teacher
- By Subject

**New fields:**
- Parent Exercise (for variants)
- Variant Order (position in variant list)
- Optional Question Count (shows which questions are optional)

### Exercise Choice Admin (New)
**List shows:**
- Title
- Teacher
- Subject
- Choice Type (difficulty, variant, language, topic, style)
- Number of Exercises
- Published Status

**Features:**
- Filter exercises with checkbox list
- Create/Edit/Delete choice groups
- See exercise count
- Manage which exercises are available

### Student Exercise Choice Admin (New)
**List shows:**
- Student Name
- Choice Group Name
- Number of Exercises Selected
- When They Made the Selection

**Features:**
- Search by student name or choice group
- See which exercises each student selected
- Filter by choice group or date
- View selection history

---

## Choice Types Explained

### Difficulty (سطح دشواری)
Students pick their difficulty level
```
[ ] Easy
[ ] Medium  
[ ] Hard
```

### Variant (نسخه متفاوت)
Students choose between versions
```
[ ] Version A
[ ] Version B
[ ] Version C
```

### Language (زبان)
Students pick exercise language
```
[ ] فارسی (Persian)
[ ] English
```

### Topic (موضوع)
Students select topics to practice
```
[ ] Topic 1 - Algebraic Expressions
[ ] Topic 2 - Linear Equations
[ ] Topic 3 - Quadratic Equations
```

### Style (سبک)
Students choose exercise format
```
[ ] Multiple Choice
[ ] Free Response
[ ] Short Answer
```

---

## Permissions Summary

| Action | Teacher | Student | Admin |
|--------|---------|---------|-------|
| Create choice group | ✓ Own | ✗ | ✓ |
| Edit choice group | ✓ Own | ✗ | ✓ |
| Delete choice group | ✓ Own | ✗ | ✓ |
| View all choices | ✓ | ✓ Published | ✓ |
| Select exercises | ✗ | ✓ | ✓ |
| View own selections | ✓ | ✓ | ✓ |
| View all selections | ✗ | ✗ | ✓ |
| Edit own selection | ✗ | ✓ | ✓ |

---

## Files Changed

- `exercise/models.py` - Added ExerciseChoice & StudentExerciseChoice
- `exercise/serializers.py` - Added serializers for choices
- `exercise/views.py` - Added 5 new view classes
- `exercise/urls.py` - Added 8 new URL patterns
- `exercise/admin.py` - Added 2 new admin classes, updated 1

**New Documentation:**
- `EXERCISE_CHOICE_GUIDE.md` - Complete technical guide
- `OPTIONAL_EXERCISES_IMPLEMENTATION.md` - Implementation details

---

## Testing Your Setup

### Test 1: Create via Admin
1. Go to Admin Panel
2. Exercise Choices → Add
3. Fill form, Save
4. See it in list with filters

### Test 2: Create via API
```bash
# Get teacher token first
POST /api/token/
# Use token to create choice
POST /api/exercises/choices/
```

### Test 3: Student Selection
```bash
# Get student token
# List available choices
GET /api/exercises/choices/
# Make selection
POST /api/exercises/student-choices/
# View selection
GET /api/exercises/student-choices/
```

### Test 4: Admin Filters
1. Go to Exercise Choices
2. Filter by "difficulty"
3. See only difficulty-based groups
4. Filter by "published=yes"
5. See only published groups

---

## Error Messages (Persian)

| Error | Cause | Fix |
|-------|-------|-----|
| "شما قبلاً برای این گروه انتخاب کرده‌اید" | Student selected twice | Update instead of create |
| "دسترسی محدود است" | Wrong permissions | Check token is correct role |
| "دسته تمرین یافت نشد" | Wrong ID | Check ID in request |
| "فقط معلمان می‌توانند..." | Non-teacher creating | Use teacher token |

---

## Next Advanced Features

After this works, you can add:
- [ ] Deadline for selections
- [ ] Points for making selection
- [ ] Auto-assign if no selection made
- [ ] Bulk selection via spreadsheet
- [ ] Choice analytics (which exercises are popular)
- [ ] Time tracking per selected exercise
- [ ] Weighted choices (some count more)

---

## Support Commands

```bash
# Check models are correct
python manage.py showmigrations exercise

# See all URL patterns
python manage.py show_urls | grep choice

# Run tests (when ready)
python manage.py test exercise

# Check for errors
python manage.py check

# Shell to test manually
python manage.py shell
```

---

## Database Schema (After Migration)

```sql
-- New tables created:
exercise_exercisechoice
  - id (PK)
  - title
  - description
  - teacher_id (FK)
  - subject_id (FK)
  - choice_type
  - required_choices
  - is_published
  - created_at
  - updated_at

exercise_exercisechoice_exercises (M2M)
  - id (PK)
  - exercisechoice_id (FK)
  - exercise_id (FK)

exercise_studentexercisechoice
  - id (PK)
  - student_id (FK)
  - exercise_choice_group_id (FK)
  - confirmed_at
  - created_at
  - updated_at
  - UNIQUE(student_id, exercise_choice_group_id)

exercise_studentexercisechoice_selected_exercises (M2M)
  - id (PK)
  - studentexercisechoice_id (FK)
  - exercise_id (FK)
```

---

## Troubleshooting

### Migration Fails
```bash
# Check for syntax errors in models
python manage.py check

# Try makemigrations with verbosity
python manage.py makemigrations exercise -v 3

# If conflicts, delete migrations and recreate
```

### Can't See in Admin
```bash
# Check app is in INSTALLED_APPS
python manage.py check

# Check admin.py has @admin.register decorators
# Check models are imported in admin.py
```

### API Returns 404
```bash
# Check URLs are added to urls.py
# Check you're hitting right endpoint
# Check token is valid (not expired)
```

### Permission Denied
```bash
# Check token is for correct user type
# Teachers creating choices must use teacher token
# Students selecting must use student token
```

---

## You're Ready! 🎉

Everything is set up. Just run:

```bash
python manage.py makemigrations exercise
python manage.py migrate
python manage.py runserver
```

Then:
1. Go to Admin → Create choice group
2. Test API endpoints
3. Students can select exercises
4. View results in admin

All files are ready. Enjoy your optional exercises system!
