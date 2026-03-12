from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class PrivateS3Storage(S3Boto3Storage):
    """
    Storage para arquivos que devem ser mantidos privados.
    Gera URLs assinadas com tempo de expiração curto.
    """
    default_acl = None
    file_overwrite = False
    
    # Forçamos a assinatura via querystring para buckets privados
    querystring_auth = True
    querystring_expire = 3600 # 1 hora
    
    # IMPORTANTE: Para sa-east-1, precisamos garantir que a assinatura v4 e o SSL sejam usados
    signature_version = 's3v4'
    addressing_style = 'virtual'
    
    def __init__(self, *args, **kwargs):
        # Garante que as configurações do settings.py sejam passadas corretamente
        kwargs.setdefault('bucket_name', getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None))
        kwargs.setdefault('region_name', getattr(settings, 'AWS_S3_REGION_NAME', ''))
        super().__init__(*args, **kwargs)
