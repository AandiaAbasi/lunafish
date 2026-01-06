# Field Creation API - Frontend Integration Guide

## Overview
This guide explains how to send data from the frontend to create practice fields (questions) in the exercise system.

## Endpoint
```
POST /api/exercise/field/create/
```

## Authentication
Requires JWT token in Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Content-Type
**IMPORTANT:** Must use multipart/form-data for file upload support
```
Content-Type: multipart/form-data
```

---

## Request Body Structure

### Basic Fields (Required for All Types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ Yes | Question title/text |
| `type` | string | ✅ Yes | Question type: `"input"`, `"checkbox"`, or `"radioButton"` |
| `is_required` | string | ✅ Yes | Is question required: `"0"` or `"1"` |
| `sort` | string | ✅ Yes | Sort order (numeric string) |
| `guide` | string | ❌ No | Guidance text for the question |
| `des` | string | ❌ No | Description/additional info |

### File Upload Fields (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `image_path` | File | Image file for the question |
| `audio_path` | File | Audio file for the question |
| `video_path` | File | Video file for the question |

---

## Details Array Format

**CRITICAL:** Details must be sent using **form array notation**, NOT as JSON string.

### Format Pattern
```
details[INDEX][FIELD_NAME]
```

### For Input Type Questions (`type: "input"`)

Input questions are typing questions where students write text answers.

**Required fields per detail:**
```
details[0][title]: "Question prompt text"
details[0][correct_answer]: "Expected correct answer"
details[0][sort]: "0"
```

**Example:**
```
details[0][title]: "کلمه اول را بنویسید"
details[0][correct_answer]: "سلام"
details[0][sort]: "0"

details[1][title]: "کلمه دوم را بنویسید"
details[1][correct_answer]: "خداحافظ"
details[1][sort]: "1"
```

### For Checkbox/RadioButton Types (`type: "checkbox"` or `type: "radioButton"`)

These are multiple choice questions.

**Required fields per detail:**
```
details[0][title]: "Option text"
details[0][is_correct]: "0" or "1"
details[0][sort]: "0"
```

**Example:**
```
details[0][title]: "گزینه الف"
details[0][is_correct]: "1"
details[0][sort]: "0"

details[1][title]: "گزینه ب"
details[1][is_correct]: "0"
details[1][sort]: "1"

details[2][title]: "گزینه ج"
details[2][is_correct]: "1"
details[2][sort]: "2"
```

---

## Complete Examples

### Example 1: Input Type with Audio File

```javascript
const formData = new FormData();

// Basic fields
formData.append('title', 'تمرین املا');
formData.append('type', 'input');
formData.append('is_required', '1');
formData.append('sort', '0');
formData.append('guide', 'به صدا گوش دهید و کلمه را بنویسید');

// Details array (form notation)
formData.append('details[0][title]', 'کلمه اول را بنویسید');
formData.append('details[0][correct_answer]', 'سلام');
formData.append('details[0][sort]', '0');

formData.append('details[1][title]', 'کلمه دوم را بنویسید');
formData.append('details[1][correct_answer]', 'خداحافظ');
formData.append('details[1][sort]', '1');

// File upload
const audioFile = document.getElementById('audioInput').files[0];
formData.append('audio_path', audioFile);

// Send request
fetch('/api/exercise/field/create/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        // Don't set Content-Type - let browser set it with boundary
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

### Example 2: Checkbox Type with Image

```javascript
const formData = new FormData();

// Basic fields
formData.append('title', 'انتخاب پاسخ‌های صحیح');
formData.append('type', 'checkbox');
formData.append('is_required', '1');
formData.append('sort', '0');
formData.append('guide', 'چند گزینه صحیح است');
formData.append('des', 'می‌توانید چند گزینه انتخاب کنید');

// Details array - multiple choice options
formData.append('details[0][title]', 'گزینه الف');
formData.append('details[0][is_correct]', '1');  // Correct
formData.append('details[0][sort]', '0');

formData.append('details[1][title]', 'گزینه ب');
formData.append('details[1][is_correct]', '0');  // Incorrect
formData.append('details[1][sort]', '1');

formData.append('details[2][title]', 'گزینه ج');
formData.append('details[2][is_correct]', '1');  // Correct
formData.append('details[2][sort]', '2');

formData.append('details[3][title]', 'گزینه د');
formData.append('details[3][is_correct]', '0');  // Incorrect
formData.append('details[3][sort]', '3');

