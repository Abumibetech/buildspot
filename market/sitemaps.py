from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Product, Store


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["home", "market"]

    def location(self, item):
        return reverse(item)


class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Store.objects.filter(is_active=True).order_by("pk")


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Product.objects.filter(
            available=True,
            store__is_active=True,
        ).select_related("store").order_by("pk")

    def location(self, item):
        return reverse(
            "product_detail",
            args=[item.store.slug, item.slug],
        )
