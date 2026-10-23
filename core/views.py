from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render

from .forms import ContactForm
from .models import (CareerEntry, Organization, Presentation, Project, Publication, Resource, SiteSettings)

EXPERTISE = [
    ("Hemophilia and bleeding disorders", "Clinical care, research and education for people with hemophilia A and B and related disorders."),
    ("Hemophilic joint disease", "How blood in the joint leads to synovitis and arthropathy, and where treatment could intervene."),
    ("Inhibitors and immune tolerance", "Managing inhibitors, bypassing agents and immune tolerance induction."),
    ("Gene therapy", "Strategy for hemophilia A gene therapy and a shared vocabulary for gene editing."),
    ("von Willebrand disease", "Diagnosis, bleeding scores and treatment studies."),
    ("Advocacy and collaboration", "Partnerships between patient groups, industry and researchers to speed new medicines."),
]


def _filter_page(request, qs, per_page=25):
    page = Paginator(qs, per_page).get_page(request.GET.get("page"))
    return page


def home(request):
    s = SiteSettings.get()
    n_pubs = Publication.objects.count()
    stats = [
        (s.peer_reviewed_total or Publication.objects.filter(kind="article").count(), "peer-reviewed papers"),
        (s.h_index, "H-index"),
        (Presentation.objects.filter(kind="lecture").count(), "invited lectures"),
        (Project.objects.count(), "projects and funded studies"),
        (CareerEntry.objects.filter(kind="honor", visible=True).count(), "honors and awards"),
    ]
    ctx = {
        "stats": stats,
        "current_roles": Project.objects.filter(ongoing=True, kind="leadership")[:6],
        "featured_pub": Publication.objects.filter(featured=True).first() or Publication.objects.filter(kind="article").first(),
        "featured_project": Project.objects.filter(featured=True).first() or Project.objects.filter(ongoing=True).first(),
        "featured_pres": Presentation.objects.filter(featured=True).first() or Presentation.objects.exclude(year=None).first(),
        "expertise": EXPERTISE,
        "n_pubs": n_pubs,
    }
    return render(request, "core/home.html", ctx)


def about(request):
    entries = CareerEntry.objects.filter(visible=True)
    ctx = {
        "experience": entries.filter(kind="experience"),
        "education": entries.filter(kind="education"),
        "appointments": entries.filter(kind="appointment"),
        "honors": entries.filter(kind="honor"),
        "certs": entries.filter(kind="certification"),
        "leadership": Organization.objects.filter(kind="leadership"),
    }
    return render(request, "core/about.html", ctx)


def publications(request):
    qs = Publication.objects.all()
    kind, topic, q = request.GET.get("kind", ""), request.GET.get("topic", ""), request.GET.get("q", "").strip()
    year = request.GET.get("year", "")
    if kind in dict(Publication.KINDS):
        qs = qs.filter(kind=kind)
    if topic in dict(Publication.TOPICS):
        qs = qs.filter(topic=topic)
    if year.isdigit():
        qs = qs.filter(year=int(year))
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(authors__icontains=q) | Q(journal__icontains=q))
    years = Publication.objects.order_by("-year").values_list("year", flat=True).distinct()
    ctx = {"page": _filter_page(request, qs, 20), "kinds": Publication.KINDS, "topics": Publication.TOPICS,
           "years": years, "kind": kind, "topic": topic, "q": q, "year": year,
           "total": Publication.objects.count()}
    return render(request, "core/publications.html", ctx)


def presentations(request):
    qs = Presentation.objects.all()
    kind, q = request.GET.get("kind", ""), request.GET.get("q", "").strip()
    if kind in dict(Presentation.KINDS):
        qs = qs.filter(kind=kind)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(event__icontains=q))
    with_media = Presentation.objects.exclude(Q(slides="") & Q(video_file="") & Q(video_url="")).count()
    ctx = {"page": _filter_page(request, qs, 25), "kinds": Presentation.KINDS, "kind": kind, "q": q,
           "total": Presentation.objects.count(), "with_media": with_media}
    return render(request, "core/presentations.html", ctx)


def projects(request):
    qs = Project.objects.all()
    kind = request.GET.get("kind", "")
    if kind in dict(Project.KINDS):
        qs = qs.filter(kind=kind)
    ctx = {"page": _filter_page(request, qs, 20), "kinds": Project.KINDS, "kind": kind,
           "total": Project.objects.count(), "active": Project.objects.filter(ongoing=True).count()}
    return render(request, "core/projects.html", ctx)


def organizations(request):
    groups = []
    for key, label in Organization.KINDS:
        items = Organization.objects.filter(kind=key)
        if items:
            groups.append((label, items))
    return render(request, "core/organizations.html", {"groups": groups})


def resources(request):
    qs = Resource.objects.all()
    kind = request.GET.get("kind", "")
    if kind in dict(Resource.KINDS):
        qs = qs.filter(kind=kind)
    present = set(Resource.objects.values_list("kind", flat=True))
    kinds = [(k, l) for k, l in Resource.KINDS if k in present]
    return render(request, "core/resources.html", {"resources": qs, "kinds": kinds, "kind": kind,
                                                   "total": Resource.objects.count()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        target = settings.CONTACT_EMAIL or SiteSettings.get().email_primary
        try:
            send_mail(f"Website message: {msg.get_topic_display()}",
                      f"From: {msg.first_name} {msg.last_name} <{msg.email}>\n\n{msg.message}",
                      settings.DEFAULT_FROM_EMAIL, [target], fail_silently=True)
        except Exception:
            pass
        return redirect("contact_thanks")
    return render(request, "core/contact.html", {"form": form})


def contact_thanks(request):
    return render(request, "core/contact_thanks.html")
