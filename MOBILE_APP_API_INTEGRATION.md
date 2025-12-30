# 🔌 Exercise API - Mobile App Integration Guide

سازگار با React Native، Flutter، و سایر فریمورک‌های موبایل

---

## 🔐 احراز هویت

### دریافت Token

```javascript
// 1. ارسال OTP
POST /api/send-otp/
{
  "identifier": "09121234567",  // شماره تلفن یا ایمیل
  "purpose": "login"
}

// Response 200 OK
{
  "success": true,
  "message": "Verification code sent."
}
```

```javascript
// 2. تایید OTP و دریافت Token
POST /api/verify-otp/
{
  "identifier": "09121234567",
  "code": "123456"
}

// Response 200 OK
{
  "success": true,
  "user": {
    "id": 1,
    "name": "علی حسینی",
    "role": "student"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLC...",
    "refresh": "eyJ0eXAiOiJKV1QiLC..."
  }
}
```

### استفاده در درخواست‌ها

```javascript
const headers = {
  "Authorization": `Bearer ${accessToken}`,
  "Content-Type": "application/json"
};
```

---

## 📚 API Endpoints

### 1️⃣ دریافت آزمون (Student + Teacher)

```
GET /api/exercise/exam/{subject_id}/
```

#### پارامترها

| نام | نوع | الزامی | توضیح |
|-----|-----|--------|-------|
| subject_id | Integer | ✅ | ID کلاس/موضوع |

#### درخواست

```bash
curl -X GET "http://api.example.com/api/exercise/exam/5/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

#### پاسخ 200 OK

```json
{
  "id": 5,
  "subject_id": 5,
  "subject_title": "ریاضی 1",
  "total_questions": 3,
  "questions": [
    {
      "id": 1,
      "title": "دو به اضافه دو برابر است با:",
      "type": "radioButton",
      "is_required": 1,
      "guide": "جواب صحیح را انتخاب کنید",
      "des": "سؤال ریاضی ساده",
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "sort": 0,
      "details": [
        {
          "id": 1,
          "title": "3",
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
          "title": "4",
          "second_title": null,
          "image_path": null,
          "is_correct": 1,
          "guide": "آفرین! جواب صحیح است",
          "des": null,
          "sort": 1,
          "is_required": 0
        }
      ]
    },
    {
      "id": 2,
      "title": "نام خود را بنویسید",
      "type": "input",
      "is_required": 1,
      "guide": "نام کامل خود را وارد کنید",
      "details": []
    },
    {
      "id": 3,
      "title": "کدام مورد درست است؟",
      "type": "checkbox",
      "is_required": 1,
      "details": [
        {
          "id": 10,
          "title": "فرانسه در اروپا است",
          "is_correct": 1
        }
      ]
    }
  ]
}
```

#### Errors

```json
// 404 Not Found
{
  "error": "موضوع تدریسی یافت نشد"
}

// 403 Forbidden
{
  "error": "شما دسترسی به این موضوع ندارید"
}
```

#### کد نمونه (React Native)

```javascript
const getExam = async (subjectId) => {
  try {
    const response = await fetch(
      `http://api.example.com/api/exercise/exam/${subjectId}/`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch exam');
    
    const data = await response.json();
    setExam(data);
    return data;
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در دریافت آزمون');
  }
};
```

---

### 2️⃣ ارسال پاسخ‌های آزمون (Student)

```
POST /api/exercise/exam/{subject_id}/submit/
```

#### پارامترها

| نام | نوع | الزامی | توضیح |
|-----|-----|--------|-------|
| subject_id | Integer | ✅ | ID کلاس/موضوع |

#### بدنه درخواست

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
      "value": "علی حسینی"
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

#### شرح پارامترها

**برای سؤالات انتخابی (radioButton, checkbox):**
```javascript
{
  "field_id": 1,           // ID سؤال
  "field_detail_id": 2     // ID گزینه انتخاب شده
}
```

**برای سؤالات تایپی (input):**
```javascript
{
  "field_id": 2,           // ID سؤال
  "value": "متن پاسخ"      // متن وارد شده
}
```

**برای چند گزینه‌ای (checkbox):**
```javascript
// یک object برای هر انتخاب
{
  "field_id": 3,
  "field_detail_id": 10
},
{
  "field_id": 3,
  "field_detail_id": 11
}
```

#### درخواست

```bash
curl -X POST "http://api.example.com/api/exercise/exam/5/submit/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "teachingsubject_id": 5,
    "answers": [
      {"field_id": 1, "field_detail_id": 2}
    ]
  }'
