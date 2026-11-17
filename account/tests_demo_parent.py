"""Tests for the separate demo parent credential flow."""
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from account.models import ParentProfile, User


class SofiaDemoParentTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="sofia.martins.lf", name="Sofia Martins",
            role="user", password="Student-Password-For-Tests-Only",
        )

    def test_preview_does_not_create_parent(self):
        call_command("setup_sofia_demo_parent", stdout=StringIO())
        self.assertFalse(ParentProfile.objects.filter(student=self.student).exists())

    def test_parent_has_independent_password_and_can_log_in(self):
        parent_secret = "Parent-Passphrase-For-Tests-Only"
        with patch.dict("os.environ", {"LUNAFISH_DEMO_PARENT_PASSWORD": parent_secret}):
            call_command(
                "setup_sofia_demo_parent",
                apply=True, confirm_presentation=True,
                stdout=StringIO(),
            )
        parent = ParentProfile.objects.get(
            student=self.student, parent_name="Mariana Martins",
        )
        self.assertTrue(parent.is_active)
        self.assertTrue(parent.verify_password(parent_secret))
        self.assertFalse(parent.verify_password("Student-Password-For-Tests-Only"))
        self.assertTrue(self.student.check_password("Student-Password-For-Tests-Only"))
        api = APIClient()
        response = api.post("/api/parent/login/", {
            "username": self.student.username, "password": parent_secret,
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)

    def test_existing_parent_requires_explicit_reset(self):
        with patch.dict("os.environ", {"LUNAFISH_DEMO_PARENT_PASSWORD": "First-Demo-Parent-Password"}):
            call_command("setup_sofia_demo_parent", apply=True, confirm_presentation=True, stdout=StringIO())
        with patch.dict("os.environ", {"LUNAFISH_DEMO_PARENT_PASSWORD": "Second-Demo-Parent-Password"}):
            with self.assertRaises(CommandError):
                call_command("setup_sofia_demo_parent", apply=True, confirm_presentation=True, stdout=StringIO())
            call_command(
                "setup_sofia_demo_parent",
                apply=True, confirm_presentation=True, reset_existing=True,
                stdout=StringIO(),
            )
        parent = ParentProfile.objects.get(student=self.student, parent_name="Mariana Martins")
        self.assertTrue(parent.verify_password("Second-Demo-Parent-Password"))
