from io import BytesIO
import mimetypes

from django.core.files.base import ContentFile
from PIL import Image


class ImageProcessor:
    MAX_SIZE = (512, 512)

    def resize(self, image_file):
        image = Image.open(image_file)
        
        # Manter o modo de cor correto (RGB para JPEG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        image.thumbnail(self.MAX_SIZE, Image.LANCZOS)
        buffer = BytesIO()
        
        # Mantém o formato original ou usa JPEG como padrão
        img_format = image.format if image.format else "JPEG"
        image.save(buffer, format=img_format, quality=90)

        # Garantir o Content-Type correto
        content_type = mimetypes.guess_type(image_file.name)[0] or f"image/{img_format.lower()}"
        
        content_file = ContentFile(buffer.getvalue())
        content_file.content_type = content_type # Isso ajuda o S3 a identificar o arquivo
        
        return content_file
