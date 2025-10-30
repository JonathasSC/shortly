from django.test import TestCase
from django.urls import reverse

from apps.account.models import User


class RegisterViewTests(TestCase):
    def test_register_page_loads_successfully(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/register.html")

    def test_register_creates_user(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "StrongPassword123",
            "password2": "StrongPassword123",
        }
        response = self.client.post(reverse("register"), data)
        
        form = response.context.get("form")
        if form:
            print(form.errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

        self.assertTrue(User.objects.filter(username="newuser").exists())


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="12345"
        )

    def test_login_page_loads_successfully(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_valid_login_redirects_to_home(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "12345"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_authenticated_user_is_redirected(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="logoutuser",
            password="12345"
        )

    def test_logout_redirects_to_login(self):
        self.client.login(username="logoutuser", password="12345")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
