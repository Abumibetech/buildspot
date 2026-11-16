from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [

    path("about/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "About BuildSpot",
            "page_intro": "A marketplace designed to make discovering building materials and suppliers simpler.",
            "sections": [
                {"heading": "What is BuildSpot?", "paragraphs": [
                    "BuildSpot is an online marketplace that helps people discover building-materials suppliers and explore products offered by stores.",
                    "The platform brings store information, product listings and building-related community features together in one place."
                ]},
                {"heading": "What you can do on BuildSpot", "items": [
                    "Explore stores and browse building-materials listings.",
                    "View product descriptions, images and prices where supplied by sellers.",
                    "Contact stores about products and availability.",
                    "Create material requests and receive responses from participating suppliers.",
                    "Save stores and products for later.",
                    "Participate in the Materials Community."
                ]},
                {"heading": "For buyers", "paragraphs": [
                    "Buyers can use BuildSpot to discover suppliers, compare the information made available by stores and contact sellers directly. Buyers should confirm prices, product specifications, stock availability, delivery arrangements and payment terms with the seller before making a purchase."
                ]},
                {"heading": "For sellers", "paragraphs": [
                    "Businesses can create a store presence and publish product information to help potential customers discover their offerings. Sellers are responsible for ensuring that their store details, product descriptions, prices and contact information are accurate and up to date."
                ]},
                {"heading": "Our approach", "paragraphs": [
                    "We aim to provide a useful, accessible and straightforward online marketplace for the building industry. BuildSpot continues to improve its features and user experience."
                ]}
            ]
        }), name="about"),
    path("contact/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "Contact BuildSpot",
            "page_intro": "Have a question, feedback or concern? Contact BuildSpot through our official Facebook, Instagram, TikTok or email channels.",
            "sections": [
                {"heading": "Official customer contact", "paragraphs": [
                    "For general questions, feedback, account-related concerns or assistance using BuildSpot, contact our team through our official Facebook or Instagram pages, TikTok account or email address."
                ]},
                {"heading": "When contacting us", "items": [
                    "Describe your question or concern clearly.",
                    "Include the relevant store, product or page link where applicable.",
                    "Do not send passwords, payment card details or other sensitive login information.",
                    "For privacy-related requests, clearly state that your message concerns personal information or privacy."
                ]},
                {"heading": "Marketplace transactions", "paragraphs": [
                    "For questions about a particular product, price, order, delivery or payment, buyers should also contact the relevant seller directly using the contact details provided on that seller's store page."
                ]}
            ]
        }), name="contact"),
    path("privacy-policy/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "Privacy Policy",
            "page_intro": "This policy explains how BuildSpot handles information when people visit or use the marketplace.",
            "sections": [
                {"heading": "Information you provide", "paragraphs": [
                    "Depending on how you use BuildSpot, information may include account and registration details, store names and business details, contact information, location details, product listings, enquiries, material requests, photographs, community posts, comments and messages submitted through the platform."
                ]},
                {"heading": "Information generated through use", "paragraphs": [
                    "The platform may process information about saved stores and products, recently viewed listings, notifications, browser push-notification subscriptions and interactions with marketplace features. Technical information may also be processed to operate, protect and troubleshoot the website."
                ]},
                {"heading": "How information is used", "items": [
                    "To create and maintain accounts and store pages.",
                    "To display products, stores and community contributions.",
                    "To help buyers and sellers communicate about products and material requests.",
                    "To provide saved-item features and notifications.",
                    "To maintain website security, prevent misuse and improve platform performance.",
                    "To understand website usage and improve the user experience."
                ]},
                {"heading": "Information visible to other users", "paragraphs": [
                    "Store names, business descriptions, store locations, seller contact details, product listings and other information published on public pages may be visible to visitors.",
                    "Information submitted in an enquiry or material request may be made available to the relevant store or participating sellers so they can respond. Think carefully before publishing personal information in public posts or uploading photographs."
                ]},
                {"heading": "Cookies and analytics", "paragraphs": [
                    "BuildSpot uses browser technologies such as cookies where needed for website functions, including account sessions and security protections.",
                    "BuildSpot also uses Google Analytics, which may use cookies or similar technologies to help understand how visitors use the website. You can review Google's information about how it uses data from sites and apps that use its services."
                ]},
                {"heading": "Advertising and third-party services", "paragraphs": [
                    "BuildSpot uses Google advertising code and may display advertisements from Google AdSense when advertising is approved and enabled. When advertisements are served, Google and other third-party vendors may use cookies or similar technologies to serve ads, measure advertising performance, limit repeated advertisements and, depending on applicable settings, provide personalised advertising.",
                    "Third-party vendors, including Google, may use cookies to serve advertisements based on a visitor's previous visits to BuildSpot or other websites. In connection with ad serving, these providers may place and read cookies on a visitor's browser or use web beacons, IP addresses and other identifiers as described in their privacy policies.",
                    "Visitors can manage or opt out of personalised advertising by visiting Google Ads Settings at https://adssettings.google.com/. Visitors can also find information about opting out of some third-party vendors' personalised advertising cookies at https://www.aboutads.info/.",
                    "For more information about how Google uses information from websites that use its services, visit https://policies.google.com/technologies/partner-sites. The website may also link to other third-party services whose privacy practices are governed by their own policies."
                ]},
                {"heading": "Notifications", "paragraphs": [
                    "If you choose to enable browser push notifications, the browser may provide a push subscription that allows the website to deliver notifications. You can manage or revoke notification permission through your browser or device settings."
                ]},
                {"heading": "Data security and retention", "paragraphs": [
                    "We use reasonable measures intended to protect information handled by the platform. No website or internet transmission can be guaranteed to be completely secure.",
                    "Information may be retained for as long as needed to operate the service, maintain accounts and records, address disputes, protect the platform or meet applicable obligations. Actual retention depends on the type of information and the circumstances."
                ]},
                {"heading": "Your choices and privacy requests", "paragraphs": [
                    "You can choose what information you submit and can manage browser cookies and notification permissions through your device or browser. You may contact BuildSpot to ask about personal information associated with your use of the platform or to request an appropriate correction or deletion, subject to applicable requirements and legitimate record-keeping needs."
                ]},
                {"heading": "Children's privacy", "paragraphs": [
                    "BuildSpot is intended for people using an online marketplace responsibly. If you believe a child has submitted personal information to the platform, contact us so the concern can be reviewed."
                ]},
                {"heading": "Changes to this policy", "paragraphs": [
                    "This policy may be updated when the website, its features or its data practices change. The latest version will be published on this page."
                ]}
            ]
        }), name="privacy_policy"),
    path("terms/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "Terms of Use",
            "page_intro": "These terms explain the basic rules for accessing and using BuildSpot.",
            "sections": [
                {"heading": "Using the platform", "paragraphs": [
                    "By accessing or using BuildSpot, you agree to use the website lawfully and responsibly. Do not interfere with the operation or security of the platform or attempt to access accounts or information without permission."
                ]},
                {"heading": "Accounts and information", "paragraphs": [
                    "You are responsible for keeping your account credentials secure and for the accuracy of information you submit. Do not impersonate another person or create misleading business or product information."
                ]},
                {"heading": "Marketplace role", "paragraphs": [
                    "BuildSpot provides an online platform for discovering stores, viewing product listings and facilitating communication between users. Unless expressly stated otherwise, BuildSpot is not the seller of products listed by independent stores and is not a party to transactions between buyers and sellers.",
                    "Sellers are responsible for their products, prices, stock, descriptions, representations, delivery arrangements and fulfilment. Buyers should independently confirm important details with sellers before paying or placing an order."
                ]},
                {"heading": "Listings and user content", "paragraphs": [
                    "Users must only publish content they are entitled to share. Listings and community contributions must be accurate, lawful and relevant. BuildSpot may review, restrict or remove content that breaches these terms or creates a risk to users or the platform."
                ]},
                {"heading": "Prohibited conduct", "items": [
                    "Fraud, scams, impersonation or deceptive business practices.",
                    "False, misleading or unauthorised product listings.",
                    "Harassment, threats, hate speech or abusive conduct.",
                    "Spam, malicious links or attempts to compromise accounts.",
                    "Content that infringes another person's rights or violates applicable law."
                ]},
                {"heading": "Third-party services and links", "paragraphs": [
                    "The website may link to external websites or services. BuildSpot does not control those services and users should review their terms and policies before using them."
                ]},
                {"heading": "Changes and availability", "paragraphs": [
                    "Features may be updated, suspended or changed as the platform develops. We aim to keep the website available but do not guarantee uninterrupted or error-free operation."
                ]},
                {"heading": "Contact", "paragraphs": [
                    "Questions about these terms can be sent through the official BuildSpot contact page linked below."
                ]}
            ]
        }), name="terms"),
    path("seller-guidelines/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "Seller Guidelines",
            "page_intro": "Clear, accurate store and product information helps buyers make informed decisions.",
            "sections": [
                {"heading": "Provide truthful business details", "items": [
                    "Use your genuine business or trading name.",
                    "Provide accurate contact details and business location information.",
                    "Keep your store description and profile information current.",
                    "Do not impersonate another business or claim an affiliation you do not have."
                ]},
                {"heading": "Create accurate product listings", "items": [
                    "Use clear product names and relevant descriptions.",
                    "Upload images that represent the actual product being offered.",
                    "Keep prices, units, discounts and availability accurate.",
                    "Explain important specifications, sizes, brands and conditions where relevant.",
                    "Update or remove listings that are no longer available."
                ]},
                {"heading": "Communicate responsibly", "paragraphs": [
                    "Respond to enquiries professionally and provide clear information about payment, collection, delivery, warranties and other transaction terms. Do not request unnecessary sensitive personal or financial information."
                ]},
                {"heading": "Prohibited listings and behaviour", "paragraphs": [
                    "Do not publish fraudulent, illegal, counterfeit, deceptive or unauthorised listings. Do not manipulate reviews, misuse customer information, spam buyers or harass other users."
                ]},
                {"heading": "Seller responsibility", "paragraphs": [
                    "Sellers are responsible for the accuracy of their listings and for agreements they make directly with buyers. BuildSpot may restrict or remove listings or accounts that breach platform rules."
                ]}
            ]
        }), name="seller_guidelines"),
    path("community-guidelines/", TemplateView.as_view(
        template_name="market/info_page.html",
        extra_context={
            "page_title": "Community Guidelines",
            "page_intro": "Help make the BuildSpot Materials Community useful, respectful and relevant to the building industry.",
            "sections": [
                {"heading": "Be respectful", "paragraphs": [
                    "Treat other members with courtesy. Disagreement is acceptable; harassment, threats, intimidation and personal attacks are not."
                ]},
                {"heading": "Share useful and honest information", "items": [
                    "Keep posts relevant to building, materials, projects, suppliers and related topics.",
                    "Share accurate information and make it clear when something is an opinion.",
                    "Only upload photographs and content you have permission to share.",
                    "Avoid misleading claims, fake offers and impersonation."
                ]},
                {"heading": "No spam or harmful content", "paragraphs": [
                    "Do not use the community for repetitive advertising, scams, malicious links, illegal content, hate speech or the distribution of private information without permission."
                ]},
                {"heading": "Privacy and safety", "paragraphs": [
                    "Do not publish passwords, financial details, private addresses or another person's personal information without a lawful reason and permission. Be careful when arranging transactions or meeting people you first encountered online."
                ]},
                {"heading": "Moderation", "paragraphs": [
                    "Content that violates these guidelines may be removed or restricted. Accounts that repeatedly or seriously breach the rules may lose access to community features."
                ]}
            ]
        }), name="community_guidelines"),

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
    path("community/requests/<int:request_id>/quote/", views.quotation_create, name="community_quotation_create"),
    path("community/quotations/<int:quotation_id>/accept/", views.quotation_accept, name="community_quotation_accept"),
    path("community/quotations/<int:quotation_id>/decline/", views.quotation_decline, name="community_quotation_decline"),
    path("community/requests/new/", views.material_request_create, name="community_request_create"),
    path("community/requests/<int:request_id>/close/", views.material_request_close, name="community_request_close"),
    path("community/notifications/", views.community_notifications, name="community_notifications"),
    path("community/notifications/<int:notification_id>/read/", views.community_notification_read, name="community_notification_read"),path("",views.home,name="home"),path("market/",views.market_list,name="market"),path("deals/", views.todays_deals, name="todays_deals"),path("buyer/join/",views.buyer_signup,name="buyer_signup"),path("seller/join/",views.signup,name="signup"),path("seller/dashboard/",views.seller_dashboard,name="seller_dashboard"),path("seller/profile/",views.store_profile,name="store_profile"),
    path("seller/showroom/sections/add/", views.showroom_section_add, name="showroom_section_add"),
    path("seller/showroom/sections/<int:pk>/edit/", views.showroom_section_edit, name="showroom_section_edit"),
    path("seller/showroom/sections/<int:pk>/delete/", views.showroom_section_delete, name="showroom_section_delete"),
path("seller/products/add/",views.product_add,name="product_add"),path("seller/products/<int:pk>/edit/",views.product_edit,name="product_edit"),path("seller/products/<int:pk>/delete/",views.product_delete,name="product_delete"),path("login/",views.BuildSpotLoginView.as_view(template_name="market/login.html"),name="login"),path("logout/",auth_views.LogoutView.as_view(),name="logout"),path("stores/<slug:slug>/",views.store_detail,name="store_detail"),path("stores/<slug:store_slug>/products/<slug:product_slug>/",views.product_detail,name="product_detail")
,
    path("favourites/", views.my_favourites, name="my_favourites"),
    path("favourites/product/<int:product_id>/toggle/", views.toggle_saved_product, name="toggle_saved_product"),
    path("favourites/store/<int:store_id>/toggle/", views.toggle_saved_store, name="toggle_saved_store"),
]
