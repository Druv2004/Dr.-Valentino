"""Load Dr. Valentino's CV content into the database.

    python manage.py seed_cv            # only fills empty tables
    python manage.py seed_cv --reset    # wipes content tables and reloads (does NOT touch uploaded files or messages)
"""
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import CareerEntry, Organization, Presentation, Project, Publication, SiteSettings

DATA = Path(__file__).resolve().parents[2] / "data" / "cv_data.json"

BIO = """Dr Valentino is a Professor of Pediatrics at Rush University Medical Center in Chicago, Illinois USA. His professional goal is to improve the health and wellbeing of people with bleeding disorders globally through research, advocacy and education.

To advance this goal, he serves as President of the [World Federation of Hemophilia USA](https://wfh.org/usa/) to advance the global mission of the World Federation of Hemophilia (WFH) in the United States and as an Entrepreneur in Residence for the National Bleeding Disorders Foundation (NBDF) venture philanthropy program, [Pathway to Cures](https://www.pathwaytocures.org/), to drive transformation in the diagnosis and treatment of blood disorders globally.

His vision for a new paradigm for collaborative research in bleeding disorders has resulted in NBDF's [Bleeding Disorders Research Collaborative](https://www.bleeding.org/research/bleeding-disorders-research-collaborative) (BDRC), for which he serves as the Interim Executive Director. He is co-leader of the [Paladin Consortium](https://sites.tufts.edu/paladinconsortium/), dedicated to transforming the pace of medicines development through optimizing patient advocacy group-industry collaborations.

Dr Valentino is editor of [Expert Review of Hematology](https://www.tandfonline.com/journals/ierr20) and a regular reviewer for numerous scientific journals including Journal of Thrombosis and Hemostasis, Research and Practice in Thrombosis and Haemostasis, Haemophilia, and Blood.

His research has focused on the molecular mechanisms leading to joint disease in people with hemophilia, and he has published extensively in this area. He is a regular participant in international humanitarian aid programs with WFH to advance the standard of care for people with hemophilia in low- and middle-income countries."""

HERO_INTRO = ("Dr Valentino is a Professor of Pediatrics at Rush University Medical Center in Chicago. Through research, "
              "advocacy and education he works to improve the health and wellbeing of people with bleeding disorders worldwide.")

QUOTE = ("Directing the health care for individuals afflicted with bleeding and blood clotting disorders provides a sense of "
         "personal satisfaction and accomplishment.")

