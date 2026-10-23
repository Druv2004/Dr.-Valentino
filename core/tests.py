import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CareerEntry, ContactMessage, Presentation, Profile, Publication, Resource, SiteSettings


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_cv", verbosity=0)

    def test_pages_load(self):
        for name in ["home", "about", "publications", "presentations", "projects", "organizations", "resources", "contact"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_note_changes_applied(self):
        home = self.client.get(reverse("home")).content.decode()
        self.assertNotIn("30+", home)
        self.assertNotIn("years experience", home.lower())
        self.assertNotIn("year + experience", home.lower())
        self.assertEqual(SiteSettings.get().phone, "(630) 267-0553")
        self.assertIn("(630) 267-0553", self.client.get(reverse("contact")).content.decode())

    def test_filters(self):
        r = self.client.get(reverse("publications"), {"topic": "joint"})
        self.assertGreater(r.context["page"].paginator.count, 0)
        r = self.client.get(reverse("publications"), {"q": "zzzz-no-match"})
        self.assertContains(r, "No publications match")

    def test_contact_form(self):
        r = self.client.post(reverse("contact"), {"first_name": "A", "last_name": "B", "email": "a@b.co", "topic": "media", "message": "Hi"})
        self.assertRedirects(r, reverse("contact_thanks"))
        self.assertEqual(ContactMessage.objects.count(), 1)
        r = self.client.post(reverse("contact"), {"first_name": "A", "last_name": "B", "email": "a@b.co", "topic": "media", "message": "Hi", "website": "spam"})
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_admin_upload_shows_on_site(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            get_user_model().objects.create_superuser("admin", "a@b.co", "pw12345!")
            self.client.login(username="admin", password="pw12345!")
            f = SimpleUploadedFile("slides.pdf", b"%PDF-1.4 test", content_type="application/pdf")
            r = self.client.post(reverse("dash_new", args=["resources"]),
                                 {"title": "Test deck", "kind": "presentation", "description": "d", "added": "2026-01-01", "file": f})
            self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["form"].errors)
            page = self.client.get(reverse("resources"))
            self.assertContains(page, "Test deck")
            self.assertContains(page, "/media/resources/slides")
            Resource.objects.all().delete()

    def test_video_embed(self):
        r = Resource(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertIn("youtube-nocookie.com/embed/dQw4w9WgXcQ", r.embed_url)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_cv", verbosity=0)
        for name, role in [("mgr", "manager"), ("ed", "editor"), ("view", "viewer")]:
            call_command("create_manager", username=name, password="StrongPass123x", role=role, verbosity=0)
        get_user_model().objects.create_superuser("boss", "b@b.co", "StrongPass123x")

    def login(self, name):
        self.client.logout()
        self.assertTrue(self.client.login(username=name, password="StrongPass123x"))

    def test_login_required(self):
        for url in ["/dashboard/", "/dashboard/publications/", "/dashboard/site/", "/dashboard/team/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertIn("/login/", r["Location"])

    def test_login_flow(self):
        r = self.client.post("/login/", {"username": "mgr", "password": "wrong"})
        self.assertContains(r, "Incorrect username or password")
        r = self.client.post("/login/", {"username": "mgr", "password": "StrongPass123x"})
        self.assertRedirects(r, "/dashboard/")

    def test_every_page_renders_for_manager(self):
        self.login("mgr")
        urls = ["/dashboard/", "/dashboard/site/", "/dashboard/password/", "/dashboard/messages/"]
        for k in ["career", "publications", "presentations", "projects", "organizations", "resources"]:
            urls += [f"/dashboard/{k}/", f"/dashboard/{k}/new/"]
        for u in urls:
            self.assertEqual(self.client.get(u).status_code, 200, u)
        self.assertEqual(self.client.get("/dashboard/nonsense/").status_code, 404)

    def test_manager_edits_experience_and_site_text(self):
        self.login("mgr")
        entry = CareerEntry.objects.filter(kind="experience").first()
        r = self.client.post(f"/dashboard/career/{entry.pk}/", {"kind": "experience", "period": "2030", "title": "Edited by manager",
                                                                 "organization": "Org", "details": "", "sort_year": 2030, "visible": "on"})
        self.assertEqual(r.status_code, 302)
        self.assertContains(self.client.get("/about/"), "Edited by manager")
        s = SiteSettings.get()
        data = {n: getattr(s, n) for n in ["full_name", "short_title", "tagline", "hero_headline", "hero_intro", "bio", "phone",
                                          "email_primary", "email_secondary", "office_name", "office_address", "academic_name",
                                          "academic_address", "academic_phone", "h_index", "peer_reviewed_total"]}
        data["phone"] = "(111) 222-3333"
        self.assertEqual(self.client.post("/dashboard/site/", data).status_code, 302)
        self.assertContains(self.client.get("/contact/"), "(111) 222-3333")

    def test_upload_video_presentation_and_clear(self):
        self.login("mgr")
        up = SimpleUploadedFile("talk.pdf", b"%PDF-1.4 x", content_type="application/pdf")
        r = self.client.post("/dashboard/presentations/new/", {"title": "New talk", "event": "Somewhere", "year": 2026, "kind": "lecture",
                                                                "video_url": "https://youtu.be/dQw4w9WgXcQ", "slides": up})
        self.assertEqual(r.status_code, 302)
        page = self.client.get("/presentations/?q=New+talk")
        self.assertContains(page, "youtube-nocookie.com/embed/dQw4w9WgXcQ")
        self.assertContains(page, "/media/presentations/talk")
        obj = Presentation.objects.get(title="New talk")
        r = self.client.post(f"/dashboard/presentations/{obj.pk}/", {"title": "New talk", "event": "Somewhere", "year": 2026, "kind": "lecture",
                                                                       "video_url": "", "clear__slides": "on"})
        self.assertEqual(r.status_code, 302)
        obj.refresh_from_db()
        self.assertFalse(obj.slides)

    def test_bad_file_type_rejected(self):
        self.login("mgr")
        bad = SimpleUploadedFile("evil.exe", b"MZ", content_type="application/octet-stream")
        r = self.client.post("/dashboard/resources/new/", {"title": "x", "kind": "document", "added": "2026-01-01", "file": bad})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "not allowed")

    def test_roles(self):
        pub = Publication.objects.first()
        # editor: can edit, cannot delete / change site / see team
        self.login("ed")
        self.assertEqual(self.client.get("/dashboard/publications/new/").status_code, 200)
        self.assertEqual(self.client.post(f"/dashboard/publications/{pub.pk}/delete/").status_code, 403)
        self.assertEqual(self.client.get("/dashboard/site/").status_code, 403)
        self.assertEqual(self.client.get("/dashboard/team/").status_code, 403)
        # viewer: read-only
        self.login("view")
        self.assertEqual(self.client.get("/dashboard/publications/").status_code, 200)
        self.assertEqual(self.client.get("/dashboard/publications/new/").status_code, 403)
        self.assertEqual(self.client.post(f"/dashboard/publications/{pub.pk}/", {"title": "x"}).status_code, 403)
        # manager: can delete, cannot manage team
        self.login("mgr")
        self.assertEqual(self.client.get("/dashboard/team/").status_code, 403)
        self.assertEqual(self.client.post(f"/dashboard/publications/{pub.pk}/delete/").status_code, 302)
        self.assertFalse(Publication.objects.filter(pk=pub.pk).exists())
        # admin: team page works and can create accounts
        self.login("boss")
        r = self.client.post("/dashboard/team/", {"username": "newperson", "password": "AnotherStrong99!", "role": "editor", "active": "on"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Profile.objects.get(user__username="newperson").role, "editor")

    def test_messages_flow(self):
        self.client.post("/contact/", {"first_name": "A", "last_name": "B", "email": "a@b.co", "topic": "media", "message": "Hello"})
        self.login("mgr")
        m = ContactMessage.objects.get()
        self.assertContains(self.client.get("/dashboard/"), "1")
        self.client.post(f"/dashboard/messages/{m.pk}/", {"handled": "on", "notes": "called"})
        m.refresh_from_db()
        self.assertTrue(m.handled)
        self.assertContains(self.client.get("/dashboard/messages/export/"), "Hello")

    def test_hero_photo_fallback(self):
        site = SiteSettings.get()
        site.photo = ""
        site.save()
        self.assertContains(self.client.get("/"), "core/portrait.jpg")
