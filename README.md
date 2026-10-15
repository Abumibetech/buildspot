# BuildSpot — Django Building Materials Marketplace

A responsive Django marketplace for building-material sellers in Nigeria. Includes public store discovery, digital showrooms, product catalogue uploads, buyer enquiries, seller dashboard, admin-managed advertisements, theme toggle and PWA shell.

## Requirements
- Python 3.10+ (recommended Python 3.12)

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations market
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000. Admin is at `/admin/`.

## Main workflows
- Buyers choose **EXPLORE MARKET**, search stores by product/store name, state or city, then open a store's public showroom.
- Buyers can send product-specific or general enquiries. These appear in the seller dashboard and Django admin. Email backend is console by default; seller notification is currently in-dashboard/admin rather than push/email.
- Sellers choose **Open a store**, register, update their business details, upload product images and optional video URLs, manage availability and review enquiries.
- Admins manage categories, stores, verification, products, enquiries, and advertisements in Django admin.

## Production notes
This project is a working foundation, but a production launch still requires deployment-specific environment variables, a strong `SECRET_KEY`, `DEBUG=False`, HTTPS, PostgreSQL configuration, email delivery, backups, image/video storage policy, spam protection/rate limiting, privacy/terms pages, and security review. For production, configure `ALLOWED_HOSTS` and database settings in `buildspot/settings.py`; the included default database is SQLite for local development. Video upload is via external video URL; product photos upload to media storage.

## Admin advertisements
Create an Advertisement in Django admin, upload a banner image, enter its destination URL, choose homepage/market/store placement, set start/end dates as needed, and activate it. (Current placement filters active flag; add date-window filtering before a paid campaign launch.)
