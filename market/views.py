import json
import re
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Count, Max
from django.utils.text import slugify
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .models import SavedProduct, SavedStore, Store, Product, ShowroomSection, Category, Advertisement, Enquiry, MaterialRequest, SellerQuotation, CommunityNotification, CommunityPost, CommunityComment, CommunityPostReaction, CommunityCommentReaction, PushSubscription, RecentlyViewed, ProductGalleryImage, MaterialRequestGalleryImage, CommunityPostGalleryImage, ShowroomSectionGalleryImage
from .forms import BuyerSignupForm, SellerSignupForm, StoreForm, ProductForm, ShowroomSectionForm, EnquiryForm, MaterialRequestForm, SellerQuotationForm, CommunityPostForm, STATE_CHOICES
from .daily_inspiration import get_daily_inspiration



def _save_gallery_images(parent, uploaded_files, gallery_model, relation_name):
    """Save validated gallery files using Django's configured storage backend."""
    for uploaded_file in uploaded_files:
        gallery_model.objects.create(
            **{relation_name: parent, "image": uploaded_file}
        )


def _record_recently_viewed(request, *, product=None, store=None):
    """Record a visit privately for the signed-in user or current session."""
    if not request.user.is_authenticated and not request.session.session_key:
        request.session.create()

    user = request.user if request.user.is_authenticated else None
    session_key = "" if user else request.session.session_key

    # Keep product visits and showroom visits as separate history entries.
    if product is not None:
        target_filter = {"product": product, "store__isnull": True}
        history_filter = {"product__isnull": False}
    elif store is not None:
        target_filter = {"store": store, "product__isnull": True}
        history_filter = {"store__isnull": False}
    else:
        return

    RecentlyViewed.objects.filter(
        user=user, session_key=session_key, **target_filter
    ).delete()

    RecentlyViewed.objects.create(
        user=user,
        session_key=session_key,
        product=product,
        store=store,
    )

    # Keep at most 20 recent entries of each kind for this visitor.
    old_ids = list(
        RecentlyViewed.objects.filter(
            user=user, session_key=session_key, **history_filter
        ).order_by("-viewed_at").values_list("pk", flat=True)[20:]
    )
    if old_ids:
        RecentlyViewed.objects.filter(pk__in=old_ids).delete()


class BuildSpotLoginView(LoginView):
    """Send sellers to their store and buyers to the community by default."""

    def get_default_redirect_url(self):
        if self.request.user.is_authenticated and Store.objects.filter(
            owner=self.request.user
        ).exists():
            return "/seller/dashboard/"
        return "/community/"

def _normalize_material(value):
    """Normalize material names for case- and punctuation-insensitive matching."""
    words = re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).split()
    # Handle common singular/plural differences without changing words like glass.
    return [word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss")
            else word for word in words]


def _material_matches(requested, product_name, category_name=""):
    """Match a requested material to a product name or its category."""
    wanted = _normalize_material(requested)
    if not wanted:
        return False

    for candidate in (product_name, category_name):
        available_words = _normalize_material(candidate)
        if available_words and all(word in available_words for word in wanted):
            return True
    return False


