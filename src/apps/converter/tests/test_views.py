from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.common.utils import CommonUtils

User = get_user_model()


class UrlViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.client = Client()
        self.user = User.objects.create_user(
            username='jonathas.cardoso', password='password')
        self.anonymous_ip = '123.123.123.123'
        self.url_data = {
            'original_url': 'https://example.com'
        }

    def test_home_view_get(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/home.html')
