from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from market.sitemaps import StaticViewSitemap, StoreSitemap, ProductSitemap
sitemaps = {
    "static": StaticViewSitemap,
    "stores": StoreSitemap,
    "products": ProductSitemap,
}

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),path("admin/", admin.site.urls), path("", include("market.urls"))]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
