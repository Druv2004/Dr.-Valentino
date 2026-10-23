"""Control Center: the staff dashboard used to manage every part of the website.

Roles (see core.models.Profile):
  admin   - everything, including team accounts (superusers are always admin)
  manager - all content, site settings, message export, deletion
  editor  - add and edit content, work on messages. No deletion, settings or export
  viewer  - read-only
"""
import csv
import os

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import (CareerEntry, ContactMessage, Organization, Presentation, Profile, Project, Publication, Resource,
                     SiteSettings)

# ---------------------------------------------------------------- roles
CAN = {
    "view": {"admin", "manager", "editor", "viewer"},
    "edit": {"admin", "manager", "editor"},
    "delete": {"admin", "manager"},
    "settings": {"admin", "manager"},
    "export": {"admin", "manager"},
    "users": {"admin"},
}


def role_of(user):
    if user.is_superuser:
        return "admin"
    if not user.is_active:
        return "none"
    return getattr(getattr(user, "profile", None), "role", "viewer")


def deny_unless(request, action):
    if role_of(request.user) not in CAN[action]:
        return HttpResponseForbidden(render(request, "dashboard/forbidden.html", status=403).content)
    return None


def dash_context(request):
    r = role_of(request.user)
    return {"role": r, "role_label": dict(Profile.ROLES).get(r, "Viewer"),
            "can_edit": r in CAN["edit"], "can_delete": r in CAN["delete"], "can_settings": r in CAN["settings"],
            "can_export": r in CAN["export"], "can_users": r in CAN["users"],
            "new_messages": ContactMessage.objects.filter(handled=False).count()}


def page(request, template, ctx=None, status=200):
    c = dash_context(request)
    c.update(ctx or {})
    return render(request, template, c, status=status)


# ---------------------------------------------------------------- forms
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DOC_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".pps", ".ppsx", ".xls", ".xlsx", ".csv", ".txt", ".zip", ".key"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v"}
ALLOWED_EXT = IMAGE_EXT | DOC_EXT | VIDEO_EXT