def home(request):
    ads = Advertisement.objects.filter(active=True, placement="home")
    # Store recommendations are ranked after browsing interests are known.
    stores = []
    products = list(
        Product.objects.filter(
            available=True, store__is_active=True
        ).select_related("store", "category").order_by("-created_at")[:8]
    )

    # Keep browsing history private to the signed-in user or this browser session.
    if request.user.is_authenticated:
        history = RecentlyViewed.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        history = (
            RecentlyViewed.objects.filter(
                user__isnull=True, session_key=session_key
            )
            if session_key
            else RecentlyViewed.objects.none()
        )

    recent_product_records = list(
        history.filter(
            product__isnull=False,
            product__available=True,
            product__store__is_active=True,
        )
        .select_related("product__store", "product__category")
        .order_by("-viewed_at")[:6]
    )
    recent_store_records = list(
        history.filter(
            store__isnull=False,
            store__is_active=True,
        )
        .select_related("store")
        .order_by("-viewed_at")[:6]
    )

    # De-duplicate history entries in case an older visit created duplicates.
    recent_products = []
    seen_product_ids = set()
    for record in recent_product_records:
        item = record.product
        if item.pk not in seen_product_ids:
            recent_products.append(item)
            seen_product_ids.add(item.pk)

    recent_stores = []
    seen_store_ids = set()
    for record in recent_store_records:
        item = record.store
        if item.pk not in seen_store_ids:
            recent_stores.append(item)
            seen_store_ids.add(item.pk)

    # Build interest signals from recently viewed items and the buyer's own requests.
    interest_texts = []
    for item in recent_products:
        interest_texts.extend([
            item.name or "",
            item.category.name if item.category else "",
        ])

    if request.user.is_authenticated:
        buyer_requests = MaterialRequest.objects.filter(
            buyer=request.user
        ).order_by("-created_at")[:5]
        for material_request in buyer_requests:
            interest_texts.extend([
                material_request.material or "",
                material_request.requirements or "",
            ])

    stop_words = {
        "and", "the", "for", "with", "from", "your", "you", "are",
        "this", "that", "have", "need", "wanted", "want", "please",
        "material", "materials", "building", "project", "good", "best",
    }
    terms = set()
    for text in interest_texts:
        terms.update(
            word for word in re.findall(r"[a-z0-9]+", text.casefold())
            if len(word) > 2 and word not in stop_words
        )

    # Rank a bounded set of available products to keep homepage queries modest.
    candidates = list(
        Product.objects.filter(
            available=True, store__is_active=True
        )
        .select_related("store", "category")
        .order_by("-created_at")[:250]
    )
    # Rank active stores using listing activity, quality, freshness and buyer interests.
    store_candidates = list(
        Store.objects.filter(is_active=True)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__available=True),
                distinct=True,
            ),
            photo_count=Count(
                "products",
                filter=(
                    Q(products__available=True)
                    & ~Q(products__image="")
                ),
                distinct=True,
            ),
            described_count=Count(
                "products",
                filter=(
                    Q(products__available=True)
                    & ~Q(products__description="")
                ),
                distinct=True,
            ),
            latest_product_at=Max(
                "products__created_at",
                filter=Q(products__available=True),
            ),
        )
    )

    # Use the recent product candidates already fetched for recommendations.
    store_product_text = {}
    store_product_scores = {}
    for item in candidates:
        store_id = item.store_id
        name = (item.name or "").casefold()
        category = (
            item.category.name.casefold() if item.category else ""
        )
        description = (item.description or "").casefold()

        store_product_text.setdefault(store_id, []).append(
            f"{name} {category} {description}"
        )

        match_score = (
            sum(2 for term in terms if term in name)
            + sum(3 for term in terms if term in category)
            + sum(1 for term in terms if term in description)
        )
        store_product_scores[store_id] = (
            store_product_scores.get(store_id, 0) + match_score
        )

    recently_interested_store_ids = {
        item.store_id for item in recent_products
    }
    recently_viewed_store_ids = {
        item.pk for item in recent_stores
    }

    for store in store_candidates:
        # More available products help, with a cap so one large seller
        # cannot dominate the entire section.
        score = min(store.product_count, 20) * 2

        # Complete listings with photos and descriptions are more useful.
        score += min(store.photo_count, 8) * 1.5
        score += min(store.described_count, 8)

        # Reward recent uploads so active sellers can rise naturally.
        if store.latest_product_at:
            age_days = (
                timezone.now() - store.latest_product_at
            ).days
            if age_days <= 7:
                score += 14
            elif age_days <= 30:
                score += 8
            elif age_days <= 90:
                score += 3

        if store.verification_status == "verified":
            score += 3

        # Personalize using product names, categories, descriptions,
        # and the store's own business/location information.
        store_text = " ".join([
            store.business_name or "",
            store.description or "",
            store.city or "",
            store.state or "",
            *store_product_text.get(store.pk, []),
        ]).casefold()

        score += sum(2 for term in terms if term in store_text)
        score += min(store_product_scores.get(store.pk, 0), 12)

        # A store associated with the visitor's recent interests can
        # be surfaced again rather than treating every visit as new.
        if store.pk in recently_interested_store_ids:
            score += 6
        if store.pk in recently_viewed_store_ids:
            score += 3

        store._recommendation_score = score

    store_candidates.sort(
        key=lambda store: (
            store._recommendation_score,
            store.latest_product_at or store.created_at,
            store.created_at,
        ),
        reverse=True,
    )
    stores = store_candidates[:6]

    recent_ids = {item.pk for item in recent_products}
    homepage_ids = {item.pk for item in products}

    scored = []
    for item in candidates:
        if item.pk in recent_ids:
            continue
        name = (item.name or "").casefold()
        category = (
            item.category.name.casefold() if item.category else ""
        )
        description = (item.description or "").casefold()
        searchable = f"{name} {category} {description}"
        score = sum(1 for term in terms if term in searchable)

        # Give exact product-name and category interest extra weight.
        score += sum(2 for term in terms if term in name)
        score += sum(3 for term in terms if term in category)
        scored.append((score, item.created_at, item))

    if terms:
        scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    else:
        scored.sort(key=lambda entry: entry[1], reverse=True)

    recommended_products = [
        item for score, created_at, item in scored
        if score > 0 and item.pk not in homepage_ids
    ][:8]

    # If there are too few matches, fill with other recent available listings.
    if len(recommended_products) < 4:
        already_selected = {
            item.pk for item in recommended_products
        } | recent_ids | homepage_ids
        for score, created_at, item in scored:
            if item.pk not in already_selected:
                recommended_products.append(item)
                already_selected.add(item.pk)
            if len(recommended_products) >= 8:
                break

    deal_products = Product.objects.filter(
        available=True,
        store__is_active=True,
        price__isnull=False,
        original_price__gt=__import__("django.db.models", fromlist=["F"]).F("price"),
    ).filter(
        Q(deal_expires_at__isnull=True) | Q(deal_expires_at__gt=timezone.now())
    ).select_related("store", "category").order_by("-created_at")[:8]

    return render(request, "market/home.html", {
        "ads": ads,
        "stores": stores,
        "products": products,
        "recent_products": recent_products,
        "recent_stores": recent_stores,
        "recommended_products": recommended_products,
        "deal_products": deal_products,
        "daily_inspiration": get_daily_inspiration(),
    })


def todays_deals(request):
    deal_products = Product.objects.filter(
        available=True,
        store__is_active=True,
        price__isnull=False,
        original_price__gt=__import__("django.db.models", fromlist=["F"]).F("price"),
    ).filter(
        Q(deal_expires_at__isnull=True) | Q(deal_expires_at__gt=timezone.now())
    ).select_related("store", "category").order_by("-created_at")

    return render(request, "market/todays_deals.html", {
        "deal_products": deal_products,
    })


def market_list(request):
    q = request.GET.get("q", "").strip()
    state = request.GET.get("state", "").strip()
    city = request.GET.get("city", "").strip()

    stores = Store.objects.filter(
        is_active=True
    ).select_related("owner").annotate(
        product_count=Count(
            "products",
            filter=Q(products__available=True),
            distinct=True,
        )
    )

    matching_sections = ShowroomSection.objects.filter(
        store__is_active=True
    ).select_related("store").annotate(
        product_count=Count(
            "products",
            filter=Q(products__available=True),
            distinct=True,
        )
    )

    if q:
        stores = stores.filter(
            Q(business_name__icontains=q)
            | Q(description__icontains=q)
            | Q(products__name__icontains=q)
            | Q(products__category__name__icontains=q)
            | Q(showroom_sections__name__icontains=q)
            | Q(showroom_sections__description__icontains=q)
        ).distinct()

        matching_sections = matching_sections.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
        )

    if state:
        stores = stores.filter(state__icontains=state)
        matching_sections = matching_sections.filter(
            store__state__icontains=state
        )

    if city:
        stores = stores.filter(city__icontains=city)
        matching_sections = matching_sections.filter(
            store__city__icontains=city
        )

    return render(request, "market/market.html", {
        "stores": stores.distinct(),
        "matching_sections": matching_sections,
        "q": q,
        "state": state,
        "city": city,
        "ads": Advertisement.objects.filter(
            active=True,
            placement="market",
        ),
    })

