from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from market.models import Product, Store


class TodaysDealsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="deals_seller_test",
            password="test-password-123",
        )
        cls.store = Store.objects.create(
            owner=cls.user,
            business_name="Deals Test Store",
            slug="deals-test-store",
            state="Plateau",
            city="Jos",
            is_active=True,
        )

    def make_product(self, **overrides):
        defaults = {
            "store": self.store,
            "name": "Discounted Cement",
            "slug": "discounted-cement",
            "description": "Test product",
            "price": Decimal("8000.00"),
            "original_price": Decimal("10000.00"),
            "available": True,
        }
        defaults.update(overrides)
        return Product.objects.create(**defaults)

    def test_valid_discount_appears(self):
        product = self.make_product()
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertIn(product, response.context["deal_products"])

    def test_expired_discount_is_excluded(self):
        product = self.make_product(
            name="Expired Cement",
            slug="expired-cement",
            deal_expires_at=timezone.now() - timedelta(hours=1),
        )
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertNotIn(product, response.context["deal_products"])

    def test_unavailable_product_is_excluded(self):
        product = self.make_product(
            name="Unavailable Cement",
            slug="unavailable-cement",
            available=False,
        )
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertNotIn(product, response.context["deal_products"])

    def test_inactive_store_deal_is_excluded(self):
        self.store.is_active = False
        self.store.save(update_fields=["is_active"])
        product = self.make_product()
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertNotIn(product, response.context["deal_products"])

    def test_non_discounted_product_is_excluded(self):
        product = self.make_product(
            name="No Discount Cement",
            slug="no-discount-cement",
            original_price=Decimal("8000.00"),
        )
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertNotIn(product, response.context["deal_products"])

    def test_discount_without_expiry_is_allowed(self):
        product = self.make_product(deal_expires_at=None)
        response = self.client.get(
            reverse("todays_deals"),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )
        self.assertIn(product, response.context["deal_products"])

    def test_discount_percentage_and_savings(self):
        product = self.make_product()
        self.assertEqual(product.discount_percent, 20)
        self.assertEqual(product.savings_amount, Decimal("2000.00"))

    def test_original_price_not_above_current_price_has_no_discount(self):
        product = self.make_product(
            original_price=Decimal("7000.00"),
        )
        self.assertEqual(product.discount_percent, 0)
        self.assertEqual(product.savings_amount, 0)
