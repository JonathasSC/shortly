from uuid import uuid4


class ShortCodeGenerator:
    def __init__(self, length=8):
        self.length = length

    def generate(self):
        return str(uuid4()).replace('-', '')[:self.length]

    def generate_unique(self, model, field_name):
        while True:
            code = self.generate()
            filter_kwargs = {field_name: code}
            if not model.objects.filter(**filter_kwargs).exists():
                return code


class UserRequestUtil:
    def get_client_ip(self, request):
        return (
            request.META.get("HTTP_CF_CONNECTING_IP")
            or request.META.get("HTTP_X_FORWARDED_FOR")
            or request.META.get("REMOTE_ADDR")
        )

    def get_country(self, request):
        return request.META.get("HTTP_CF_IPCOUNTRY")