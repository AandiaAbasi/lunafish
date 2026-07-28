"""
Custom template tags for adviser app.
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ dict|get_item:key }}
    """
    if not isinstance(dictionary, dict):
        return ''
    return dictionary.get(key, '')


@register.filter
def get_weight(weights_dict, scale_code):
    """
    Get weight value from weights dictionary by scale code.
    Usage: {{ option_data.weights|get_weight:scale.code }}
    """
    if not isinstance(weights_dict, dict):
        return 0
    return weights_dict.get(scale_code, 0)


@register.filter
def get_by_code(queryset_or_list, code):
    """
    Get a scale object from queryset/list by code.
    Usage: {{ scales|get_by_code:scale_code }}
    """
    try:
        for item in queryset_or_list:
            if hasattr(item, 'code') and item.code == code:
                return item
    except (TypeError, AttributeError):
        pass
    return None


@register.filter
def div(value, arg):
    """
    Divide value by arg.
    Usage: {{ 100|div:5 }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