```

#### پاسخ 201 Created

```json
{
  "data": {
    "id": 42,
    "user": 1,
    "user_name": "علی حسینی",
    "teachingsubject": 5,
    "subject_title": "ریاضی 1",
    "score": 2,
    "correct": 2,
    "incorrect": 1,
    "created_at": "2025-12-30T14:30:00Z",
    "details": [
      {
        "id": 1,
        "field": 1,
        "field_title": "دو به اضافه دو برابر است با:",
        "field_type": "radioButton",
        "field_detail": 2,
        "option_title": "4",
        "value": null,
        "score": 1
      },
      {
        "id": 2,
        "field": 2,
        "field_title": "نام خود را بنویسید",
        "field_type": "input",
        "field_detail": null,
        "option_title": null,
        "value": "علی حسینی",
        "score": 0
      },
      {
        "id": 3,
        "field": 3,
        "field_title": "کدام مورد درست است؟",
        "field_type": "checkbox",
        "field_detail": 10,
        "option_title": "فرانسه در اروپا است",
        "value": null,
        "score": 1
      }
    ]
  },
  "message": "پاسخ‌ها با موفقیت ثبت شدند"
}
```

#### Errors

```json
// 400 Bad Request
{
  "error": "داده‌های نامعتبر",
  "details": {
    "answers": ["حداقل یک پاسخ الزامی است"]
  }
}

// 404 Not Found
{
  "error": "موضوع تدریسی یافت نشد"
}

