from modeltranslation.translator import translator, TranslationOptions
from .models import User


class UserTranslationOptions(TranslationOptions):
    fields = ('name', 'bio')
translator.register(User, UserTranslationOptions)