class DashForm(forms.ModelForm):
    """ModelForm with friendly file inputs (current file + remove tick) and safe-extension checks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_names = []
        for name, f in list(self.fields.items()):
            if isinstance(f, forms.FileField):
                f.widget = forms.FileInput()
                f.current = getattr(self.instance, name, None) if self.instance.pk else None
                self.file_names.append(name)
                if f.current:
                    self.fields["clear__" + name] = forms.BooleanField(required=False, label="Remove the current file")
            elif isinstance(f.widget, forms.Textarea):
                f.widget.attrs.setdefault("rows", 4)
            if name == "kind":
                f.label = "Type"

    def clean(self):
        data = super().clean()
        for name in self.file_names:
            up = self.files.get(name)
            if up and os.path.splitext(up.name)[1].lower() not in ALLOWED_EXT:
                self.add_error(name, "This file type is not allowed. Use an image, PDF, Office document or MP4/WebM video.")
        return data

    def save(self, commit=True):
        for name in self.file_names:
            if self.cleaned_data.get("clear__" + name) and name not in self.files:
                setattr(self.instance, name, "")
        return super().save(commit)


def make_form(model, fields):
    class Meta:
        pass
    Meta.model, Meta.fields = model, fields
    return type(f"{model.__name__}DashForm", (DashForm,), {"Meta": Meta})


def groups_for(form, groups):
    """[(title, [(bound_field, clear_bound_field|None), ...]), ...]"""
    out = []
    for title, names in groups:
        rows = [(form[n], form["clear__" + n] if "clear__" + n in form.fields else None) for n in names]
        out.append((title, rows))
    return out


# ---------------------------------------------------------------- section configuration
SECTIONS = {
    "publications": dict(
        model=Publication, title="Publications", singular="publication", eyebrow="RESEARCH OUTPUT",
        blurb="Journal articles, invited reviews, books and chapters. Attach a PDF if the paper may be shared.",
        search=["title", "authors", "journal"], filters=[("kind", "All types", Publication.KINDS), ("topic", "All topics", Publication.TOPICS)],
        columns=[("Year", "year", False), ("Title", "title", True), ("Type", "kind", False), ("Topic", "topic", False), ("Home", "featured", False)],
        groups=[("Details", ["title", "authors", "journal", "year", "kind", "topic"]),
                ("Links and files", ["url", "pdf"]), ("Display", ["featured"])]),
    "presentations": dict(
        model=Presentation, title="Presentations", singular="presentation", eyebrow="TALKS AND LECTURES",
        blurb="Lectures, conference talks and webinars. Add slides, upload a video, or paste a YouTube/Vimeo link.",
        search=["title", "event"], filters=[("kind", "All types", Presentation.KINDS)],
        columns=[("Year", "year", False), ("Title", "title", True), ("Type", "kind", False), ("Slides / video", "has_media", False), ("Home", "featured", False)],
        groups=[("Details", ["title", "event", "year", "kind"]),
                ("Slides and video", ["slides", "video_file", "video_url"]), ("Display", ["featured"])]),
    "projects": dict(
        model=Project, title="Projects", singular="project", eyebrow="RESEARCH AND INITIATIVES",
        blurb="Current initiatives, laboratory and clinical research, and education programs.",
        search=["title", "description", "role"], filters=[("kind", "All types", Project.KINDS)],
        columns=[("Period", "period", False), ("Project", "title", True), ("Role", "role", False), ("Type", "kind", False), ("Active", "ongoing", False)],
        groups=[("Details", ["title", "role", "kind", "description"]),
                ("Dates", ["start_year", "end_year", "ongoing"]),
                ("Link, image and file", ["url", "image", "file"]), ("Display", ["featured"])]),
    "career": dict(
        model=CareerEntry, title="Experience and education", singular="entry", eyebrow="ABOUT PAGE",
        blurb="Career roles, education, academic appointments, board certification, honors and awards.",
        search=["title", "organization", "details"], filters=[("kind", "All types", CareerEntry.KINDS)],
        columns=[("Period", "period", False), ("Title", "title", True), ("Organization", "organization", False), ("Type", "kind", False), ("Shown", "visible", False)],
        groups=[("Details", ["kind", "period", "title", "organization", "details"]), ("Display", ["sort_year", "visible"])]),
    "organizations": dict(
        model=Organization, title="Organizations", singular="organization", eyebrow="AFFILIATIONS",
        blurb="Leadership roles, societies, journals and committees.",
        search=["name", "role", "description"], filters=[("kind", "All types", Organization.KINDS)],
        columns=[("Organization", "name", True), ("Role", "role", False), ("Period", "period", False), ("Type", "kind", False)],
        groups=[("Details", ["name", "kind", "role", "period", "description", "url"]), ("Display", ["sort_year"])]),
    "resources": dict(
        model=Resource, title="Videos and resources", singular="resource", eyebrow="DOWNLOAD CENTER",
        blurb="Videos, slide decks, documents and links shown on the Resources page.",
        search=["title", "description"], filters=[("kind", "All types", Resource.KINDS)],
        columns=[("Title", "title", True), ("Type", "kind", False), ("Content", "has_content", False), ("Added", "added", False), ("Featured", "featured", False)],
        groups=[("Details", ["title", "kind", "description", "added"]),
                ("Content (use any one)", ["file", "video_url", "external_url", "thumbnail"]), ("Display", ["featured"])]),
}
for _k, _c in SECTIONS.items():
    _c["key"] = _k
    _c["form"] = make_form(_c["model"], [n for _, names in _c["groups"] for n in names])

SETTINGS_GROUPS = [
    ("Home page", ["full_name", "short_title", "tagline", "hero_headline", "hero_intro", "pull_quote", "photo"]),
    ("About page", ["bio", "cv_file"]),
    ("Contact details", ["phone", "email_primary", "email_secondary", "office_name", "office_address",
                         "academic_name", "academic_address", "academic_phone"]),
    ("Profiles", ["orcid_url", "pubmed_url", "linkedin_url", "researchgate_url"]),
    ("Numbers on Home", ["h_index", "peer_reviewed_total"]),
]
SettingsForm = make_form(SiteSettings, [n for _, names in SETTINGS_GROUPS for n in names])


# ---------------------------------------------------------------- auth views
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
        if user and user.is_active:
            login(request, user)
            nxt = request.GET.get("next", "")
            ok = nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
            return redirect(nxt if ok else "dashboard")
        messages.error(request, "Incorrect username or password.")
    return render(request, "dashboard/login.html")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        messages.success(request, "Password changed.")
        return redirect("dashboard")
    return page(request, "dashboard/password.html", {"form": form})


# ---------------------------------------------------------------- overview
@login_required
def overview(request):
    ctx = {
        "stats": [("Publications", Publication.objects.count(), f"{Publication.objects.filter(kind='article').count()} journal articles", "▣"),
                  ("Presentations", Presentation.objects.count(), f"{Presentation.objects.filter(kind='lecture').count()} invited lectures", "◫"),
                  ("Videos and resources", Resource.objects.count(), (lambda n: f"{n} video{'' if n == 1 else 's'}")(Resource.objects.filter(kind='video').count()), "▶"),
                  ("New messages", ContactMessage.objects.filter(handled=False).count(), f"{ContactMessage.objects.count()} received in total", "✉")],
        "recent_messages": ContactMessage.objects.all()[:6],
        "recent_resources": Resource.objects.all()[:5],
        "quick": [("Add a video or resource", "dash_new", "resources"), ("Add a presentation", "dash_new", "presentations"),
                  ("Add a publication", "dash_new", "publications"), ("Add a project", "dash_new", "projects"),
                  ("Add experience or education", "dash_new", "career"), ("Add an organization", "dash_new", "organizations")],
    }
    return page(request, "dashboard/index.html", ctx)


# ---------------------------------------------------------------- generic CRUD
def _cfg(key):
    if key not in SECTIONS:
        raise Http404
    return SECTIONS[key]


@login_required
def section_list(request, key):
    cfg = _cfg(key)
    qs = cfg["model"].objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        cond = Q()
        for f in cfg["search"]:
            cond |= Q(**{f + "__icontains": q})
        qs = qs.filter(cond)
    active = {}
    for field, _label, choices in cfg["filters"]:
        v = request.GET.get(field, "")
        if v in dict(choices):
            qs = qs.filter(**{field: v})
            active[field] = v
    pg = Paginator(qs, 25).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return page(request, "dashboard/list.html", {"cfg": cfg, "page": pg, "q": q, "active": active,
                                                 "qs": params.urlencode() + "&" if params else ""})


@login_required
def section_edit(request, key, pk=None):
    cfg = _cfg(key)
    if request.method == "POST" or pk is None:
        denied = deny_unless(request, "edit")
        if denied:
            return denied
    obj = get_object_or_404(cfg["model"], pk=pk) if pk else None
    form = cfg["form"](request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Saved. The {cfg['singular']} is now on the website.")
        return redirect("dash_edit", key=key, pk=saved.pk)
    if request.method == "POST":
        messages.error(request, "Some details need fixing. Check the marked fields.")
    return page(request, "dashboard/form.html", {"cfg": cfg, "obj": obj, "form": form, "groups": groups_for(form, cfg["groups"]),
                                                 "heading": f"Edit {cfg['singular']}" if obj else f"Add a {cfg['singular']}",
                                                 "back_url": reverse("dash_list", kwargs={"key": key})})


@login_required
@require_POST
def section_delete(request, key, pk):
    denied = deny_unless(request, "delete")
    if denied:
        return denied
    cfg = _cfg(key)
    get_object_or_404(cfg["model"], pk=pk).delete()
    messages.success(request, f"The {cfg['singular']} was deleted.")
    return redirect("dash_list", key=key)


# ---------------------------------------------------------------- site settings
@login_required
def settings_manage(request):
    denied = deny_unless(request, "settings")
    if denied:
        return denied
    obj = SiteSettings.get()
    form = SettingsForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Website details updated.")
        return redirect("settings_manage")
    if request.method == "POST":
        messages.error(request, "Some details need fixing. Check the marked fields.")
    return page(request, "dashboard/form.html", {"cfg": None, "obj": obj, "form": form, "groups": groups_for(form, SETTINGS_GROUPS),
                                                 "heading": "Site and profile", "eyebrow": "WEBSITE DETAILS",
                                                 "blurb": "Name, biography, photo, CV, contact details and profile links used across the website.",
                                                 "back_url": None})


# ---------------------------------------------------------------- messages
@login_required
def messages_manage(request):
    qs = ContactMessage.objects.all()
    state, q = request.GET.get("state", ""), request.GET.get("q", "").strip()
    if state == "new":
        qs = qs.filter(handled=False)
    elif state == "handled":
        qs = qs.filter(handled=True)
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))
    pg = Paginator(qs, 25).get_page(request.GET.get("page"))
    return page(request, "dashboard/messages.html", {"page": pg, "state": state, "q": q})


@login_required
def message_detail(request, pk):
    obj = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        denied = deny_unless(request, "edit")
        if denied:
            return denied
        obj.handled = request.POST.get("handled") == "on"
        obj.notes = request.POST.get("notes", "")[:4000]
        obj.save()
        messages.success(request, "Message updated.")
        return redirect("message_detail", pk=pk)
    return page(request, "dashboard/message_detail.html", {"obj": obj})


@login_required
@require_POST
def message_delete(request, pk):
    denied = deny_unless(request, "delete")
    if denied:
        return denied
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.success(request, "Message deleted.")
    return redirect("messages_manage")


@login_required
def messages_export(request):
    denied = deny_unless(request, "export")
    if denied:
        return denied
    res = HttpResponse(content_type="text/csv")
    res["Content-Disposition"] = 'attachment; filename="website-messages.csv"'
    w = csv.writer(res)
    w.writerow(["Received", "First name", "Last name", "Email", "Subject", "Message", "Handled", "Notes"])
    for m in ContactMessage.objects.all():
        w.writerow([m.created.strftime("%Y-%m-%d %H:%M"), m.first_name, m.last_name, m.email, m.get_topic_display(), m.message,
                    "yes" if m.handled else "no", m.notes])
    return res


# ---------------------------------------------------------------- team
class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=Profile.ROLES, initial="manager")
    active = forms.BooleanField(initial=True, required=False)

    def clean_username(self):
        v = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=v).exists():
            raise forms.ValidationError("That username is already taken.")
        return v

    def clean_password(self):
        validate_password(self.cleaned_data["password"])
        return self.cleaned_data["password"]


@login_required
def users_manage(request):
    denied = deny_unless(request, "users")
    if denied:
        return denied
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(username=d["username"], password=d["password"], email=d["email"],
                                        first_name=d["first_name"], last_name=d["last_name"], is_active=d["active"])
        Profile.objects.create(user=user, role=d["role"])
        messages.success(request, "Account created.")
        return redirect("users_manage")
    return page(request, "dashboard/users.html", {"users": User.objects.select_related("profile").order_by("username"), "form": form})


@login_required
def user_edit(request, pk):
    denied = deny_unless(request, "users")
    if denied:
        return denied
    u = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        u.first_name = request.POST.get("first_name", "").strip()
        u.last_name = request.POST.get("last_name", "").strip()
        u.email = request.POST.get("email", "").strip()
        if not u.is_superuser:
            u.is_active = request.POST.get("active") == "on"
            profile, _ = Profile.objects.get_or_create(user=u)
            new_role = request.POST.get("role", "viewer")
            profile.role = new_role if new_role in dict(Profile.ROLES) else "viewer"
            profile.save()
        new_pw = request.POST.get("new_password", "")
        if new_pw:
            try:
                validate_password(new_pw, u)
                u.set_password(new_pw)
            except forms.ValidationError as e:
                messages.error(request, " ".join(e.messages))
                return redirect("user_edit", pk=pk)
        u.save()
        messages.success(request, "Account updated.")
        return redirect("users_manage")
    return page(request, "dashboard/user_edit.html", {"obj": u, "roles": Profile.ROLES})


def not_found(request, exception):
    return render(request, "404.html", status=404)
