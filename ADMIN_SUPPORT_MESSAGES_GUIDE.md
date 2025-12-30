# صفحه مدیریت پیام‌های پشتیبانی برای ادمین
# Admin Support Messages Management Page

## 📋 اطلاعات فایل

**مکان فایل:** `/templates/admin_support_messages.html`

**ویژگی‌های صفحه:**
- ✅ ریسپانسیو (موبایل، تبلت، دسکتاپ)
- ✅ طراحی مینیمال و مدرن
- ✅ رنگ‌های محدود (سفید، خاکستری، آبی، مشکی)
- ✅ آیکن‌های Font Awesome (بدون ایموجی)
- ✅ لیست پیام‌های دریافتی
- ✅ مشاهده جزئیات پیام
- ✅ پاسخ مستقیم به پیام
- ✅ حذف پیام
- ✅ فیلترکردن براساس وضعیت
- ✅ نمایش فایل‌های ضمیمه و دانلود آن‌ها
- ✅ صفحه‌بندی (pagination)

---

## 🚀 راه‌های استفاده

### 1. اضافه کردن صفحه به Admin Panel

**گزینه الف:** اضافه کردن به Django Admin

درون `classroom/admin.py`:

```python
from django.urls import path
from django.views.generic import TemplateView

class SupportMessageAdminSite(admin.AdminSite):
    site_header = "مدیریت پیام‌های پشتیبانی"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('support-messages/', TemplateView.as_view(template_name='admin_support_messages.html'), 
                 name='support_messages_dashboard'),
        ]
        return custom_urls + urls
```

**گزینه ب:** استفاده مستقل

```
http://yourserver/templates/admin_support_messages.html
```

### 2. اضافه کردن URL در پروژه

درون `fofofish/urls.py`:

```python
from django.views.generic import TemplateView

urlpatterns = [
    ...
    path('admin/support-messages/', TemplateView.as_view(
        template_name='admin_support_messages.html'
    ), name='admin_support_messages'),
]
```

### 3. دسترسی به صفحه

```
http://yourserver/admin/support-messages/
```

---

## 🔌 API Endpoints مورد استفاده

صفحه از API endpoints زیر استفاده می‌کند:

### 1. دریافت لیست پیام‌ها
```
GET /api/support-messages/
GET /api/support-messages/?status=sent
GET /api/support-messages/?status=read
GET /api/support-messages/?page=2
```

**پاسخ:**
```json
{
  "count": 25,
  "next": "/api/support-messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher_id": 5,
      "sender_id": 5,
      "sender_name": "محمد علی",
      "message_text": "متن پیام",
      "status": "sent",
      "created_at": "2024-12-26T14:30:00Z",
      "read_at": null,
      "attachments": [
        {
          "id": 1,
          "file_url": "/media/support_messages/2024/12/file.pdf",
          "file_name": "file.pdf"
        }
      ]
    }
  ]
}
```

### 2. علامت‌گذاری پیام خوانده‌شده
```
PATCH /api/support-messages/<message_id>/
```

**پاسخ:**
```json
{
  "id": 1,
  "status": "read",
  "read_at": "2024-12-26T14:35:00Z"
}
```

### 3. ارسال پاسخ (پیام جدید)
```
POST /api/support-messages/
Content-Type: multipart/form-data

teacher_id: 5
sender_id: 5
message_text: "متن پاسخ"
attachments: file1.pdf (optional)
```

### 4. حذف پیام
```
DELETE /api/support-messages/<message_id>/
```

**پاسخ:**
```
204 No Content
```

### 5. دریافت اطلاعات کاربر فعلی
```
GET /api/user/
```

---

## 🎨 ویژگی‌های طراحی

### Sidebar (سمت چپ)
- فیلتر براساس وضعیت پیام
- نمایش تعداد پیام‌ها برای هر فیلتر
- دکمه‌های کلیکی برای فیلتر کردن

### Messages Container (وسط)
- لیست تمام پیام‌ها
- نمایش نام فرستنده
- نمایش پیش‌نمایش متن پیام
- نمایش زمان ارسال
- نشانه‌های "جدید" و تعداد فایل‌های ضمیمه
- صفحه‌بندی در پایین

### Detail Panel (پایین)
- نمایش جزئیات کامل پیام
- نمایش وضعیت (ارسال‌شده/خوانده‌شده)
- فایل‌های ضمیمه قابل دانلود
- دکمه‌های "پاسخ دادن" و "حذف"

