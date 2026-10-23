from .models import SiteSettings

NAV = [("home", "Home"), ("about", "About"), ("publications", "Publications"), ("presentations", "Presentations"),
       ("projects", "Projects"), ("organizations", "Organizations"), ("resources", "Resources"), ("contact", "Contact")]


def site(request):
    return {"site": SiteSettings.get(), "nav_items": NAV,
            "current": request.resolver_match.url_name if request.resolver_match else ""}
