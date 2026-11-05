# crimes/templatetags/crime_filters.py
from django import template

register = template.Library()

@register.filter
def confidence_color(value):
    """Return Bootstrap color class based on confidence percentage"""
    try:
        confidence = int(value)
        if confidence >= 90:
            return 'danger'
        elif confidence >= 70:
            return 'warning'
        elif confidence >= 50:
            return 'info'
        else:
            return 'success'
    except:
        return 'secondary'

@register.filter
def type_color(value):
    """Return color based on update type"""
    color_map = {
        'SITE_VISIT': 'primary',
        'WITNESS_STATEMENT': 'success',
        'EVIDENCE_COLLECTED': 'info',
        'SUSPECT_IDENTIFIED': 'warning',
        'ARRAEST_MADE': 'danger',
        'CHARGESHEET_PREPARED': 'dark',
        'OTHER': 'secondary',
    }
    return color_map.get(value, 'secondary')

@register.filter
def status_color(value):
    """Return color based on biometric status"""
    color_map = {
        'NOT_CAPTURED': 'danger',
        'CAPTURED': 'warning',
        'VERIFIED': 'info',
        'MATCH_FOUND': 'danger',
        'SUSPICIOUS': 'warning',
    }
    return color_map.get(value, 'secondary')

@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status"""
    return queryset.filter(status=status)

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)