from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    path("push/unsubscribe/", views.push_unsubscribe, name="push_unsubscribe"),
    path("push/subscribe/", views.push_subscribe, name="push_subscribe"),
    path("push/vapid-public-key/", views.push_vapid_public_key, name="push_vapid_public_key"),
    path("people/<int:user_id>/", views.public_profile, name="public_profile"),
    path("community/notifications/updates/", views.community_notification_updates, name="community_notification_updates"),

    path("community/", views.community, name="community"),
    path("community/posts/new/", views.community_post_create, name="community_post_create"),
    path("community/posts/<int:post_id>/edit/", views.community_post_edit, name="community_post_edit"),
    path("community/posts/<int:post_id>/delete/", views.community_post_delete, name="community_post_delete"),
    path("community/posts/<int:post_id>/comment/", views.community_comment_create, name="community_comment_create"),
    path("community/posts/<int:post_id>/react/", views.community_post_react, name="community_post_react"),
    path("community/comments/<int:comment_id>/reply/", views.community_comment_reply, name="community_comment_reply"),
    path("community/comments/<int:comment_id>/react/", views.community_comment_react, name="community_comment_react"),
    path("community/requests/<int:request_id>/", views.material_request_detail, name="community_request_detail"),
    path("community/requests/new/", views.material_request_create, name="community_request_create"),
    path("community/requests/<int:request_id>/close/", views.material_request_close, name="community_request_close"),
    path("community/notifications/", views.community_notifications, name="community_notifications"),
    path("community/notifications/<int:notification_id>/read/", views.community_notification_read, name="community_notification_read"),path("",views.home,name="home"),path("market/",views.market_list,name="market"),path("buyer/join/",views.buyer_signup,name="buyer_signup"),path("seller/join/",views.signup,name="signup"),path("seller/dashboard/",views.seller_dashboard,name="seller_dashboard"),path("seller/profile/",views.store_profile,name="store_profile"),path("seller/products/add/",views.product_add,name="product_add"),path("seller/products/<int:pk>/edit/",views.product_edit,name="product_edit"),path("seller/products/<int:pk>/delete/",views.product_delete,name="product_delete"),path("login/",views.BuildSpotLoginView.as_view(template_name="market/login.html"),name="login"),path("logout/",auth_views.LogoutView.as_view(),name="logout"),path("stores/<slug:slug>/",views.store_detail,name="store_detail"),path("stores/<slug:store_slug>/products/<slug:product_slug>/",views.product_detail,name="product_detail")]