// 403 Forbidden
{
  "error": "شما می‌توانید تنها برای موضوعات فعال آزمون حل کنید"
}
```

#### کد نمونه (React Native)

```javascript
const submitExam = async (subjectId, answers) => {
  try {
    setLoading(true);
    
    const response = await fetch(
      `http://api.example.com/api/exercise/exam/${subjectId}/submit/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          teachingsubject_id: subjectId,
          answers: answers
        })
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'خطا در ارسال');
    }
    
    const result = await response.json();
    
    // نمایش نتیجه
    showScore(result.data.score, result.data.details.length);
    navigation.navigate('Results', { attemptId: result.data.id });
    
  } catch (error) {
    console.error('Error:', error);
    showError(error.message);
  } finally {
    setLoading(false);
  }
};
```

---

### 3️⃣ دریافت لیست نتایج (Student + Teacher)

```
GET /api/exercise/results/
```

#### پارامترهای Query

| نام | نوع | الزامی | توضیح |
|-----|-----|--------|-------|
| subject_id | Integer | ❌ | فیلتر بر حسب کلاس |
| page | Integer | ❌ | شماره صفحه (پیش‌فرض: 1) |
| page_size | Integer | ❌ | تعداد در هر صفحه (پیش‌فرض: 20) |

#### درخواست

```bash
# بدون فیلتر
curl -X GET "http://api.example.com/api/exercise/results/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# با فیلتر
curl -X GET "http://api.example.com/api/exercise/results/?subject_id=5&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### پاسخ 200 OK

```json
{
  "count": 15,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 42,
      "teachingsubject": 5,
      "subject_title": "ریاضی 1",
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
      "subject_title": "ریاضی 1",
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

#### کد نمونه (React Native)

```javascript
const getResults = async (subjectId = null) => {
  try {
    const query = new URLSearchParams();
    if (subjectId) query.append('subject_id', subjectId);
    query.append('page_size', 20);
    
    const response = await fetch(
      `http://api.example.com/api/exercise/results/?${query}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch results');
    
    const data = await response.json();
    setResults(data.results);
    setTotalCount(data.count);
    
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در دریافت نتایج');
  }
};
```

---

### 4️⃣ دریافت جزئیات یک تلاش (Student + Teacher)

```
GET /api/exercise/results/{attempt_id}/
```

#### پارامترها

| نام | نوع | الزامی | توضیح |
|-----|-----|--------|-------|
| attempt_id | Integer | ✅ | ID تلاش/امتحان |

#### درخواست

```bash
curl -X GET "http://api.example.com/api/exercise/results/42/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### پاسخ 200 OK

```json
{
  "id": 42,
  "user": 1,
  "user_name": "علی حسینی",
  "teachingsubject": 5,
  "subject_title": "ریاضی 1",
  "score": 2,
  "correct": 2,
  "incorrect": 1,
  "created_at": "2025-12-30T14:30:00Z",
  "details": [
    {
      "id": 1,
      "field": 1,
      "field_title": "دو به اضافه دو برابر است با:",
      "field_type": "radioButton",
      "field_detail": 2,
      "option_title": "4",
      "value": null,
      "score": 1
    },
    {
      "id": 2,
      "field": 2,
      "field_title": "نام خود را بنویسید",
      "field_type": "input",
      "field_detail": null,
      "option_title": null,
      "value": "علی حسینی",
      "score": 0
    },
    {
      "id": 3,
      "field": 3,
      "field_title": "کدام مورد درست است؟",
      "field_type": "checkbox",
      "field_detail": 10,
      "option_title": "فرانسه در اروپا است",
      "value": null,
      "score": 1
    }
  ]
}
```

#### کد نمونه (React Native)

```javascript
const getAttemptDetails = async (attemptId) => {
  try {
    const response = await fetch(
      `http://api.example.com/api/exercise/results/${attemptId}/`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch details');
    
    const data = await response.json();
    setAttemptDetails(data);
    
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در دریافت جزئیات');
  }
};
```

---

### 5️⃣ ایجاد سؤال (Teacher Only)

```
POST /api/exercise/field/create/
```

#### بدنه درخواست

```json
{
  "title": "دو به اضافه دو برابر است با:",
  "type": "radioButton",
  "is_required": 1,
  "guide": "جواب صحیح را انتخاب کنید",
  "des": "سؤال ریاضی ساده",
  "image_path": null,
  "audio_path": null,
  "video_path": null,
  "sort": 0,
  "details": [
    {
      "title": "3",
      "is_correct": 0,
      "sort": 0
    },
    {
      "title": "4",
      "is_correct": 1,
      "sort": 1,
      "guide": "آفرین! جواب صحیح است"
    }
  ]
}
```

#### درخواست

```bash
curl -X POST "http://api.example.com/api/exercise/field/create/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "دو به اضافه دو برابر است با:",
    "type": "radioButton",
    "is_required": 1,
    "details": [
      {"title": "3", "is_correct": 0},
      {"title": "4", "is_correct": 1}
    ]
  }'
```

#### پاسخ 201 Created

```json
{
  "data": {
    "id": 1,
    "title": "دو به اضافه دو برابر است با:",
    "type": "radioButton",
    "is_required": 1,
    "guide": "جواب صحیح را انتخاب کنید",
    "des": "سؤال ریاضی ساده",
    "details": [
      {
        "id": 1,
        "title": "3",
        "is_correct": 0
      },
      {
        "id": 2,
        "title": "4",
        "is_correct": 1
      }
    ]
  },
  "message": "سؤال با موفقیت ایجاد شد"
}
```

---

### 6️⃣ ایجاد آزمون (Teacher Only)

```
POST /api/exercise/exam/create/
```

#### بدنه درخواست

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
    }
  ]
}
```

#### درخواست

```bash
curl -X POST "http://api.example.com/api/exercise/exam/create/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "teachingsubject_id": 5,
    "questions": [
      {"field_id": 1, "step": 0, "sort": 0, "type": "radioButton"}
    ]
  }'
```

#### پاسخ 201 Created

