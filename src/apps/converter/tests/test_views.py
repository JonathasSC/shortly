from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.common.utils import CommonUtils
from apps.converter.models import AccessEvent, Url, UrlMetadata

User = get_user_model()


class UrlViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.client = Client()
        self.user = User.objects.create_user(
            username='jonathas.cardoso', email='jonathas@test.com', password='password')
        self.anonymous_ip = '123.123.123.123'
        self.url_data = {
            'original_url': 'https://example.com'
        }

    def test_home_view_get(self):
        response = self.client.get(reverse('converter:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/home.html')


def _make_url(user, original_url='https://example.com', is_permanent=False, is_direct=False):
    url = Url.objects.create(original_url=original_url, created_by=user)
    UrlMetadata.objects.create(url=url, is_permanent=is_permanent, is_direct=is_direct)
    return url


class QrCodeImageViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass')
        self.other = User.objects.create_user(username='other', email='other@test.com', password='pass')
        self.url = _make_url(self.owner)

    def test_returns_png_for_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_response_is_valid_png(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertTrue(response.content[:4] == b'\x89PNG')

    def test_cache_control_header(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertIn('max-age=3600', response.get('Cache-Control', ''))

    def test_content_disposition_is_inline(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertIn('inline', response.get('Content-Disposition', ''))
        self.assertIn(self.url.short_code, response.get('Content-Disposition', ''))

    def test_requires_login(self):
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertRedirects(response, f'/account/login/?next=/url/{self.url.short_code}/qr.png')

    def test_returns_404_for_non_owner(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': self.url.short_code})
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_code(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-qr', kwargs={'short_code': 'nonexist'})
        )
        self.assertEqual(response.status_code, 404)


class UrlDetailViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.client = Client()
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass')
        self.other = User.objects.create_user(username='other', email='other@test.com', password='pass')
        self.url = _make_url(self.owner)

    def _detail_url(self, url=None):
        url = url or self.url
        return reverse('converter:url-detail', kwargs={'short_code': url.short_code})

    def test_requires_login(self):
        response = self.client.get(self._detail_url())
        self.assertRedirects(
            response, f'/account/login/?next=/url/{self.url.short_code}/'
        )

    def test_returns_200_for_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/url_detail.html')

    def test_returns_404_for_non_owner(self):
        self.client.force_login(self.other)
        response = self.client.get(self._detail_url())
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_code(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('converter:url-detail', kwargs={'short_code': 'nonexist'})
        )
        self.assertEqual(response.status_code, 404)

    def test_context_has_days_until_expiry(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url())
        self.assertIn('days_until_expiry', response.context)
        days = response.context['days_until_expiry']
        self.assertIsNotNone(days)
        self.assertGreaterEqual(days, 0)
        self.assertLessEqual(days, 7)

    def test_days_until_expiry_is_none_for_permanent_url(self):
        url = _make_url(self.owner, is_permanent=True)
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url(url))
        self.assertIsNone(response.context['days_until_expiry'])

    def test_days_until_expiry_is_none_when_expired(self):
        url = _make_url(self.owner)
        url.created_at = timezone.now() - timedelta(days=8)
        url.save()
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url(url))
        self.assertTrue(response.context['is_expired'])
        self.assertIsNone(response.context['days_until_expiry'])

    def test_context_total_clicks_and_unique_visitors(self):
        AccessEvent.objects.create(url=self.url, ip_address='1.1.1.1')
        AccessEvent.objects.create(url=self.url, ip_address='1.1.1.1')
        AccessEvent.objects.create(url=self.url, ip_address='2.2.2.2')
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url())
        self.assertEqual(response.context['total_clicks'], 3)
        self.assertEqual(response.context['unique_visitors'], 2)

    def test_context_has_metadata(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url())
        self.assertIsNotNone(response.context['metadata'])

    def test_context_has_short_url(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._detail_url())
        self.assertIn(self.url.short_code, response.context['short_url'])
