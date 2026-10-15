from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify

from .models import Store, Product, Enquiry

STATE_CHOICES = [('', 'Select a state or territory'), ('Abia', 'Abia - Capital: Umuahia'), ('Adamawa', 'Adamawa - Capital: Yola'), ('Akwa Ibom', 'Akwa Ibom - Capital: Uyo'), ('Anambra', 'Anambra - Capital: Awka'), ('Bauchi', 'Bauchi - Capital: Bauchi'), ('Bayelsa', 'Bayelsa - Capital: Yenagoa'), ('Benue', 'Benue - Capital: Makurdi'), ('Borno', 'Borno - Capital: Maiduguri'), ('Cross River', 'Cross River - Capital: Calabar'), ('Delta', 'Delta - Capital: Asaba'), ('Ebonyi', 'Ebonyi - Capital: Abakaliki'), ('Edo', 'Edo - Capital: Benin City'), ('Ekiti', 'Ekiti - Capital: Ado-Ekiti'), ('Enugu', 'Enugu - Capital: Enugu'), ('Federal Capital Territory (FCT)', 'Federal Capital Territory (FCT) - Capital: Abuja'), ('Gombe', 'Gombe - Capital: Gombe'), ('Imo', 'Imo - Capital: Owerri'), ('Jigawa', 'Jigawa - Capital: Dutse'), ('Kaduna', 'Kaduna - Capital: Kaduna'), ('Kano', 'Kano - Capital: Kano'), ('Katsina', 'Katsina - Capital: Katsina'), ('Kebbi', 'Kebbi - Capital: Birnin Kebbi'), ('Kogi', 'Kogi - Capital: Lokoja'), ('Kwara', 'Kwara - Capital: Ilorin'), ('Lagos', 'Lagos - Capital: Ikeja'), ('Nasarawa', 'Nasarawa - Capital: Lafia'), ('Niger', 'Niger - Capital: Minna'), ('Ogun', 'Ogun - Capital: Abeokuta'), ('Ondo', 'Ondo - Capital: Akure'), ('Osun', 'Osun - Capital: Osogbo'), ('Oyo', 'Oyo - Capital: Ibadan'), ('Plateau', 'Plateau - Capital: Jos'), ('Rivers', 'Rivers - Capital: Port Harcourt'), ('Sokoto', 'Sokoto - Capital: Sokoto'), ('Taraba', 'Taraba - Capital: Jalingo'), ('Yobe', 'Yobe - Capital: Damaturu'), ('Zamfara', 'Zamfara - Capital: Gusau')]
CITY_CHOICES = [('', 'Select a state first'), ('Aba', 'Aba'), ('Abakaliki', 'Abakaliki'), ('Abeokuta', 'Abeokuta'), ('Abuja', 'Abuja'), ('Ado-Ekiti', 'Ado-Ekiti'), ('Afikpo', 'Afikpo'), ('Agbani', 'Agbani'), ('Agbor', 'Agbor'), ('Ahoada', 'Ahoada'), ('Ajah', 'Ajah'), ('Akure', 'Akure'), ('Akwanga', 'Akwanga'), ('Anka', 'Anka'), ('Argungu', 'Argungu'), ('Asaba', 'Asaba'), ('Asokoro', 'Asokoro'), ('Auchi', 'Auchi'), ('Awka', 'Awka'), ('Azare', 'Azare'), ('Badagry', 'Badagry'), ('Bali', 'Bali'), ('Bama', 'Bama'), ('Bauchi', 'Bauchi'), ('Benin City', 'Benin City'), ('Bida', 'Bida'), ('Billiri', 'Billiri'), ('Birnin Kebbi', 'Birnin Kebbi'), ('Biu', 'Biu'), ('Bonny', 'Bonny'), ('Brass', 'Brass'), ('Bukuru', 'Bukuru'), ('Bwari', 'Bwari'), ('Calabar', 'Calabar'), ('Damaturu', 'Damaturu'), ('Daura', 'Daura'), ('Dukku', 'Dukku'), ('Dutse', 'Dutse'), ('Ede', 'Ede'), ('Effurun', 'Effurun'), ('Eket', 'Eket'), ('Ekpoma', 'Ekpoma'), ('Ekwulobia', 'Ekwulobia'), ('Eleme', 'Eleme'), ('Enugu', 'Enugu'), ('Epe', 'Epe'), ('Festac', 'Festac'), ('Funtua', 'Funtua'), ('Garki', 'Garki'), ('Gashua', 'Gashua'), ('Gboko', 'Gboko'), ('Gombe', 'Gombe'), ('Gumel', 'Gumel'), ('Gusau', 'Gusau'), ('Gwadabawa', 'Gwadabawa'), ('Gwagwalada', 'Gwagwalada'), ('Gwarzo', 'Gwarzo'), ('Hadejia', 'Hadejia'), ('Ibadan', 'Ibadan'), ('Idah', 'Idah'), ('Ijebu-Ode', 'Ijebu-Ode'), ('Ijero-Ekiti', 'Ijero-Ekiti'), ('Ikare-Akoko', 'Ikare-Akoko'), ('Ikeja', 'Ikeja'), ('Ikere-Ekiti', 'Ikere-Ekiti'), ('Ikirun', 'Ikirun'), ('Ikom', 'Ikom'), ('Ikorodu', 'Ikorodu'), ('Ikot Ekpene', 'Ikot Ekpene'), ('Ilaro', 'Ilaro'), ('Ilawe-Ekiti', 'Ilawe-Ekiti'), ('Ile-Ife', 'Ile-Ife'), ('Ilesa', 'Ilesa'), ('Ilorin', 'Ilorin'), ('Iseyin', 'Iseyin'), ('Jalingo', 'Jalingo'), ("Jama'are", "Jama'are"), ('Jebba', 'Jebba'), ('Jimeta', 'Jimeta'), ('Jos', 'Jos'), ('Kabba', 'Kabba'), ('Kaduna', 'Kaduna'), ('Kafanchan', 'Kafanchan'), ('Kano', 'Kano'), ('Karu', 'Karu'), ('Katsina', 'Katsina'), ('Katsina-Ala', 'Katsina-Ala'), ('Kaura Namoda', 'Kaura Namoda'), ('Kazaure', 'Kazaure'), ('Keffi', 'Keffi'), ('Kontagora', 'Kontagora'), ('Kubwa', 'Kubwa'), ('Kuje', 'Kuje'), ('Kumo', 'Kumo'), ('Lafia', 'Lafia'), ('Lafiagi', 'Lafiagi'), ('Lagos Island', 'Lagos Island'), ('Lekki', 'Lekki'), ('Lokoja', 'Lokoja'), ('Lugbe', 'Lugbe'), ('Maiduguri', 'Maiduguri'), ('Maitama', 'Maitama'), ('Makurdi', 'Makurdi'), ('Malumfashi', 'Malumfashi'), ('Mararaba', 'Mararaba'), ('Mbaise', 'Mbaise'), ('Minna', 'Minna'), ('Misau', 'Misau'), ('Monguno', 'Monguno'), ('Mubi', 'Mubi'), ('Nembe', 'Nembe'), ('New Bussa', 'New Bussa'), ('Nguru', 'Nguru'), ('Nnewi', 'Nnewi'), ('Nsukka', 'Nsukka'), ('Numan', 'Numan'), ('Obudu', 'Obudu'), ('Offa', 'Offa'), ('Ogbia', 'Ogbia'), ('Ogbomoso', 'Ogbomoso'), ('Ogoja', 'Ogoja'), ('Ohafia', 'Ohafia'), ('Oji River', 'Oji River'), ('Okene', 'Okene'), ('Okigwe', 'Okigwe'), ('Omoku', 'Omoku'), ('Ondo', 'Ondo'), ('Onitsha', 'Onitsha'), ('Onueke', 'Onueke'), ('Orlu', 'Orlu'), ('Oron', 'Oron'), ('Osogbo', 'Osogbo'), ('Ota', 'Ota'), ('Otukpo', 'Otukpo'), ('Owerri', 'Owerri'), ('Owo', 'Owo'), ('Oyo', 'Oyo'), ('Pankshin', 'Pankshin'), ('Port Harcourt', 'Port Harcourt'), ('Potiskum', 'Potiskum'), ('Rano', 'Rano'), ('Sagamu', 'Sagamu'), ('Saki', 'Saki'), ('Saminaka', 'Saminaka'), ('Sapele', 'Sapele'), ('Serti', 'Serti'), ('Shendam', 'Shendam'), ('Sokoto', 'Sokoto'), ('Suleja', 'Suleja'), ('Surulere', 'Surulere'), ('Talata Mafara', 'Talata Mafara'), ('Tambuwal', 'Tambuwal'), ('Udi', 'Udi'), ('Ughelli', 'Ughelli'), ('Umuahia', 'Umuahia'), ('Uromi', 'Uromi'), ('Uyo', 'Uyo'), ('Victoria Island', 'Victoria Island'), ('Warri', 'Warri'), ('Wudil', 'Wudil'), ('Wukari', 'Wukari'), ('Wurno', 'Wurno'), ('Wuse', 'Wuse'), ('Yaba', 'Yaba'), ('Yauri', 'Yauri'), ('Yenagoa', 'Yenagoa'), ('Yola', 'Yola'), ('Zaria', 'Zaria'), ('Zuru', 'Zuru')]


class SellerSignupForm(UserCreationForm):
    email = forms.EmailField()
    business_name = forms.CharField(max_length=160)
    phone = forms.CharField(max_length=30)
    state = forms.ChoiceField(choices=STATE_CHOICES)
    city = forms.ChoiceField(choices=CITY_CHOICES)
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "Street, building, estate, market or shop address"
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StoreForm(forms.ModelForm):
    state = forms.ChoiceField(choices=STATE_CHOICES)
    city = forms.ChoiceField(choices=CITY_CHOICES)
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
            "email", "state", "city", "address",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category", "name", "description", "price", "price_unit",
            "image", "video_url", "available",
        ]

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
