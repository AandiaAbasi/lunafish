from modeltranslation.translator import translator, TranslationOptions
from .models import Field


class FieldTranslationOptions(TranslationOptions):
    fields = ('title', 'des')

translator.register(Field, FieldTranslationOptions)
