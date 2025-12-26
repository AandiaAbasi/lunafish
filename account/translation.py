from modeltranslation.translator import translator, TranslationOptions
from .models import User
from .admin import RegularUserProxy, TeacherUserProxy


class UserTranslationOptions(TranslationOptions):
    fields = ('name', 'bio')

translator.register(User, UserTranslationOptions)
translator.register(RegularUserProxy, UserTranslationOptions)
translator.register(TeacherUserProxy, UserTranslationOptions)
