# TWO-STEP Field Creation Implementation

## Complete Code for Two-Step Flow

### 1. Serializers (Already Added to exercise_serializers.py)

The serializers are already in place:
- `FieldCreateSerializer` - Step 1 (multipart, NO details)
- `FieldDetailBulkSerializer` - Step 2 (JSON, replaces all details)

### 2. Views (Add to api/views.py)

Replace the existing `CreateFieldAPIView` with these two views:

```python
# ==================== STEP 1: Create Field (Multipart, NO Details) ====================

class CreateFieldStep1APIView(APIView):
    """
    STEP 1: Create Field with file uploads (multipart/form-data)
    
    Does NOT accept details. Details are created in Step 2 using the returned field_id.
    Only teachers can create fields.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # ONLY multipart, NO JSON
    
    @extend_schema(
        tags=['Exercise - Questions (Two-Step)'],
        summary='Step 1: Create Field (NO details)',
        description='Create question field with file uploads. Does NOT accept details array.',
        request=None,
        responses={
            201: OpenApiResponse(description="Field created successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Only teachers can create fields"),
        }
    )
    def post(self, request):
        from exercise.models import Field
        from .exercise_serializers import FieldCreateSerializer
        
        # Only teachers can create fields
        if request.user.role != 'teacher':
            return Response({
                'ok': False,
                'error': _('تنها معلمان می‌توانند سؤال ایجاد کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Ignore any 'details' or 'details[...]' keys completely
        # Extract only the allowed fields
        field_data = {}
        allowed_fields = ['title', 'type', 'is_required', 'sort', 'guide', 'des']
        for field in allowed_fields:
            if field in request.data:
                field_data[field] = request.data[field]
        
        # Add file fields
        for file_field in ['image_path', 'audio_path', 'video_path']:
            if file_field in request.FILES:
                field_data[file_field] = request.FILES[file_field]
        
        serializer = FieldCreateSerializer(data=field_data, context={'request': request})
        if serializer.is_valid():
            field = serializer.save()
            return Response({
                'ok': True,
                'data': {
                    'id': field.id,
                    'title': field.title,
                    'type': field.type,
                    'is_required': field.is_required,
                    'sort': field.sort,
                    'guide': field.guide,
                    'des': field.des,
                    'image_path': field.image_path,
                    'audio_path': field.audio_path,
                    'video_path': field.video_path,
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'ok': False,
            'error': _('داده‌های نامعتبر'),
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ==================== STEP 2: Create FieldDetails (JSON) ====================

class CreateFieldDetailsStep2APIView(APIView):
    """
    STEP 2: Create/Replace FieldDetails for a Field (JSON)
    
    Replaces ALL existing details for the specified field_id.
    Validates based on Field.type.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser,)  # ONLY JSON, NO multipart
    
    @extend_schema(
        tags=['Exercise - Questions (Two-Step)'],
        summary='Step 2: Create FieldDetails',
        description='Create/replace all details for a field. Uses field_id from URL. Validates based on field type.',
        request=None,
        responses={
            201: OpenApiResponse(description="Details created successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Field not found"),
        }
    )
    def post(self, request, field_id):
        from exercise.models import Field
        from .exercise_serializers import FieldDetailBulkSerializer, FieldDetailSerializer
        
        # Get the field
        try:
            field = Field.objects.get(id=field_id)
        except Field.DoesNotExist:
            return Response({
                'ok': False,
                'error': _('سؤال یافت نشد')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permission - only field owner (teacher) can add details
        if request.user.role != 'teacher':
            return Response({
                'ok': False,
                'error': _('تنها معلمان می‌توانند details ایجاد کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Optional: Check if user is the field owner
        try:
            if hasattr(field, 'teacher') and field.teacher != request.user:
                return Response({
                    'ok': False,
                    'error': _('شما مجاز به ویرایش این سؤال نیستید')
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            pass  # teacher field might not exist yet
        
        # Validate and create details
        serializer = FieldDetailBulkSerializer(
            data=request.data,
            context={'field': field, 'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            
            # Serialize the created details for response
            details_serializer = FieldDetailSerializer(result['details'], many=True)
            
            return Response({
                'ok': True,
                'data': {
                    'field_id': result['field_id'],
                    'details': details_serializer.data
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'ok': False,
            'error': _('داده‌های نامعتبر'),
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
```

### 3. URLs (Add to api/urls.py)

Replace or add these URL patterns:

```python
from .views import CreateFieldStep1APIView, CreateFieldDetailsStep2APIView

urlpatterns = [
    # ... existing patterns ...
    
    # TWO-STEP Field Creation
    path('exercise/field/create/', CreateFieldStep1APIView.as_view(), name='create-field-step1'),
    path('exercise/field/<int:field_id>/details/', CreateFieldDetailsStep2APIView.as_view(), name='create-field-details-step2'),
    
    # ... other patterns ...
]
```

## Frontend Implementation (React Native / Expo)

### Step 1: Create Field (Multipart)

```typescript
// practiceService.ts
export const createFieldStep1 = async (
  token: string,
  fieldData: {
    title: string;
    type: 'input' | 'checkbox' | 'radioButton';
    is_required: number;
    sort: number;
    guide?: string;
    des?: string;
  },
  files?: {
    image_path?: string;
    audio_path?: string;
    video_path?: string;
  }
): Promise<{ id: number }> => {
  const formData = new FormData();
  
  // Add basic fields
  formData.append('title', fieldData.title);
  formData.append('type', fieldData.type);
  formData.append('is_required', String(fieldData.is_required));
  formData.append('sort', String(fieldData.sort));
  if (fieldData.guide) formData.append('guide', fieldData.guide);
  if (fieldData.des) formData.append('des', fieldData.des);
  
  // Add files
  if (files?.image_path) {
    const filename = files.image_path.split('/').pop() || 'image.jpg';
    formData.append('image_path', {
      uri: files.image_path,
      name: filename,
      type: 'image/jpeg',
    } as any);
  }
  
  // Similar for audio and video...
  
  const response = await axios.post(
    `${API_BASE}/exercise/field/create/`,
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
  throw new Error(response.data.error || 'Failed to create field');
};
```

### Step 2: Create Details (JSON)

```typescript
export const createFieldDetailsStep2 = async (
  token: string,
  fieldId: number,
  details: Array<{
    title: string;
    sort?: number;
    correct_answer?: string;  // for input type
    is_correct?: number;      // for checkbox/radioButton
  }>
): Promise<any> => {
  const response = await axios.post(
    `${API_BASE}/exercise/field/${fieldId}/details/`,
    { details },
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
  throw new Error(response.data.error || 'Failed to create details');
};
```

### Complete Flow in Component

```typescript
const handleSubmit = async () => {
  setLoading(true);
  
  try {
    // STEP 1: Create Field
    const fieldResult = await createFieldStep1(
      authToken,
      {
        title: title.trim(),
        type: fieldType as 'input' | 'checkbox' | 'radioButton',
        is_required: 1,
        sort: 0,
        guide: guide.trim() || undefined,
        des: description.trim() || undefined,
      },
      {
        image_path: imageFiles[0]?.uri,
        audio_path: audioFiles[0]?.uri,
        video_path: videoFiles[0]?.uri,
      }
    );
    
    console.log(`✅ Field created with ID: ${fieldResult.id}`);
    
    // STEP 2: Create Details
    const detailsArray = fieldType === 'input'
      ? inputOptions.map((opt, idx) => ({
          title: opt.title.trim(),
          correct_answer: opt.correctAnswer.trim(),
          sort: idx,
        }))
      : choiceOptions.map((opt, idx) => ({
          title: opt.title.trim(),
          is_correct: opt.isCorrect ? 1 : 0,
          sort: idx,
        }));
    
    await createFieldDetailsStep2(authToken, fieldResult.id, detailsArray);
    
    console.log(`✅ Details created for Field ${fieldResult.id}`);
    
    Alert.alert('Success', 'سؤال با موفقیت ایجاد شد');
  } catch (error) {
    const message = parseApiError(error);
    Alert.alert('Error', message);
  } finally {
    setLoading(false);
  }
};
```

## Benefits of Two-Step Approach

1. **✅ No multipart parsing issues** - Details are sent as pure JSON
2. **✅ Clean separation** - Files and data are handled separately
3. **✅ Better validation** - Type-specific validation in Step 2
4. **✅ Atomic details replacement** - All details replaced in one transaction
5. **✅ Easier debugging** - Clear separation of concerns
6. **✅ Scalable** - Can add update endpoint using same Step 2 logic

## Testing

### Test Step 1 (cURL)
```bash
curl -X POST "https://fofofish.app/api/exercise/field/create/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=تست سوال" \
  -F "type=input" \
  -F "is_required=1" \
  -F "sort=0" \
  -F "audio_path=@audio.mp3"
```

### Test Step 2 (cURL)
```bash
curl -X POST "https://fofofish.app/api/exercise/field/123/details/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "details": [
      {"title": "سوال اول", "correct_answer": "پاسخ اول", "sort": 0}
    ]
  }'
```
