from django.utils import timezone
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from .models import Store, Product, ShowroomSection, Enquiry, MaterialRequest, SellerQuotation, CommunityPost, BuyerProfile

STATE_CHOICES = [
    ('Abia', 'Abia'),
    ('Adamawa', 'Adamawa'),
    ('Akwa Ibom', 'Akwa Ibom'),
    ('Anambra', 'Anambra'),
    ('Bauchi', 'Bauchi'),
    ('Bayelsa', 'Bayelsa'),
    ('Benue', 'Benue'),
    ('Borno', 'Borno'),
    ('Cross River', 'Cross River'),
    ('Delta', 'Delta'),
    ('Ebonyi', 'Ebonyi'),
    ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'),
    ('Enugu', 'Enugu'),
    ('Gombe', 'Gombe'),
    ('Imo', 'Imo'),
    ('Jigawa', 'Jigawa'),
    ('Kaduna', 'Kaduna'),
    ('Kano', 'Kano'),
    ('Katsina', 'Katsina'),
    ('Kebbi', 'Kebbi'),
    ('Kogi', 'Kogi'),
    ('Kwara', 'Kwara'),
    ('Lagos', 'Lagos'),
    ('Nasarawa', 'Nasarawa'),
    ('Niger', 'Niger'),
    ('Ogun', 'Ogun'),
    ('Ondo', 'Ondo'),
    ('Osun', 'Osun'),
    ('Oyo', 'Oyo'),
    ('Plateau', 'Plateau'),
    ('Rivers', 'Rivers'),
    ('Sokoto', 'Sokoto'),
    ('Taraba', 'Taraba'),
    ('Yobe', 'Yobe'),
    ('Zamfara', 'Zamfara'),
    ('Federal Capital Territory (FCT)', 'Federal Capital Territory (FCT)'),
]

