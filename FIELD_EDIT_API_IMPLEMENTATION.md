# Field Edit API Implementation

## Summary

Implemented full CRUD update operations for Fields and FieldDetails with integrity checks and file management.

## New Endpoints

### 1. Update Field
**PUT/PATCH** `/api/exercise/field/<field_id>/update/`

- **Content-Type**: `multipart/form-data`
- **Authorization**: Required (Bearer token)
- **Permission**: Only the teacher who created the field can update it
- **Immutable Field**: `type` cannot be changed after creation
- **File Management**: When new files are uploaded, old files are automatically deleted from storage

**Request Body (multipart):**
```
title: "عنوان جدید"
is_required: 1
sort: 0
guide: "راهنمای جدید"
des: "توضیحات جدید"

// برای آپلود فایل جدید (فایل قبلی خودکار پاک می‌شود):
image_path: [NEW_FILE]  // Optional - uploads new file, auto-deletes old one
audio_path: [NEW_FILE]  // Optional - uploads new file, auto-deletes old one
video_path: [NEW_FILE]  // Optional - uploads new file, auto-deletes old one

// برای حذف فایل بدون آپلود فایل جدید:
delete_image_path: true  // Optional - deletes image without uploading new one
delete_audio_path: true  // Optional - deletes audio without uploading new one
delete_video_path: true  // Optional - deletes video without uploading new one
```

**Response (200):**
```json
{
  "ok": true,
  "data": {
    "id": 123,
    "title": "عنوان جدید",
    "type": "input",
    "is_required": 1,
    "sort": 0,
    "guide": "راهنمای جدید",
    "des": "توضیحات جدید",
    "image_path": "exercise_images/abc123.jpg",
    "audio_path": "exercise_audio/def456.mp3",
    "video_path": "exercise_videos/ghi789.mp4"
  },
  "message": "سؤال با موفقیت ویرایش شد"
}
```

**Error Responses:**
- `403 Forbidden` - Not the field owner
- `404 Not Found` - Field doesn't exist
- `400 Bad Request` - Invalid data

---

### 2. Update Field Detail
**PUT/PATCH** `/api/exercise/field/detail/<detail_id>/update/`

- **Content-Type**: `application/json`
- **Authorization**: Required (Bearer token)
- **Permission**: Only the teacher who created the parent field can update details
- **Type-Based Validation**: Validates based on parent field type

**Request Body (JSON):**
```json
{
  "title": "گزینه جدید",
  "second_title": "عنوان دوم",
  "is_required": 0,
  "image_path": "path/to/image.jpg",
  "is_correct": 1,         // For checkbox/radioButton types
  "correct_answer": "پاسخ",  // For input types
  "guide": "راهنما",
  "des": "توضیحات",
  "sort": 0
}
```

**Response (200):**
```json
{
  "ok": true,
  "data": {
    "id": 456,
    "field_id": 123,
    "title": "گزینه جدید",
    "second_title": "عنوان دوم",
    "is_required": 0,
    "image_path": "path/to/image.jpg",
    "is_correct": 1,
    "correct_answer": null,
    "guide": "راهنما",
    "des": "توضیحات",
    "sort": 0
  },
  "message": "جزئیات سؤال با موفقیت ویرایش شد"
}
```

**Validation Rules:**
- **For `input` type**: 
  - `correct_answer` is required
  - `is_correct` should not be used (or must be -1)
- **For `checkbox`/`radioButton` types**:
  - `is_correct` must be 0, 1, or -1
  - `correct_answer` should not be used

**Error Responses:**
- `403 Forbidden` - Not the field owner
- `404 Not Found` - Detail doesn't exist
- `400 Bad Request` - Invalid data or validation errors

---

## Implementation Details

### Serializers (api/exercise_serializers.py)

1. **FieldUpdateSerializer**:
   - Extends `ModelSerializer` for Field model
   - Makes `type` read-only (immutable after creation)
   - Handles file upload with `FileField` overrides
   - Deletes old files before saving new ones
   - Uses UUID-based filenames in organized folders

2. **FieldDetailUpdateSerializer**:
   - Extends `ModelSerializer` for FieldDetail model
   - Validates based on parent Field.type
   - Enforces type-specific field requirements
   - Supports partial updates (PATCH)

### Views (api/views.py)

1. **UpdateFieldAPIView**:
   - Supports PUT and PATCH methods
   - Uses `MultiPartParser` and `FormParser` for file uploads
   - Checks teacher role and ownership
   - Returns formatted response with updated data

2. **UpdateFieldDetailAPIView**:
   - Supports PUT and PATCH methods
   - Uses `JSONParser` for JSON requests
   - Checks teacher role and ownership through parent field
   - Uses `select_related('field')` for efficiency

### URLs (api/urls.py)

