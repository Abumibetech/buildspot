from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, SavedProduct, SavedStore, Store


class BuildSpotFavouritesTests(TestCase):
    password = "Safe-favourites-test-123!"

    def setUp(self):
        self.buyer = User.objects.create_user(
            username="favourites_buyer",
            password=self.password,
        )
        self.other_buyer = User.objects.create_user(
            username="favourites_other",
            password=self.password,
        )
        self.seller = User.objects.create_user(
            username="favourites_seller",
            password=self.password,
        )
        self.store = Store.objects.create(
            owner=self.seller,
            business_name="Favourites Test Store",
            slug="favourites-test-store",
            phone="08012345678",
            state="Plateau",
            city="Jos",
            address="Test address",
        )
        self.category = Category.objects.create(
            name="Favourites Test Category",
            slug="favourites-test-category",
        )
        self.product = Product.objects.create(
            store=self.store,
            category=self.category,
            name="Favourites Test Cement",
            slug="favourites-test-cement",
            description="Test product",
            price="10000.00",
            available=True,
        )

    def test_favourites_page_requires_login(self):
        response = self.client.get(reverse("my_favourites"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_anonymous_user_cannot_save_product(self):
        response = self.client.post(
            reverse("toggle_saved_product", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedProduct.objects.exists())

    def test_user_can_save_product(self):
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("toggle_saved_product", args=[self.product.pk])
        )
        self.assertRedirects(response, reverse("my_favourites"))
        self.assertTrue(
            SavedProduct.objects.filter(
                user=self.buyer, product=self.product
            ).exists()
        )

    def test_user_can_remove_saved_product(self):
        SavedProduct.objects.create(user=self.buyer, product=self.product)
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("toggle_saved_product", args=[self.product.pk])
        )

        self.assertRedirects(response, reverse("my_favourites"))
        self.assertFalse(
            SavedProduct.objects.filter(
                user=self.buyer, product=self.product
            ).exists()
        )

    def test_repeated_product_save_does_not_create_duplicates(self):
        self.client.force_login(self.buyer)
        url = reverse("toggle_saved_product", args=[self.product.pk])

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            SavedProduct.objects.filter(
                user=self.buyer, product=self.product
            ).count(),
            0,
        )

    def test_user_can_save_and_remove_store(self):
        self.client.force_login(self.buyer)
        url = reverse("toggle_saved_store", args=[self.store.pk])

        response = self.client.post(url)
        self.assertRedirects(response, reverse("my_favourites"))
        self.assertTrue(
            SavedStore.objects.filter(
                user=self.buyer, store=self.store
            ).exists()
        )

        self.client.post(url)
        self.assertFalse(
            SavedStore.objects.filter(
                user=self.buyer, store=self.store
            ).exists()
        )

    def test_get_cannot_toggle_saved_product(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse("toggle_saved_product", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(SavedProduct.objects.exists())

    def test_users_only_see_their_own_favourites(self):
        SavedProduct.objects.create(user=self.buyer, product=self.product)
        SavedStore.objects.create(user=self.buyer, store=self.store)

        self.client.force_login(self.other_buyer)
        response = self.client.get(reverse("my_favourites"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["saved_products"], []
        )
        self.assertQuerySetEqual(
            response.context["saved_stores"], []
        )
        self.assertNotContains(response, "Favourites Test Cement")
        self.assertNotContains(response, "Favourites Test Store")

    def test_saved_product_appears_on_favourites_page(self):
        SavedProduct.objects.create(user=self.buyer, product=self.product)
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("my_favourites"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favourites Test Cement")
        self.assertContains(response, "Favourites Test Store")

    def test_unavailable_product_cannot_be_saved(self):
        self.product.available = False
        self.product.save()
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("toggle_saved_product", args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(SavedProduct.objects.exists())
