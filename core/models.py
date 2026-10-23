import re
from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    """Single row holding the text, contact details and files used across the site."""
    full_name = models.CharField(max_length=120, default="Leonard A. Valentino, MD")
    short_title = models.CharField("Role line", max_length=200, default="Professor of Pediatrics, Rush University Medical Center")
    tagline = models.CharField(max_length=200, default="Translational hematologist and health equity advocate")
    hero_headline = models.CharField(max_length=250, default="Improving the health and wellbeing of people with bleeding disorders, everywhere.")
    hero_intro = models.TextField(help_text="Short paragraph under the headline on the Home page.")
    bio = models.TextField(help_text="Full biography for the About page. Separate paragraphs with a blank line. "
                                     "Links can be written as [text](https://address).")
    pull_quote = models.CharField(max_length=300, blank=True)
    photo = models.ImageField(upload_to="site/", blank=True, help_text="Portrait shown on the About page and Home page.")
    cv_file = models.FileField("CV (PDF)", upload_to="site/", blank=True,
                               help_text="Upload the public version of the CV. Shows as the Download CV button.")

    phone = models.CharField(max_length=40, default="(630) 267-0553")
    email_primary = models.EmailField(default="lvalentino@pathwaytocures.org")
    email_secondary = models.EmailField(blank=True, default="info@pathwaytocures.org")
    office_name = models.CharField(max_length=200, default="Pathway to Cures, National Bleeding Disorders Venture Fund")
    office_address = models.TextField(default="1230 Avenue of the Americas, 16th Floor\nNew York, NY 10020\nUnited States")
    academic_name = models.CharField(max_length=200, blank=True, default="Rush University Medical Center")
    academic_address = models.TextField(blank=True, default="1653 West Congress Parkway, Jelke Building, Room 1591\nChicago, Illinois 60612")
    academic_phone = models.CharField(max_length=40, blank=True, default="(312) 942-8114")

    orcid_url = models.URLField(blank=True, default="https://orcid.org/0000-0002-7927-6418")
    pubmed_url = models.URLField(blank=True, default="https://pubmed.ncbi.nlm.nih.gov/?term=Valentino+LA%5BAuthor%5D")
    linkedin_url = models.URLField(blank=True)
    researchgate_url = models.URLField(blank=True)

    h_index = models.PositiveIntegerField("H-index", default=49)
    peer_reviewed_total = models.PositiveIntegerField("Peer-reviewed papers (stated total)", default=175,
                                                     help_text="Shown on Home. Leave 0 to count the papers listed on the site instead.")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"hero_intro": "", "bio": ""})
        return obj

    @property
    def photo_url(self):
        """Uploaded portrait, or the bundled one so the hero is never empty."""
        from django.templatetags.static import static
        return self.photo.url if self.photo else static("core/portrait.jpg")

    @property
    def phone_href(self):
        return re.sub(r"[^\d+]", "", self.phone)

    @property
    def office_address_lines(self):
        return self.office_address.splitlines()

    @property
    def academic_address_lines(self):
        return self.academic_address.splitlines()


class CareerEntry(models.Model):
    EXPERIENCE, EDUCATION, APPOINTMENT, HONOR, CERT = "experience", "education", "appointment", "honor", "certification"
    KINDS = [(EXPERIENCE, "Professional experience"), (EDUCATION, "Education"), (APPOINTMENT, "Academic appointment"),
             (HONOR, "Honor or award"), (CERT, "Board certification")]
    kind = models.CharField(max_length=20, choices=KINDS)
    period = models.CharField(max_length=40, help_text='e.g. "2020–2023" or "2024–present"')
    title = models.CharField(max_length=250)
    organization = models.CharField(max_length=250, blank=True)
    details = models.TextField(blank=True, help_text="Optional. One point per line.")
    sort_year = models.PositiveIntegerField(default=0, help_text="Used for ordering, newest first (use the start year).")
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "-sort_year", "id"]
        verbose_name = "career, education or honor entry"
        verbose_name_plural = "career, education and honors"

    def __str__(self):
        return f"{self.period} {self.title}"

    @property
    def detail_lines(self):
        return [l.strip() for l in self.details.splitlines() if l.strip()]


class Publication(models.Model):
    ARTICLE, REVIEW, CHAPTER = "article", "review", "chapter"
    KINDS = [(ARTICLE, "Journal article"), (REVIEW, "Invited review"), (CHAPTER, "Book, chapter or supplement")]
    TOPICS = [("hemophilia", "Hemophilia"), ("inhibitors", "Inhibitors"), ("joint", "Joint disease"),
              ("gene_therapy", "Gene therapy"), ("vwd", "von Willebrand disease"), ("oncology", "Oncology and transplant"),
              ("other", "Other")]
    title = models.TextField()
    authors = models.TextField(blank=True)
    journal = models.CharField("Journal / citation", max_length=400, blank=True)
    year = models.PositiveIntegerField(db_index=True)
    kind = models.CharField(max_length=10, choices=KINDS, default=ARTICLE)
    topic = models.CharField(max_length=20, choices=TOPICS, default="other")
    url = models.URLField("Link (DOI / PubMed)", blank=True, max_length=500)
    pdf = models.FileField("PDF upload", upload_to="publications/", blank=True)
    featured = models.BooleanField(default=False, help_text="Show on the Home page.")

    class Meta:
        ordering = ["-year", "id"]

    def __str__(self):
        return f"{self.year} {self.title[:80]}"


