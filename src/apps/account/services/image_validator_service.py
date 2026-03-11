from PIL import Image


class ImageValidator:

    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    @classmethod
    def validate_extension(cls, filename):

        ext = filename.split(".")[-1].lower()

        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError("Invalid image extension.")

    @staticmethod
    def validate_image(file):

        try:
            img = Image.open(file)
            img.verify()
        except Exception:
            raise ValueError("Invalid image file.")