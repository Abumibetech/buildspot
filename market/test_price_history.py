from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from market.models import Product, ProductPriceHistory, Store


class ProductPriceHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="price_history_test",
            password="test-password-123",
        )
        cls.store = Store.objects.create(
            owner=cls.user,
            business_name="Price History Test Store",
            slug="price-history-test-store",
            state="Plateau",
            city="Jos",
            is_active=True,
        )

    def make_product(self, **overrides):
        defaults = {
            "store": self.store,
            "name": "Test Cement",
            "slug": "test-cement",
            "price": Decimal("8000.00"),
            "available": True,
        }
        defaults.update(overrides)
        return Product.objects.create(**defaults)

    def test_initial_price_is_recorded(self):
        product = self.make_product()

        history = product.price_history.all()

        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().price, Decimal("8000.00"))

    def test_changed_price_creates_new_history_entry(self):
        product = self.make_product()

        product.price = Decimal("7500.00")
        product.save()

        history = list(product.price_history.values_list("price", flat=True))

        self.assertEqual(
            history,
            [Decimal("8000.00"), Decimal("7500.00")],
        )

    def test_description_edit_does_not_create_price_entry(self):
        product = self.make_product()

        product.description = "Updated product description"
        product.save()

        self.assertEqual(product.price_history.count(), 1)

    def test_saving_without_price_in_update_fields_does_not_record_unsaved_price(self):
        product = self.make_product()

        product.price = Decimal("7000.00")
        product.description = "Description update"
        product.save(update_fields=["description"])

        product.refresh_from_db()

        self.assertEqual(product.price, Decimal("8000.00"))
        self.assertEqual(product.price_history.count(), 1)

    def test_price_in_update_fields_is_recorded(self):
        product = self.make_product()

        product.price = Decimal("7000.00")
        product.save(update_fields=["price"])

        self.assertEqual(product.price_history.count(), 2)
        self.assertEqual(
            product.price_history.last().price,
            Decimal("7000.00"),
        )

    def test_product_without_initial_price_has_no_history(self):
        product = self.make_product(price=None)

        self.assertEqual(product.price_history.count(), 0)

        product.price = Decimal("6500.00")
        product.save()

        self.assertEqual(product.price_history.count(), 1)
        self.assertEqual(
            product.price_history.first().price,
            Decimal("6500.00"),
        )


    def test_product_detail_displays_recorded_price_history(self):
        product = self.make_product()

        response = self.client.get(
            reverse(
                "product_detail",
                args=[product.store.slug, product.slug],
            ),
            HTTP_HOST="buildspot.pythonanywhere.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Price History")
        self.assertContains(response, "₦8000.00")
