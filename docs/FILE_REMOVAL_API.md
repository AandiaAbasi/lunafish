# TeachingSubject File Removal API

## Overview
The TeachingSubject update API now supports explicit file removal using boolean flags. This allows teachers to remove the `cover_image` and/or `demo_video` files from a teaching subject without replacing them.

## Implementation Details

### Modified Components

#### 1. New Serializer: `TeachingSubjectUpdateSerializer`
**File:** `api/classroom_serializers.py`

A specialized serializer for update operations that:
- Accepts the same fields as `TeachingSubjectSerializer` (title, description, level, cover_image, demo_video, min_age, max_age, is_active)
- Adds two new write-only boolean fields:
  - `remove_cover_image` (optional, default=False)
  - `remove_demo_video` (optional, default=False)
- Handles file deletion and field nullification in the `update()` method
- Only touches the specified removal flags (explicit removal, not automatic)

#### 2. Updated View: `TeachingSubjectUpdateAPIView`
**File:** `api/views.py`

Enhanced to:
- Use `TeachingSubjectUpdateSerializer` for validation and updates
- Parse removal flags from form data (handles both string and boolean values)
- Return the full subject data using `TeachingSubjectSerializer` after update
- Maintains all existing permission checks and data validation

### Key Features

✅ **Explicit Removal:** Files are only removed if you explicitly set the removal flag to `true`  
✅ **File Storage Cleanup:** Deleted files are actually removed from storage (S3, local disk, etc.)  
✅ **Partial Updates:** You can remove one file while uploading another, or update fields without touching files  
✅ **Backward Compatible:** Existing update requests work exactly as before  
✅ **Multipart Form Support:** Works with `multipart/form-data` for file uploads

## API Usage

### Endpoint
```
POST /api/teaching-subjects/{id}/update/
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | No | Subject title |
| description | string | No | Subject description |
| level | string | No | Level: beginner/intermediate/advanced |
| cover_image | file | No | New cover image (jpg/png) |
| demo_video | file | No | New demo video (mp4/webm) |
| min_age | integer | No | Minimum student age |
| max_age | integer | No | Maximum student age |
| is_active | boolean | No | Whether subject is active |
| **remove_cover_image** | **boolean** | **No** | **Set to true to remove cover_image** |
| **remove_demo_video** | **boolean** | **No** | **Set to true to remove demo_video** |

### Authentication
- Required: JWT token in `Authorization: Bearer {token}` header
- Allowed: Teacher (own subject) or Admin

### Response (200 OK)
```json
{
  "data": {
    "id": 5,
    "teacher_name": "علی محمدی",
    "title": "ریاضیات پایه‌ای",
    "description": "دوره آموزشی ریاضیات برای دانش‌آموزان پایه...",
    "level": "beginner",
    "level_display": "مبتدی",
    "cover_image": null,
    "demo_video": null,
    "min_age": 12,
    "max_age": 18,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "موضوع تدریسی با موفقیت ویرایش شد"
}
```

### Error Responses

**400 Bad Request** - Invalid data:
```json
{
  "error": "داده‌های نامعتبر",
  "details": {
    "level": ["Select a valid choice. invalid is not one of the available choices."]
  }
}
```

**403 Forbidden** - Permission denied:
```json
{
  "error": "شما دسترسی به ویرایش این موضوع ندارید"
}
```

**404 Not Found** - Subject doesn't exist:
```json
{
  "error": "موضوع تدریسی یافت نشد"
}
```

## Usage Examples

### Example 1: Remove only cover_image

**Request (multipart/form-data):**
```bash
curl -X POST http://localhost:8000/api/teaching-subjects/5/update/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "remove_cover_image=true"
```

**Result:** The `cover_image` field is set to `null` in storage, file is deleted.

### Example 2: Remove only demo_video

**Request:**
```bash
curl -X POST http://localhost:8000/api/teaching-subjects/5/update/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "remove_demo_video=true"
```

**Result:** The `demo_video` field is set to `null` in storage, file is deleted.

### Example 3: Remove both files

**Request:**
```bash
curl -X POST http://localhost:8000/api/teaching-subjects/5/update/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "remove_cover_image=true" \
  -F "remove_demo_video=true"
```

**Result:** Both fields set to `null`, both files deleted from storage.

### Example 4: Replace cover_image and remove demo_video

**Request:**
```bash
curl -X POST http://localhost:8000/api/teaching-subjects/5/update/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "cover_image=@/path/to/new_image.jpg" \
  -F "remove_demo_video=true"
```

**Result:** 
- Old cover_image is deleted and replaced with new file
- demo_video is removed (set to null)

### Example 5: Update other fields without removing files

**Request:**
```bash
curl -X POST http://localhost:8000/api/teaching-subjects/5/update/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=ریاضیات پیشرفته" \
  -F "level=advanced"
```

**Result:** Title and level are updated, files remain unchanged.

### Example 6: Python/JavaScript client example

**Python:**
```python
import requests

headers = {
    'Authorization': f'Bearer {jwt_token}'
}

files = {
    'remove_cover_image': (None, 'true'),
}

data = {
    'title': 'Updated Title',
}

response = requests.post(
    'http://localhost:8000/api/teaching-subjects/5/update/',
    headers=headers,
    files=files,
    data=data
)

print(response.json())
```

**JavaScript:**
```javascript
const formData = new FormData();
formData.append('remove_cover_image', 'true');
formData.append('title', 'Updated Title');

const response = await fetch(
  'http://localhost:8000/api/teaching-subjects/5/update/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    },
    body: formData
  }
);

const result = await response.json();
console.log(result);
```

## Implementation Details

### File Removal Logic

When `remove_cover_image=true` or `remove_demo_video=true`:

1. Check if the file field has a value
2. Delete the file from storage using Django's file field `.delete()` method
3. Set the field to `None` (NULL in database)
4. Call `.save()` to persist changes

```python
# From TeachingSubjectUpdateSerializer.update()
if remove_cover_image:
    if instance.cover_image:
        instance.cover_image.delete(save=False)  # Delete from storage
    instance.cover_image = None  # Set field to NULL
```

### Data Validation

The view handles various input formats:

- **String booleans:** `"true"`, `"false"`, `"1"`, `"0"` → converted to Python bool
- **Numeric values:** Ages are validated and converted to integers
- **Choice fields:** Level must match predefined choices (beginner/intermediate/advanced)
- **Array handling:** FormData sometimes wraps single values in arrays

### Storage Compatibility

Works with any Django storage backend:
- Local file system
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
- Custom storage classes

The file deletion is delegated to the storage backend through Django's file field API.

## Notes

- **No automatic deletion:** Files are only removed when you explicitly set the removal flag to `true`
- **Safe partial updates:** You can update any combination of fields without affecting others
- **Permission preserved:** Only the subject's teacher or admins can update
- **Response format:** Always returns the full updated subject object using `TeachingSubjectSerializer`
