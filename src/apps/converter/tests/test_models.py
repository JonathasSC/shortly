from django.contrib.auth.models import User
from django.test import TestCase

from apps.converter.models import AccessEvent, Url


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
            counter=1
        )

        self.assertIsNotNone(event.pk)
        self.assertEqual(event.url, self.url)
        self.assertEqual(event.ip_address, '123.123.123.123')
        self.assertEqual(event.counter, 1)

    def test_multiple_access_events(self):
        AccessEvent.objects.create(
            url=self.url,
            ip_address='111.111.111.111',
            counter=1
        )
        AccessEvent.objects.create(
            url=self.url,
            ip_address='222.222.222.222',
            counter=2
        )

        events = AccessEvent.objects.filter(url=self.url)
        self.assertEqual(events.count(), 2)
        self.assertEqual(events[0].ip_address, '111.111.111.111')
        self.assertEqual(events[1].ip_address, '222.222.222.222')
