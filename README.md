# Dr. Leonard A. Valentino: website (Django)

Full-stack Django site with a MICRA-style Control Center dashboard so the client or manager can update everything without touching code.

## Run it

    ./setup.sh                       # install, migrate, load CV content
    python3 manage.py createsuperuser
    python3 manage.py runserver      # http://127.0.0.1:8000/  (dashboard sign-in at /login/)

Tests: `python3 manage.py test`

## Pages
Home, About, Publications, Presentations, Projects, Organizations, Resources, Contact (the form saves to the database, shows in the dashboard Messages, and emails the address in Site settings or `CONTACT_EMAIL`).

## Control Center (the dashboard for the client and manager)
Sign in at **/login/** (or click "Staff login" in the site footer). It opens **/dashboard/**, styled after the MICRA dashboard.

| To do this | Open |
|---|---|
| Change name, biography, photo, CV, phone, emails, addresses, LinkedIn/ORCID/PubMed links | **Site and profile** |
| Update experience, education, appointments, honors | **Experience and education** |
| Add or edit papers (optional PDF upload) | **Publications** |
| Add talks with slides, an uploaded video, or a YouTube/Vimeo link | **Presentations** |
| Add initiatives, research, trials (optional image or file) | **Projects** |
| Societies, journals, committees, leadership | **Organizations** |
| Upload videos, slide decks and documents, or add links | **Videos and resources** |
| Read and answer contact-form messages, download CSV | **Messages** |
| Create logins and choose roles | **Team and access** (administrator only) |

Tick **Featured** on a publication, project or presentation to show it in the Home page highlights. Every save goes live immediately.

### Roles
- **Administrator** (any superuser): everything, including accounts.
- **Manager**: all content, site details, deleting, message export.
- **Content editor**: add and edit content and work on messages. Cannot delete, change site details or export.
- **Viewer**: read-only.

Create the first accounts:

    python3 manage.py createsuperuser                      # administrator
    python3 manage.py create_manager --username manager --password "..."            # manager
    python3 manage.py create_manager --username editor1 --password "..." --role editor

Uploads accept images, PDF, Office files, CSV/TXT/ZIP and MP4/WebM/MOV video. Django's own admin is still available at `/dj-admin/` for administrators.

## Changes from the handwritten notes
- Home: "30 year + experience" removed (hero text and stats strip).
- Phone **(630) 267-0553** added (Contact page and footer).
- Bio from the client used on Home and About.
- Client can upload video, presentations, publications, projects and resources through the admin.
- CV details loaded from the CV PDF. `python3 manage.py seed_cv --reset` reloads them. `tools/parse_cv.py` regenerates `core/data/cv_data.json` from a `pdftotext -layout` export of the CV.

## Deploying
Set environment variables: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS=yourdomain.com`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com`. For email: `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `CONTACT_EMAIL`.
Then run `python3 manage.py collectstatic --noinput` and `gunicorn config.wsgi`. Static files are served by WhiteNoise. Uploaded files live in `media/`, so use a host with a persistent disk (Render, Railway, Fly.io, a VPS) or add object storage. Vercel, where the old site lived, cannot run Django with a database and uploads.

## Not published on purpose
The CV contains a home address, date of birth, family names and a medical license number. None of these appear on the site. Upload a public version of the CV under Site settings before enabling the Download CV button.
