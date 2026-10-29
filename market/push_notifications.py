import json
import logging
from pathlib import Path

from django.conf import settings

from pywebpush import WebPushException, webpush

from .models import PushSubscription

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = Path.home() / ".buildspot-vapid" / "private.pem"
VAPID_CONTACT = "mailto:abumibej@gmail.com"


def send_web_push(user_ids, title, body, url="/community/"):
    """
    Send a browser push to subscribed devices belonging to user_ids.

    Returns counts for attempted deliveries, successful deliveries,
    and failed deliveries. In-app notifications are managed separately.
    """
    user_ids = set(user_ids or [])
    if not user_ids:
        return {"attempted": 0, "sent": 0, "failed": 0}

    if not VAPID_PRIVATE_KEY.is_file():
        logger.error("BuildSpot VAPID private key is missing.")
        return {"attempted": 0, "sent": 0, "failed": 0}

    payload = json.dumps({
        "title": str(title)[:160],
        "body": str(body)[:500],
        "url": url if isinstance(url, str) and url.startswith("/") and not url.startswith("//") else "/community/",
    })

    subscriptions = PushSubscription.objects.filter(
        user_id__in=user_ids
    ).only("id", "endpoint", "p256dh", "auth")

    attempted = sent = failed = 0

    for subscription in subscriptions.iterator():
        attempted += 1
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=str(VAPID_PRIVATE_KEY),
                vapid_claims={"sub": VAPID_CONTACT},
                timeout=10,
            )
            sent += 1
        except WebPushException as exc:
            failed += 1
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

            if status_code in (404, 410):
                PushSubscription.objects.filter(pk=subscription.pk).delete()
                logger.info(
                    "Removed expired BuildSpot push subscription %s.",
                    subscription.pk,
                )
            else:
                logger.warning(
                    "BuildSpot push delivery failed for subscription %s "
                    "(HTTP status: %s).",
                    subscription.pk,
                    status_code,
                )
        except Exception:
            failed += 1
            logger.exception(
                "Unexpected BuildSpot push error for subscription %s.",
                subscription.pk,
            )

    return {"attempted": attempted, "sent": sent, "failed": failed}
