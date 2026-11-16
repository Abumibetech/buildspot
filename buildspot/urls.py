from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from market.sitemaps import StaticViewSitemap, StoreSitemap, ProductSitemap


# BuildSpot advertising and search-engine discovery files.
def buildspot_ads_txt(request):
    return HttpResponse(
        "google.com, pub-4901860117581932, DIRECT, f08c47fec0942fa0\n",
        content_type="text/plain",
    )


def buildspot_robots_txt(request):
    return HttpResponse(
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://www.buildspot.store/sitemap.xml\n",
        content_type="text/plain",
    )


def buildspot_service_worker(request):
    """Serve the BuildSpot service worker from the website root."""
    worker_path = settings.BASE_DIR / "static" / "pwa" / "sw.js"
    try:
        worker_code = worker_path.read_text(encoding="utf-8")
    except OSError:
        return HttpResponse(
            "BuildSpot service worker unavailable.",
            status=404,
            content_type="text/plain",
        )

    response = HttpResponse(
        worker_code,
        content_type="application/javascript; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache"
    response["Service-Worker-Allowed"] = "/"
    return response

sitemaps = {
    "static": StaticViewSitemap,
    "stores": StoreSitemap,
    "products": ProductSitemap,
}

urlpatterns = [
    path("sw.js", buildspot_service_worker, name="service_worker"),
    path("ads.txt", buildspot_ads_txt, name="ads_txt"),
    path("robots.txt", buildspot_robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),path("admin/", admin.site.urls), path("", include("market.urls"))]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# BuildSpot branded page for missing URLs and records.
handler404 = "market.views.buildspot_custom_404"
