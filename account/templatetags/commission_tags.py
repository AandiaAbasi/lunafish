"""
Template tags for commission rate calculations
"""
import logging
from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def get_teacher_commission(teacher, transaction_type='purchase'):
    """
    Get commission rate information for a teacher

    Usage:
        {% load commission_tags %}
        {% get_teacher_commission teacher as commission_data %}
        {{ commission_data.rate }}
        {{ commission_data.is_custom }}

    Args:
        teacher: User object (teacher)
        transaction_type: 'purchase', 'custom_order', or 'gift'

    Returns:
        dict with 'rate' (Decimal) and 'is_custom' (bool)
    """
    try:
        if not teacher:
            return {
                'is_custom': False
            }

        is_custom = hasattr(teacher, 'commission_rate_override') and teacher.commission_rate_override is not None

        return {
            'is_custom': is_custom
        }
    except Exception as e:
        # Fallback to default if error
        logger = logging.getLogger(__name__)
        logger.error(_("Error getting commission rate: %s") % str(e))

        return {
            'rate': 30.00,
            'is_custom': False
        }


@register.filter
def commission_percentage(value):
    """
    Format commission rate as percentage

    Usage: {{ rate|commission_percentage }}
    """
    try:
        return f"{float(value):.0f}%"
    except (ValueError, TypeError):
        return _("N/A")