CITY_CHOICES = [('', 'Select a state first'), ('Aba', 'Aba'), ('Abakaliki', 'Abakaliki'), ('Abeokuta', 'Abeokuta'), ('Abuja', 'Abuja'), ('Ado-Ekiti', 'Ado-Ekiti'), ('Afikpo', 'Afikpo'), ('Agbani', 'Agbani'), ('Agbor', 'Agbor'), ('Ahoada', 'Ahoada'), ('Ajah', 'Ajah'), ('Akure', 'Akure'), ('Akwanga', 'Akwanga'), ('Anka', 'Anka'), ('Argungu', 'Argungu'), ('Asaba', 'Asaba'), ('Asokoro', 'Asokoro'), ('Auchi', 'Auchi'), ('Awka', 'Awka'), ('Azare', 'Azare'), ('Badagry', 'Badagry'), ('Bali', 'Bali'), ('Bama', 'Bama'), ('Bauchi', 'Bauchi'), ('Benin City', 'Benin City'), ('Bida', 'Bida'), ('Billiri', 'Billiri'), ('Birnin Kebbi', 'Birnin Kebbi'), ('Biu', 'Biu'), ('Bonny', 'Bonny'), ('Brass', 'Brass'), ('Bukuru', 'Bukuru'), ('Bwari', 'Bwari'), ('Calabar', 'Calabar'), ('Damaturu', 'Damaturu'), ('Daura', 'Daura'), ('Dukku', 'Dukku'), ('Dutse', 'Dutse'), ('Ede', 'Ede'), ('Effurun', 'Effurun'), ('Eket', 'Eket'), ('Ekpoma', 'Ekpoma'), ('Ekwulobia', 'Ekwulobia'), ('Eleme', 'Eleme'), ('Enugu', 'Enugu'), ('Epe', 'Epe'), ('Festac', 'Festac'), ('Funtua', 'Funtua'), ('Garki', 'Garki'), ('Gashua', 'Gashua'), ('Gboko', 'Gboko'), ('Gombe', 'Gombe'), ('Gumel', 'Gumel'), ('Gusau', 'Gusau'), ('Gwadabawa', 'Gwadabawa'), ('Gwagwalada', 'Gwagwalada'), ('Gwarzo', 'Gwarzo'), ('Hadejia', 'Hadejia'), ('Ibadan', 'Ibadan'), ('Idah', 'Idah'), ('Ijebu-Ode', 'Ijebu-Ode'), ('Ijero-Ekiti', 'Ijero-Ekiti'), ('Ikare-Akoko', 'Ikare-Akoko'), ('Ikeja', 'Ikeja'), ('Ikere-Ekiti', 'Ikere-Ekiti'), ('Ikirun', 'Ikirun'), ('Ikom', 'Ikom'), ('Ikorodu', 'Ikorodu'), ('Ikot Ekpene', 'Ikot Ekpene'), ('Ilaro', 'Ilaro'), ('Ilawe-Ekiti', 'Ilawe-Ekiti'), ('Ile-Ife', 'Ile-Ife'), ('Ilesa', 'Ilesa'), ('Ilorin', 'Ilorin'), ('Iseyin', 'Iseyin'), ('Jalingo', 'Jalingo'), ("Jama'are", "Jama'are"), ('Jebba', 'Jebba'), ('Jimeta', 'Jimeta'), ('Jos', 'Jos'), ('Kabba', 'Kabba'), ('Kaduna', 'Kaduna'), ('Kafanchan', 'Kafanchan'), ('Kano', 'Kano'), ('Karu', 'Karu'), ('Katsina', 'Katsina'), ('Katsina-Ala', 'Katsina-Ala'), ('Kaura Namoda', 'Kaura Namoda'), ('Kazaure', 'Kazaure'), ('Keffi', 'Keffi'), ('Kontagora', 'Kontagora'), ('Kubwa', 'Kubwa'), ('Kuje', 'Kuje'), ('Kumo', 'Kumo'), ('Lafia', 'Lafia'), ('Lafiagi', 'Lafiagi'), ('Lagos Island', 'Lagos Island'), ('Lekki', 'Lekki'), ('Lokoja', 'Lokoja'), ('Lugbe', 'Lugbe'), ('Maiduguri', 'Maiduguri'), ('Maitama', 'Maitama'), ('Makurdi', 'Makurdi'), ('Malumfashi', 'Malumfashi'), ('Mararaba', 'Mararaba'), ('Mbaise', 'Mbaise'), ('Minna', 'Minna'), ('Misau', 'Misau'), ('Monguno', 'Monguno'), ('Mubi', 'Mubi'), ('Nembe', 'Nembe'), ('New Bussa', 'New Bussa'), ('Nguru', 'Nguru'), ('Nnewi', 'Nnewi'), ('Nsukka', 'Nsukka'), ('Numan', 'Numan'), ('Obudu', 'Obudu'), ('Offa', 'Offa'), ('Ogbia', 'Ogbia'), ('Ogbomoso', 'Ogbomoso'), ('Ogoja', 'Ogoja'), ('Ohafia', 'Ohafia'), ('Oji River', 'Oji River'), ('Okene', 'Okene'), ('Okigwe', 'Okigwe'), ('Omoku', 'Omoku'), ('Ondo', 'Ondo'), ('Onitsha', 'Onitsha'), ('Onueke', 'Onueke'), ('Orlu', 'Orlu'), ('Oron', 'Oron'), ('Osogbo', 'Osogbo'), ('Ota', 'Ota'), ('Otukpo', 'Otukpo'), ('Owerri', 'Owerri'), ('Owo', 'Owo'), ('Oyo', 'Oyo'), ('Pankshin', 'Pankshin'), ('Port Harcourt', 'Port Harcourt'), ('Potiskum', 'Potiskum'), ('Rano', 'Rano'), ('Sagamu', 'Sagamu'), ('Saki', 'Saki'), ('Saminaka', 'Saminaka'), ('Sapele', 'Sapele'), ('Serti', 'Serti'), ('Shendam', 'Shendam'), ('Sokoto', 'Sokoto'), ('Suleja', 'Suleja'), ('Surulere', 'Surulere'), ('Talata Mafara', 'Talata Mafara'), ('Tambuwal', 'Tambuwal'), ('Udi', 'Udi'), ('Ughelli', 'Ughelli'), ('Umuahia', 'Umuahia'), ('Uromi', 'Uromi'), ('Uyo', 'Uyo'), ('Victoria Island', 'Victoria Island'), ('Warri', 'Warri'), ('Wudil', 'Wudil'), ('Wukari', 'Wukari'), ('Wurno', 'Wurno'), ('Wuse', 'Wuse'), ('Yaba', 'Yaba'), ('Yauri', 'Yauri'), ('Yenagoa', 'Yenagoa'), ('Yola', 'Yola'), ('Zaria', 'Zaria'), ('Zuru', 'Zuru')]


