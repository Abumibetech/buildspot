from django.contrib import admin
from .models import Store, Category, Product, Enquiry, Advertisement
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin): list_display=("business_name","owner","city","state","verification_status","is_active"); list_filter=("verification_status","state","is_active"); search_fields=("business_name","owner__username","city","address"); prepopulated_fields={"slug":("business_name",)}
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin): list_display=("name","store","category","price","available","created_at"); list_filter=("available","category"); search_fields=("name","store__business_name")
@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin): list_display=("buyer_name","store","product","status","created_at"); list_filter=("status","created_at"); search_fields=("buyer_name","buyer_email","store__business_name")
@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin): list_display=("title","placement","active","starts_at","ends_at"); list_filter=("placement","active")
admin.site.register(Category)
admin.site.site_header="BuildSpot Administration"
admin.site.site_title="BuildSpot Admin"
admin.site.index_title="Marketplace management"
