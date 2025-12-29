from modeltranslation.translator import translator, TranslationOptions
from .models import Field, FieldDetail, CategoryField, Order, OrderDetail


class FieldTranslationOptions(TranslationOptions):
    fields = ('title', 'des', 'guide')

translator.register(Field, FieldTranslationOptions)


class FieldDetailTranslationOptions(TranslationOptions):
    fields = ('title', 'second_title', 'des', 'guide')

translator.register(FieldDetail, FieldDetailTranslationOptions)


class CategoryFieldTranslationOptions(TranslationOptions):
    fields = ('type',)

translator.register(CategoryField, CategoryFieldTranslationOptions)
