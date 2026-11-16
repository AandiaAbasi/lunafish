from django.contrib import admin
from django.test import SimpleTestCase

from account.admin import RegularUserProxy, TeacherUserProxy
from account.models import User
from classroom.models import Course, Package, TeachingSubject


class AdminMediaEditingTests(SimpleTestCase):
    """Regression coverage: allow media changes without opening business fields."""

    def test_teacher_profile_photo_is_editable(self):
        model_admin = admin.site._registry[TeacherUserProxy]
        teacher = User(role='teacher')
        readonly = model_admin.get_readonly_fields(request=None, obj=teacher)
        self.assertNotIn('profile_photo_path', readonly)
        self.assertIn('profile_photo_display', readonly)
        self.assertIn('profile_photo_path', model_admin.get_fieldsets(None, teacher)[3][1]['fields'])

    def test_student_photo_is_editable_but_account_fields_remain_readonly(self):
        model_admin = admin.site._registry[RegularUserProxy]
        student = User(role='user')
        readonly = model_admin.get_readonly_fields(request=None, obj=student)
        self.assertNotIn('profile_photo_path', readonly)
        for field in ('username', 'email', 'phone', 'english_level'):
            self.assertIn(field, readonly)

    def test_subject_cover_is_editable_without_changing_subject(self):
        model_admin = admin.site._registry[TeachingSubject]
        readonly = model_admin.get_readonly_fields(request=None, obj=TeachingSubject())
        self.assertNotIn('cover_image', readonly)
        self.assertIn('cover_image_preview', readonly)
        for field in ('teacher', 'title', 'description', 'demo_video'):
            self.assertIn(field, readonly)

    def test_course_cover_is_editable_without_changing_course(self):
        model_admin = admin.site._registry[Course]
        self.assertNotIn('cover_image', model_admin.get_readonly_fields(None, Course()))
        for field in ('subject', 'price', 'title', 'session_count'):
            self.assertIn(field, model_admin.get_readonly_fields(None, Course()))
        self.assertIn('cover_image_preview', model_admin.readonly_fields)

    def test_package_admin_limits_edits_to_cover(self):
        model_admin = admin.site._registry[Package]
        fields = model_admin.fields
        readonly = model_admin.readonly_fields
        editable_fields = set(fields) - set(readonly)
        self.assertEqual(editable_fields, {'cover_image'})
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))
