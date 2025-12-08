from functools import lru_cache

from apps.toggler.models import FeatureFlag


@lru_cache(maxsize=50)
def is_feature_enabled(name: str) -> bool:
    try:
        return FeatureFlag.objects.get(name=name).enabled
    except FeatureFlag.DoesNotExist:
        return False
