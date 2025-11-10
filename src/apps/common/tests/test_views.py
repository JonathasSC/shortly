from django.test import TestCase
from django.urls import reverse


class NotFoundViewTest(TestCase):
    def test_notfound_view_status_code_and_template(self):
        url = reverse('notfound')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'common/404.html')
