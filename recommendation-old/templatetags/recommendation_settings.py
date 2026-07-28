from django import template

from recommendation.form_settings import show_translation_fields


register = template.Library()


@register.simple_tag
def recommendation_translation_fields_enabled():
    return show_translation_fields()
