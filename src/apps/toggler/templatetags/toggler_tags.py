from django import template
from apps.toggler.models import FeatureFlag

register = template.Library()


def check_flag(user, feature_name: str) -> bool:
    if user is None or not hasattr(user, "is_authenticated"):
        return False

    try:
        flag = FeatureFlag.objects.get(name=feature_name)
    except FeatureFlag.DoesNotExist:
        return False

    if not flag.enabled:
        return False

    if flag.superuser_only:
        return user.is_superuser

    return user.is_authenticated


@register.filter(name="feature_enabled")
def feature_enabled_filter(user, feature_name: str):
    return check_flag(user, feature_name)