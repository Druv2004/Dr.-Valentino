from django.contrib import admin
from django.utils.html import format_html
from .models import (CareerEntry, ContactMessage, Organization, Presentation, Project, Publication, Resource, SiteSettings)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Home page", {"fields": ["full_name", "short_title", "tagline", "hero_headline", "hero_intro", "pull_quote", "photo"]}),
        ("About page", {"fields": ["bio", "cv_file"]}),
        ("Contact details", {"fields": ["phone", "email_primary", "email_secondary", "office_name", "office_address",
                                        "academic_name", "academic_address", "academic_phone"]}),
        ("Profiles", {"fields": ["orcid_url", "pubmed_url", "linkedin_url", "researchgate_url"]}),
        ("Numbers shown on Home", {"fields": ["h_index", "peer_reviewed_total"]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        obj = SiteSettings.get()
        return redirect("admin:core_sitesettings_change", obj.pk)


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ["short_title", "year", "kind", "topic", "featured", "has_pdf"]
    list_filter = ["kind", "topic", "featured", "year"]
    search_fields = ["title", "authors", "journal"]
    list_editable = ["featured"]
    list_per_page = 50

    @admin.display(description="Title")
    def short_title(self, o):
        return o.title[:100]

    @admin.display(boolean=True, description="PDF")
    def has_pdf(self, o):
        return bool(o.pdf)


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ["short_title", "year", "kind", "has_media", "featured"]
    list_filter = ["kind", "featured", "year"]
    search_fields = ["title", "event"]
    list_editable = ["featured"]
    list_per_page = 50

    @admin.display(description="Title")
    def short_title(self, o):
        return o.title[:100]

    @admin.display(boolean=True, description="Slides / video")
    def has_media(self, o):
        return bool(o.slides or o.video_file or o.video_url)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["short_title", "kind", "role", "start_year", "end_year", "ongoing", "featured"]
    list_filter = ["kind", "ongoing", "featured"]
    search_fields = ["title", "description", "role"]
    list_editable = ["ongoing", "featured"]
    list_per_page = 50

    @admin.display(description="Title")
    def short_title(self, o):
        return o.title[:100]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "period", "kind"]
    list_filter = ["kind"]
    search_fields = ["name", "role"]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "added", "featured", "has_file"]
    list_filter = ["kind", "featured"]
    search_fields = ["title", "description"]
    fieldsets = [
        (None, {"fields": ["title", "kind", "description", "added", "featured"]}),
        ("Content (use any one)", {"fields": ["file", "video_url", "external_url", "thumbnail"]}),
    ]

    @admin.display(boolean=True, description="Has content")
    def has_file(self, o):
        return bool(o.file or o.video_url or o.external_url)


@admin.register(CareerEntry)
class CareerEntryAdmin(admin.ModelAdmin):
    list_display = ["period", "title", "organization", "kind", "visible"]
    list_filter = ["kind", "visible"]
    search_fields = ["title", "organization"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "email", "topic", "handled"]
    list_filter = ["topic", "handled"]
    list_editable = ["handled"]
    readonly_fields = ["first_name", "last_name", "email", "topic", "message", "created"]

    @admin.display(description="From")
    def name(self, o):
        return f"{o.first_name} {o.last_name}"

    def has_add_permission(self, request):
        return False
