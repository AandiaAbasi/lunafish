"""
Custom template filters for phone number formatting and number formatting
"""
from django import template
from account.utils import format_phone_display

register = template.Library()


@register.filter(name='phone_display')
def phone_display(value):
    """
    Convert phone number from +98 format to 09 format
    Usage in template: {{ user.phone|phone_display }}
    """
    return format_phone_display(value)


@register.filter(name='intcomma')
def intcomma(value):
    """
    Format number with comma separators (thousands separator)
    Usage in template: {{ price|intcomma }}
    Example: 1234567 -> 1,234,567
    """
    try:
        # Convert to float first to handle Decimal and other numeric types
        value = float(value)
        # Convert to int if it's a whole number
        if value.is_integer():
            value = int(value)
        # Format with commas
        return "{:,}".format(value)
    except (ValueError, TypeError, AttributeError):
        return value
