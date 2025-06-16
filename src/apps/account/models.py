from django.db.models import ImageField, Model, UUIDField, OneToOneField, OneToOneField, CASCADE
from uuid6 import uuid7
from .utils import ProfileUtils
from django.contrib.auth.models import User


profile_utils: ProfileUtils = ProfileUtils()


class UserProfile(Model):
    id: UUIDField = UUIDField(
        primary_key=True,
        editable=False,
        default=uuid7
    )

    user: OneToOneField = OneToOneField(User, on_delete=CASCADE)

    profile_picture = ImageField(
        upload_to=profile_utils.generate_image_path,
        default=profile_utils.get_random_profile_image
    )

    def __str__(self):
        return f"Perfil de {self.user.username}"