# (kind, period, title, organization, details, sort_year)
CAREER = [
    ("experience", "2024–present", "President", "World Federation of Hemophilia USA", "", 2024),
    ("experience", "2024–present", "Entrepreneur in Residence", "Pathway to Cures, National Bleeding Disorders Foundation", "", 2024),
    ("experience", "2024–2026", "Executive Committee Co-Chair", "Paladin Consortium", "", 2024),
    ("experience", "2024–2025", "Interim Executive Director, National Research Blueprint", "National Bleeding Disorders Foundation", "", 2024),
    ("experience", "2023–2024", "President and Chief Executive Officer", "National Bleeding Disorders Foundation", "", 2023),
    ("experience", "2021–2024", "Chief Executive Officer", "Pathway to Cures",
     "Overall strategic leadership and financial oversight of the venture philanthropy fund", 2021),
    ("experience", "2020–2023", "President and Chief Executive Officer", "National Hemophilia Foundation",
     "Strategic leadership and financial oversight of the Foundation\nOversight of the philanthropic activities of the Foundation", 2020),
    ("experience", "2017–2020", "Vice President, Strategy Lead, Hematology, Global Medical Affairs", "Spark Therapeutics",
     "Led a global medical team of six\nStrategic planning for hemophilia A gene therapy (SPK-8011 and SPK-8016)", 2017),
    ("experience", "2016–2017", "Vice President, Head, Hematology, Global Medical Affairs", "Shire Inc.",
     "Led a global medical team of 25\nStrategic planning for a worldwide hemophilia portfolio of eleven products\nGlobal medical launch planning for five products", 2016),
    ("experience", "2015–2016", "Senior Medical Director, Head, Hematology, Global Medical Affairs", "Baxalta US, Inc.",
     "Led a global medical team of 45\nSupported enrollment in the Phase IIIb/IV PROPEL study and the Phase IV Rixubis post-marketing safety study", 2015),
    ("experience", "2014–2015", "Senior Medical Director, Global Medical Affairs", "Baxter Healthcare, Inc.",
     "Led hematology disease and product education of country medical organizations", 2014),
    ("experience", "1998–2013", "Director, Section of Pediatric Hematology/Oncology", "Rush Medical College, Rush University, Chicago",
     "Led a team of 45 including physicians, nurses, research scientists, social workers and research staff", 1998),
    ("experience", "1998–2013", "Director, Rush University Hemophilia and Thrombophilia Center", "Rush University Medical Center, Chicago",
     "Led a team of 30 clinicians, scientists and staff\nOversight of the hemophilia pharmacy program", 1998),
    ("experience", "1995–1999", "Director, Comprehensive Hemophilia Program", "Rush Children's Hospital, Chicago", "", 1995),
    ("education", "1987–1990", "Fellowship, Hematology/Oncology", "UCLA School of Medicine, Los Angeles, California", "", 1987),
    ("education", "1984–1987", "Residency in Pediatrics (Chief Resident 1986–87)", "University of Illinois Medical Center, Chicago, Illinois", "", 1984),
    ("education", "1980–1984", "M.D.", "Creighton University School of Medicine, Omaha, Nebraska", "", 1980),
    ("education", "1976–1980", "B.S.", "Creighton University, College of Arts and Sciences, Omaha, Nebraska", "", 1976),
    ("appointment", "2009–present", "Professor of Pediatrics", "Rush Medical College, Rush University, Chicago", "", 2009),
    ("appointment", "1998–2008", "Associate Professor of Pediatrics", "Rush Medical College, Chicago", "", 1998),
    ("appointment", "1990–1998", "Assistant Professor of Pediatrics", "Rush Medical College, Chicago", "", 1990),
    ("certification", "1990–present", "Diplomate, American Board of Pediatrics", "", "", 1990),
    ("certification", "1991–present", "Sub-board certification in Hematology/Oncology", "American Board of Pediatrics", "", 1991),
    ("honor", "2012", "America's Top Doctors, Cancer", "Castle Connolly, Ltd.", "", 2012),
    ("honor", "2011", "Chicago's Top Doctors", "Chicago Magazine", "", 2011),
    ("honor", "2005", "America's Top Doctors, Cancer", "Castle Connolly, Ltd.", "", 2005),
    ("honor", "2003", "Chicago Metro Area Top Doctor", "Castle Connolly, Ltd.", "", 2003),
    ("honor", "2001–2013", "America's Top Doctors, Pediatric Hematology", "Castle Connolly, Ltd.", "", 2001),
    ("honor", "1997", "Chicago Metro Area Top Doctor", "Castle Connolly, Ltd.", "", 1997),
    ("honor", "1988", "Mead Johnson Award for teaching excellence", "UCLA Pediatric Housestaff, UCLA Medical Center", "", 1988),
    ("honor", "1987–1988", "Regular Clinical Fellowship", "American Cancer Society, UCLA Medical Center", "", 1987),
    ("honor", "1984", "William A. Albano, M.D. Award for Outstanding Student Research", "Creighton University School of Medicine", "", 1984),
]

