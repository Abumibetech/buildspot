from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.utils.text import slugify
from .models import Store, Product, Category, Advertisement, Enquiry
from .forms import SellerSignupForm, StoreForm, ProductForm, EnquiryForm

def home(request):
    ads=Advertisement.objects.filter(active=True, placement="home")
    stores=Store.objects.filter(is_active=True).annotate(product_count=Count("products", filter=Q(products__available=True))).order_by("-created_at")[:6]
    products=Product.objects.filter(available=True, store__is_active=True).select_related("store")[:8]
    return render(request,"market/home.html",{"ads":ads,"stores":stores,"products":products})

def market_list(request):
    stores=Store.objects.filter(is_active=True).select_related("owner").annotate(product_count=Count("products", filter=Q(products__available=True))).distinct()
    q=request.GET.get("q","").strip(); state=request.GET.get("state","").strip(); city=request.GET.get("city","").strip()
    if q: stores=stores.filter(Q(business_name__icontains=q)|Q(description__icontains=q)|Q(products__name__icontains=q)|Q(products__category__name__icontains=q)).distinct()
    if state: stores=stores.filter(state__icontains=state)
    if city: stores=stores.filter(city__icontains=city)
    return render(request,"market/market.html",{"stores":stores,"q":q,"state":state,"city":city,"ads":Advertisement.objects.filter(active=True,placement="market")})

def store_detail(request, slug):
    store=get_object_or_404(Store,slug=slug,is_active=True)
    products=store.products.filter(available=True).select_related("category")
    form=EnquiryForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        enquiry=form.save(commit=False); enquiry.store=store
        pid=request.POST.get("product_id")
        if pid: enquiry.product=Product.objects.filter(pk=pid,store=store).first()
        enquiry.save();
        if store.owner.email:
            send_mail(f"New BuildSpot enquiry for {store.business_name}", f"Buyer: {enquiry.buyer_name}\nEmail: {enquiry.buyer_email}\nPhone: {enquiry.buyer_phone}\nProduct: {enquiry.product or 'General enquiry'}\nQuantity: {enquiry.quantity}\nDelivery location: {enquiry.delivery_location}\n\n{enquiry.message}", None, [store.owner.email], fail_silently=True)
        messages.success(request,"Your request has been sent to the seller. They can contact you using the details you provided."); return redirect(store.get_absolute_url())
    return render(request,"market/store_detail.html",{"store":store,"products":products,"form":form,"ads":Advertisement.objects.filter(active=True,placement="store")})

def signup(request):
    form = SellerSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
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
            email=user.email,
            state=form.cleaned_data["state"],
            city=form.cleaned_data["city"],
            address=form.cleaned_data["address"],
        )
        login(request, user)
        messages.success(
            request,
            "Your seller account and store are ready. You can now add products."
        )
        return redirect("seller_dashboard")
    return render(request, "market/signup.html", {"form": form})


@login_required
def seller_dashboard(request):
    store=Store.objects.filter(owner=request.user).first()
    if not store:
        messages.info(request,"Create a seller profile to manage your store."); return redirect("signup")
    if request.method=="POST":
        form=StoreForm(request.POST,request.FILES,instance=store)
        if form.is_valid(): form.save(); messages.success(request,"Store profile updated."); return redirect("seller_dashboard")
    else: form=StoreForm(instance=store)
    return render(request,"market/dashboard.html",{"store":store,"form":form,"products":store.products.all(),"enquiries":store.enquiries.select_related("product")[:20]})

@login_required
def product_add(request):
    store=get_object_or_404(Store,owner=request.user)
    form=ProductForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        product=form.save(commit=False); product.store=store; product.slug=slugify(product.name); base=product.slug or "product"; slug=base; i=2
        while Product.objects.filter(store=store,slug=slug).exists(): slug=f"{base}-{i}"; i+=1
        product.slug=slug; product.save(); messages.success(request,"Product added to your showroom."); return redirect("seller_dashboard")
    return render(request,"market/product_form.html",{"form":form,"heading":"Add a product"})

@login_required
def product_edit(request, pk):
    store=get_object_or_404(Store,owner=request.user); product=get_object_or_404(Product,pk=pk,store=store)
    form=ProductForm(request.POST or None,request.FILES or None,instance=product)
    if request.method=="POST" and form.is_valid(): form.save(); messages.success(request,"Product updated."); return redirect("seller_dashboard")
    return render(request,"market/product_form.html",{"form":form,"heading":"Edit product"})

@login_required
def product_delete(request, pk):
    store=get_object_or_404(Store,owner=request.user); product=get_object_or_404(Product,pk=pk,store=store)
    if request.method=="POST": product.delete(); messages.success(request,"Product deleted.")
    return redirect("seller_dashboard")

def product_detail(request, store_slug, product_slug):
    store=get_object_or_404(Store,slug=store_slug,is_active=True); product=get_object_or_404(Product,store=store,slug=product_slug,available=True)
    form=EnquiryForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        enquiry=form.save(commit=False); enquiry.store=store; enquiry.product=product; enquiry.save();
        if store.owner.email:
            send_mail(f"New BuildSpot enquiry for {product.name}", f"Buyer: {enquiry.buyer_name}\nEmail: {enquiry.buyer_email}\nPhone: {enquiry.buyer_phone}\nQuantity: {enquiry.quantity}\nDelivery location: {enquiry.delivery_location}\n\n{enquiry.message}", None, [store.owner.email], fail_silently=True)
        messages.success(request,"Your product enquiry has been sent."); return redirect(product_detail_url(store,product))
    return render(request,"market/product_detail.html",{"store":store,"product":product,"form":form})

def product_detail_url(store, product):
    from django.urls import reverse
    return reverse("product_detail",args=[store.slug,product.slug])