def store_detail(request, slug):
    store = get_object_or_404(Store, slug=slug, is_active=True)

    sections = store.showroom_sections.annotate(
        product_count=Count("products")
    ).prefetch_related("gallery_images")

    products = store.products.filter(
        available=True
    ).select_related("category", "showroom_section")

    selected_section_slug = request.GET.get("section", "").strip()
    selected_section = sections.filter(
        slug=selected_section_slug
    ).first() if selected_section_slug else None

    if selected_section:
        products = products.filter(showroom_section=selected_section)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    form = EnquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        enquiry = form.save(commit=False)
        enquiry.store = store
        pid = request.POST.get("product_id")
        if pid:
            enquiry.product = Product.objects.filter(
                pk=pid, store=store
            ).first()
        enquiry.save()

        if store.owner.email:
            send_mail(
                f"New BuildSpot enquiry for {store.business_name}",
                f"Buyer: {enquiry.buyer_name}\nEmail: {enquiry.buyer_email}\nPhone: {enquiry.buyer_phone}\nProduct: {enquiry.product or 'General enquiry'}\nQuantity: {enquiry.quantity}\nDelivery location: {enquiry.delivery_location}\n\n{enquiry.message}",
                None,
                [store.owner.email],
                fail_silently=True,
            )

        messages.success(
            request,
            "Your request has been sent to the seller. They can contact you using the details you provided.",
        )
        return redirect(store.get_absolute_url())

    _record_recently_viewed(request, store=store)

    return render(request, "market/store_detail.html", {
        "store": store,
        "products": products,
        "sections": sections,
        "selected_section": selected_section,
        "search_query": search_query,
        "form": form,
        "ads": Advertisement.objects.filter(
            active=True, placement="store"
        ),
    })

def signup(request):
    form = SellerSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()

                business_name = form.cleaned_data["business_name"].strip()
                base = slugify(business_name) or f"store-{user.username}"
                slug = base
                number = 2

                while Store.objects.filter(slug=slug).exists():
                    slug = f"{base}-{number}"
                    number += 1

                Store.objects.create(
                    owner=user,
                    business_name=business_name,
                    slug=slug,
                    phone=form.cleaned_data["phone"],
                    whatsapp=form.cleaned_data.get("whatsapp", "").strip(),
                    email=user.email,
                    state=form.cleaned_data["state"],
                    city="",
                    address=form.cleaned_data["address"],
                    description=form.cleaned_data.get("description", "").strip(),
                )

            login(request, user)
            messages.success(
                request,
                "Your BuildSpot account and seller profile are ready. "
                "You can now add products."
            )
            return redirect("seller_dashboard")

        except IntegrityError:
            form.add_error(
                None,
                "We could not finish creating your account and store. "
                "Please check your details and try again. If this continues, "
                "contact the site administrator."
            )

    return render(request, "market/signup.html", {"form": form})


def buyer_signup(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    safe_next = (
        next_url
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        else ""
    )

    if request.user.is_authenticated:
        return redirect(safe_next or "community")

    form = BuyerSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            "Your BuildSpot buyer account is ready. Welcome to the community!",
        )
        return redirect(safe_next or "community")

    return render(
        request,
        "market/buyer_signup.html",
        {"form": form, "next": safe_next},
    )


@login_required
def seller_dashboard(request):
    store=Store.objects.filter(owner=request.user).first()
    if not store:
        messages.info(request,"Create a seller profile to manage your store."); return redirect("signup")
    if request.method=="POST":
        form=StoreForm(request.POST,request.FILES,instance=store)
        if form.is_valid(): form.save(); messages.success(request,"Store profile updated."); return redirect("seller_dashboard")
    else: form=StoreForm(instance=store)
    return render(request,"market/dashboard.html",{"store":store,"form":form,"products":store.products.select_related("showroom_section").all(),"sections":store.showroom_sections.annotate(product_count=Count("products")).prefetch_related("gallery_images"),"enquiries":store.enquiries.select_related("product")[:20]})

@login_required
def showroom_section_add(request):
    store = get_object_or_404(Store, owner=request.user)
    form = ShowroomSectionForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        section = form.save(commit=False)
        section.store = store
        base = slugify(section.name) or "section"
        slug = base
        number = 2

        while ShowroomSection.objects.filter(store=store, slug=slug).exists():
            slug = f"{base}-{number}"
            number += 1

        section.slug = slug
        section.save()
        _save_gallery_images(
            section,
            form.cleaned_data.get("gallery_images", []),
            ShowroomSectionGalleryImage,
            "section",
        )
        messages.success(request, "Showroom section created.")
        return redirect("seller_dashboard")

    return render(request, "market/showroom_section_form.html", {
        "form": form,
        "heading": "Create showroom section",
    })


@login_required
def showroom_section_edit(request, pk):
    store = get_object_or_404(Store, owner=request.user)
    section = get_object_or_404(ShowroomSection, pk=pk, store=store)
    form = ShowroomSectionForm(
        request.POST or None,
        request.FILES or None,
        instance=section,
    )

    if request.method == "POST" and form.is_valid():
        section = form.save(commit=False)
        base = slugify(section.name) or "section"
        slug = base
        number = 2

        while ShowroomSection.objects.filter(
            store=store, slug=slug
        ).exclude(pk=section.pk).exists():
            slug = f"{base}-{number}"
            number += 1

        section.slug = slug
        section.save()
        _save_gallery_images(
            section,
            form.cleaned_data.get("gallery_images", []),
            ShowroomSectionGalleryImage,
            "section",
        )
        messages.success(request, "Showroom section updated.")
        return redirect("seller_dashboard")

    return render(request, "market/showroom_section_form.html", {
        "form": form,
        "heading": "Edit showroom section",
        "section": section,
    })