# (kind, name, role, period, description, url, sort_year)
ORGS = [
    ("leadership", "World Federation of Hemophilia USA", "President", "2024–present",
     "Advances the global mission of the World Federation of Hemophilia in the United States.", "https://wfh.org/usa/", 2024),
    ("leadership", "Pathway to Cures", "Entrepreneur in Residence", "2024–present",
     "The National Bleeding Disorders Foundation's venture philanthropy program.", "https://www.pathwaytocures.org/", 2024),
    ("leadership", "Bleeding Disorders Research Collaborative", "Interim Executive Director", "",
     "A new paradigm for collaborative research in bleeding disorders, from the National Bleeding Disorders Foundation.",
     "https://www.bleeding.org/research/bleeding-disorders-research-collaborative", 2024),
    ("leadership", "Paladin Consortium", "Co-leader", "2024–present",
     "Transforming the pace of medicines development through patient advocacy group and industry collaboration.",
     "https://sites.tufts.edu/paladinconsortium/", 2024),
    ("leadership", "Expert Review of Hematology", "Editor", "", "", "https://www.tandfonline.com/journals/ierr20", 2020),
    ("past", "National Bleeding Disorders Foundation", "President and Chief Executive Officer", "2023–2024", "", "", 2023),
    ("past", "National Hemophilia Foundation", "President and Chief Executive Officer", "2020–2023", "", "", 2020),
    ("past", "Pathway to Cures", "Chief Executive Officer", "2021–2024", "", "", 2021),
    ("past", "Hemophilia and Thrombosis Research Society", "President", "2005–2008", "", "", 2005),
    ("society", "World Federation of Hemophilia", "Member; Musculoskeletal Committee", "2000–present", "", "https://wfh.org/", 2000),
    ("society", "American Society of Hematology", "Member", "1993–present", "", "https://www.hematology.org/", 1993),
    ("society", "International Society on Thrombosis and Haemostasis", "Member", "1999–present", "", "https://www.isth.org/", 1999),
    ("society", "National Hemophilia Foundation", "Member", "1996–present", "", "", 1996),
    ("society", "Hemophilia and Thrombosis Research Society", "Member", "2000–present", "", "", 2000),
    ("society", "Medical Affairs Professional Society", "Member", "2015–present", "", "", 2015),
    ("society", "Foundation for Women and Girls with Blood Disorders", "Member", "2020–present", "", "", 2020),
    ("journal", "Expert Review of Hematology", "Editor", "", "", "https://www.tandfonline.com/journals/ierr20", 2020),
    ("journal", "Journal of Thrombosis and Hemostasis", "Reviewer", "2005–present", "", "", 2005),
    ("journal", "Research and Practice in Thrombosis and Haemostasis", "Reviewer", "", "", "", 2020),
    ("journal", "Haemophilia", "Reviewer; Editorial Board 2011–2013", "2005–present", "", "", 2005),
    ("journal", "Blood", "Reviewer", "2000–2018", "", "", 2000),
    ("journal", "American Journal of Hematology", "Reviewer", "2005–2015", "", "", 2005),
    ("journal", "Pediatric Blood and Cancer", "Reviewer", "2004–2015", "", "", 2004),
    ("committee", "World Federation of Hemophilia USA", "Board of Directors", "2022–present", "", "", 2022),
    ("committee", "Medical Affairs Professional Society", "Patient Centricity Working Group", "2018–present", "", "", 2018),
    ("committee", "National Hemophilia Foundation", "Medical and Scientific Advisory Council", "2005–2008", "", "", 2005),
    ("committee", "Hemophilia Foundation of Illinois", "Board of Directors; Chair, Medical Advisory Committee", "1995–2002", "", "", 1995),
    ("committee", "International Society on Thrombosis and Haemostasis", "Factor VIII/IX Subcommittee, Scientific and Standardization Committee", "2009–2013", "", "", 2009),
]

# Current roles shown on Home and Projects
LEADERSHIP_PROJECTS = [
    ("World Federation of Hemophilia USA", "President", "Advances the global mission of the World Federation of Hemophilia in the United States.", "https://wfh.org/usa/", 2024, True),
    ("Pathway to Cures", "Entrepreneur in Residence", "Venture philanthropy from the National Bleeding Disorders Foundation, driving transformation in the diagnosis and treatment of blood disorders worldwide.", "https://www.pathwaytocures.org/", 2024, True),
    ("Bleeding Disorders Research Collaborative", "Interim Executive Director", "A new paradigm for collaborative research in bleeding disorders, from the National Bleeding Disorders Foundation.", "https://www.bleeding.org/research/bleeding-disorders-research-collaborative", 2024, False),
    ("Paladin Consortium", "Co-leader", "Transforming the pace of medicines development by optimizing collaboration between patient advocacy groups and industry.", "https://sites.tufts.edu/paladinconsortium/", 2024, False),
    ("Expert Review of Hematology", "Editor", "Editing a peer-reviewed journal covering the diagnosis and treatment of blood disorders.", "https://www.tandfonline.com/journals/ierr20", None, False),
    ("International humanitarian aid with WFH", "Regular participant", "Programs to advance the standard of care for people with hemophilia in low- and middle-income countries.", "https://wfh.org/", None, False),
]

