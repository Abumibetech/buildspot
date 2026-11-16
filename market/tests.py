from django.test import TestCase
from django.urls import reverse
class HomeTests(TestCase):
    def test_homepage_loads(self):
        response=self.client.get(reverse("home")); self.assertEqual(response.status_code,200); self.assertContains(response,"EXPLORE MARKET")
    def test_market_loads(self): self.assertEqual(self.client.get(reverse("market")).status_code,200)


from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, CommunityNotification, MaterialRequest, Product, SellerQuotation, Store


class MaterialRequestNotificationTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="request_buyer", password="test-password-123"
        )
        self.matching_seller = User.objects.create_user(
            username="matching_seller", password="test-password-123"
        )
        self.other_city_seller = User.objects.create_user(
            username="other_city_seller", password="test-password-123"
        )
        self.other_state_seller = User.objects.create_user(
            username="other_state_seller", password="test-password-123"
        )
        self.inactive_seller = User.objects.create_user(
            username="inactive_seller", password="test-password-123"
        )

        def create_store(owner, name, state, city, active=True):
            return Store.objects.create(
                owner=owner,
                business_name=name,
                slug=name.lower().replace(" ", "-"),
                phone="08012345678",
                state=state,
                city=city,
                address="Private store address",
                is_active=active,
            )

        matching_store = create_store(
            self.matching_seller, "Matching Supplier", "Kano", "Kano"
        )
        other_city_store = create_store(
            self.other_city_seller, "Other City Supplier", "Kano", "Bichi"
        )
        create_store(
            self.other_state_seller, "Other State Supplier", "Kaduna State", "Kano"
        )
        create_store(
            self.inactive_seller, "Inactive Supplier", "Kano", "Kano",
            active=False,
        )

        cement_category, _ = Category.objects.get_or_create(
            name="Cement",
            defaults={"slug": "cement"},
        )
        for store, slug in (
            (matching_store, "cement"),
            (other_city_store, "cement"),
        ):
            Product.objects.create(
                store=store,
                category=cement_category,
                name="Cement",
                slug=slug,
                available=True,
            )

    def test_request_notifies_active_sellers_across_selected_state_only(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("community_request_create"),
            {
                "state": "Kano",
                "city": "Kano",
                "delivery_location": "PRIVATE ADDRESS 14 EXAMPLE STREET",
                "buyer_whatsapp": "",
                "material": "Cement",
                "quantity": "50 bags",
                "requirements": "General purpose",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(MaterialRequest.objects.count(), 1)

        request_obj = MaterialRequest.objects.get()
        self.assertEqual(
            request_obj.delivery_location, "PRIVATE ADDRESS 14 EXAMPLE STREET"
        )

        notifications = CommunityNotification.objects.all()
        self.assertEqual(notifications.count(), 2)
        recipients = set(notifications.values_list("recipient__username", flat=True))
        self.assertEqual(
            recipients, {"matching_seller", "other_city_seller"}
        )
        self.assertNotIn("other_state_seller", recipients)
        self.assertNotIn("inactive_seller", recipients)
        self.assertNotIn("request_buyer", recipients)

        for notification in notifications:
            self.assertIn("Cement", notification.message)
            self.assertIn("50 bags", notification.message)
            self.assertIn("Kano", notification.message)
            self.assertNotIn(
                request_obj.delivery_location, notification.message
            )
            self.assertNotIn(
                request_obj.delivery_location, notification.url
            )

    def test_public_community_request_hides_exact_delivery_address(self):
        request_obj = MaterialRequest.objects.create(
            buyer=self.buyer,
            state="Kano",
            city="Kano",
            delivery_location="PRIVATE ADDRESS 14 EXAMPLE STREET",
            material="Cement",
            quantity="50 bags",
        )

        response = self.client.get(reverse("community"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cement")
        self.assertContains(response, "Kano")
        self.assertNotContains(response, request_obj.delivery_location)

    def test_request_with_whatsapp_shows_contact_link_without_address(self):
        request_obj = MaterialRequest.objects.create(
            buyer=self.buyer,
            state="Kano",
            city="Kano",
            delivery_location="PRIVATE ADDRESS 14 EXAMPLE STREET",
            buyer_whatsapp="08012345678",
            material="Cement",
            quantity="50 bags",
        )

        response = self.client.get(reverse("community"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact buyer on WhatsApp")
        self.assertContains(response, "https://wa.me/2348012345678")
        self.assertNotContains(response, request_obj.delivery_location)


class CrossCityQuotationTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="cross_city_buyer",
            password="test-password-123",
        )
        self.seller = User.objects.create_user(
            username="cross_city_seller",
            password="test-password-123",
        )
        self.other_state_seller = User.objects.create_user(
            username="different_state_seller",
            password="test-password-123",
        )

        self.seller_store = Store.objects.create(
            owner=self.seller,
            business_name="Bichi Building Supplies",
            slug="bichi-building-supplies",
            phone="08012345678",
            state="Kano",
            city="Bichi",
            address="Bichi store address",
            is_active=True,
        )

        Store.objects.create(
            owner=self.other_state_seller,
            business_name="Kaduna Building Supplies",
            slug="kaduna-building-supplies",
            phone="08012345679",
            state="Kaduna State",
            city="Kaduna",
            address="Kaduna store address",
            is_active=True,
        )

        self.material_request = MaterialRequest.objects.create(
            buyer=self.buyer,
            state="Kano",
            city="Kano",
            delivery_location="PRIVATE BUYER ADDRESS",
            material="Cement",
            quantity="50 bags",
            status="open",
        )

    def test_seller_in_another_city_of_same_state_can_see_quote_form(self):
        self.client.force_login(self.seller)

        response = self.client.get(
            reverse(
                "community_request_detail",
                args=[self.material_request.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send your quotation")

    def test_seller_in_another_city_of_same_state_can_submit_quote(self):
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse(
                "community_quotation_create",
                args=[self.material_request.pk],
            ),
            {
                "price": "500000",
                "price_unit": "total",
                "delivery_days": "2",
                "delivery_details": "Delivery to Kano available; fee included",
                "message": "We can supply and deliver the requested cement.",
            },
        )

        self.assertEqual(response.status_code, 302)

        quotation = SellerQuotation.objects.get(
            material_request=self.material_request,
            store=self.seller_store,
        )
        self.assertEqual(str(quotation.price), "500000.00")
        self.assertEqual(quotation.status, "submitted")

        self.assertTrue(
            CommunityNotification.objects.filter(
                recipient=self.buyer,
                title="A seller sent you a quotation",
            ).exists()
        )

    def test_seller_in_another_state_cannot_submit_quote(self):
        self.client.force_login(self.other_state_seller)

        response = self.client.get(
            reverse(
                "community_request_detail",
                args=[self.material_request.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Send your quotation")

        response = self.client.post(
            reverse(
                "community_quotation_create",
                args=[self.material_request.pk],
            ),
            {
                "price": "500000",
                "price_unit": "total",
                "delivery_days": "2",
                "delivery_details": "Delivery available",
                "message": "Test quotation",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            SellerQuotation.objects.filter(
                material_request=self.material_request,
            ).count(),
            0,
        )