### Modal (Popup)
- فرم ارسال پاسخ
- فیلد متن برای نوشتن پاسخ
- فیلد فایل برای اضافه کردن ضمیمه
- دکمه‌های "ارسال" و "انصراف"

---

## 🔐 نیازمندی‌های امنیتی

### 1. Authentication
صفحه نیاز به احراز‌هویت دارد. توکن JWT می‌تواند از:
- `localStorage.access_token` (پیش‌فرض)
- `meta[name="auth-token"]` (meta tag)
- Header `Authorization: Bearer TOKEN`

### 2. Authorization
فقط ادمین‌ها می‌توانند پیام‌ها را مشاهده و مدیریت کنند:
```python
permission_classes = [IsAuthenticated]
# API باید بررسی کند که کاربر ادمین است
```

### 3. CSRF Protection
صفحه CSRF token را جستجو می‌کند:
```html
<input type="hidden" name="csrfmiddlewaretoken" value="...">
```

---

## 💡 نکات مهم

### 1. مدل SupportMessage
```python
class SupportMessage(BaseModel):
    teacher = ForeignKey(User, role='teacher' or 'admin')
    sender = ForeignKey(User, nullable=True)
    message_text = TextField(nullable=True)
    status = CharField(choices=['sent', 'read'])
    read_at = DateTimeField(nullable=True)
```

### 2. Endpoints مورد نیاز
- ✅ `GET /api/support-messages/` - لیست پیام‌ها
- ✅ `POST /api/support-messages/` - ارسال پیام
- ✅ `PATCH /api/support-messages/<id>/` - علامت خوانده‌شده
- ✅ `DELETE /api/support-messages/<id>/` - حذف پیام
- ✅ `GET /api/user/` - اطلاعات کاربر فعلی

### 3. فایل‌های ضمیمه
- نمایش خودکار آیکن بر اساس نوع فایل
- دانلود مستقیم از URL
- محدودیت اندازه فایل (بر اساس تنظیمات سرور)

### 4. Responsive Design
- **موبایل:** ستون واحد، Sidebar پنهان‌شده
- **تبلت:** 2 ستون، Sidebar کنار پیام‌ها
- **دسکتاپ:** 3 ستون، Sidebar، Messages، Detail

---

## 🐛 حل مشکلات عام

### مشکل: صفحه پیام‌ها نمی‌بارد
**حل:**
1. بررسی کنید که توکن احراز‌هویت معتبر است
2. چک کنید که URL API صحیح است
3. Console را باز کنید (F12) و بررسی کنید logs

### مشکل: فایل‌های ضمیمه نمایش نمی‌یابند
**حل:**
1. اطمینان دهید که `MEDIA_URL` و `MEDIA_ROOT` درست تنظیم شده‌اند
2. بررسی کنید که فایل‌ها در مسیر صحیح ذخیره شده‌اند

### مشکل: Modal برای پاسخ باز نمی‌شود
**حل:**
1. Console را بررسی کنید برای JavaScript errors
2. بررسی کنید که `#replyModal` element موجود است

---

## 📝 نمونه‌ی استفاده

```html
<!-- در یک صفحه HTML دیگر -->
<iframe src="/admin/support-messages/" style="width: 100%; height: 800px; border: none;"></iframe>

<!-- یا به صورت مستقل -->
<link rel="stylesheet" href="/static/css/admin_support_messages.css">
<script src="/static/js/admin_support_messages.js"></script>
```

---

## 🔄 Updated API Endpoints

### GET /api/user/
دریافت اطلاعات کاربر فعلی

**پاسخ:**
```json
{
  "id": 5,
  "username": "admin",
  "name": "تیم پشتیبانی",
  "email": "admin@example.com",
  "role": "admin"
}
```

---

## 📱 توافق‌پذیری مرورگر

- ✅ Chrome (آخرین نسخه)
- ✅ Firefox (آخرین نسخه)
- ✅ Safari (آخرین نسخه)
- ✅ Edge (آخرین نسخه)
- ✅ موبایل Browsers

---

## 🎯 خطوات نهایی

برای فعال کردن صفحه:

1. فایل `admin_support_messages.html` را به `/templates/` کپی کنید ✓
2. API endpoints را بررسی کنید ✓
3. DELETE endpoint را اضافه کنید (انجام‌شد ✓)
4. `/api/user/` endpoint را اضافه کنید (انجام‌شد ✓)
5. صفحه را از طریق مرورگر باز کنید
6. لاگین کنید (اگر لازم است)
7. پیام‌ها را مدیریت کنید!

---

**حاضر به استفاده! 🚀**
