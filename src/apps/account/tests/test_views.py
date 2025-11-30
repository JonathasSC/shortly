from django.test import TestCase
from django.urls import reverse

from apps.account.models import User
from apps.common.utils import CommonUtils


class RegisterViewTests(TestCase):
    def test_register_page_loads_successfully(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/register.html")

    def test_register_creates_user(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Strong@Password123",
            "confirm_password": "Strong@Password123",
        }
        response = self.client.post(reverse("register"), data)
        
        form = response.context
        if form:
            print(form.errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_fails_with_mismatched_passwords(self):
        data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "Strong@Password123",
            "confirm_password": "WrongPassword456",
        }
        response = self.client.post(reverse("register"), data)
        form = response.context["form"]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form.errors)
        self.assertIn('As senhas não coincidem.', form.errors['__all__'])
        self.assertFalse(User.objects.filter(username="user2").exists())

    def test_register_fails_with_invalid_password_size(self):
        data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "J@2",
            "confirm_password": "J@2",
        }
        response = self.client.post(reverse("register"), data)
        form = response.context["form"]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form.errors)
        self.assertIn("password", form.errors)
        self.assertFalse(User.objects.filter(username="user2").exists())

    def test_register_fails_with_invalid_password_without_special_char(self):
        data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "J2323",
            "confirm_password": "J2323",
        }
        response = self.client.post(reverse("register"), data)
        form = response.context["form"]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form.errors)
        self.assertIn("password", form.errors)
        self.assertFalse(User.objects.filter(username="user2").exists())


class UserLoginViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
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
        self.client.force_login(self.user)
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class LogoutViewTests(TestCase):
    def setUp(self):
        CommonUtils().disable_welcome_signal()
        self.user = User.objects.create_user(
            username="logoutuser",
            password="12345"
        )

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
                                                                                                                                                        