from modeltranslation.translator import TranslationOptions


class TitleTranslationOptions(TranslationOptions):
    fields = ("title",)
    
class DesTranslationOptions(TranslationOptions):
    fields = ("des",)
class DescriptionTranslationOptions(TranslationOptions):
    fields = ("description",)
class QuestionTextTranslationOptions(TranslationOptions):
    fields = ("question_text",)
class OptionTextTranslationOptions(TranslationOptions):
    fields = ("option_text",)

class SlugTranslationOptions(TranslationOptions):
    fields = ("slug",)


class TitleGuideDesTranslationOptions(TranslationOptions):
    fields = ("title", "guide", "des")


class FullFieldTranslationOptions(TranslationOptions):
    fields = ("title", "second_title", "guide", "des")
