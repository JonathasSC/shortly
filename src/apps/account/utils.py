import os
import random
from django.utils.text import slugify
from datetime import datetime


class ProfileUtils:
    def generate_image_path(instance, filename):
        filename_base, filename_ext = os.path.splitext(filename)
        return f"profile_images/{slugify(instance.user.username)}_{datetime.now().date()}{filename_ext}"

    def get_random_profile_image(self):
        image_dir = 'media/profile_images'
        if not os.path.exists(image_dir):
            return 'default.png'
        image_files = os.listdir(image_dir)
        if image_files:
            return os.path.join('profile_images', random.choice(image_files))
        return 'default.png'
