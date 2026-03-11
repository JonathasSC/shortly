from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


class ImageProcessor:
    MAX_SIZE = (512, 512)

    def resize(self, image_file):
        image = Image.open(image_file)
        image.thumbnail(self.MAX_SIZE, Image.LANCZOS)
        buffer = BytesIO()
        format = image.format if image.format else "JPEG"
        image.save(buffer, format=format, quality=90)

        return ContentFile(buffer.getvalue())
