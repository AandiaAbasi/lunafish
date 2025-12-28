# � Implementation Guide - Separate Student & Teacher Apps

## 📁 Available API Specifications

Now you have **TWO separate files** - one for each app:

### 📱 Student App
**File:** `STUDENT_APP_API_SPECS.md`
- 7 Sections (Authentication, Courses, Lessons, Live Class, Quiz, Progress, Attendance)
- 30+ API endpoints
- For building the **Student-facing application**

### 👨‍🏫 Teacher App
**File:** `TEACHER_APP_API_SPECS.md`
- 7 Sections (Profile, Courses, Lessons, Live Class, Quizzes, Analytics, Badges)
- 25+ API endpoints
- For building the **Teacher-facing application**

---

## 🎯 How to Use These Files

### **For Student App Development:**

1. Open `STUDENT_APP_API_SPECS.md`
2. Pick a section (e.g., "Section 1: Authentication & User Profile")
3. Copy the entire section text
4. Open a new Copilot chat
5. Paste and ask:
   ```
   Implement this Student App section with TypeScript/React:
   [paste section here]
   
   Requirements:
   - Use React hooks
   - Implement error handling
   - Add loading states
   - Mobile responsive
   ```
6. You'll get a complete implementation!

### **For Teacher App Development:**

1. Open `TEACHER_APP_API_SPECS.md`
2. Pick a section (e.g., "Section 2: Create & Manage Courses")
3. Copy the entire section text
4. Open a new Copilot chat
5. Paste and ask:
   ```
   Implement this Teacher App section with TypeScript/React:
   [paste section here]
   
   Requirements:
   - Use React hooks
   - Implement error handling
   - Add loading states
   - Desktop & tablet responsive
   ```
6. You'll get a complete implementation!

---

## 📋 Recommended Implementation Order

### Student App (Priority: High)
1. ✅ **Section 1: Authentication** - Must have first
2. ✅ **Section 2: Course Discovery** - Core feature
3. ✅ **Section 3: Lessons & Enrollment** - Core feature
4. ⏳ **Section 5: Quiz** - Assessment feature
5. ⏳ **Section 7: Attendance** - Tracking feature
6. 🚀 **Section 4: Live Class** - Advanced (needs Agora SDK)
7. 🚀 **Section 6: Progress** - Analytics (Phase 2)

### Teacher App (Priority: High)
1. ✅ **Section 1: Profile** - Setup first
2. ✅ **Section 2: Create Courses** - Core feature
3. ✅ **Section 3: Create Lessons** - Core feature
4. ✅ **Section 5: Create Quizzes** - Assessment
5. 🚀 **Section 4: Live Class** - Advanced (needs Agora SDK)
6. 🚀 **Section 6: Analytics** - Dashboards (Phase 2)
7. 🚀 **Section 7: Badges** - Rewards (Phase 3)

---

## 🛠️ Tech Stack Setup (Before Starting)

```bash
# Frontend Framework
npm create vite@latest my-app -- --template react-ts

# Install dependencies
npm install
npm install axios react-router-dom @tanstack/react-query
npm install tailwindcss postcss autoprefixer
npm install agora-rtc-sdk-ng  # For video conferencing
```

---

## 🔑 Key Implementation Notes

### Authentication
- **Token Storage:** Use secure localStorage or sessionStorage
- **Token Refresh:** Implement refresh token logic
- **OTP Verification:** 6-digit code, resendable after timeout

### API Calls
- **Base URL:** `http://localhost:8000/api/` (development)
- **Headers:** Always include `Authorization: Bearer {token}`
- **Error Handling:** Implement proper error messages

### State Management
- Use React Context API or Zustand for global state
- Store user profile, token, selected course
- Persist authentication across page reloads

### Forms
- Validate all inputs before submission
- Show loading state during submission
- Display success/error messages

### Agora Integration
1. Get `appId` from Agora console
2. Generate tokens from backend
3. Initialize SDK with token
4. Join channel with user ID & channel name

---

## 🔄 Data Flow Example

### Student App - Lesson Join Flow:
```
Login 
  ↓
Browse Courses 
  ↓
View Course Details 
  ↓
Enroll in Lesson 
  ↓
View Lesson Details 
  ↓
Generate Agora Token 
  ↓
Join Live Class 
  ↓
Use Whiteboard 
  ↓
Take Quiz 
  ↓
View Attendance
```