@login_required
@require_POST
def showroom_section_delete(request, pk):
    store = get_object_or_404(Store, owner=request.user)
    section = get_object_or_404(ShowroomSection, pk=pk, store=store)
    section.delete()
    messages.success(
        request,
        "Showroom section deleted. Its products have been kept in your catalogue.",
    )
    return redirect("seller_dashboard")


@login_required
def store_profile(request):
    store = Store.objects.filter(owner=request.user).first()
    if not store:
        messages.info(request, "Create a seller profile to manage your store.")
        return redirect("signup")

    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Store profile updated.")
            return redirect("store_profile")
    else:
        form = StoreForm(instance=store)

    return render(
        request,
        "market/store_profile.html",
        {"store": store, "form": form},
    )


@login_required
def product_add(request):
    store=get_object_or_404(Store,owner=request.user)
    form=ProductForm(request.POST or None,request.FILES or None,store=store)
    if request.method=="POST" and form.is_valid():
        product=form.save(commit=False); product.store=store; product.slug=slugify(product.name); base=product.slug or "product"; slug=base; i=2
        while Product.objects.filter(store=store,slug=slug).exists(): slug=f"{base}-{i}"; i+=1
        product.slug=slug; product.save()
        _save_gallery_images(
            product,
            form.cleaned_data.get("gallery_images", []),
            ProductGalleryImage,
            "product",
        )

        # Notify only buyers with an open request matching this available product.
        buyer_ids = []

        if product.available and store.is_active:
            matching_requests = MaterialRequest.objects.filter(
                status="open",
                state__iexact=store.state,
            ).exclude(buyer=request.user).select_related("buyer")

            category_name = product.category.name if product.category_id else ""
            buyer_ids = sorted({
                item.buyer_id
                for item in matching_requests
                if _material_matches(item.material, product.name, category_name)
            })

        if buyer_ids:
            from .push_notifications import send_web_push

            product_title = f"New product match: {product.name}"
            product_message = (
                f"A seller in {store.state} added {product.name}, "
                "which matches an open material request. Tap to view the product."
            )[:500]
            product_url = product_detail_url(store, product)

            CommunityNotification.objects.bulk_create([
                CommunityNotification(
                    recipient_id=buyer_id,
                    title=product_title,
                    message=product_message,
                    url=product_url,
                )
                for buyer_id in buyer_ids
            ])

            send_web_push(
                buyer_ids,
                title=product_title,
                body=product_message,
                url=product_url,
            )

        messages.success(request,"Product added to your showroom.")
        return redirect("seller_dashboard")
    return render(request,"market/product_form.html",{"form":form,"heading":"Add a product"})

@login_required
def product_edit(request, pk):
    store=get_object_or_404(Store,owner=request.user); product=get_object_or_404(Product,pk=pk,store=store)
    form=ProductForm(request.POST or None,request.FILES or None,instance=product,store=store)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        _save_gallery_images(
            product,
            form.cleaned_data.get("gallery_images", []),
            ProductGalleryImage,
            "product",
        )
        messages.success(request, "Product updated.")
        return redirect("seller_dashboard")
    return render(request,"market/product_form.html",{"form":form,"heading":"Edit product"})

@login_required
def product_delete(request, pk):
    store=get_object_or_404(Store,owner=request.user); product=get_object_or_404(Product,pk=pk,store=store)
    if request.method=="POST": product.delete(); messages.success(request,"Product deleted.")
    return redirect("seller_dashboard")

def product_detail(request, store_slug, product_slug):
    store=get_object_or_404(Store,slug=store_slug,is_active=True); product=get_object_or_404(Product,store=store,slug=product_slug,available=True)
    _record_recently_viewed(request, product=product)
    form=EnquiryForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        enquiry=form.save(commit=False); enquiry.store=store; enquiry.product=product; enquiry.save();
        if store.owner.email:
            send_mail(f"New BuildSpot enquiry for {product.name}", f"Buyer: {enquiry.buyer_name}\nEmail: {enquiry.buyer_email}\nPhone: {enquiry.buyer_phone}\nQuantity: {enquiry.quantity}\nDelivery location: {enquiry.delivery_location}\n\n{enquiry.message}", None, [store.owner.email], fail_silently=True)
        messages.success(request,"Your product enquiry has been sent."); return redirect(product_detail_url(store,product))
    product_path = product_detail_url(store, product)
    product_absolute_url = request.build_absolute_uri(product_path)
    if request.get_host() == "buildspot.pythonanywhere.com":
        product_absolute_url = f"https://{request.get_host()}{product_path}"
    product_image_absolute_url = (
        request.build_absolute_uri(product.image.url) if product.image else ""
    )
    whatsapp_message = (
        f"Hello, I am interested in {product.name} on BuildSpot. "
        f"Please share price and availability. Product details and picture: "
        f"{product_absolute_url}"
    )

    price_history = list(
        product.price_history.order_by("-recorded_at", "-pk")[:6]
    )
    has_verified_price_drop = (
        len(price_history) >= 2
        and price_history[0].price < price_history[1].price
    )

    return render(request, "market/product_detail.html", {
        "store": store,
        "product": product,
        "form": form,
        "product_absolute_url": product_absolute_url,
        "product_image_absolute_url": product_image_absolute_url,
        "whatsapp_message": whatsapp_message,
        "price_history": price_history,
        "has_verified_price_drop": has_verified_price_drop,
    })

def product_detail_url(store, product):
    from django.urls import reverse
    return reverse("product_detail",args=[store.slug,product.slug])



