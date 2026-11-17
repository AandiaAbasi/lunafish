"""Regression tests for bilingual placement test editing and student payloads."""
from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from recommendation.forms import PsychologicalTestForm, TestQuestionForm, QuestionOptionForm
from recommendation.models import (
    PsychologicalTest, TestQuestion, QuestionOption, StudentTestResponse, StudentAnswer,
)


class BilingualPlacementTestTests(TestCase):
    def setUp(self):
        self.test = PsychologicalTest.objects.create(
            title_fa="آزمون آزمایشی",
            title_en="Placement exam",
            description_fa="توضیحات فارسی",
            description_en="English description",
            is_active=True,
        )
        self.question = TestQuestion.objects.create(
            test=self.test,
            question_text_fa="پایتخت فرانسه کجاست؟",
            question_text_en="What is the capital of France?",
            order=1,
        )
        self.option = QuestionOption.objects.create(
            question=self.question,
            option_text_fa="پاریس",
            option_text_en="Paris",
            order=1,
        )
        user_model = get_user_model()
        self.student = user_model.objects.create_user(
            username="bilingual-placement-student", password="testing-12345",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    @override_settings(RECOMMENDATION_SHOW_TRANSLATION_FIELDS=False)
    def test_admin_forms_always_show_editable_english_inputs(self):
        for form_class, english_field in (
            (PsychologicalTestForm, "title_en"),
            (TestQuestionForm, "question_text_en"),
            (QuestionOptionForm, "option_text_en"),
        ):
            with self.subTest(field=english_field):
                form = form_class()
                self.assertIn(english_field, form.fields)
                self.assertNotIsInstance(form.fields[english_field].widget, forms.HiddenInput)

    def test_list_and_detail_use_requested_language(self):
        urls = (
            reverse("recommendation:psychological_tests_list"),
            reverse("recommendation:psychological_test_detail", args=[self.test.pk]),
        )
        for lang, expected_title, expected_question, expected_option in (
            ("fa", "آزمون آزمایشی", "پایتخت فرانسه کجاست؟", "پاریس"),
            ("en", "Placement exam", "What is the capital of France?", "Paris"),
        ):
            with self.subTest(lang=lang):
                listing = self.client.get(urls[0], {"lang": lang}, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(listing.status_code, 200, listing.data)
                self.assertEqual(listing.data["data"]["tests"][0]["title"], expected_title)
                detail = self.client.get(urls[1], {"lang": lang}, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(detail.status_code, 200, detail.data)
                self.assertEqual(detail.data["data"]["test"]["title"], expected_title)
                question = detail.data["data"]["questions"][0]
                self.assertEqual(question["text"], expected_question)
                self.assertEqual(question["options"][0]["text"], expected_option)

    def test_accept_language_header_alone_selects_translation(self):
        url = reverse("recommendation:psychological_test_detail", args=[self.test.pk])
        result = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["data"]["test"]["title"], "Placement exam")
        self.assertEqual(
            result.data["data"]["questions"][0]["options"][0]["text"],
            "Paris",
        )

    def test_saved_answer_text_follows_language_without_changing_ids(self):
        response = StudentTestResponse.objects.create(
            test=self.test, user=self.student, status="completed",
            started_at=timezone.now(), completed_at=timezone.now(),
        )
        StudentAnswer.objects.create(
            response=response, question=self.question, selected_option=self.option,
        )
        url = reverse("recommendation:psychological_test_view_answers", args=[self.test.pk])
        for lang, expected_text in (("fa", "پاریس"), ("en", "Paris")):
            with self.subTest(lang=lang):
                result = self.client.get(url, {"lang": lang}, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(result.status_code, 200, result.data)
                row = result.data["data"]["questions_with_answers"][0]
                self.assertEqual(row["answer"]["selected_option_id"], self.option.pk)
                self.assertEqual(row["answer"]["selected_option_text"], expected_text)
                self.assertEqual(row["question"]["options"][0]["text"], expected_text)
