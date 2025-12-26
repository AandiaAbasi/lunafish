from modeltranslation.translator import translator, TranslationOptions
from .models import About, Term, Privacy, Contact, Article, FAQ, Banner


class AboutTranslationOptions(TranslationOptions):
    fields = ('title', 'content')
    empty_values = ('title', 'content')
translator.register(About, AboutTranslationOptions)

class TermTranslationOptions(TranslationOptions):
    fields = ('title', 'content')
    empty_values = ('title', 'content')
translator.register(Term, TermTranslationOptions)

class PrivacyTranslationOptions(TranslationOptions):
    fields = ('title', 'content')
    empty_values = ('title', 'content')
translator.register(Privacy, PrivacyTranslationOptions)

class ContactTranslationOptions(TranslationOptions):
    fields = ('title', 'value')
    empty_values = ('title', 'value')
translator.register(Contact, ContactTranslationOptions)

class ArticleTranslationOptions(TranslationOptions):
    fields = ('title', 'short_description', 'content')
    empty_values = ('title', 'short_description', 'content')
translator.register(Article, ArticleTranslationOptions)

class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')
    empty_values = ('question', 'answer')
translator.register(FAQ, FAQTranslationOptions)

class BannerTranslationOptions(TranslationOptions):
    fields = ('title', 'sub_title')
    empty_values = ('title', 'sub_title')
translator.register(Banner, BannerTranslationOptions)
