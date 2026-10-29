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

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=160)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(max_length=40, default="unit")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    video_url = models.URLField(blank=True, help_text="Optional link to a product video")
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]; unique_together = [("store","slug")]
    def __str__(self): return self.name

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
