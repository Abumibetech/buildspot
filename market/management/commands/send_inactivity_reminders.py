from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from market.models import UserActivity, ComebackReminderLog
from market.push_notifications import send_web_push


REMINDERS = {
    1: (
        "BuildSpot misses you 🧡",
        "We miss you! Come back to BuildSpot and discover trusted building-material suppliers.",
        timedelta(hours=48),
    ),
    2: (
        "Your next project starts here! 🏗️",
        "Explore products, compare prices and discover new stores on BuildSpot.",
        timedelta(hours=96),
    ),
    3: (
        "Don't miss out! 🔔",
        "New products, great deals and building-material suppliers are waiting for you.",
        timedelta(hours=144),
    ),
}


class Command(BaseCommand):
    help = "Send comeback push reminders to inactive BuildSpot users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show eligible reminders without sending notifications or saving logs.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        checked = 0
        eligible = 0
        attempted = 0
        delivered = 0
        failed = 0

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN: no notifications will be sent.")
            )

        activities = (
            UserActivity.objects
            .select_related("user")
            .filter(user__push_subscriptions__isnull=False)
            .distinct()
            .iterator(chunk_size=200)
        )

        for activity in activities:
            checked += 1

            inactive_for = now - activity.last_seen

            sent_stages = set(
                ComebackReminderLog.objects.filter(
                    user_id=activity.user_id,
                    activity_since=activity.last_seen,
                ).values_list("stage", flat=True)
            )

            # Send only the next reminder in sequence.
            # Never send multiple stages to the same user in one run.
            stage = None

            if (
                1 not in sent_stages
                and inactive_for >= REMINDERS[1][2]
            ):
                stage = 1

            elif (
                1 in sent_stages
                and 2 not in sent_stages
                and inactive_for >= REMINDERS[2][2]
            ):
                stage = 2

            elif (
                2 in sent_stages
                and 3 not in sent_stages
                and inactive_for >= REMINDERS[3][2]
            ):
                stage = 3

            if stage is None:
                continue

            eligible += 1
            title, body, _threshold = REMINDERS[stage]

            hours = inactive_for.total_seconds() / 3600

            self.stdout.write(
                f"{'[DRY RUN] ' if dry_run else ''}"
                f"User: {activity.user.username} | "
                f"Stage: {stage} | "
                f"Inactive: {hours:.1f} hours"
            )

            if dry_run:
                continue

            attempted += 1

            try:
                result = send_web_push(
                    user_ids=[activity.user_id],
                    title=title,
                    body=body,
                    url="/market/",
                )

                sent_count = result.get("sent", 0)
                failed_count = result.get("failed", 0)

                if sent_count > 0:
                    ComebackReminderLog.objects.create(
                        user_id=activity.user_id,
                        activity_since=activity.last_seen,
                        stage=stage,
                    )
                    delivered += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Delivered stage {stage} to "
                            f"{activity.user.username} "
                            f"({sent_count} device(s) succeeded)."
                        )
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"No successful delivery for "
                            f"{activity.user.username}. "
                            f"It will be eligible for retry."
                        )
                    )

                if failed_count:
                    self.stdout.write(
                        f"Unsuccessful device deliveries: {failed_count}"
                    )

            except Exception as exc:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Error sending to {activity.user.username}: {exc}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("========== REMINDER SUMMARY ==========")
        self.stdout.write(f"Users checked: {checked}")
        self.stdout.write(f"Eligible reminders: {eligible}")
        self.stdout.write(f"Users attempted: {attempted}")
        self.stdout.write(f"Successful user deliveries: {delivered}")
        self.stdout.write(f"Failed users: {failed}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run completed. No notifications or reminder logs were created."
                )
            )
