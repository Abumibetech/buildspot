from datetime import timedelta

from django.utils import timezone

from .models import UserActivity


class UserActivityMiddleware:
    """
    Track authenticated page visits without writing to the database
    on every request. Background polling and static resources are excluded.
    """

    EXCLUDED_PREFIXES = (
        "/static/",
        "/media/",
        "/push/",
        "/community/notifications/updates/",
    )

    EXCLUDED_PATHS = {
        "/sw.js",
        "/service-worker.js",
        "/robots.txt",
        "/favicon.ico",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or "/"

        if (
            request.method == "GET"
            and path not in self.EXCLUDED_PATHS
            and not path.startswith(self.EXCLUDED_PREFIXES)
            and getattr(request, "user", None)
            and request.user.is_authenticated
        ):
            now = timezone.now()
            cutoff = now - timedelta(minutes=15)

            activity, created = UserActivity.objects.get_or_create(
                user_id=request.user.pk,
                defaults={"last_seen": now},
            )

            if not created:
                UserActivity.objects.filter(
                    pk=activity.pk,
                    last_seen__lt=cutoff,
                ).update(last_seen=now)

        return self.get_response(request)
