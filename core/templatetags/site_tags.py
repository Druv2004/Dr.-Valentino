import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


@register.filter
def rich_paragraphs(text):
    """Blank-line separated paragraphs; [label](https://url) becomes a safe link."""
    out = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        if not block.strip():
            continue
        html = escape(block.strip())
        html = LINK.sub(lambda m: f'<a href="{m.group(2)}" rel="noopener" target="_blank">{m.group(1)}</a>', html)
        out.append(f"<p>{html}</p>")
    return mark_safe("\n".join(out))


@register.filter
def first_paragraph(text):
    return rich_paragraphs(re.split(r"\n\s*\n", (text or "").strip())[0])


@register.simple_tag(takes_context=True)
def qs_without(context, *keys):
    """Current query string minus the given keys (used by filter and pagination links)."""
    q = context["request"].GET.copy()
    for k in keys:
        q.pop(k, None)
    s = q.urlencode()
    return s + "&" if s else ""


@register.simple_tag
def dashboard_stats():
    from core.models import (CareerEntry, ContactMessage, Organization, Presentation, Project, Publication, Resource)
    return {
        "resources": Resource.objects.count(), "publications": Publication.objects.count(),
        "presentations": Presentation.objects.count(), "projects": Project.objects.count(),
        "career": CareerEntry.objects.count(), "organizations": Organization.objects.count(),
        "unread": ContactMessage.objects.filter(handled=False).count(),
        "videos": Resource.objects.filter(kind="video").count(),
    }


@register.simple_tag
def cell(obj, name):
    """Render one table cell for the dashboard: choices show their label, booleans become pills."""
    from django.db import models as m
    from django.utils.html import format_html
    val = getattr(obj, name, "")
    if callable(val):
        val = val()
    disp = getattr(obj, f"get_{name}_display", None)
    if disp:
        return format_html('<span class="pill">{}</span>', disp())
    if isinstance(val, bool):
        return format_html('<span class="pill {}">{}</span>', "resolved" if val else "closed", "Yes" if val else "No")
    if val in (None, ""):
        return "–"
    s = str(val)
    return s if len(s) < 110 else s[:107] + "..."


@register.filter
def dictget(d, key):
    return (d or {}).get(key)


@register.filter
def basename(value):
    import os
    return os.path.basename(str(value))
