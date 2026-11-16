from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import re

class Store(models.Model):
    VERIFICATION = [("pending","Pending"),("verified","Verified"),("rejected","Rejected")]
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="store")
    business_name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=30)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    state = models.CharField(max_length=80)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    verification_status = models.CharField(max_length=12, choices=VERIFICATION, default="pending")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.business_name
    def get_absolute_url(self): return reverse("store_detail", args=[self.slug])

    @property
    def whatsapp_link_number(self):
        """Return a WhatsApp-compatible number using digits only."""
        number = re.sub(r"\D", "", self.whatsapp or "")
        if number.startswith("00"):
            number = number[2:]
        if number.startswith("0"):
            number = "234" + number[1:]
        return number


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class ShowroomSection(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="showroom_sections",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="showroom_sections/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "pk"]
        unique_together = [("store", "slug")]

    def __str__(self):
        return f"{self.store.business_name} — {self.name}"


class ShowroomSectionGalleryImage(models.Model):
    section = models.ForeignKey(
        ShowroomSection,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="showroom_sections/gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Gallery image for {self.section.name}"


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    showroom_section = models.ForeignKey(
        ShowroomSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Optional previous price for a genuine discount.",
    )
    deal_expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Optional date and time when this offer ends.",
    )
    price_unit = models.CharField(max_length=40, default="unit")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    video_url = models.URLField(blank=True, help_text="Optional link to a product video")
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]; unique_together = [("store","slug")]
    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        update_fields = kwargs.get("update_fields")
        price_is_being_saved = (
            update_fields is None or "price" in update_fields
        )
        previous_price = None

        if not is_new and price_is_being_saved:
            previous_price = (
                type(self).objects.filter(pk=self.pk)
                .values_list("price", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if (
            price_is_being_saved
            and self.price is not None
            and (is_new or previous_price != self.price)
        ):
            ProductPriceHistory.objects.create(
                product=self,
                price=self.price,
            )

    @property
    def discount_percent(self):
        """Whole-number discount percentage for a genuine price reduction."""
        if self.price is None or self.original_price is None:
            return 0
        if self.original_price <= 0 or self.original_price <= self.price:
            return 0
        return int(((self.original_price - self.price) * 100) / self.original_price)

    @property
    def savings_amount(self):
        if self.price is None or self.original_price is None:
            return 0
        if self.original_price <= self.price:
            return 0
        return self.original_price - self.price


class ProductPriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_history",
    )
    price = models.DecimalField(max_digits=14, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["recorded_at", "pk"]
        verbose_name_plural = "product price histories"

    def __str__(self):
        return f"{self.product.name}: {self.price} at {self.recorded_at}"


class Enquiry(models.Model):
    STATUS = [("new","New"),("replied","Replied"),("closed","Closed")]
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="enquiries")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="enquiries")
    buyer_name = models.CharField(max_length=120)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=30, blank=True)
    delivery_location = models.CharField(max_length=180, blank=True)
    quantity = models.CharField(max_length=80, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.buyer_name} → {self.store.business_name}"

class Advertisement(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="advertisements/")
    target_url = models.URLField()
    placement = models.CharField(max_length=40, choices=[("home","Homepage"),("market","Market page"),("store","Store pages")], default="home")
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title


