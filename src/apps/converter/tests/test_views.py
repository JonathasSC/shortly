from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class UrlViewTests(TestCase):
    def setUp(self):
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