Added two new routes:
```python
path('exercise/field/<int:field_id>/update/', views.UpdateFieldAPIView.as_view())
path('exercise/field/detail/<int:detail_id>/update/', views.UpdateFieldDetailAPIView.as_view())
```

---

## File Management

### Automatic File Deletion

When updating a field with new files:

1. **Old File Detected**: Checks if field has existing file path
2. **Delete Old**: Attempts to delete the old file from storage
3. **Save New**: Generates UUID-based filename and saves new file
4. **Update Path**: Updates the model field with new path

**File Organization:**
- Images: `exercise_images/UUID.ext`
- Audio: `exercise_audio/UUID.ext`
- Video: `exercise_videos/UUID.ext`

**Error Handling**: If old file deletion fails (file not found, permission error), the error is caught and ignored to prevent update failure.

---

## Security & Integrity

### Permission Checks

✅ Only authenticated teachers can update  
✅ Only field owner can update field  
✅ Only field owner can update field details  
✅ Type field is immutable after creation  

### Validation Rules

✅ Type-specific validation for field details  
✅ Required fields enforced based on field type  
✅ Invalid field combinations rejected  

### Data Integrity

✅ Old files deleted when new ones uploaded  
✅ Soft delete with django-safedelete  
✅ Foreign key relationships maintained  

---

## Testing

### Test Update Field - Upload New File
```bash
curl -X PUT "https://fofofish.app/api/exercise/field/123/update/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=عنوان جدید" \
  -F "is_required=1" \
  -F "sort=0" \
  -F "audio_path=@new_audio.mp3"
```

### Test Update Field - Delete File Without Upload
```bash
curl -X PUT "https://fofofish.app/api/exercise/field/123/update/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=عنوان" \
  -F "delete_image_path=true" \
  -F "delete_audio_path=true"
```

### Test Update Field - Mixed (Delete One, Upload Another)
```bash
curl -X PUT "https://fofofish.app/api/exercise/field/123/update/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=عنوان" \
  -F "delete_image_path=true" \
  -F "audio_path=@new_audio.mp3"
```

### Test Update Field Detail
```bash
curl -X PUT "https://fofofish.app/api/exercise/field/detail/456/update/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "گزینه جدید",
    "is_correct": 1,
    "sort": 0
  }'
```

---

## Complete API Flow

### Creating a Field (Two-Step):
1. **POST** `/api/exercise/field/create/` - Create field (multipart)
2. **POST** `/api/exercise/field/{field_id}/details/` - Add details (JSON)

### Updating a Field:
3. **PUT** `/api/exercise/field/{field_id}/update/` - Update field (multipart)
4. **PUT** `/api/exercise/field/detail/{detail_id}/update/` - Update detail (JSON)

### Deleting a Field:
5. **DELETE** `/api/exercise/field/{field_id}/delete/` - Delete field

### Listing Fields:
6. **GET** `/api/exercise/fields/teacher/` - List teacher's fields

---

## Frontend Implementation Guide

### 1. Update Field (React Native / Expo)

```typescript
// services/practiceService.ts

export const updateField = async (
  token: string,
  fieldId: number,
  fieldData: {
    title?: string;
    is_required?: number;
    sort?: number;
    guide?: string;
    des?: string;
  },
  files?: {
    image_path?: string;  // File URI to upload
    audio_path?: string;  // File URI to upload
    video_path?: string;  // File URI to upload
  },
  deleteFlags?: {
    delete_image_path?: boolean;  // Set true to delete without upload
    delete_audio_path?: boolean;  // Set true to delete without upload
    delete_video_path?: boolean;  // Set true to delete without upload
  }
): Promise<any> => {
  const formData = new FormData();
  
  // Add text fields
  if (fieldData.title !== undefined) formData.append('title', fieldData.title);
  if (fieldData.is_required !== undefined) formData.append('is_required', String(fieldData.is_required));
  if (fieldData.sort !== undefined) formData.append('sort', String(fieldData.sort));
  if (fieldData.guide !== undefined) formData.append('guide', fieldData.guide);
  if (fieldData.des !== undefined) formData.append('des', fieldData.des);
  
  // Add file uploads
  if (files?.image_path) {
    const filename = files.image_path.split('/').pop() || 'image.jpg';
    formData.append('image_path', {
      uri: files.image_path,
      name: filename,
      type: 'image/jpeg',
    } as any);
  }
  
  if (files?.audio_path) {
    const filename = files.audio_path.split('/').pop() || 'audio.mp3';
    formData.append('audio_path', {
      uri: files.audio_path,
      name: filename,
      type: 'audio/mpeg',
    } as any);
  }
  
  if (files?.video_path) {
    const filename = files.video_path.split('/').pop() || 'video.mp4';
    formData.append('video_path', {
      uri: files.video_path,
      name: filename,
      type: 'video/mp4',
    } as any);
  }
  
  // Add deletion flags
  if (deleteFlags?.delete_image_path) {
    formData.append('delete_image_path', 'true');
  }
  if (deleteFlags?.delete_audio_path) {
    formData.append('delete_audio_path', 'true');
  }
  if (deleteFlags?.delete_video_path) {
    formData.append('delete_video_path', 'true');
  }
  
  const response = await axios.put(
    `${API_BASE}/exercise/field/${fieldId}/update/`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  
  if (response.data.ok) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to update field');
};

export const updateFieldDetail = async (
  token: string,
  detailId: number,
  detailData: {
    title?: string;
    second_title?: string;
    is_required?: number;
    image_path?: string;
    is_correct?: number;
    correct_answer?: string;
    guide?: string;
    des?: string;
    sort?: number;
  }
): Promise<any> => {
  const response = await axios.put(
    `${API_BASE}/exercise/field/detail/${detailId}/update/`,
    detailData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  if (response.data.ok) {
    return response.data.data;
  }
  throw new Error(response.data.error || 'Failed to update detail');
};

export const deleteField = async (
  token: string,
  fieldId: number
): Promise<void> => {
  const response = await axios.delete(
    `${API_BASE}/exercise/field/${fieldId}/delete/`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  
  if (!response.data.ok) {
    throw new Error(response.data.error || 'Failed to delete field');
  }
};
```

