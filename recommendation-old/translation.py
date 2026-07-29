from modeltranslation.translator import register
from .models import PsychologicalTest, TestQuestion, QuestionOption, TestScale, ScaleInterpretation

from basetranslation.translation_base import (
    TitleTranslationOptions,
    DescriptionTranslationOptions,
    QuestionTextTranslationOptions,
    OptionTextTranslationOptions
)


@register(PsychologicalTest)
class PsychologicalTestTranslation(TitleTranslationOptions, DescriptionTranslationOptions):
    pass

@register(TestQuestion)
class TestQuestionTranslation(QuestionTextTranslationOptions):
    pass

@register(QuestionOption)
class QuestionOptionTranslation(OptionTextTranslationOptions):
    pass

@register(TestScale)
class TestScaleTranslation(TitleTranslationOptions,DescriptionTranslationOptions):
    pass

@register(ScaleInterpretation)
class ScaleInterpretationTranslation(TitleTranslationOptions,DescriptionTranslationOptions):
    pass