```json
{
  "data": {
    "id": 5,
    "subject_id": 5,
    "subject_title": "ریاضی 1",
    "total_questions": 2,
    "questions": [
      {
        "id": 1,
        "field_id": 1,
        "field_title": "دو به اضافه دو برابر است با:",
        "type": "radioButton",
        "details": [
          {
            "id": 1,
            "title": "3",
            "is_correct": 0
          }
        ]
      }
    ]
  },
  "message": "آزمون با موفقیت ایجاد شد"
}
```

---

## 🎯 Workflow نمونه

### برای دانشآموز

```javascript
// 1. آزمون را دریافت کنید
const exam = await getExam(5);

// 2. دانشآموز پاسخ می‌دهد
const answers = [
  { field_id: 1, field_detail_id: 2 },
  { field_id: 2, value: "علی حسینی" }
];

// 3. ارسال کنید
const result = await submitExam(5, answers);

// 4. نتیجه را نمایش دهید
console.log(`نمره: ${result.data.score}/${result.data.details.length}`);

// 5. نتایج قدیم را ببینید
const results = await getResults();

// 6. جزئیات یک تلاش
const details = await getAttemptDetails(result.data.id);
```

---

## ⚠️ خطاهای معمول

| Error | معنی | حل |
|-------|------|-----|
| 401 | Token نامعتبر | دوباره login کنید |
| 403 | دسترسی رد شد | صاحب منبع نیستید |
| 404 | موجود نیست | ID را چک کنید |
| 400 | داده نامعتبر | پارامترها را بررسی کنید |
| 500 | خطای سرور | بعداً امتحان کنید |

---

## 🔍 Debugging

### لاگ کردن درخواست

```javascript
const api = async (method, endpoint, body = null) => {
  const url = `http://api.example.com${endpoint}`;
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  };
  
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  console.log(`${method} ${url}`, body);
  
  const response = await fetch(url, options);
  const data = await response.json();
  
  console.log(`Response ${response.status}:`, data);
  
  return { status: response.status, data };
};
```

### تست با Postman

1. Authorization → Bearer Token
2. Headers → Content-Type: application/json
3. Body → raw JSON
4. Send

---

## 📱 نمونه کامل (React Native)

```javascript
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';

const ExamScreen = ({ route }) => {
  const { subjectId } = route.params;
  const [exam, setExam] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // دریافت آزمون
  const loadExam = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://api.example.com/api/exercise/exam/${subjectId}/`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      const data = await response.json();
      setExam(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // ارسال پاسخ‌ها
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const formattedAnswers = Object.entries(answers).map(
        ([fieldId, answer]) => ({
          field_id: parseInt(fieldId),
          ...answer
        })
      );

      const response = await fetch(
        `http://api.example.com/api/exercise/exam/${subjectId}/submit/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            teachingsubject_id: subjectId,
            answers: formattedAnswers
          })
        }
      );

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!exam) {
    return <Text>آزمون در حال بارگذاری...</Text>;
  }

  if (result) {
    return (
      <View>
        <Text>نمره شما: {result.score}/{result.details.length}</Text>
        <Text>درصد: {((result.score / result.details.length) * 100).toFixed(2)}%</Text>
      </View>
    );
  }

  return (
    <ScrollView>
      {exam.questions.map((question) => (
        <View key={question.id}>
          <Text>{question.title}</Text>
          {question.type === 'input' && (
            <TextInput
              placeholder="پاسخ خود را وارد کنید"
              onChangeText={(text) =>
                setAnswers({
                  ...answers,
                  [question.id]: { value: text }
                })
              }
            />
          )}
          {(question.type === 'radioButton' ||
            question.type === 'checkbox') &&
            question.details.map((detail) => (
              <TouchableOpacity
                key={detail.id}
                onPress={() =>
                  setAnswers({
                    ...answers,
                    [question.id]: { field_detail_id: detail.id }
                  })
                }
              >
                <Text>{detail.title}</Text>
              </TouchableOpacity>
            ))}
        </View>
      ))}
      <TouchableOpacity onPress={handleSubmit} disabled={loading}>
        <Text>ارسال</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

export default ExamScreen;
```

---

**موفق باشید! 🚀**