TOPIC_RULES = [
    ("gene_therapy", r"gene (therapy|editing|transfer)|vector|aav|lexicon"),
    ("vwd", r"von willebrand|\bvwd\b|\bvwf\b"),
    ("inhibitor", r"inhibitor|immune tolerance|bypass|eptacog|emicizumab"),
    ("joint", r"synov|arthrop|joint|hemarthros|haemarthros|cartilage|bone resorption"),
    ("oncology", r"neuroblastoma|ganglioside|transplant|leukemi|leukaemi|cancer|tumou?r|metasta|lymphoma|breast"),
    ("hemophilia", r"h(a)?emophil|factor (viii|ix|vii)|fviii|fix\b|prophyla|bleed|coagulat|thromb|rixubis|advate|feiba"),
]


def topic_for(text):
    t = text.lower()
    for topic, pat in TOPIC_RULES:
        if re.search(pat, t):
            return "inhibitors" if topic == "inhibitor" else topic
    return "other"


class Command(BaseCommand):
    help = "Load CV content (publications, presentations, projects, career, organizations) into the database."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing content rows first.")

    def handle(self, *args, **opts):
        if opts["reset"]:
            for m in (Publication, Presentation, Project, Organization, CareerEntry):
                m.objects.all().delete()

        s = SiteSettings.get()
        if opts["reset"] or not s.bio:
            s.hero_intro, s.bio, s.pull_quote = HERO_INTRO, BIO, QUOTE
            s.save()

        if not s.photo:
            src = DATA.parent / "seed_media" / "portrait.jpg"
            if src.exists():
                from django.core.files import File
                with src.open("rb") as fh:
                    s.photo.save("portrait.jpg", File(fh), save=False)
        if not s.linkedin_url:
            s.linkedin_url = "https://www.linkedin.com/in/leonardvalentinomd/"
        s.save()

        data = json.loads(DATA.read_text(encoding="utf-8"))

        if not Publication.objects.exists():
            rows = []
            for p in data["publications"]:
                rows.append(Publication(title=p["title"], authors=p["authors"], journal=p["journal"][:400], year=p["year"] or 0,
                                        kind=p["kind"], url=p["url"][:500], topic=topic_for(p["title"] + " " + p["journal"])))
            Publication.objects.bulk_create(rows)
            fp = Publication.objects.filter(title__startswith="Mouse trials and human triumphs").first()
            if fp:
                fp.featured = True; fp.save()

        if not Presentation.objects.exists():
            Presentation.objects.bulk_create([Presentation(title=p["title"], event=p["event"], year=p["year"], kind=p["kind"])
                                              for p in data["presentations"]])
            fl = Presentation.objects.filter(kind="lecture", title__icontains="Hemophilic synovitis").first() \
                or Presentation.objects.filter(kind="lecture", title__icontains="Hemophilia").first()
            if fl:
                fl.featured = True; fl.save()

        if not Project.objects.exists():
            rows = [Project(title=t, role=r, description=d, url=u, start_year=y, ongoing=True, kind="leadership", featured=f)
                    for t, r, d, u, y, f in LEADERSHIP_PROJECTS]
            rows += [Project(title=p["title"], role=p["role"], description=p["description"], kind=p["kind"],
                             start_year=p["start"], end_year=p["end"]) for p in data["projects"]]
            Project.objects.bulk_create(rows)

        if not Organization.objects.exists():
            Organization.objects.bulk_create([Organization(kind=k, name=n, role=r, period=p, description=d, url=u, sort_year=y)
                                              for k, n, r, p, d, u, y in ORGS])

        if not CareerEntry.objects.exists():
            CareerEntry.objects.bulk_create([CareerEntry(kind=k, period=p, title=t, organization=o, details=d, sort_year=y)
                                             for k, p, t, o, d, y in CAREER])

        self.stdout.write(self.style.SUCCESS(
            f"Loaded: {Publication.objects.count()} publications, {Presentation.objects.count()} presentations, "
            f"{Project.objects.count()} projects, {Organization.objects.count()} organizations, {CareerEntry.objects.count()} career entries."))
