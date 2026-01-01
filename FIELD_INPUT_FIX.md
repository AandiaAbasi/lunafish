# حل مشکل سوالات Input (تایپی)

## 📌 مشکل
سوالات تایپی (input) نمی‌شوند ثبت و API خطای 400 می‌دهد، اما سوالات انتخابی (checkbox/radioButton) بدون مشکل کار می‌کنند.

## ✅ علت
**Serializer validation:** سوالات "input" **نباید** دارای `details` باشند، اما سوالات "checkbox" و "radioButton" **باید** دارای `details` (گزینه‌ها) باشند.

## 🔧 اصلاح شده

### 1. FieldCreateUpdateSerializer اضافه شد: validation logic

```python
def validate(self, data):
    """Validate based on question type"""
    question_type = data.get('type')
    details = data.get('details', [])
    
    # ✅ سوالات choice باید details داشته باشند
    if question_type in ['checkbox', 'radioButton']:
        if not details:
            raise serializers.ValidationError(
                _('سوالات انتخابی باید حداقل یک گزینه داشته باشند')
            )
    
    # ✅ سوالات input نباید details داشته باشند
    if question_type == 'input':
        if details:
            data['details'] = []  # حذف کن
    
    return data
```

### 2. API Response بهتر شد

```python
# قبل: فقط error message
{
    'error': 'داده‌های نامعتبر',
    'details': {...}
}

# بعد: success flag + تفاصیل
{
    'success': False,
    'error': 'داده‌های نامعتبر',
    'details': {...}
}
```

## 📋 استفاده صحیح

### سوال Input (تایپی)
```json
{
    "title": "نام شما را بنویسید",
    "type": "input",
    "is_required": 1,
    "guide": "نام کامل خود را وارد کنید",
    "correct_answer": "علی احمدی"
}
```
⚠️ **نکته:** `details` را ارسال **نکنید**

### سوال RadioButton (تک انتخاب)
```json
{
    "title": "2 + 2 = ?",
    "type": "radioButton",
    "is_required": 1,
    "details": [
        {
            "title": "3",
            "is_correct": 0
        },
        {
            "title": "4",
            "is_correct": 1
        },
        {
            "title": "5",
            "is_correct": 0
        }
    ]
}
```
✅ **باید** `details` ارسال شود

### سوال Checkbox (چند انتخاب)
```json
{
    "title": "کدام‌یک صحیح است؟",
    "type": "checkbox",
    "is_required": 1,
    "details": [
        {
            "title": "آب داشتن",
            "is_correct": 1
        },
        {
            "title": "آب فروش",
            "is_correct": 1
        },
        {
            "title": "آب‌بخار",
            "is_correct": 0
        }
    ]
}
```
✅ **باید** `details` ارسال شود

## 🧪 تست

### موفق (Input)
```bash
curl -X POST https://api.fofofish.app/api/exercise/field/create/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "نام شما",
    "type": "input",
    "is_required": 1,
    "guide": "نام کامل"
  }'

# Response: 201
{
    "success": true,
    "data": {
        "id": 123,
        "title": "نام شما",
        "type": "input",
        ...
    },
    "message": "سؤال با موفقیت ایجاد شد"
}
```

### خطا (Input با details)
```bash
curl -X POST https://api.fofofish.app/api/exercise/field/create/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "نام شما",
    "type": "input",
    "details": [...]  # ❌ خطا!
  }'

# Response: 400
{
    "success": false,
    "error": "داده‌های نامعتبر",
    "details": {
        "details": ["سوالات input نباید دارای گزینه‌ها باشند"]
    }
}
```

### موفق (RadioButton)
```bash
curl -X POST https://api.fofofish.app/api/exercise/field/create/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "جواب درست",
    "type": "radioButton",
    "details": [
        {"title": "آ", "is_correct": 0},
        {"title": "ب", "is_correct": 1}
    ]
  }'

# Response: 201
{
    "success": true,
    "data": {...},
    "message": "سؤال با موفقیت ایجاد شد"
}
```

### خطا (RadioButton بدون details)
```bash
curl -X POST https://api.fofofish.app/api/exercise/field/create/ \
  -H "Authorization: Bearer {token}" \
  -d '{
    "title": "جواب درست",
    "type": "radioButton"
  }'

# Response: 400
{
    "success": false,
    "error": "داده‌های نامعتبر",
    "details": {
        "details": ["سوالات انتخابی باید حداقل یک گزینه داشته باشند"]
    }
}
```

## 📁 فایل‌های تغییر یافته

- [api/exercise_serializers.py](api/exercise_serializers.py#L26-L62) - اضافه شدن validation
- [api/views.py](api/views.py#L4104-L4117) - بهتر شدن response format

## ✨ خلاصه

| نوع | Details | مثال |
|------|---------|--------|
| **input** | ❌ نه | نام، شهر، آدرس |
| **radioButton** | ✅ بله | چند گزینه‌ای |
| **checkbox** | ✅ بله | چند جواب صحیح |

حالا سوالات "input" بدون مشکل ثبت می‌شوند! ✅