class SellerSignupForm(UserCreationForm):
    email = forms.EmailField()
    business_name = forms.CharField(max_length=160)
    phone = forms.CharField(max_length=30)
    whatsapp = forms.CharField(
        label="WhatsApp number",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            "type": "tel",
            "autocomplete": "tel",
            "placeholder": "e.g. +2348012345678",
        }),
        help_text="Optional. Include your country code so buyers can reach you.",
    )
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        label="State where your shop is located",
        help_text="Choose the state where your shop operates. This is not your state of origin.",
    )
    description = forms.CharField(
        label="What do you do?",
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "For example: building materials supplier, contractor, tiler, plumber, electrician, architect, or buyer.",
        }),
    )
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "Street, building, estate, market or shop address"
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user



class BuyerSignupForm(UserCreationForm):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "placeholder": "you@example.com",
        }),
    )
    whatsapp = forms.CharField(
        label="WhatsApp number",
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel",
            "placeholder": "e.g. 08012345678",
        }),
        help_text="Optional. Add your WhatsApp number so you can be contacted when needed.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        whatsapp = (self.cleaned_data.get("whatsapp") or "").strip()

        if commit:
            user.save()
            BuyerProfile.objects.update_or_create(
                user=user,
                defaults={"whatsapp": whatsapp},
            )

        return user


class StoreForm(forms.ModelForm):
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        label="State where your shop is located",
        help_text="Choose the state where your shop operates. This is not your state of origin.",
    )
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "Street, building, estate, market or shop address"
        }),
    )

    class Meta:
        model = Store
        fields = [
            "business_name", "logo", "description", "phone", "whatsapp",
            "email", "state", "address",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].label = "What do you do?"
        self.fields["description"].required = False
        self.fields["description"].widget.attrs.update({
            "rows": 4,
            "placeholder": "Describe your work, business, services or the materials you supply.",
        })
        # Preserve older city/state values already stored in the database.
        if self.instance and self.instance.pk:
            old_state = self.instance.state
            old_city = self.instance.city
            if old_state and old_state not in dict(STATE_CHOICES):
                self.fields["state"].choices.append((old_state, old_state))
            if old_city and old_city not in dict(CITY_CHOICES):
                self.fields["city"].choices.append((old_city, old_city))

    def save(self, commit=True):
        store = super().save(commit=False)
        if not store.slug and store.business_name:
            base = slugify(store.business_name) or "store"
            slug = base
            number = 2
            while Store.objects.filter(slug=slug).exclude(pk=store.pk).exists():
                slug = f"{base}-{number}"
                number += 1
            store.slug = slug
        if commit:
            store.save()
            self.save_m2m()
        return store


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """Validate genuine image uploads, each no larger than 5 MB."""

    widget = MultipleFileInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={
            "accept": "image/*",
            "multiple": True,
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]

        from PIL import Image, UnidentifiedImageError

        for uploaded in files:
            if uploaded.size > 5 * 1024 * 1024:
                raise ValidationError(
                    f"{uploaded.name}: each gallery image must be 5 MB or smaller."
                )

            try:
                uploaded.seek(0)
                with Image.open(uploaded) as image:
                    image.verify()
            except (
                UnidentifiedImageError,
                OSError,
                ValueError,
                Image.DecompressionBombError,
            ):
                raise ValidationError(
                    f"{uploaded.name}: this file is not a valid supported image."
                )
            finally:
                uploaded.seek(0)

        return files


class ShowroomSectionForm(forms.ModelForm):
    gallery_images = MultipleImageField(
        required=False,
        label="Additional showroom images",
        help_text="You can add as many images as you want. Maximum 5 MB per image.",
    )

    class Meta:
        model = ShowroomSection
        fields = ["name", "description", "cover_image"]

    def clean_gallery_images(self):
        return self.cleaned_data.get("gallery_images", [])


