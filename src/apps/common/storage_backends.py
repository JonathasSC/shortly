from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PrivateS3Storage(S3Boto3Storage):
    default_acl = None
    file_overwrite = False

    querystring_auth = True
    querystring_expire = 3600  # 1 hora

    signature_version = 's3v4'
    addressing_style = 'virtual'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('bucket_name', getattr(
            settings, 'AWS_STORAGE_BUCKET_NAME', None))
        kwargs.setdefault('region_name', getattr(
            settings, 'AWS_S3_REGION_NAME', ''))
        super().__init__(*args, **kwargs)