// File upload
const imageFile = document.getElementById('imageInput').files[0];
formData.append('image_path', imageFile);

// Send request
fetch('/api/exercise/field/create/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

### Example 3: RadioButton Type (Single Choice)

```javascript
const formData = new FormData();

// Basic fields
formData.append('title', 'کدام گزینه صحیح است؟');
formData.append('type', 'radioButton');
formData.append('is_required', '1');
formData.append('sort', '0');

// Details array - only ONE can be correct
formData.append('details[0][title]', 'پاسخ اول');
formData.append('details[0][is_correct]', '0');
formData.append('details[0][sort]', '0');

formData.append('details[1][title]', 'پاسخ دوم');
formData.append('details[1][is_correct]', '1');  // This is the correct answer
formData.append('details[1][sort]', '1');

formData.append('details[2][title]', 'پاسخ سوم');
formData.append('details[2][is_correct]', '0');
formData.append('details[2][sort]', '2');

// Send request
fetch('/api/exercise/field/create/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

### Example 4: Multiple File Uploads

```javascript
const formData = new FormData();

formData.append('title', 'سوال کامل با تصویر، صدا و ویدیو');
formData.append('type', 'checkbox');
formData.append('is_required', '1');
formData.append('sort', '0');

// Add options
formData.append('details[0][title]', 'گزینه یک');
formData.append('details[0][is_correct]', '1');
formData.append('details[0][sort]', '0');

formData.append('details[1][title]', 'گزینه دو');
formData.append('details[1][is_correct]', '0');
formData.append('details[1][sort]', '1');

// Upload multiple files
const imageFile = document.getElementById('imageInput').files[0];
const audioFile = document.getElementById('audioInput').files[0];
const videoFile = document.getElementById('videoInput').files[0];

if (imageFile) formData.append('image_path', imageFile);
if (audioFile) formData.append('audio_path', audioFile);
if (videoFile) formData.append('video_path', videoFile);

// Send request
fetch('/api/exercise/field/create/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

---

## React/React Native Example

### Using Axios in React

```javascript
import axios from 'axios';

const createField = async (fieldData) => {
    const formData = new FormData();
    
    // Basic fields
    formData.append('title', fieldData.title);
    formData.append('type', fieldData.type);
    formData.append('is_required', fieldData.isRequired ? '1' : '0');
    formData.append('sort', fieldData.sort.toString());
    
    if (fieldData.guide) {
        formData.append('guide', fieldData.guide);
    }
    
    if (fieldData.des) {
        formData.append('des', fieldData.des);
    }
    
    // Details array
    fieldData.details.forEach((detail, index) => {
        formData.append(`details[${index}][title]`, detail.title);
        formData.append(`details[${index}][sort]`, index.toString());
        
        if (fieldData.type === 'input') {
            formData.append(`details[${index}][correct_answer]`, detail.correctAnswer);
        } else {
            formData.append(`details[${index}][is_correct]`, detail.isCorrect ? '1' : '0');
        }
    });
    
    // Files
    if (fieldData.imageFile) {
        formData.append('image_path', fieldData.imageFile);
    }
    
    if (fieldData.audioFile) {
        formData.append('audio_path', fieldData.audioFile);
    }
    
    if (fieldData.videoFile) {
        formData.append('video_path', fieldData.videoFile);
    }
    
    try {
        const response = await axios.post(
            '/api/exercise/field/create/',
            formData,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data',
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error creating field:', error.response?.data);
        throw error;
    }
};

// Usage
const fieldData = {
    title: 'سوال نمونه',
    type: 'checkbox',
    isRequired: true,
    sort: 0,
    guide: 'راهنمای سوال',
    details: [
        { title: 'گزینه 1', isCorrect: true },
        { title: 'گزینه 2', isCorrect: false },
    ],
    imageFile: selectedImage,  // File object from input
};

createField(fieldData)
    .then(result => console.log('Field created:', result))
    .catch(error => console.error('Failed:', error));
```

---

## Response Format

### Success Response (201 Created)

```json
{
    "id": 123,
    "title": "تمرین املا",
    "type": "input",
    "is_required": true,
    "image_path": "exercise_images/abc123def456.jpg",
    "audio_path": "exercise_audio/xyz789.mp3",
    "video_path": null,
    "guide": "به صدا گوش دهید",
    "des": "توضیحات",
    "sort": 0,
    "details": [
        {
            "id": 456,
            "title": "کلمه اول را بنویسید",
            "second_title": null,
            "image_path": null,
            "is_correct": null,
            "correct_answer": "سلام",
            "guide": null,
            "des": null,
            "sort": 0,
            "is_required": null
        }
    ]
}
```

### Error Responses

#### 400 Bad Request - Missing Details
```json
{
    "details": [
        "سوالات تایپی باید حداقل یک detail برای ذخیره پاسخ صحیح داشته باشند"
    ]
}
```

#### 400 Bad Request - Missing Correct Answer
```json
{
    "details": [
        "سوالات تایپی باید حداقل یک detail با correct_answer داشته باشند"
    ]
}
```

#### 400 Bad Request - Validation Error
```json
{
    "title": ["این فیلد الزامی است"],
    "type": ["این فیلد الزامی است"]
}
```

#### 401 Unauthorized
```json
{
    "detail": "توکن احراز هویت ارائه نشده است."
}
```

---

## Important Notes

### ✅ DO's

1. **Always use `multipart/form-data`** when uploading files
2. **Use form array notation** for details: `details[0][title]`, `details[0][correct_answer]`
3. **Send is_required as string**: `"0"` or `"1"`, not boolean
4. **Send is_correct as string**: `"0"` or `"1"` for choice questions
5. **Include at least one detail** for all question types
6. **For input type**: Each detail must have `correct_answer`
7. **For checkbox/radioButton**: Each detail must have `is_correct`
8. **Let browser set Content-Type boundary** automatically (don't manually set it in JavaScript)

### ❌ DON'Ts

1. ❌ Don't send details as JSON string
2. ❌ Don't use `application/json` content type when uploading files
3. ❌ Don't send boolean values (use strings `"0"` or `"1"`)
4. ❌ Don't forget to include Authorization header
5. ❌ Don't manually set Content-Type boundary in fetch/axios
6. ❌ Don't create input-type questions without `correct_answer` in details
7. ❌ Don't create checkbox/radioButton questions without `is_correct` in details

---

## Common Errors and Solutions

### Error: "یک رشته معتبر نیست" (Not a valid string)
**Cause:** Trying to upload files without using multipart/form-data

**Solution:** Ensure Content-Type is `multipart/form-data` and files are appended to FormData correctly

### Error: "سوالات تایپی باید حداقل یک detail برای ذخیره پاسخ صحیح داشته باشند"
**Cause:** Input-type questions submitted without details array

**Solution:** Always include at least one detail with `correct_answer` for input-type questions

### Error: Details not being parsed
**Cause:** Sending details as JSON string instead of form array notation

**Solution:** Use `details[0][title]` format, not `details: '[{...}]'`

### Error: "توکن احراز هویت ارائه نشده است"
**Cause:** Missing or invalid JWT token

**Solution:** Include valid JWT token in Authorization header: `Bearer <token>`

---

## Testing with cURL

```bash
curl -X POST "https://fofofish.app/api/exercise/field/create/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=تست سوال" \
  -F "type=input" \
  -F "is_required=1" \
  -F "sort=0" \
  -F "details[0][title]=پاسخ را بنویسید" \
  -F "details[0][correct_answer]=جواب صحیح" \
  -F "details[0][sort]=0" \
  -F "audio_path=@/path/to/audio.mp3"
```

---

## Question Types Summary

| Type | Purpose | Details Requirements |
|------|---------|---------------------|
| `input` | Typing/text entry | `correct_answer` required in each detail |
| `checkbox` | Multiple choice (multiple correct) | `is_correct` required in each detail |
| `radioButton` | Single choice (one correct) | `is_correct` required in each detail |

---

## File Upload Specifications

- **Supported file fields:** `image_path`, `audio_path`, `video_path`
- **All file uploads are optional**
- **Files are automatically saved with UUID filenames** to prevent conflicts
- **Files are organized in folders:**
  - Images: `exercise_images/`
  - Audio: `exercise_audio/`
  - Videos: `exercise_videos/`
- **Original file extensions are preserved**

---

## Need Help?

If you encounter issues:
1. Check that you're using `multipart/form-data`
2. Verify the details array is in correct form notation format
3. Ensure authentication token is valid
4. Check that required fields for question type are included
5. Review the error response for specific validation messages
