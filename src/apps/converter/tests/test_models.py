from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.converter.models import AccessEvent, Url

User = get_user_model()


class UrlModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='Example',
            email='example@email.com'
        )

        self.url = Url.objects.create(
            original_url='https://sh0rtly.com',
            created_by=self.user
        )

    def test_url_create(self):
        url = Url.objects.get(original_url='https://sh0rtly.com')
        self.assertEqual(url.original_url, 'https://sh0rtly.com')
        self.assertIsNotNone(url.short_code)
        self.assertIsNotNone(url.expires_at)
        self.assertFalse(url.is_expired())


class AccessEventModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='AccessUser',
            email='accessuser@email.com'
        )

        self.url = Url.objects.create(
            original_url='https://example.com',
            created_by=self.user
        )

    def test_access_event_creation(self):
        event = AccessEvent.objects.create(
            url=self.url,
            ip_address='123.123.123.123',
        )

        self.assertIsNotNone(event.pk)
        self.assertEqual(event.url, self.url)
        self.assertEqual(event.ip_address, '123.123.123.123')

    def test_multiple_access_events(self):
        AccessEvent.objects.create(
            url=self.url,
            ip_address='111.111.111.111',
        )
        AccessEvent.objects.create(
            url=self.url,
            ip_address='222.222.222.222',
        )

        events = AccessEvent.objects.filter(
            url=self.url).order_by('created_at')
        self.assertEqual(events.count(), 2)
        self.assertEqual(events[0].ip_address, '111.111.111.111')
        self.assertEqual(events[1].ip_address, '222.222.222.222')