def public_profile(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    store = Store.objects.filter(
        owner=profile_user, is_active=True
    ).first()

    posts = CommunityPost.objects.filter(
        author=profile_user
    ).select_related("author")[:20]

    material_requests = MaterialRequest.objects.filter(
        buyer=profile_user
    ).select_related("buyer")[:20]

    return render(request, "market/public_profile.html", {
        "profile_user": profile_user,
        "store": store,
        "posts": posts,
        "material_requests": material_requests,
        "post_count": CommunityPost.objects.filter(
            author=profile_user
        ).count(),
        "request_count": MaterialRequest.objects.filter(
            buyer=profile_user
        ).count(),
    })


def community(request):
    state = request.GET.get("state", "").strip()
    requests = MaterialRequest.objects.filter(
        status="open"
    ).select_related("buyer")

    stores = Store.objects.filter(is_active=True).order_by("-created_at")
    if state:
        requests = requests.filter(state__iexact=state)
        stores = stores.filter(state__iexact=state)
        if state.casefold() in {
            "federal capital territory (fct)", "fct", "abuja"
        }:
            community_title = "Federal Capital Territory (FCT) Building Material Market"
        elif state.casefold().endswith(" state"):
            community_title = f"{state} Building Material Market"
        else:
            community_title = f"{state} State Building Material Market"
    else:
        community_title = "Nigeria Building Materials Community"

    unread_notification_count = 0
    if request.user.is_authenticated:
        unread_notification_count = CommunityNotification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

    # Absolute public URLs are needed by WhatsApp's link-preview crawler.
    community_absolute_url = request.build_absolute_uri(request.get_full_path())
    community_image_absolute_url = request.build_absolute_uri(
        "/static/img/logo.jpeg"
    )

    if request.get_host() == "buildspot.pythonanywhere.com":
        community_absolute_url = (
            f"https://{request.get_host()}{request.get_full_path()}"
        )
        community_image_absolute_url = (
            f"https://{request.get_host()}/static/img/logo.jpeg"
        )

    return render(request, "market/community.html", {
        "requests": requests[:100],
        "state": state,
        "state_choices": STATE_CHOICES,
        "form": MaterialRequestForm(),
        "community_title": community_title,
        "community_absolute_url": community_absolute_url,
        "community_image_absolute_url": community_image_absolute_url,
        "stores": stores[:12],
        "unread_notification_count": unread_notification_count,
        "posts": CommunityPost.objects.select_related("author")[:50],
        "post_form": CommunityPostForm(),
    })


@login_required
def material_request_create(request):
    if request.method != "POST":
        return redirect("community")

    form = MaterialRequestForm(request.POST, request.FILES)
    if not form.is_valid():
        requests = MaterialRequest.objects.filter(status="open").select_related("buyer")
        selected_state = request.POST.get("state", "").strip()
        if selected_state:
            requests = requests.filter(state__iexact=selected_state)
        stores = Store.objects.filter(
            is_active=True
        ).order_by("-created_at")
        if selected_state:
            stores = stores.filter(state__iexact=selected_state)
            if selected_state.casefold() in {
                "federal capital territory (fct)", "fct", "abuja"
            }:
                community_title = "Federal Capital Territory (FCT) Building Material Market"
            elif selected_state.casefold().endswith(" state"):
                community_title = f"{selected_state} Building Material Market"
            else:
                community_title = f"{selected_state} State Building Material Market"
        else:
            community_title = "Nigeria Building Materials Community"

        unread_notification_count = 0
        if request.user.is_authenticated:
            unread_notification_count = CommunityNotification.objects.filter(
                recipient=request.user, is_read=False
            ).count()

        return render(request, "market/community.html", {
            "requests": requests[:100],
            "state": selected_state,
            "state_choices": STATE_CHOICES,
            "form": form,
            "community_title": community_title,
            "stores": stores[:12],
            "unread_notification_count": unread_notification_count,
        }, status=400)

    material_request = form.save(commit=False)
    material_request.buyer = request.user
    material_request.save()
    _save_gallery_images(
        material_request,
        form.cleaned_data.get("gallery_images", []),
        MaterialRequestGalleryImage,
        "material_request",
    )

    # Notify active sellers in the selected state only if they stock
    # an available product matching the request. Never expose the exact
    # delivery address in notification text or URLs.
    from urllib.parse import urlencode

    candidate_stores = Store.objects.filter(
        is_active=True,
        state__iexact=material_request.state,
    ).exclude(owner=request.user).prefetch_related(
        "products__category"
    )

    seller_ids = sorted({
        candidate.owner_id
        for candidate in candidate_stores
        if any(
            product.available
            and _material_matches(
                material_request.material,
                product.name,
                product.category.name if product.category_id else "",
            )
            for product in candidate.products.all()
        )
    })

    location_label = (
        f"{material_request.city}, {material_request.state}"
        if material_request.city.strip()
        else f"anywhere in {material_request.state}"
    )

    request_title = f"New buyer request: {material_request.material}"
    request_message = (
        f"A buyer is looking for {material_request.quantity} "
        f"of {material_request.material} in {location_label}. "
        "Open BuildSpot to view the request and contact the buyer if relevant."
    )[:500]
    request_url = f"/community/requests/{material_request.pk}/"

    # Keep the existing in-app notifications.
    CommunityNotification.objects.bulk_create([
        CommunityNotification(
            recipient_id=seller_id,
            title=request_title,
            message=request_message,
            url=request_url,
        )
        for seller_id in seller_ids
    ])

    # Also send real browser push to subscribed sellers in this state.
    # The message contains city/state only, never the delivery address.
    if seller_ids:
        from .push_notifications import send_web_push
        send_web_push(
            seller_ids,
            title=request_title,
            body=request_message,
            url=request_url,
        )

    messages.success(
        request,
        "Your material request has been posted to your state community."
    )
    return redirect(f"/community/?state={material_request.state}")


@login_required
def quotation_create(request, request_id):
    material_request = get_object_or_404(
        MaterialRequest, pk=request_id, status="open"
    )
    # The buyer must never submit a quotation to their own request.
    if material_request.buyer_id == request.user.pk:
        messages.error(request, "You cannot submit a quotation to your own request.")
        return redirect("community_request_detail", request_id=material_request.pk)

    # Recheck that the request is still open before accepting a quotation.
    if material_request.status != "open":
        messages.error(request, "This material request is no longer accepting quotations.")
        return redirect("community_request_detail", request_id=material_request.pk)

    if material_request.quotations.filter(status="accepted").exists():
        messages.info(request, "A quotation has already been accepted for this request.")
        return redirect("community_request_detail", request_id=material_request.pk)

    store = get_object_or_404(Store, owner=request.user, is_active=True)

    # Sellers anywhere within the requested state may submit quotations.
    # The buyer's city remains the preferred delivery destination.
    if store.state.strip().casefold() != material_request.state.strip().casefold():
        messages.error(
            request,
            "Your store must be in the same state as this request to submit a quotation."
        )
        return redirect("community_request_detail", request_id=material_request.pk)

    if request.method != "POST":
        return redirect("community_request_detail", request_id=material_request.pk)

    if SellerQuotation.objects.filter(
        material_request=material_request, store=store
    ).exists():
        messages.info(
            request,
            "Your store has already submitted a quotation for this request."
        )
        return redirect("community_request_detail", request_id=material_request.pk)

    form = SellerQuotationForm(request.POST)
    if form.is_valid():
        quotation = form.save(commit=False)
        quotation.material_request = material_request
        quotation.store = store
        quotation.save()

        CommunityNotification.objects.create(
            recipient=material_request.buyer,
            title="A seller sent you a quotation",
            message=(
                f"{store.business_name} quoted ₦{quotation.price} "
                f"for {material_request.material}."
            ),
            url=f"/community/requests/{material_request.pk}/",
        )
        messages.success(request, "Your quotation has been sent to the buyer.")
    else:
        messages.error(
            request,
            "The quotation could not be submitted. Check the price and required fields."
        )

    return redirect("community_request_detail", request_id=material_request.pk)



def material_request_detail(request, request_id):
    material_request = get_object_or_404(
        MaterialRequest.objects.select_related("buyer"),
        pk=request_id,
    )

    context = {"item": material_request}

    # Only the buyer who created the request can see all quotations.
    if request.user.is_authenticated and request.user.pk == material_request.buyer_id:
        context["quotations"] = (
            material_request.quotations.select_related("store").all()
        )

    # Sellers can see only their own quotation and may quote only once.
    if (
        request.user.is_authenticated
        and request.user.pk != material_request.buyer_id
    ):
        try:
            store = Store.objects.get(owner=request.user, is_active=True)
        except Store.DoesNotExist:
            store = None

        if store:
            same_state = (
                store.state.strip().casefold()
                == material_request.state.strip().casefold()
            )
            # City is a preferred delivery destination, not a seller eligibility restriction.
            if same_state:
                context["seller_store"] = store
                context["seller_quotation"] = (
                    material_request.quotations.filter(store=store).first()
                )

                has_accepted_quotation = material_request.quotations.filter(
                    status="accepted"
                ).exists()

                if (
                    material_request.status == "open"
                    and not has_accepted_quotation
                    and context["seller_quotation"] is None
                ):
                    context["quotation_form"] = SellerQuotationForm()

    return render(
        request,
        "market/material_request_detail.html",
        context,
    )

@login_required
@require_POST
def quotation_accept(request, quotation_id):
    quotation = get_object_or_404(
        SellerQuotation.objects.select_related(
            "material_request", "store", "store__owner"
        ),
        pk=quotation_id,
        material_request__buyer=request.user,
    )
    material_request = quotation.material_request

    accepted_seller_ids = []
    declined_seller_ids = []

    with transaction.atomic():
        material_request = MaterialRequest.objects.get(pk=material_request.pk)
        quotation = SellerQuotation.objects.select_related(
            "store", "store__owner"
        ).get(pk=quotation.pk)

        if material_request.status != "open":
            messages.error(request, "This material request is no longer open.")
            return redirect(
                "community_request_detail", request_id=material_request.pk
            )

        if quotation.status != "submitted":
            messages.info(request, "This quotation has already been processed.")
            return redirect(
                "community_request_detail", request_id=material_request.pk
            )

        if material_request.quotations.filter(status="accepted").exists():
            messages.info(request, "A quotation has already been accepted.")
            return redirect(
                "community_request_detail", request_id=material_request.pk
            )

        quotation.status = "accepted"
        quotation.save(update_fields=["status", "updated_at"])

        accepted_seller = quotation.store.owner
        accepted_seller_ids.append(accepted_seller.pk)

        CommunityNotification.objects.create(
            recipient=accepted_seller,
            title="Your quotation was accepted!",
            message=(
                f"The buyer accepted your quotation for "
                f"{material_request.material}."
            ),
            url=(
                f"/community/requests/{material_request.pk}/"
                f"#community-quotation-{quotation.pk}"
            ),
        )

        other_quotes = list(
            SellerQuotation.objects.select_related(
                "store", "store__owner"
            ).filter(
                material_request=material_request,
                status="submitted",
            ).exclude(pk=quotation.pk)
        )

        for other in other_quotes:
            other.status = "declined"
            other.save(update_fields=["status", "updated_at"])

            seller = other.store.owner
            declined_seller_ids.append(seller.pk)

            CommunityNotification.objects.create(
                recipient=seller,
                title="Quotation not selected",
                message=(
                    f"The buyer accepted another seller's quotation for "
                    f"{material_request.material}. Thank you for responding."
                ),
                url=(
                    f"/community/requests/{material_request.pk}/"
                    f"#community-quotation-{other.pk}"
                ),
            )

    # Send browser push after the database transaction succeeds.
    from .push_notifications import send_web_push

    send_web_push(
        list(set(accepted_seller_ids)),
        title="Quotation accepted!",
        body=f"Your quotation for {material_request.material} was accepted.",
        url=(
            f"/community/requests/{material_request.pk}/"
            f"#community-quotation-{quotation.pk}"
        ),
    )

    if declined_seller_ids:
        send_web_push(
            list(set(declined_seller_ids)),
            title="Quotation update",
            body=(
                f"The buyer selected another quotation for "
                f"{material_request.material}."
            ),
            url=f"/community/requests/{material_request.pk}/",
        )

    messages.success(
        request,
        "Quotation accepted. All other submitted quotations have been declined.",
    )
    return redirect("community_request_detail", request_id=material_request.pk)


@login_required
@require_POST
def quotation_decline(request, quotation_id):
    quotation = get_object_or_404(
        SellerQuotation.objects.select_related(
            "material_request", "store", "store__owner"
        ),
        pk=quotation_id,
        material_request__buyer=request.user,
    )
    material_request = quotation.material_request
    seller = quotation.store.owner

    with transaction.atomic():
        material_request = MaterialRequest.objects.get(pk=material_request.pk)
        quotation = SellerQuotation.objects.get(pk=quotation.pk)

        if quotation.status != "submitted":
            messages.info(request, "This quotation has already been processed.")
            return redirect(
                "community_request_detail", request_id=material_request.pk
            )

        if material_request.status != "open":
            messages.error(request, "This material request is no longer open.")
            return redirect(
                "community_request_detail", request_id=material_request.pk
            )

        quotation.status = "declined"
        quotation.save(update_fields=["status", "updated_at"])

        CommunityNotification.objects.create(
            recipient=seller,
            title="Your quotation was declined",
            message=(
                f"The buyer declined your quotation for "
                f"{material_request.material}."
            ),
            url=(
                f"/community/requests/{material_request.pk}/"
                f"#community-quotation-{quotation.pk}"
            ),
        )

    from .push_notifications import send_web_push

    send_web_push(
        [seller.pk],
        title="Quotation declined",
        body=f"Your quotation for {material_request.material} was declined.",
        url=(
            f"/community/requests/{material_request.pk}/"
            f"#community-quotation-{quotation.pk}"
        ),
    )

    messages.success(request, "The quotation has been declined.")
    return redirect("community_request_detail", request_id=material_request.pk)




@login_required
def material_request_close(request, request_id):
    if request.method != "POST":
        return redirect("community")

    material_request = get_object_or_404(
        MaterialRequest, pk=request_id, buyer=request.user
    )
    if material_request.status == "open":
        material_request.status = "fulfilled"
        material_request.save(update_fields=["status"])
        messages.success(request, "Your material request has been marked fulfilled.")
    else:
        messages.info(request, "This request is no longer open.")

    return redirect(f"/community/?state={material_request.state}")



@login_required
def community_notification_updates(request):
    """Return only this user's new notifications for live in-app alerts."""
    try:
        after_id = max(0, int(request.GET.get("after", "0")))
    except (TypeError, ValueError):
        after_id = 0

    updates = CommunityNotification.objects.filter(
        recipient=request.user,
        pk__gt=after_id,
    ).order_by("pk")[:20]

    latest_id = after_id
    items = []
    for notification in updates:
        latest_id = max(latest_id, notification.pk)
        items.append({
            "id": notification.pk,
            "title": notification.title,
            "message": notification.message,
            "url": notification.url or "/community/notifications/",
            "created_at": notification.created_at.isoformat(),
        })

    unread_count = CommunityNotification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return JsonResponse({
        "notifications": items,
        "latest_id": latest_id,
        "unread_count": unread_count,
    })

@login_required
def community_notifications(request):
    status = request.GET.get("status", "all")
    if status not in {"all", "unread", "read"}:
        status = "all"

    notifications = CommunityNotification.objects.filter(
        recipient=request.user
    )

    if status == "unread":
        notifications = notifications.filter(is_read=False)
    elif status == "read":
        notifications = notifications.filter(is_read=True)

    notifications = notifications[:100]

    unread_count = CommunityNotification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return render(request, "market/community_notifications.html", {
        "notifications": notifications,
        "notification_status": status,
        "notification_unread_count": unread_count,
    })


@login_required
def community_notification_read(request, notification_id):
    if request.method != "POST":
        return redirect("community_notifications")

    notification = get_object_or_404(
        CommunityNotification,
        pk=notification_id,
        recipient=request.user,
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("community_notifications")


@login_required
def community_post_create(request):
    if request.method != "POST":
        return redirect("community")

    form = CommunityPostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        _save_gallery_images(
            post,
            form.cleaned_data.get("gallery_images", []),
            CommunityPostGalleryImage,
            "post",
        )
        messages.success(request, "Your community post has been published.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect("community")


@login_required
def community_post_edit(request, post_id):
    post = get_object_or_404(CommunityPost, pk=post_id, author=request.user)

    if request.method == "POST":
        form = CommunityPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            _save_gallery_images(
                post,
                form.cleaned_data.get("gallery_images", []),
                CommunityPostGalleryImage,
                "post",
            )
            messages.success(request, "Your community post has been updated.")
            return redirect("community")
    else:
        form = CommunityPostForm(instance=post)

    return render(request, "market/community_post_edit.html", {
        "form": form,
        "post": post,
    })


@login_required
def community_post_delete(request, post_id):
    if request.method != "POST":
        return redirect("community")

    post = get_object_or_404(CommunityPost, pk=post_id, author=request.user)
    if post.photo:
        post.photo.delete(save=False)
    post.delete()
    messages.success(request, "Your community post has been deleted.")
    return redirect("community")


# BuildSpot community social actions.
@login_required
def community_comment_create(request, post_id):
    if request.method != "POST":
        return redirect("community")

    post = get_object_or_404(CommunityPost, pk=post_id)
    body = request.POST.get("body", "").strip()

    if not body:
        messages.error(request, "Please enter a comment.")
    elif len(body) > 2000:
        messages.error(request, "Comments must be 2,000 characters or fewer.")
    else:
        comment = CommunityComment.objects.create(
            post=post, author=request.user, body=body
        )
        if post.author_id != request.user.id:
            CommunityNotification.objects.create(
                recipient=post.author,
                title="New comment on your community post",
                message=f"{request.user.username} commented on your post.",
                url=f"/community/#community-comment-{comment.pk}",
            )
        messages.success(request, "Your comment has been added.")

    return redirect(f"/community/#community-post-{post.pk}")


@login_required
def community_comment_reply(request, comment_id):
    if request.method != "POST":
        return redirect("community")

    parent = get_object_or_404(
        CommunityComment.objects.select_related("post", "author"),
        pk=comment_id,
    )
    post = parent.post
    body = request.POST.get("body", "").strip()

    if not body:
        messages.error(request, "Please enter a reply.")
    elif len(body) > 2000:
        messages.error(request, "Replies must be 2,000 characters or fewer.")
    else:
        reply = CommunityComment.objects.create(
            post=post,
            author=request.user,
            parent=parent,
            body=body,
        )
        recipients = {parent.author_id}
        if post.author_id != request.user.id:
            recipients.add(post.author_id)
        recipients.discard(request.user.id)

        for recipient_id in recipients:
            recipient = (
                parent.author if recipient_id == parent.author_id
                else post.author
            )
            CommunityNotification.objects.create(
                recipient=recipient,
                title="New reply in the community",
                message=f"{request.user.username} replied to a comment.",
                url=f"/community/#community-reply-{reply.pk}",
            )
        messages.success(request, "Your reply has been added.")

    return redirect(f"/community/#community-post-{post.pk}")


@login_required
def community_post_react(request, post_id):
    if request.method != "POST":
        return redirect("community")

    post = get_object_or_404(CommunityPost, pk=post_id)
    reaction, created = CommunityPostReaction.objects.get_or_create(
        post=post, user=request.user
    )

    if not created:
        reaction.delete()
        messages.success(request, "Your reaction has been removed.")
    else:
        if post.author_id != request.user.id:
            CommunityNotification.objects.create(
                recipient=post.author,
                title="Someone liked your community post",
                message=f"{request.user.username} liked your post.",
                url=f"/community/#community-post-{post.pk}",
            )
        messages.success(request, "You liked this post.")

    return redirect(f"/community/#community-post-{post.pk}")


@login_required
def community_comment_react(request, comment_id):
    if request.method != "POST":
        return redirect("community")

    comment = get_object_or_404(
        CommunityComment.objects.select_related("post", "author"),
        pk=comment_id,
    )
    reaction, created = CommunityCommentReaction.objects.get_or_create(
        comment=comment, user=request.user
    )

    if not created:
        reaction.delete()
        messages.success(request, "Your comment reaction has been removed.")
    else:
        if comment.author_id != request.user.id:
            CommunityNotification.objects.create(
                recipient=comment.author,
                title="Someone liked your comment",
                message=f"{request.user.username} liked your comment.",
                url=(
                    f"/community/#community-reply-{comment.pk}"
                    if comment.parent_id
                    else f"/community/#community-comment-{comment.pk}"
                ),
            )
        messages.success(request, "You liked this comment.")

    return redirect(f"/community/#community-post-{comment.post_id}")


def push_vapid_public_key(request):
    """Return only the public VAPID key to the browser."""
    key_file = Path.home() / ".buildspot-vapid" / "public.txt"
    try:
        public_key = key_file.read_text().strip()
    except OSError:
        return JsonResponse({"error": "Push notifications are not configured."}, status=503)
    if not public_key:
        return JsonResponse({"error": "Push notifications are not configured."}, status=503)
    return JsonResponse({"publicKey": public_key})


@login_required
@require_POST
def push_subscribe(request):
    """Save the current user's browser push subscription."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh = keys["p256dh"]
        auth = keys["auth"]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid subscription data."}, status=400)

    if not all(isinstance(v, str) and v for v in (endpoint, p256dh, auth)):
        return JsonResponse({"error": "Incomplete subscription data."}, status=400)
    if not endpoint.startswith("https://") or len(endpoint) > 2000:
        return JsonResponse({"error": "Invalid push endpoint."}, status=400)

    subscription, created = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": request.user, "p256dh": p256dh, "auth": auth},
    )
    return JsonResponse({"ok": True, "created": created})


@login_required
@require_POST
def push_unsubscribe(request):
    """Remove this endpoint only if it belongs to the logged-in user."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        endpoint = data["endpoint"]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid endpoint data."}, status=400)

    if not isinstance(endpoint, str) or not endpoint:
        return JsonResponse({"error": "Endpoint is required."}, status=400)

    deleted, _ = PushSubscription.objects.filter(
        user=request.user, endpoint=endpoint
    ).delete()
    return JsonResponse({"ok": True, "deleted": bool(deleted)})


@login_required
def my_favourites(request):
    saved_products = SavedProduct.objects.filter(
        user=request.user,
        product__available=True,
        product__store__is_active=True,
    ).select_related("product", "product__store", "product__category")

    saved_stores = SavedStore.objects.filter(
        user=request.user,
        store__is_active=True,
    ).select_related("store")

    return render(
        request,
        "market/my_favourites.html",
        {
            "saved_products": saved_products,
            "saved_stores": saved_stores,
        },
    )


@login_required
@require_POST
def toggle_saved_product(request, product_id):
    product = get_object_or_404(
        Product, pk=product_id, available=True, store__is_active=True
    )
    saved, created = SavedProduct.objects.get_or_create(
        user=request.user, product=product
    )
    if not created:
        saved.delete()
        messages.success(request, "Product removed from your favourites.")
    else:
        messages.success(request, "Product saved to your favourites.")
    return redirect("my_favourites")


@login_required
@require_POST
def toggle_saved_store(request, store_id):
    store = get_object_or_404(Store, pk=store_id, is_active=True)
    saved, created = SavedStore.objects.get_or_create(
        user=request.user, store=store
    )
    if not created:
        saved.delete()
        messages.success(request, "Store removed from your favourites.")
    else:
        messages.success(request, "Store saved to your favourites.")
    return redirect("my_favourites")


def buildspot_custom_404(request, exception=None):
    """Render BuildSpot's branded page for unavailable pages and requests."""
    from django.shortcuts import render
    return render(request, "404.html", status=404)
