from django.test import TestCase
from django.urls import reverse
class HomeTests(TestCase):
    def test_homepage_loads(self):
        response=self.client.get(reverse("home")); self.assertEqual(response.status_code,200); self.assertContains(response,"EXPLORE MARKET")
    def test_market_loads(self): self.assertEqual(self.client.get(reverse("market")).status_code,200)
