from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from market.daily_inspiration import get_daily_inspiration
from market.models import DailyInspirationPushLog, PushSubscription
from market.push_notifications import send_web_push


class Command(BaseCommand):
    help = "Send the daily BuildSpot inspiration to subscribed devices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many devices are pending without sending notifications.",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        inspiration = get_daily_inspiration()

        already_sent = DailyInspirationPushLog.objects.filter(
            sent_date=today
        ).values_list("subscription_id", flat=True)

        pending = PushSubscription.objects.exclude(
            pk__in=already_sent
        ).order_by("user_id", "pk")

        pending_count = pending.count()

        self.stdout.write(f"Date (BuildSpot local time): {today}")
        self.stdout.write(f"Daily theme: {inspiration['theme']}")
        self.stdout.write(f"Subscribed devices pending: {pending_count}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN: no notifications were sent and no delivery records were created."
            ))
            return

        if not pending_count:
            self.stdout.write(self.style.SUCCESS(
                "No subscribed devices need today's notification."
            ))
            return

        title = "BuildSpot Daily Inspiration"
        body = f"{inspiration['quote']} — {inspiration['theme']}"
        target_url = "/#bs-daily-inspiration"

        devices_by_user = defaultdict(list)
        for user_id, subscription_id in pending.values_list("user_id", "pk").iterator():
            devices_by_user[user_id].append(subscription_id)

        total_attempted = 0
        total_sent = 0
        total_failed = 0

        for user_id, subscription_ids in devices_by_user.items():
            result = send_web_push(
                [user_id],
                title,
                body,
                target_url,
                subscription_ids=subscription_ids,
            )

            total_attempted += result["attempted"]
            total_sent += result["sent"]
            total_failed += result["failed"]

            successful_ids = result.get("sent_subscription_ids", [])
            if successful_ids:
                DailyInspirationPushLog.objects.bulk_create(
                    [
                        DailyInspirationPushLog(
                            subscription_id=subscription_id,
                            sent_date=today,
                        )
                        for subscription_id in successful_ids
                    ],
                    ignore_conflicts=True,
                )

        self.stdout.write(f"Delivery attempts: {total_attempted}")
        self.stdout.write(f"Successful deliveries: {total_sent}")
        self.stdout.write(f"Failed deliveries: {total_failed}")

        if total_sent:
            self.stdout.write(self.style.SUCCESS(
                "Successful device deliveries have been recorded for today."
            ))

        if total_attempted == 0:
            self.stdout.write(self.style.WARNING(
                "No delivery was attempted. Check the VAPID private key and server logs."
            ))
        elif total_failed:
            self.stdout.write(self.style.WARNING(
                "Failed devices were not marked as sent and can be retried on the next run."
            ))