### Teacher App - Lesson Management Flow:
```
Login 
  ↓
Create Course 
  ↓
Add Materials 
  ↓
Create Lessons 
  ↓
Create Quizzes 
  ↓
View Enrollments 
  ↓
Start Live Class 
  ↓
Manage Whiteboard 
  ↓
End Class & Mark Attendance 
  ↓
View Analytics
```

---

## 💾 File Structure Example

```
student-app/
  ├── src/
  │   ├── pages/
  │   │   ├── Auth.tsx           (Section 1)
  │   │   ├── Courses.tsx        (Section 2)
  │   │   ├── Lessons.tsx        (Section 3)
  │   │   ├── LiveClass.tsx      (Section 4)
  │   │   ├── Quiz.tsx           (Section 5)
  │   │   ├── Progress.tsx       (Section 6)
  │   │   └── Attendance.tsx     (Section 7)
  │   ├── components/
  │   │   ├── Navbar.tsx
  │   │   ├── CourseCard.tsx
  │   │   ├── VideoGrid.tsx
  │   │   └── ...
  │   ├── hooks/
  │   │   ├── useAuth.ts
  │   │   ├── useCourse.ts
  │   │   └── ...
  │   ├── services/
  │   │   ├── api.ts
  │   │   └── agora.ts
  │   └── App.tsx

teacher-app/
  ├── src/
  │   ├── pages/
  │   │   ├── Profile.tsx        (Section 1)
  │   │   ├── Courses.tsx        (Section 2)
  │   │   ├── Lessons.tsx        (Section 3)
  │   │   ├── LiveClass.tsx      (Section 4)
  │   │   ├── Quizzes.tsx        (Section 5)
  │   │   ├── Analytics.tsx      (Section 6)
  │   │   └── Badges.tsx         (Section 7)
  │   ├── components/
  │   ├── hooks/
  │   ├── services/
  │   └── App.tsx
```

---

## 🧪 Testing Approach

For each section implemented:
1. **Manual Testing:** Use Postman to test APIs
2. **Component Testing:** Test React components with React Testing Library
3. **Integration Testing:** Test full flows end-to-end
4. **Visual Testing:** Verify UI matches designs

---

## ⚠️ Important Notes

1. **Separate Deployments:** Student and Teacher apps should be separate (different URLs/ports)
2. **Same Backend:** Both apps use the same Django backend API
3. **Role-Based Access:** Backend controls access based on user role
4. **Security:** Never expose API keys or tokens in code
5. **CORS:** Ensure backend allows CORS for both app domains

---

## 📞 Common API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success - GET/PUT |
| 201 | Created - POST successful |
| 204 | No Content - DELETE successful |
| 400 | Bad Request - Invalid data |
| 401 | Unauthorized - Token missing/invalid |
| 403 | Forbidden - No permission |
| 404 | Not Found - Resource doesn't exist |
| 500 | Server Error |

---

## 🎓 Learning Resources

- **React Hooks:** https://react.dev/reference/react
- **Axios:** https://axios-http.com/
- **Agora SDK:** https://docs.agora.io/en/sdks
- **Tailwind CSS:** https://tailwindcss.com/docs
- **React Router:** https://reactrouter.com/

---

## ✅ Checklist Before Going Live

### Student App
- [ ] Authentication working (login/OTP)
- [ ] Course discovery functional
- [ ] Can enroll in lessons
- [ ] Live class video works
- [ ] Quiz system functional
- [ ] Attendance tracking works

### Teacher App
- [ ] Login and profile setup
- [ ] Can create courses
- [ ] Can create lessons
- [ ] Can start live class
- [ ] Can create quizzes
- [ ] Analytics dashboard shows data

### Both Apps
- [ ] Error handling for all endpoints
- [ ] Loading states visible
- [ ] Mobile responsive
- [ ] Token refresh working
- [ ] User logout functional

---

## 📞 Quick Reference Commands

```bash
# Development server
npm run dev

# Build for production
npm build

# Lint code
npm run lint

# Run tests
npm test

# API calls example (using axios)
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/'
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

**Ready to start building? 🚀**

1. Pick one section from either `STUDENT_APP_API_SPECS.md` or `TEACHER_APP_API_SPECS.md`
2. Copy the section
3. Ask Copilot to implement it
4. Integrate into your app
5. Move to next section

**Good luck! Happy coding! 💻✨**
