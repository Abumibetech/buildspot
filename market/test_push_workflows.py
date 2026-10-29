from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Category,
    CommunityNotification,
    MaterialRequest,
    Product,
    Store,
)


class PushWorkflowTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="push_test_buyer",
            password="test-password-123",
        )
        self.seller = User.objects.create_user(
            username="push_test_seller",
            password="test-password-123",
        )
        self.store = Store.objects.create(
            owner=self.seller,
            business_name="Push Test Supplies",
            slug="push-test-supplies",
            phone="08012345678",
            state="Kano",
            city="Kano",
            address="Test store address",
            is_active=True,
        )
        self.category = Category.objects.create(
            name="Cement",
            slug="cement",
        )

    @patch("market.push_notifications.send_web_push")
    def test_new_request_sends_push_to_active_sellers_in_state(self, send_push):
        Product.objects.create(
            store=self.store,
            category=self.category,
            name="Cement",
            slug="cement",
            available=True,
        )
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("community_request_create"),
            {
                "state": "Kano",
                "city": "Kano",
                "delivery_location": "PRIVATE TEST ADDRESS",
                "buyer_whatsapp": "",
                "material": "Cement",
                "quantity": "20 bags",
                "requirements": "Test request",
            },
        )

        self.assertEqual(response.status_code, 302)
        notification = CommunityNotification.objects.get(
            recipient=self.seller
        )
        self.assertIn("Cement", notification.title)
        self.assertIn("20 bags", notification.message)
        self.assertNotIn("PRIVATE TEST ADDRESS", notification.message)
        self.assertNotIn("PRIVATE TEST ADDRESS", notification.url)
        send_push.assert_called_once()
        args, kwargs = send_push.call_args
        self.assertIn(self.seller.pk, args[0])
        self.assertNotIn("PRIVATE TEST ADDRESS", kwargs["body"])


    @patch("market.push_notifications.send_web_push")
    def test_new_request_does_not_notify_seller_with_unrelated_products(
        self, send_push
    ):
        Product.objects.create(
            store=self.store,
            category=self.category,
            name="Cement",
            slug="cement",
            available=True,
        )

        other_seller = User.objects.create_user(
            username="unrelated_push_seller",
            password="test-password-123",
        )
        other_store = Store.objects.create(
            owner=other_seller,
            business_name="Door Supplies",
            slug="door-supplies",
            phone="08012345679",
            state="Kano",
            city="Kano",
            address="Other store address",
            is_active=True,
        )
        doors = Category.objects.create(name="Doors", slug="doors")
        Product.objects.create(
            store=other_store,
            category=doors,
            name="Wooden Door",
            slug="wooden-door",
            available=True,
        )

        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse("community_request_create"),
            {
                "state": "Kano",
                "city": "Kano",
                "delivery_location": "PRIVATE TEST ADDRESS",
                "buyer_whatsapp": "",
                "material": "Cement",
                "quantity": "20 bags",
                "requirements": "Test request",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CommunityNotification.objects.filter(
                recipient=self.seller,
                title__icontains="Cement",
            ).exists()
        )
        self.assertFalse(
            CommunityNotification.objects.filter(
                recipient=other_seller,
            ).exists()
        )
        send_push.assert_called_once()
        args, _kwargs = send_push.call_args
        self.assertIn(self.seller.pk, args[0])
        self.assertNotIn(other_seller.pk, args[0])

    @patch("market.push_notifications.send_web_push")
    def test_available_matching_product_notifies_open_request_buyer(
        self, send_push
    ):
        MaterialRequest.objects.create(
            buyer=self.buyer,
            state="Kano",
            city="Kano",
            delivery_location="PRIVATE TEST ADDRESS",
            material="Cement",
            quantity="20 bags",
            status="open",
        )
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse("product_add"),
            {
                "category": str(self.category.pk),
                "name": "General Purpose Cement",
                "description": "Test product",
                "price": "",
                "price_unit": "bag",
                "video_url": "",
                "available": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name="General Purpose Cement")
        notification = CommunityNotification.objects.get(
            recipient=self.buyer
        )
        self.assertIn("General Purpose Cement", notification.title)
        self.assertEqual(
            notification.url,
            reverse(
                "product_detail",
                args=[self.store.slug, product.slug],
            ),
        )
        self.assertNotIn("PRIVATE TEST ADDRESS", notification.message)
        send_push.assert_called_once()
        args, kwargs = send_push.call_args
        self.assertIn(self.buyer.pk, args[0])
        self.assertNotIn("PRIVATE TEST ADDRESS", kwargs["body"])

    @patch("market.push_notifications.send_web_push")
    def test_unavailable_product_does_not_notify_request_buyer(
        self, send_push
    ):
        MaterialRequest.objects.create(
            buyer=self.buyer,
            state="Kano",
            city="Kano",
            delivery_location="PRIVATE TEST ADDRESS",
            material="Cement",
            quantity="20 bags",
            status="open",
        )
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse("product_add"),
            {
                "category": str(self.category.pk),
                "name": "Unavailable Cement",
                "description": "Test product",
                "price": "",
                "price_unit": "bag",
                "video_url": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Product.objects.filter(name="Unavailable Cement").exists()
        )
        self.assertFalse(
            CommunityNotification.objects.filter(
                recipient=self.buyer
            ).exists()
        )
        send_push.assert_not_called()