class Presentation(models.Model):
    LECTURE, ABSTRACT, CONFERENCE, WEBINAR, WORKSHOP = "lecture", "abstract", "conference", "webinar", "workshop"
    KINDS = [(LECTURE, "Invited lecture"), (ABSTRACT, "Presented abstract"), (CONFERENCE, "Conference talk"),
             (WEBINAR, "Webinar"), (WORKSHOP, "Workshop")]
    title = models.TextField()
    event = models.TextField("Event, venue and date", blank=True)
    year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    kind = models.CharField(max_length=12, choices=KINDS, default=LECTURE)
    slides = models.FileField("Slides (PDF / PowerPoint)", upload_to="presentations/", blank=True)
    video_file = models.FileField("Video upload", upload_to="videos/", blank=True)
    video_url = models.URLField("Video link (YouTube / Vimeo)", blank=True)
    featured = models.BooleanField(default=False, help_text="Show on the Home page.")

    class Meta:
        ordering = ["-year", "-id"]

    def __str__(self):
        return f"{self.year or ''} {self.title[:80]}"

    @property
    def embed_url(self):
        return video_embed_url(self.video_url)

    @property
    def has_media(self):
        return bool(self.slides or self.video_file or self.video_url)


class Project(models.Model):
    LAB, CLINICAL, EDU, LEAD = "laboratory", "clinical", "educational", "leadership"
    KINDS = [(LEAD, "Leadership and initiatives"), (LAB, "Laboratory research"), (CLINICAL, "Clinical research"),
             (EDU, "Educational")]
    title = models.TextField()
    role = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=12, choices=KINDS, default=LEAD)
    start_year = models.PositiveIntegerField(null=True, blank=True)
    end_year = models.PositiveIntegerField(null=True, blank=True)
    ongoing = models.BooleanField(default=False)
    url = models.URLField("Website", blank=True)
    image = models.ImageField(upload_to="projects/", blank=True)
    file = models.FileField("Attached file", upload_to="projects/", blank=True)
    featured = models.BooleanField(default=False, help_text="Show on the Home page.")

    class Meta:
        ordering = ["-ongoing", "-start_year", "-id"]

    def __str__(self):
        return self.title[:90]

    @property
    def period(self):
        if not self.start_year:
            return ""
        if self.ongoing:
            return f"{self.start_year}–present"
        if self.end_year and self.end_year != self.start_year:
            return f"{self.start_year}–{self.end_year}"
        return str(self.start_year)


class Organization(models.Model):
    LEAD, SOCIETY, JOURNAL, COMMITTEE, PAST = "leadership", "society", "journal", "committee", "past"
    KINDS = [(LEAD, "Current leadership"), (PAST, "Past leadership"), (SOCIETY, "Professional societies"),
             (JOURNAL, "Journals (editor / reviewer)"), (COMMITTEE, "Committees and boards")]
    name = models.CharField(max_length=250)
    role = models.CharField(max_length=250, blank=True)
    period = models.CharField(max_length=40, blank=True)
    kind = models.CharField(max_length=12, choices=KINDS, default=SOCIETY)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    sort_year = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["kind", "-sort_year", "name"]

    def __str__(self):
        return self.name


class Resource(models.Model):
    VIDEO, SLIDES, DOC, PUB, LINK, OTHER = "video", "presentation", "document", "publication", "link", "other"
    KINDS = [(VIDEO, "Video"), (SLIDES, "Presentation"), (DOC, "Document"), (PUB, "Publication"),
             (LINK, "Link"), (OTHER, "Other")]
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=14, choices=KINDS, default=DOC)
    file = models.FileField("File upload", upload_to="resources/", blank=True)
    video_url = models.URLField("Video link (YouTube / Vimeo)", blank=True)
    external_url = models.URLField("External link", blank=True)
    thumbnail = models.ImageField(upload_to="resources/thumbs/", blank=True)
    added = models.DateField(default=timezone.localdate)
    featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-added", "-id"]

    def __str__(self):
        return self.title

    @property
    def embed_url(self):
        return video_embed_url(self.video_url)

    @property
    def has_content(self):
        return bool(self.file or self.video_url or self.external_url)


def video_embed_url(url):
    if not url:
        return ""
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{11})", url)
    if m:
        return f"https://www.youtube-nocookie.com/embed/{m.group(1)}"
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)", url)
    if m:
        return f"https://player.vimeo.com/video/{m.group(1)}"
    return ""


class ContactMessage(models.Model):
    TOPICS = [("collaboration", "Research collaboration"), ("speaking", "Speaking invitation"),
              ("media", "Media inquiry"), ("academic", "Academic question"), ("other", "Other")]
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    topic = models.CharField(max_length=20, choices=TOPICS, default="other")
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)
    notes = models.TextField(blank=True, help_text="Internal notes. Not shown publicly.")

    class Meta:
        ordering = ["-created"]
        verbose_name = "message"

    def __str__(self):
        return f"{self.first_name} {self.last_name}: {self.get_topic_display()}"


class Profile(models.Model):
    """Dashboard role for a login. Superusers are always Administrators."""
    ROLES = [("admin", "Administrator"), ("manager", "Manager"), ("editor", "Content editor"), ("viewer", "Viewer")]
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLES, default="viewer")

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
