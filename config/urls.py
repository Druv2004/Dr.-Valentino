from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

admin.site.site_header = "Dr. Valentino site admin"
admin.site.site_title = "Site admin"
admin.site.index_title = "Manage website content"

urlpatterns = [
    path("dj-admin/", admin.site.urls),  # Django's built-in admin (superuser only; the Control Center is the main dashboard)
    path("admin/", RedirectView.as_view(url="/dashboard/")),
    path("", include("core.dash_urls")),
    path("", include("core.urls")),
]
# Uploaded files (videos, slides, PDFs). Served by Django so uploads also work with DEBUG off;
# for heavy traffic, serve /media/ from your web server or object storage instead.
urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

handler404 = "core.dashboard.not_found"
