from django.test import TestCase
from apps.converter.models import Url
from django.contrib.auth.models import User


class UrlModelTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
            username='Example',
            email='example@email.com'
        )

        user = User.objects.get(email='example@email.com')

        Url.objects.create(
            original_url='https://sh0rtly.com',
            created_by=user
        )

    def test_url_create(self):
        url = Url.objects.get(original_url='https://sh0rtly.com')
        self.assertEqual(url.original_url, 'https://sh0rtly.com')
