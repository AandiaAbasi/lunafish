from django.http import QueryDict
from django.test import TestCase

from recommendation.models import (
    OptionScaleWeight,
    PsychologicalTest,
    QuestionOption,
    TestQuestion,
    TestScale,
)
from recommendation.services.test_service import TestService


class OptionWeightPreservationTests(TestCase):
    def setUp(self):
        self.test = PsychologicalTest.objects.create(
            title='English placement',
            test_type='english_placement',
        )
        self.question = TestQuestion.objects.create(
            test=self.test,
            question_text='Question 1',
            order=1,
        )
        self.first_option = QuestionOption.objects.create(
            question=self.question,
            option_text='First',
            order=1,
        )
        self.second_option = QuestionOption.objects.create(
            question=self.question,
            option_text='Second',
            order=2,
        )
        self.scale = TestScale.objects.create(
            test=self.test,
            code='A1',
            title='A1',
            scale_type=TestScale.ScaleType.LEVEL,
            rank=1,
            pass_score=60,
        )
        OptionScaleWeight.objects.create(
            option=self.first_option,
            scale=self.scale,
            weight=10,
        )

    def test_editing_option_text_keeps_option_id_and_weight(self):
        post_data = QueryDict('', mutable=True)
        post_data.update({
            'options-0-0-option_text_fa': 'گزینه ویرایش‌شده',
            'options-0-0-option_text_en': 'Edited option',
            'options-0-0-icon': '',
            'options-0-1-option_text_fa': 'گزینه دوم',
            'options-0-1-option_text_en': 'Second',
            'options-0-1-icon': '',
        })

        TestService._sync_question_options(self.question, 0, post_data)

        self.first_option.refresh_from_db()
        self.assertEqual(self.first_option.option_text_en, 'Edited option')
        self.assertTrue(
            OptionScaleWeight.objects.filter(
                option_id=self.first_option.id,
                scale=self.scale,
                weight=10,
            ).exists()
        )

    def test_adding_option_does_not_remove_existing_weights(self):
        post_data = QueryDict('', mutable=True)
        post_data.update({
            'options-0-0-id': str(self.first_option.id),
            'options-0-0-option_text_fa': 'اول',
            'options-0-0-option_text_en': 'First',
            'options-0-1-id': str(self.second_option.id),
            'options-0-1-option_text_fa': 'دوم',
            'options-0-1-option_text_en': 'Second',
            'options-0-2-option_text_fa': 'سوم',
            'options-0-2-option_text_en': 'Third',
        })

        TestService._sync_question_options(self.question, 0, post_data)

        self.assertEqual(self.question.options.count(), 3)
        self.assertTrue(
            OptionScaleWeight.objects.filter(
                option_id=self.first_option.id,
                scale=self.scale,
                weight=10,
            ).exists()
        )