### 2. Component Usage Examples

#### Example 1: Edit Field - Update Title Only
```typescript
const handleUpdateTitle = async () => {
  try {
    await updateField(
      authToken,
      fieldId,
      { title: 'عنوان جدید' }
    );
    Alert.alert('موفق', 'عنوان با موفقیت ویرایش شد');
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 2: Edit Field - Upload New Audio File
```typescript
const handleUploadNewAudio = async () => {
  try {
    const result = await DocumentPicker.getDocumentAsync({
      type: 'audio/*',
    });
    
    if (result.type === 'success') {
      await updateField(
        authToken,
        fieldId,
        { title: currentTitle },
        { audio_path: result.uri }
      );
      Alert.alert('موفق', 'فایل صوتی جدید آپلود شد');
    }
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 3: Edit Field - Delete Image Without Upload
```typescript
const handleDeleteImage = async () => {
  try {
    await updateField(
      authToken,
      fieldId,
      {},
      undefined,
      { delete_image_path: true }
    );
    Alert.alert('موفق', 'تصویر حذف شد');
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 4: Edit Field - Mixed Operation
```typescript
const handleMixedUpdate = async () => {
  try {
    // حذف تصویر قبلی، آپلود صدای جدید، و تغییر عنوان
    await updateField(
      authToken,
      fieldId,
      { 
        title: 'عنوان جدید',
        guide: 'راهنمای جدید'
      },
      { audio_path: newAudioUri },
      { delete_image_path: true }
    );
    Alert.alert('موفق', 'تغییرات با موفقیت ذخیره شد');
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 5: Edit Detail - Update Multiple Choice Option
```typescript
const handleUpdateChoice = async () => {
  try {
    await updateFieldDetail(
      authToken,
      detailId,
      {
        title: 'گزینه ویرایش شده',
        is_correct: 1,  // Mark as correct answer
        guide: 'توضیح این گزینه'
      }
    );
    Alert.alert('موفق', 'گزینه ویرایش شد');
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 6: Edit Detail - Update Input Type Answer
```typescript
const handleUpdateInputAnswer = async () => {
  try {
    await updateFieldDetail(
      authToken,
      detailId,
      {
        title: 'سوال ویرایش شده',
        correct_answer: 'پاسخ صحیح جدید'
      }
    );
    Alert.alert('موفق', 'پاسخ صحیح ویرایش شد');
  } catch (error) {
    Alert.alert('خطا', error.message);
  }
};
```

#### Example 7: Delete Field
```typescript
const handleDeleteField = async () => {
  Alert.alert(
    'تایید حذف',
    'آیا مطمئن هستید که می‌خواهید این سؤال را حذف کنید؟',
    [
      { text: 'لغو', style: 'cancel' },
      {
        text: 'حذف',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteField(authToken, fieldId);
            Alert.alert('موفق', 'سؤال با موفقیت حذف شد');
            navigation.goBack();
          } catch (error) {
            Alert.alert('خطا', error.message);
          }
        },
      },
    ]
  );
};
```

### 3. UI State Management

```typescript
interface EditFieldState {
  title: string;
  guide: string;
  des: string;
  is_required: number;
  sort: number;
  
  // File states
  currentImageUri: string | null;
  currentAudioUri: string | null;
  currentVideoUri: string | null;
  
  newImageUri: string | null;
  newAudioUri: string | null;
  newVideoUri: string | null;
  
  // Deletion flags
  shouldDeleteImage: boolean;
  shouldDeleteAudio: boolean;
  shouldDeleteVideo: boolean;
}

const EditFieldScreen = () => {
  const [state, setState] = useState<EditFieldState>({
    title: field.title,
    guide: field.guide,
    des: field.des,
    is_required: field.is_required,
    sort: field.sort,
    
    currentImageUri: field.image_path,
    currentAudioUri: field.audio_path,
    currentVideoUri: field.video_path,
    
    newImageUri: null,
    newAudioUri: null,
    newVideoUri: null,
    
    shouldDeleteImage: false,
    shouldDeleteAudio: false,
    shouldDeleteVideo: false,
  });
  
  const handleSave = async () => {
    try {
      await updateField(
        authToken,
        fieldId,
        {
          title: state.title,
          guide: state.guide,
          des: state.des,
          is_required: state.is_required,
          sort: state.sort,
        },
        {
          image_path: state.newImageUri || undefined,
          audio_path: state.newAudioUri || undefined,
          video_path: state.newVideoUri || undefined,
        },
        {
          delete_image_path: state.shouldDeleteImage,
          delete_audio_path: state.shouldDeleteAudio,
          delete_video_path: state.shouldDeleteVideo,
        }
      );
      Alert.alert('موفق', 'تغییرات ذخیره شد');
    } catch (error) {
      Alert.alert('خطا', error.message);
    }
  };
  
  return (
    <View>
      {/* UI components */}
      <Button title="ذخیره تغییرات" onPress={handleSave} />
    </View>
  );
};
```

---

## Important Notes for Frontend Team

### ⚠️ Critical Rules

1. **Type Field is Immutable**: 
   - هرگز نمی‌توان `type` فیلد را بعد از ساخت تغییر داد
   - اگر بخواهید نوع سوال را تغییر دهید، باید سوال جدید بسازید

2. **File Deletion Behavior**:
   - اگر فایل جدید آپلود کنید → فایل قبلی خودکار پاک می‌شود
   - اگر `delete_*_path=true` بفرستید → فایل پاک می‌شود و چیزی جایگزین نمی‌شود
   - **نمی‌توانید هم‌زمان** فایل جدید آپلود کنید و `delete_*_path=true` بفرستید (فایل جدید اولویت دارد)

3. **Detail Validation**:
   - برای سوالات `input`: فیلد `correct_answer` اجباری است
   - برای سوالات `checkbox`/`radioButton`: فیلد `is_correct` اجباری است (0=غلط، 1=درست، -1=متن)

4. **Ownership Check**:
   - فقط معلمی که سوال را ساخته می‌تواند آن را ویرایش یا حذف کند
   - اگر کاربر owner نباشد، `403 Forbidden` دریافت می‌کند

5. **Partial Updates**:
   - می‌توانید فقط فیلدهایی که می‌خواهید تغییر دهید را بفرستید
   - فیلدهای ارسال نشده تغییر نمی‌کنند

### ✅ Best Practices

1. **Show Confirmation**: همیشه قبل از حذف فایل یا سوال، از کاربر تایید بگیرید
2. **Loading States**: در حین آپلود فایل یا ذخیره تغییرات، loading indicator نشان دهید
3. **Error Handling**: پیام‌های خطا را به فارسی و واضح نمایش دهید
4. **Preview Changes**: قبل از ذخیره، تغییرات را به کاربر نشان دهید
5. **Optimistic Updates**: برای UX بهتر، تغییرات را موقتاً در UI اعمال کنید و در صورت خطا برگردانید

---

## Error Codes Reference

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | عملیات موفقیت‌آمیز بود |
| 204 | Deleted | سوال حذف شد |
| 400 | Invalid Data | داده‌های ورودی اشتباه است - جزئیات را بررسی کنید |
| 403 | Forbidden | کاربر اجازه این عملیات را ندارد (یا teacher نیست یا owner نیست) |
| 404 | Not Found | سوال یا جزئیات پیدا نشد |

---

## API Response Examples

### Successful Update
```json
{
  "ok": true,
  "data": {
    "id": 123,
    "title": "عنوان جدید",
    "type": "input",
    "is_required": 1,
    "sort": 0,
    "guide": "راهنما",
    "des": "توضیحات",
    "image_path": null,
    "audio_path": "exercise_audio/abc123.mp3",
    "video_path": null
  },
  "message": "سؤال با موفقیت ویرایش شد"
}
```

### Validation Error
```json
{
  "ok": false,
  "error": "داده‌های نامعتبر",
  "details": {
    "title": ["این مقدار لازم است"],
    "is_correct": ["برای سوالات چند گزینه‌ای، is_correct باید 0، 1 یا -1 باشد"]
  }
}
```

### Permission Error
```json
{
  "ok": false,
  "error": "شما مجاز به ویرایش این سؤال نیستید"
}
```
