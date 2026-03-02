from user_agents import parse

from apps.converter.models import AccessEvent
from apps.converter.utils import UserRequestUtil

user_request_util = UserRequestUtil()


class AccessEventService:

    @staticmethod
    def track(request, url):
        ip_address = user_request_util.get_client_ip(request)

        ua_string = request.META.get("HTTP_USER_AGENT", "")
        user_agent = parse(ua_string)

        browser = user_agent.browser.family or None
        browser_version = user_agent.browser.version_string or None
        os = user_agent.os.family or None

        device_type = (
            "Mobile" if user_agent.is_mobile
            else "Tablet" if user_agent.is_tablet
            else "PC"
        )

        referer = request.META.get("HTTP_REFERER")

        country = request.META.get("HTTP_CF_IPCOUNTRY")
        region = request.META.get("HTTP_CF_REGION")
        city = request.META.get("HTTP_CF_IPCITY")
        latitude = request.META.get("HTTP_CF_IPLATITUDE")
        longitude = request.META.get("HTTP_CF_IPLONGITUDE")

        return AccessEvent.objects.create(
            url=url,
            ip_address=ip_address,
            user_agent=ua_string,
            referer=referer,
            browser=browser,
            browser_version=browser_version,
            os=os,
            device_type=device_type,
            country=country,
            region=region,
            city=city,
            latitude=latitude,
            longitude=longitude,
            is_bot=user_agent.is_bot,
        )
        
    @staticmethod
    def get_client_ip(request):
        cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            return cf_ip

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]

        return request.META.get("REMOTE_ADDR")
