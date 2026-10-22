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