class MaterialRequest(models.Model):
    STATUS = [
        ("open", "Open"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
    ]

    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="material_requests"
    )
    state = models.CharField(max_length=80, db_index=True)
    city = models.CharField(max_length=100, blank=True)
    delivery_location = models.CharField(max_length=255)
    buyer_whatsapp = models.CharField(max_length=30, blank=True)
    material = models.CharField(max_length=160)
    quantity = models.CharField(max_length=100)
    requirements = models.TextField(blank=True)
    photo = models.ImageField(upload_to="material_requests/", blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS, default="open", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def buyer_whatsapp_link_number(self):
        import re
        number = re.sub(r"\D", "", self.buyer_whatsapp or "")
        if number.startswith("00"):
            number = number[2:]
        if number.startswith("0"):
            number = "234" + number[1:]
        return number

    def __str__(self):
        return f"{self.material} — {self.state} ({self.quantity})"


class SellerQuotation(models.Model):
    STATUS = [
        ("submitted", "Submitted"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("withdrawn", "Withdrawn"),
    ]

    material_request = models.ForeignKey(
        MaterialRequest, on_delete=models.CASCADE, related_name="quotations"
    )
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="community_quotations"
    )
    price = models.DecimalField(max_digits=14, decimal_places=2)
    price_unit = models.CharField(max_length=60, default="total")
    delivery_days = models.PositiveIntegerField(default=0)
    delivery_details = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="submitted")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["material_request", "store"],
                name="unique_store_quotation_per_request",
            )
        ]

    def __str__(self):
        return f"{self.store.business_name}: ₦{self.price} for {self.material_request.material}"


class CommunityNotification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="community_notifications"
    )
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=500)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


class CommunityPost(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildspot_community_posts",
    )
    body = models.TextField(max_length=3000)
    photo = models.ImageField(
        upload_to="community_posts/",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Community post by {self.author.username}"

class CommunityComment(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildspot_community_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post_id}"


class CommunityPostReaction(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildspot_post_reactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_community_post_reaction",
            )
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} reacted to post {self.post_id}"


class CommunityCommentReaction(models.Model):
    comment = models.ForeignKey(
        CommunityComment,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildspot_comment_reactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="unique_community_comment_reaction",
            )
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} reacted to comment {self.comment_id}"


class PushSubscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=2000, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Push subscription for user {self.user_id}"


class DailyInspirationPushLog(models.Model):
    subscription = models.ForeignKey(
        PushSubscription,
        on_delete=models.CASCADE,
        related_name="daily_inspiration_push_logs",
    )
    sent_date = models.DateField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscription", "sent_date"],
                name="unique_daily_inspiration_push_per_device_date",
            )
        ]
        ordering = ["-sent_at"]

    def __str__(self):
        return (
            f"Daily inspiration push to subscription "
            f"{self.subscription_id} on {self.sent_date}"
        )


class BuyerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="buyer_profile",
    )
    whatsapp = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Buyer profile: {self.user.username}"


class RecentlyViewed(models.Model):
    """A private record of a visitor's recently viewed product or store."""
    user = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="buildspot_recently_viewed",
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    product = models.ForeignKey(
        Product, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="recent_view_records",
    )
    store = models.ForeignKey(
        Store, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="recent_view_records",
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]

    def __str__(self):
        target = self.product or self.store or "Unknown item"
        return f"Recently viewed: {target}"


class SavedProduct(models.Model):
    """A product privately saved by a registered BuildSpot user."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_products"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="saved_by_users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_saved_product_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.product.name}"


class SavedStore(models.Model):
    """A store privately saved by a registered BuildSpot user."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_stores"
    )
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="saved_by_users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "store"],
                name="unique_saved_store_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.store.business_name}"


# Additional images for BuildSpot product, buyer-request and community galleries.
class ProductGalleryImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="product_gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Gallery image for {self.product.name}"


class MaterialRequestGalleryImage(models.Model):
    material_request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="material_request_gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Gallery image for request {self.material_request_id}"


class CommunityPostGalleryImage(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="community_post_gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"Gallery image for community post {self.post_id}"


# BuildSpot comeback reminders: authenticated user activity and reminder history.
from django.utils import timezone


class UserActivity(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="buildspot_activity",
    )
    last_seen = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f"Last activity for {self.user.username}: {self.last_seen}"


class ComebackReminderLog(models.Model):
    STAGE_CHOICES = [
        (1, "First reminder"),
        (2, "Second reminder"),
        (3, "Third reminder"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comeback_reminder_logs",
    )
    activity_since = models.DateTimeField()
    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "activity_since", "stage"],
                name="unique_comeback_reminder_per_activity_stage",
            )
        ]

    def __str__(self):
        return f"Comeback reminder {self.stage} for {self.user.username}"
