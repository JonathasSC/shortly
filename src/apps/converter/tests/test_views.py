from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.converter.models import Url


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

    def test_create_short_url_authenticated_user(self):
        self.client.login(username='jonathas.cardoso', password='password')
        response = self.client.post(
            reverse('home'), self.url_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Url.objects.filter(
            original_url='https://example.com').exists())

    def test_create_short_url_anonymous_user(self):
        response = self.client.post(
            reverse('home'),
            self.url_data,
            follow=True,
            **{'REMOTE_ADDR': self.anonymous_ip}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Url.objects.filter(
            created_by_ip=self.anonymous_ip).exists())

    def test_anonymous_user_limit_exceeded(self):
        for _ in range(5):
            self.client.post(reverse('home'), self.url_data,
                             **{'REMOTE_ADDR': self.anonymous_ip})

        response = self.client.post(reverse(
            'home'), self.url_data, follow=True, **{'REMOTE_ADDR': self.anonymous_ip})
        self.assertContains(
            response, 'Você atingiu o limite de 5 links por dia')

    def test_reuse_existing_url(self):
        self.client.login(username='jonathas.cardoso', password='password')
        url = Url.objects.create(
            original_url='https://example.com', created_by=self.user)

        response = self.client.post(
            reverse('home'), {'original_url': 'https://example.com'}, follow=True)
        self.assertContains(response, url.short_code)

    def test_middle_view_redirects_for_specific_user(self):
        url = Url.objects.create(
            original_url='https://google.com', created_by=self.user)

        response = self.client.get(
            reverse('url-redirect', kwargs={'short_code': url.short_code}))
        self.assertRedirects(response, 'https://google.com',
                             fetch_redirect_response=False)

    def test_middle_view_renders_intermediate_page(self):
        other_user = User.objects.create_user(username='maria', password='123')
        url = Url.objects.create(
            original_url='https://google.com', created_by=other_user)

        response = self.client.get(
            reverse('url-redirect', kwargs={'short_code': url.short_code}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/middle.html')
        self.assertContains(response, 'Vc está sendo redirecionado em')
