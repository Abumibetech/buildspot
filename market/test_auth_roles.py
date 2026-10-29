from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Store


class BuildSpotAuthenticationTests(TestCase):
    password = "Safe-test-password-123!"

    def setUp(self):
        self.buyer = User.objects.create_user(
            username="auth_test_buyer", password=self.password
        )
        self.seller = User.objects.create_user(
            username="auth_test_seller", password=self.password
        )
        Store.objects.create(
            owner=self.seller,
            business_name="Authentication Test Store",
            slug="authentication-test-store",
            phone="08012345678",
            state="Abuja",
            city="Abuja",
            address="Test address",
        )

    def test_buyer_login_defaults_to_community(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.buyer.username, "password": self.password},
        )
        self.assertRedirects(response, reverse("community"))

    def test_seller_login_defaults_to_seller_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.seller.username, "password": self.password},
        )
        self.assertRedirects(response, reverse("seller_dashboard"))

    def test_valid_next_destination_is_preserved(self):
        response = self.client.post(
            reverse("login") + "?next=/market/",
            {"username": self.buyer.username, "password": self.password},
        )
        self.assertRedirects(response, "/market/")

    def test_buyer_does_not_see_seller_dashboard_navigation(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, ">Seller dashboard</a>")

    def test_seller_sees_seller_dashboard_navigation(self):
        self.client.force_login(self.seller)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ">Seller dashboard</a>")

    def test_buyer_cannot_manage_seller_dashboard(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("seller_dashboard"))
        self.assertRedirects(response, reverse("signup"))
        self.assertFalse(self.client.session.get("_auth_user_id") is None)

    def test_logout_clears_buyer_session_and_returns_home(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_clears_seller_session_and_returns_home(self):
        self.client.force_login(self.seller)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
