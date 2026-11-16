"""Automatic BuildSpot Daily Inspiration content."""

from django.templatetags.static import static
from django.utils import timezone


QUOTES = [
    ("Every great building begins with a clear vision and a strong foundation.", "Vision & Foundations"),
    ("Build with patience today, and your work will stand with pride tomorrow.", "Patience & Progress"),
    ("Quality materials are an investment in the strength of tomorrow.", "Quality & Materials"),
    ("A strong foundation is never wasted effort.", "Building Strong"),
    ("Great projects are built one thoughtful decision at a time.", "Planning & Progress"),
    ("The best time to build a better future is the day you decide to begin.", "New Beginnings"),
    ("Good craftsmanship turns ordinary materials into lasting value.", "Craftsmanship"),
    ("Measure carefully, plan wisely, and build confidently.", "Planning & Precision"),
    ("A successful project starts long before the first block is laid.", "Project Planning"),
    ("Strong structures begin with strong decisions.", "Smart Decisions"),
    ("Do today's work with tomorrow's durability in mind.", "Durability"),
    ("Every finished project is proof that consistent effort works.", "Consistency"),
    ("Build something that your future self will be proud of.", "Purpose"),
    ("The right materials make a meaningful difference to every project.", "Choosing Materials"),
    ("Progress is made when preparation meets determination.", "Determination"),
    ("A reliable supplier can help turn a building plan into reality.", "Reliable Partnerships"),
    ("Don't rush the foundation; build the strength your vision deserves.", "Strong Foundations"),
    ("Great results come from attention to the smallest details.", "Attention to Detail"),
    ("A well-planned project saves time, money, and unnecessary stress.", "Smart Planning"),
    ("Build responsibly. Choose quality. Create lasting value.", "Responsible Building"),
    ("Every expert was once someone willing to learn and improve.", "Learning & Growth"),
    ("A better building journey begins with better information.", "Knowledge"),
    ("Consistency is the quiet strength behind every successful project.", "Consistency"),
    ("Your ambition deserves a solid plan and dependable materials.", "Ambition"),
    ("Build beyond today; think about the generations who may use it.", "Building for Tomorrow"),
    ("A good team, good materials, and good planning make a powerful combination.", "Teamwork"),
    ("Every challenge on a project is an opportunity to build smarter.", "Problem Solving"),
    ("Let your standards be as strong as the structures you create.", "High Standards"),
    ("The strongest results come from doing the basics exceptionally well.", "Excellence"),
    ("A building is more than materials; it is a vision made real.", "Vision"),
    ("Make every measurement count and every material serve a purpose.", "Precision"),
    ("Smart sourcing is one of the first steps towards a successful build.", "Smart Sourcing"),
    ("Take pride in the work people may depend on for years to come.", "Pride in Work"),
    ("A solid plan turns a big dream into manageable steps.", "Planning"),
    ("Keep learning, keep improving, and keep building.", "Growth"),
    ("The quality of your work is the legacy you leave behind.", "Legacy"),
    ("Build with integrity, even when nobody is watching.", "Integrity"),
    ("Great things take shape when people commit to doing things well.", "Commitment"),
    ("Today's careful choices can prevent tomorrow's costly repairs.", "Wise Choices"),
    ("Your next great project can begin with one confident step.", "Take the First Step"),
]


IMAGES = [
    "img/materials-showcase.jpg",
    "img/supplier-network-showroom.webp",
    "img/category-cement.webp",
    "img/category-tiles.webp",
    "img/category-roofing.webp",
    "img/category-plumbing.webp",
    "img/bathroom-fixtures.jpg",
    "img/decorative-tiles.jpg",
]


def get_daily_inspiration():
    """Return a stable daily quote and image using the configured local date."""
    today = timezone.localdate()
    day_number = today.toordinal()

    quote, theme = QUOTES[day_number % len(QUOTES)]
    image = IMAGES[day_number % len(IMAGES)]

    return {
        "date": today.isoformat(),
        "display_date": today.strftime("%A, %d %B %Y"),
        "quote": quote,
        "theme": theme,
        "image": static(image),
    }