class ProductForm(forms.ModelForm):
    gallery_images = MultipleImageField(
        required=False,
        label="Additional gallery images",
        help_text="Select up to 8 additional images. Maximum 5 MB per image.",
    )

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        if store is not None:
            self.fields["showroom_section"].queryset = (
                ShowroomSection.objects.filter(store=store)
            )
        else:
            self.fields["showroom_section"].queryset = ShowroomSection.objects.none()

    class Meta:
        model = Product
        fields = [
            "category", "showroom_section", "name", "description", "price", "price_unit",
            "original_price", "deal_expires_at",
            "image", "video_url", "available",
        ]
        widgets = {
            "deal_expires_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        original_price = cleaned_data.get("original_price")
        expires_at = cleaned_data.get("deal_expires_at")

        if original_price is not None:
            if price is None:
                self.add_error(
                    "price",
                    "Enter the current price to advertise a deal."
                )
            elif original_price <= price:
                self.add_error(
                    "original_price",
                    "The original price must be higher than the current price."
                )

        if expires_at is not None and expires_at <= timezone.now():
            self.add_error(
                "deal_expires_at",
                "The deal expiry must be a future date and time."
            )

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        if product.store_id and product.name:
            base = slugify(product.name) or "product"
            slug = base
            number = 2
            while Product.objects.filter(
                store_id=product.store_id, slug=slug
            ).exclude(pk=product.pk).exists():
                slug = f"{base}-{number}"
                number += 1
            product.slug = slug
        if commit:
            product.save()
            self.save_m2m()
        return product


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = [
            "buyer_name", "buyer_email", "buyer_phone",
            "delivery_location", "quantity", "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Tell the seller what you need..."
            })
        }


class MaterialRequestForm(forms.ModelForm):
    gallery_images = MultipleImageField(
        required=False,
        label="Additional gallery images",
        help_text="Select up to 8 additional images. Maximum 5 MB per image.",
    )

    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        help_text="Choose the state where the materials are needed.",
    )
    city = forms.CharField(
        required=False,
        help_text=(
            "Optional city for context. Active sellers throughout the selected state "
            "will be notified."
        ),
        widget=forms.TextInput(attrs={"placeholder": "e.g. Kano (optional)"}),
    )

    class Meta:
        model = MaterialRequest
        fields = [
            "state",
            "city",
            "delivery_location",
            "buyer_whatsapp",
            "material",
            "quantity",
            "requirements",
            "photo",
        ]
        widgets = {
            "city": forms.TextInput(attrs={"placeholder": "e.g. Kano"}),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "delivery_location": forms.TextInput(
                attrs={"placeholder": "Enter the delivery area or address"}
            ),
            "buyer_whatsapp": forms.TextInput(
                attrs={"placeholder": "Optional, e.g. 08012345678"}
            ),
            "material": forms.TextInput(
                attrs={"placeholder": "e.g. Cement, iron rods, roofing sheets"}
            ),
            "quantity": forms.TextInput(
                attrs={"placeholder": "e.g. 100 bags, 2 tonnes, 20 pieces"}
            ),
            "requirements": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe quality, brand, specifications or other requirements.",
                }
            ),
        }


class SellerQuotationForm(forms.ModelForm):
    class Meta:
        model = SellerQuotation
        fields = [
            "price",
            "price_unit",
            "delivery_days",
            "delivery_details",
            "message",
        ]
        widgets = {
            "price": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01", "placeholder": "Total price in naira"}
            ),
            "price_unit": forms.TextInput(
                attrs={"placeholder": "e.g. total, per bag, per tonne"}
            ),
            "delivery_days": forms.NumberInput(
                attrs={"min": "0", "step": "1", "placeholder": "Estimated delivery days"}
            ),
            "delivery_details": forms.TextInput(
                attrs={"placeholder": "Delivery fee or delivery arrangements"}
            ),
            "message": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Additional details for the buyer"}
            ),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Enter a price greater than zero.")
        return price


class CommunityPostForm(forms.ModelForm):
    gallery_images = MultipleImageField(
        required=False,
        label="Additional gallery images",
        help_text="Select up to 8 additional images. Maximum 5 MB per image.",
    )

    class Meta:
        model = CommunityPost
        fields = ["body", "photo"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": 3000,
                "placeholder": "Share a building tip, project update, question or market news...",
            }),
            "photo": forms.ClearableFileInput(attrs={
                "accept": "image/*",
            }),
        }

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Write something before publishing.")
        return body
