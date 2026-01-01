# تمرین و آزمون - راهنمای API برای معلمان
# Exercise & Exam API Guide for Teachers

**برای اپلیکیشن Expo + TypeScript**

---

## 📋 فهرست

1. [ایجاد سوالات (Create Questions)](#ایجاد-سوالات)
2. [ایجاد آزمون (Create Exam)](#ایجاد-آزمون)
3. [دریافت آزمون (Get Exam)](#دریافت-آزمون)
4. [مشاهده نتایج (View Results)](#مشاهده-نتایج)
5. [انواع سوالات](#انواع-سوالات)
6. [مثال‌های عملی TypeScript](#مثال‌های-عملی)

---

## ایجاد سوالات

### 1. Create Question (Field)

سوالات را قبل از ساخت آزمون باید ایجاد کرد.

**Endpoint:**
```
POST /api/exercise/field/create/
```

**Authentication:**
- Required: `IsAuthenticated`
- Role: `teacher` فقط

**Request Body:**

```json
{
  "title": "string",           // [required] متن سوال
  "type": "string",            // [required] نوع سوال: "input", "checkbox", "radioButton"
  "is_required": 0 | 1,        // [optional] آیا الزامی است (پیش‌فرض: 1)
  "guide": "string",           // [optional] راهنمای سوال
  "des": "string",             // [optional] توضیح سوال
  "sort": 0,                   // [optional] ترتیب (پیش‌فرض: 0)
  "image_path": "string",      // [optional] مسیر تصویر سوال
  "audio_path": "string",      // [optional] مسیر صدا
  "video_path": "string",      // [optional] مسیر ویدیو
  "correct_answer": "string",  // [optional] برای سوالات تایپی - پاسخ صحیح
  "details": [                 // [optional] گزینه‌های سوال (برای choice questions)
    {
      "title": "string",       // متن گزینه
      "is_correct": 0 | 1,     // آیا درست است
      "image_path": "string",  // [optional] تصویر گزینه
      "guide": "string",       // [optional] توضیح گزینه
      "sort": 0                // ترتیب گزینه
    }
  ]
}
```

**Response (201 Created):**

```json
{
  "data": {
    "id": 123,
    "title": "What is the capital of France?",
    "type": "radioButton",
    "is_required": 1,
    "guide": "European capital city",
    "des": null,
    "sort": 0,
    "image_path": null,
    "audio_path": null,
    "video_path": null,
    "correct_answer": null,
    "details": [
      {
        "id": 456,
        "title": "Paris",
        "is_correct": 1,
        "image_path": null,
        "guide": "Correct!",
        "sort": 0
      },
      {
        "id": 457,
        "title": "London",
        "is_correct": 0,
        "image_path": null,
        "guide": "Wrong, this is UK",
        "sort": 1
      }
    ]
  },
  "message": "سوال با موفقیت ایجاد شد"
}
```

**Error Responses:**

```json
{
  "error": "تنها معلمان می‌توانند سوال ایجاد کنند",
  "status": 403
}
```

```json
{
  "error": "داده‌های نامعتبر",
  "details": {
    "title": ["This field is required"]
  },
  "status": 400
}
```

---

## ایجاد آزمون

### 2. Create Exam (Assign Questions to Class)

آزمون‌ها از ترکیب سوالات برای یک کلاس (TeachingSubject) ایجاد می‌شوند.

**Endpoint:**
```
POST /api/exercise/exam/create/
```

**Authentication:**
- Required: `IsAuthenticated`
- Role: `teacher` فقط
- Owner Check: معلم صاحب کلاس باشد

**Request Body:**

```json
{
  "teachingsubject_id": 5,     // [required] شناسه کلاس/موضوع تدریسی
  "questions": [               // [required] لیست سوالات
    {
      "field_id": 1,           // شناسه سوال (از Create Question)
      "step": 0,               // مرحله/گروه سوال (0, 1, 2, ...)
      "sort": 0,               // ترتیب در مرحله
      "type": "radioButton",   // نوع سوال (input, checkbox, radioButton)
      "is_conditional": false  // [optional] سوال شرطی
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
      "step": 1,               // مرحله دوم
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
    "subject_title": "English - Intermediate",
    "questions": [
      {
        "id": 201,
        "field_id": 1,
        "field_title": "What is the capital of France?",
        "type": "radioButton",
        "step": 0,
        "sort": 0,
        "is_conditional": false,
        "details": [
          {
            "id": 456,
            "title": "Paris",
            "is_correct": 1
          },
          {
            "id": 457,
            "title": "London",
            "is_correct": 0
          }
        ]
      },
      {
        "id": 202,
        "field_id": 2,
        "field_title": "Write your name",
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

**Error Responses:**

```json
{
  "error": "تنها معلمان می‌توانند آزمون ایجاد کنند",
  "status": 403
}
```

```json
{
  "error": "موضوع تدریسی یافت نشد",
  "status": 404
}
```

```json
{
  "error": "شما می‌توانید تنها برای موضوعات خود آزمون ایجاد کنید",
  "status": 403
}
```

```json
{
  "error": "حداقل یک سوال الزامی است",
  "status": 400
}
```

---

## دریافت آزمون

### 3. Get Exam Questions

دریافت تمام سوالات و گزینه‌های یک آزمون.

**Endpoint:**
```
GET /api/exercise/exam/<subject_id>/
```

**Authentication:**
- Required: `IsAuthenticated`
- Role: معلم (صاحب کلاس) یا دانش‌آموز (برای کلاس‌های فعال)

**Path Parameters:**
- `subject_id`: شناسه کلاس/موضوع تدریسی

**Query Parameters:** (اختیاری)
```
page=1
page_size=20
```

**Response (200 OK):**

```json
{
  "id": 5,
  "subject_id": 5,
  "subject_title": "English - Intermediate",
  "questions": [
    {
      "id": 123,
      "exam_question_id": 201,
      "title": "What is the capital of France?",
      "type": "radioButton",
      "step": 0,
      "sort": 0,
      "guide": "European capital city",
      "des": null,
      "is_required": 1,
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "details": [
        {
          "id": 456,
          "title": "Paris",
          "is_correct": null,
          "image_path": null,
          "guide": "Correct!",
          "sort": 0
        },
        {
          "id": 457,
          "title": "London",
          "is_correct": null,
          "image_path": null,
          "guide": "Wrong, this is UK",
          "sort": 1
        }
      ]
    },
    {
      "id": 124,
      "exam_question_id": 202,
      "title": "Write your name",
      "type": "input",
      "step": 0,
      "sort": 1,
      "guide": "Enter your full name",
      "des": null,
      "is_required": 1,
      "image_path": null,
      "audio_path": null,
      "video_path": null,
      "details": []
    }
  ],
  "total_questions": 3
}
```

**Error Responses:**

```json
{
  "error": "موضوع تدریسی یافت نشد",
  "status": 404
}
```

```json
{
  "error": "شما دسترسی به این موضوع ندارید",
  "status": 403
}
```

---

## مشاهده نتایج

### 4. Get Exam Results (List of Attempts)

دریافت تمام تلاش‌های دانش‌آموزان برای آزمون‌های معلم.

**Endpoint:**
```
GET /api/exercise/results/
```

**Authentication:**
- Required: `IsAuthenticated`
- Role: معلم یا دانش‌آموز (خود را می‌بیند)

**Query Parameters:**

```
subject_id=5           // [optional] فیلتر بر اساس کلاس
page=1                 // [optional] شماره صفحه
page_size=20           // [optional] تعداد آیتم‌های هر صفحه
```

**Response (200 OK):**

```json
{
  "count": 15,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 1001,
      "user_name": "Ali Rezaie",
      "subject_title": "English - Intermediate",
      "score": 8,
      "correct": 8,
      "incorrect": 2,
      "total_questions": 10,
      "percentage": 80.0,
      "created_at": "2024-01-15T14:30:00Z"
    },
    {
      "id": 1002,
      "user_name": "Fatima Keshavarz",
      "subject_title": "English - Intermediate",
      "score": 9,
      "correct": 9,
      "incorrect": 1,
      "total_questions": 10,
      "percentage": 90.0,
      "created_at": "2024-01-15T15:45:00Z"
    }
  ]
}
```

### 5. Get Exam Attempt Details

دریافت جزئیات یک تلاش خاص شامل تمام پاسخ‌ها و نمرات.

**Endpoint:**
```
GET /api/exercise/results/<attempt_id>/
```

**Authentication:**
- Required: `IsAuthenticated`
- Role: معلم (صاحب کلاس) یا دانش‌آموز (خود)

**Path Parameters:**
- `attempt_id`: شناسه تلاش

**Response (200 OK):**

```json
{
  "id": 1001,
  "user_name": "Ali Rezaie",
  "user_id": 42,
  "subject_title": "English - Intermediate",
  "subject_id": 5,
  "score": 8,
  "correct": 8,
  "incorrect": 2,
  "total_questions": 10,
  "percentage": 80.0,
  "details": [
    {
      "field_id": 1,
      "field_title": "What is the capital of France?",
      "field_type": "radioButton",
      "student_answer": "Paris",
      "student_answer_id": 456,
      "correct_answer": "Paris",
      "is_correct": true,
      "score": 1
    },
    {
      "field_id": 2,
      "field_title": "Write your name",
      "field_type": "input",
      "student_answer": "Ali Rezaie",
      "student_answer_id": null,
      "correct_answer": null,
      "is_correct": true,
      "score": 1
    },
    {
      "field_id": 3,
      "field_title": "Select all correct answers",
      "field_type": "checkbox",
      "student_answer": ["Option A", "Option C"],
      "student_answer_id": [501, 503],
      "correct_answer": ["Option A", "Option C"],
      "is_correct": true,
      "score": 1
    }
  ],
  "created_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**

```json
{
  "error": "تلاش برای امتحان یافت نشد",
  "status": 404
}
```

```json
{
  "error": "شما دسترسی به این نتایج ندارید",
  "status": 403
}
```

---

## انواع سوالات

### Question Types

**1. تایپی (Input)**

سوالات باز که دانش‌آموز باید متن بنویسد.

```json
{
  "title": "Write your name",
  "type": "input",
  "is_required": 1,
  "guide": "Enter your full name",
  "correct_answer": "Ali Rezaie"
}
```

**2. تک‌گزینه‌ای (RadioButton)**

سوالات چند گزینه‌ای با یک پاسخ درست.

```json
{
  "title": "What is the capital of France?",
  "type": "radioButton",
  "is_required": 1,
  "details": [
    {
      "title": "Paris",
      "is_correct": 1,
      "guide": "Correct!"
    },
    {
      "title": "London",
      "is_correct": 0,
      "guide": "Wrong"
    }
  ]
}
```

**3. چند‌گزینه‌ای (Checkbox)**

سوالات چند گزینه‌ای با چندین پاسخ درست ممکن.

```json
{
  "title": "Select all correct answers",
  "type": "checkbox",
  "is_required": 1,
  "details": [
    {
      "title": "Option A",
      "is_correct": 1
    },
    {
      "title": "Option B",
      "is_correct": 0
    },
    {
      "title": "Option C",
      "is_correct": 1
    }
  ]
}
```

---

## مثال‌های عملی

### TypeScript - Expo

#### 1. ایجاد سوال تایپی

```typescript
import axios from 'axios';

interface CreateQuestionRequest {
  title: string;
  type: 'input' | 'checkbox' | 'radioButton';
  is_required?: 0 | 1;
  guide?: string;
  des?: string;
  correct_answer?: string;
  details?: Array<{
    title: string;
    is_correct: 0 | 1;
    image_path?: string;
    guide?: string;
    sort?: number;
  }>;
}

export async function createQuestion(
  token: string,
  questionData: CreateQuestionRequest
) {
  try {
    const response = await axios.post(
      'https://api.fofofish.app/api/exercise/field/create/',
      questionData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    console.log('Question created:', response.data.data.id);
    return response.data.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      console.error('Only teachers can create questions');
    } else if (error.response?.status === 400) {
      console.error('Invalid data:', error.response.data.details);
    }
    throw error;
  }
}

// استفاده:
const newQuestion = await createQuestion(authToken, {
  title: 'نام پایتخت فرانسه چیست؟',
  type: 'input',
  is_required: 1,
  guide: 'پاسخ: پاریس',
  correct_answer: 'پاریس'
});
```

#### 2. ایجاد سوال چند‌گزینه‌ای

```typescript
const multipleChoiceQuestion = await createQuestion(authToken, {
  title: 'پایتخت فرانسه کدام است؟',
  type: 'radioButton',
  is_required: 1,
  details: [
    {
      title: 'پاریس',
      is_correct: 1,
      guide: 'درست است!',
      sort: 0,
    },
    {
      title: 'لندن',
      is_correct: 0,
      guide: 'این پایتخت انگلستان است',
      sort: 1,
    },
    {
      title: 'برلین',
      is_correct: 0,
      guide: 'این پایتخت آلمان است',
      sort: 2,
    },
  ],
});
```

#### 3. ایجاد آزمون (اختصاص سوالات به کلاس)

```typescript
interface ExamQuestion {
  field_id: number;
  step: number;
  sort: number;
  type: 'input' | 'checkbox' | 'radioButton';
  is_conditional?: boolean;
}

interface CreateExamRequest {
  teachingsubject_id: number;
  questions: ExamQuestion[];
}

export async function createExam(
  token: string,
  examData: CreateExamRequest
) {
  try {
    const response = await axios.post(
      'https://api.fofofish.app/api/exercise/exam/create/',
      examData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    console.log('Exam created with questions:', response.data.data.total_questions);
    return response.data.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      console.error('You can only create exam for your own subjects');
    } else if (error.response?.status === 404) {
      console.error('Subject not found');
    }
    throw error;
  }
}

// استفاده:
const exam = await createExam(authToken, {
  teachingsubject_id: 5,
  questions: [
    {
      field_id: 101,
      step: 0,
      sort: 0,
      type: 'radioButton',
    },
    {
      field_id: 102,
      step: 0,
      sort: 1,
      type: 'input',
    },
    {
      field_id: 103,
      step: 1,
      sort: 0,
      type: 'checkbox',
    },
  ],
});
```

#### 4. دریافت آزمون

```typescript
export async function getExam(token: string, subjectId: number) {
  try {
    const response = await axios.get(
      `https://api.fofofish.app/api/exercise/exam/${subjectId}/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const exam = response.data;
    console.log(`Exam "${exam.subject_title}" has ${exam.total_questions} questions`);
    
    return exam;
  } catch (error: any) {
    if (error.response?.status === 404) {
      console.error('Subject/Exam not found');
    } else if (error.response?.status === 403) {
      console.error('You do not have access to this exam');
    }
    throw error;
  }
}

// استفاده:
const exam = await getExam(authToken, 5);
exam.questions.forEach((question, index) => {
  console.log(`${index + 1}. ${question.title}`);
  console.log(`   Type: ${question.type}`);
  console.log(`   Options: ${question.details.length}`);
});
```

#### 5. مشاهده نتایج آزمون

```typescript
interface ExamResult {
  id: number;
  user_name: string;
  subject_title: string;
  score: number;
  correct: number;
  incorrect: number;
  total_questions: number;
  percentage: number;
  created_at: string;
}

export async function getExamResults(
  token: string,
  subjectId?: number,
  page: number = 1,
  pageSize: number = 20
) {
  try {
    const params: any = { page, page_size: pageSize };
    if (subjectId) {
      params.subject_id = subjectId;
    }

    const response = await axios.get(
      'https://api.fofofish.app/api/exercise/results/',
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params,
      }
    );

    return {
      total: response.data.count,
      page: response.data.page,
      results: response.data.results as ExamResult[],
    };
  } catch (error) {
    console.error('Failed to fetch exam results');
    throw error;
  }
}

// استفاده:
const results = await getExamResults(authToken, 5);
results.results.forEach((result) => {
  console.log(`${result.user_name}: ${result.percentage}% (${result.correct}/${result.total_questions})`);
});
```

#### 6. مشاهده جزئیات یک تلاش

```typescript
interface AnswerDetail {
  field_id: number;
  field_title: string;
  student_answer: string | string[];
  correct_answer?: string | string[];
  is_correct: boolean;
  score: number;
}

interface ExamAttemptDetail {
  id: number;
  user_name: string;
  subject_title: string;
  score: number;
  correct: number;
  incorrect: number;
  percentage: number;
  details: AnswerDetail[];
  created_at: string;
}

export async function getExamAttemptDetail(
  token: string,
  attemptId: number
): Promise<ExamAttemptDetail> {
  try {
    const response = await axios.get(
      `https://api.fofofish.app/api/exercise/results/${attemptId}/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      console.error('Attempt not found');
    } else if (error.response?.status === 403) {
      console.error('You cannot view this attempt');
    }
    throw error;
  }
}

// استفاده:
const attemptDetail = await getExamAttemptDetail(authToken, 1001);
console.log(`Student: ${attemptDetail.user_name}`);
console.log(`Score: ${attemptDetail.score}/${attemptDetail.correct + attemptDetail.incorrect}`);

attemptDetail.details.forEach((answer, index) => {
  const status = answer.is_correct ? '✓' : '✗';
  console.log(`${index + 1}. ${status} ${answer.field_title}`);
  console.log(`   Student: ${answer.student_answer}`);
  if (answer.correct_answer) {
    console.log(`   Correct: ${answer.correct_answer}`);
  }
});
```

#### 7. Composable API Helper

```typescript
// useExerciseAPI.ts
import { useState, useCallback } from 'react';
import axios, { AxiosError } from 'axios';

const API_BASE = 'https://api.fofofish.app/api';

export function useExerciseAPI(token: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleError = (err: unknown, defaultMessage: string) => {
    const apiError = err as AxiosError;
    const message =
      apiError.response?.status === 403
        ? 'دسترسی رد شده'
        : apiError.response?.status === 404
        ? 'پیدا نشد'
        : apiError.response?.status === 400
        ? 'داده نامعتبر'
        : defaultMessage;
    setError(message);
    throw new Error(message);
  };

  const createQuestion = useCallback(
    async (data: any) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await axios.post(
          `${API_BASE}/exercise/field/create/`,
          data,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        return response.data.data;
      } catch (err) {
        handleError(err, 'Failed to create question');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  const createExam = useCallback(
    async (data: any) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await axios.post(
          `${API_BASE}/exercise/exam/create/`,
          data,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        return response.data.data;
      } catch (err) {
        handleError(err, 'Failed to create exam');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  const getExam = useCallback(
    async (subjectId: number) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          `${API_BASE}/exercise/exam/${subjectId}/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        return response.data;
      } catch (err) {
        handleError(err, 'Failed to fetch exam');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  const getResults = useCallback(
    async (subjectId?: number, page: number = 1) => {
      setIsLoading(true);
      setError(null);
      try {
        const params: any = { page, page_size: 20 };
        if (subjectId) params.subject_id = subjectId;

        const response = await axios.get(
          `${API_BASE}/exercise/results/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            params,
          }
        );
        return response.data.results;
      } catch (err) {
        handleError(err, 'Failed to fetch results');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  const getAttemptDetail = useCallback(
    async (attemptId: number) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          `${API_BASE}/exercise/results/${attemptId}/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        return response.data;
      } catch (err) {
        handleError(err, 'Failed to fetch attempt details');
      } finally {
        setIsLoading(false);
      }
    },
    [token]
  );

  return {
    isLoading,
    error,
    createQuestion,
    createExam,
    getExam,
    getResults,
    getAttemptDetail,
  };
}
```

#### 8. Screen Component Example

```typescript
import React, { useState } from 'react';
import {
  View,
  ScrollView,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { useExerciseAPI } from './useExerciseAPI';

export function CreateExamScreen({ navigation, route }: any) {
  const { authToken, subjectId } = route.params;
  const { createExam, isLoading, error } = useExerciseAPI(authToken);
  const [selectedQuestions, setSelectedQuestions] = useState<number[]>([]);

  const handleCreateExam = async () => {
    if (selectedQuestions.length === 0) {
      Alert.alert('خطا', 'حداقل یک سوال انتخاب کنید');
      return;
    }

    try {
      const questions = selectedQuestions.map((fieldId, index) => ({
        field_id: fieldId,
        step: Math.floor(index / 3), // 3 سوال در هر مرحله
        sort: index % 3,
        type: 'radioButton', // در عمل نوع را بر اساس سوال تعیین کنید
      }));

      const result = await createExam({
        teachingsubject_id: subjectId,
        questions,
      });

      Alert.alert('موفقیت', `آزمون با ${result.total_questions} سوال ایجاد شد`);
      navigation.goBack();
    } catch (err: any) {
      Alert.alert('خطا', err.message);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>ایجاد آزمون</Text>

      {/* سوالات انتخاب شده */}
      <View style={styles.selectedSection}>
        <Text style={styles.sectionTitle}>سوالات انتخاب شده ({selectedQuestions.length})</Text>
      </View>

      {/* دکمه ایجاد */}
      <TouchableOpacity
        style={[styles.button, isLoading && styles.buttonDisabled]}
        onPress={handleCreateExam}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>ایجاد آزمون</Text>
        )}
      </TouchableOpacity>

      {error && <Text style={styles.error}>{error}</Text>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#555',
    marginBottom: 10,
  },
  selectedSection: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#667eea',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#e74c3c',
    fontSize: 14,
    marginTop: 10,
    padding: 10,
    backgroundColor: '#fadbd8',
    borderRadius: 4,
  },
});
```

---

## Validation Rules

### Field (Question) Validation

| Field | Type | Rules |
|-------|------|-------|
| `title` | string | Required, Max 255 chars |
| `type` | string | Required, One of: `input`, `checkbox`, `radioButton` |
| `is_required` | int | 0 or 1, Default: 1 |
| `guide` | string | Optional, Max 255 chars |
| `des` | string | Optional, Text |
| `sort` | int | Optional, Default: 0 |
| `correct_answer` | string | Optional (for input questions) |

### CategoryField (Exam Question) Validation

| Field | Type | Rules |
|-------|------|-------|
| `field_id` | int | Required, Must exist |
| `step` | int | Required, >= 0 |
| `sort` | int | Required, >= 0 |
| `type` | string | Required, Match field type |
| `is_conditional` | bool | Optional, Default: false |

### Order (Answer Submission) Validation

| Field | Type | Rules |
|-------|------|-------|
| `teachingsubject_id` | int | Required, Must belong to teacher |
| `answers` | array | Required, Min 1 item |
| `field_id` | int | Required per answer |
| `field_detail_id` | int | Optional (for choice questions) |
| `value` | string | Optional (for text questions) |

---

## Error Codes

| Code | Message | Meaning |
|------|---------|---------|
| 400 | Invalid data | Validation error, check details field |
| 403 | Permission denied | Only teachers, wrong subject owner |
| 404 | Not found | Question, exam, or subject doesn't exist |
| 500 | Server error | Contact support |

---

## Best Practices

1. **Question Organization:**
   - Use `step` to organize questions into phases
   - Use `sort` to order questions within a phase
   - Group related questions in same step

2. **Question Design:**
   - Use clear, concise titles
   - Provide helpful guides and descriptions
   - Add media (images, audio) for complex topics
   - For input questions, set `correct_answer` for auto-grading

3. **Error Handling:**
   - Always catch errors and show user-friendly messages
   - Validate data before sending to API
   - Handle 403 responses (permission issues)
   - Handle 404 responses (missing resources)

4. **Performance:**
   - Cache exam questions locally if possible
   - Paginate results for large datasets
   - Load student attempts asynchronously

---

## Related Endpoints

- [Class Booking](./CLASS_BOOKING_API.md) - Student enrollment in classes
- [Teaching Subjects](./api/urls.py) - Class management
- [Ratings & Medals](./RATING_MEDAL_SYSTEM.md) - Student feedback

---

**Last Updated:** 2024-01-15
**API Version:** 1.0
**Status:** Active ✓
