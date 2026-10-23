"""Parse the CV text (pdftotext -layout) into core/data/cv_data.json"""
import json, re, sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
HDR = re.compile(r"^\s*Leonard Anthony J\. Valentino, M\.D\.\s+Page \d+ of \d+")

def clean(ls):
    return [l for l in ls if not HDR.match(l) and not l.startswith("\f")]

def idx(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip().startswith(prefix):
            return i
    raise KeyError(prefix)

def squash(s):
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"(?<=[A-Za-z])- (?=[a-z])", "-", s)

# ---------- numbered lists (lectures / abstracts)
def numbered(a, b):
    items, cur = [], None
    for l in clean(lines[a:b]):
        m = re.match(r"^\s{0,3}(\d+)\.\s{2,}(.*)", l)
        if m:
            cur = [m.group(2)]; items.append(cur)
        elif cur is not None and l.strip():
            cur.append(l.strip())
    return [squash(" ".join(x)) for x in items]

i_lect = idx("Selected Invited Lectures"); i_abs = idx("Presented Abstracts"); i_pub = idx("PUBLICATIONS")
lectures = numbered(i_lect + 1, i_abs)
abstracts = numbered(i_abs + 1, i_pub)

def year_of(t):
    ys = re.findall(r"(19\d{2}|20\d{2})", t)
    return int(ys[-1]) if ys else None

def split_title(t):
    t = t.replace("“", '"').replace("”", '"')
    m = re.match(r'^"(.+?)"[,.]?\s*(.*)$', t)
    if m and m.group(1):
        return m.group(1).strip(" ,"), m.group(2).strip(" .")
    return t, ""

def pres(items, kind):
    out = []
    for t in items:
        title, event = split_title(t)
        out.append(dict(title=title, event=event, year=year_of(t), kind=kind))
    return out

presentations = pres(lectures, "lecture") + pres(abstracts, "abstract")

# ---------- publications
def pubs():
    a = idx("Manuscripts published in peer reviewed journals")
    b = idx("Updated 30 April 2026")
    ent, cur = [], None
    for l in clean(lines[a + 5:b]):
        if not l.strip():
            continue
        if l.startswith(" ") :
            if cur is not None: cur.append(l.strip())
        else:
            cur = [l.strip()]; ent.append(cur)
    out = []
    for e in ent:
        t = squash(" ".join(e))
        doi = ""
        m = re.search(r"(https?://\S+)$", t)
        if m: doi = m.group(1); t = t[:m.start()].strip()
        m = re.match(r"^(.*?)\((\d{4})[a-z]?\)\.\s+(.*)$", t)
        if not m: continue
        authors, year, rest = squash(m.group(1)).rstrip(","), int(m.group(2)), m.group(3)
        m2 = re.match(r"^(.+?[?!.])\s+(.*)$", rest)
        title, journal = (m2.group(1), m2.group(2)) if m2 else (rest, "")
        out.append(dict(authors=authors, year=year, title=title.rstrip("."), journal=journal.rstrip("."), url=doi, kind="article"))
    return out
publications = pubs()

# reviews (13 irregular entries, entered by hand from the CV)
REVIEWS = [
 ("Valentino LA, Ewenstein B, Navickis RJ, Wilkes MM", "Central venous access devices in haemophilia", "Haemophilia 2004;10(2):134-46", 2004),
 ("Valentino LA, Santagostino E, Blanchette V, van den Berg M", "Managing the pediatric patient and the adolescent/adult transition", "Semin Thromb Hemost 2006;32 Suppl 2:28-31", 2006),
 ("Valentino LA, Scheiflinger F", "Future aspects of hemophilia research and care", "Semin Thromb Hemost 2006;32 Suppl 2:32-8", 2006),
 ("Valentino LA", "FEIBA prophylaxis for patients with haemophilia and inhibitors", "Haemophilia 2006;12 Suppl 5:26-31", 2006),
 ("Rodriguez-Merchan EC, Valentino L, Quintana M", "Prophylaxis and treatment of chronic synovitis in haemophilia patients with inhibitors", "Haemophilia 2007;13 Suppl 3:45-8", 2007),
 ("Valentino LA, Hakobyan N, Rodriguez N, Hoots WK", "Pathogenesis of haemophilic synovitis: experimental studies on blood-induced joint damage", "Haemophilia 2007;13 Suppl 3:10-3", 2007),
 ("Hoots WK, Rodriguez N, Boggio L, Valentino LA", "Pathogenesis of haemophilic synovitis: clinical aspects", "Haemophilia 2007;13 Suppl 3:4-9", 2007),
 ("Valentino LA, McLeod B", "Hemostasis and Transfusion", "In: Rush University Medical Center Review of Surgery, 4th edition. Philadelphia: Saunders Elsevier; 2007. p. 66-72", 2007),
 ("Verma N, Valentino LA, Chawla A", "Arthroscopic synovectomy in haemophilia: indications, technique and results", "Haemophilia 2007;13 Suppl 3:38-44", 2007),
 ("Pipe SW, Valentino LA", "Optimizing outcomes for patients with severe haemophilia A", "Haemophilia 2007;13 Suppl 4:1-16", 2007),
 ("Valentino LA", "Blood flows everywhere", "AAP News, October 2008", 2008),
 ("Valentino LA, Ismael Y, Grygotis M", "Novel drugs to treat hemophilia", "Expert Opinion on Emerging Drugs", 2011),
 ("Valentino LA, Kawji M, et al.", "Venous access in the management of hemophilia", "Blood Rev 2011;25(1):11-15", 2011),
]
for au, ti, jo, yr in REVIEWS:
    publications.append(dict(authors=au, title=ti, journal=jo, year=yr, url="", kind="review"))

# chapters / books
a = idx("Proceedings, Supplements"); b = idx("Manuscripts published in peer reviewed journals")
cur, ent = None, []
for l in clean(lines[a + 1:b]):
    if re.match(r"^\s*\d+\.\s{2,}", l): cur = [re.sub(r"^\s*\d+\.\s+", "", l)]; ent.append(cur)
    elif cur and l.strip(): cur.append(l.strip())
for e in ent:
    t = squash(" ".join(e))
    publications.append(dict(authors="", title=t, journal="", year=year_of(t) or 0, url="", kind="chapter"))

# ---------- projects (funding)
def projects(a, b, kind):
    ent, cur = [], None
    for l in clean(lines[a:b]):
        m = re.match(r"^\s{0,6}(\d{4}(?:-\d{2,4})?)\s{2,}(.*)", l)
        if m: cur = [m.group(1), m.group(2).strip()]; ent.append(cur)
        elif cur and l.strip() and re.match(r"^\s{8,}", l): cur.append(l.strip())
    out = []
    for e in ent:
        span, text = e[0], squash(" ".join(e[1:]))
        y1 = int(span[:4]); y2 = y1
        if "-" in span:
            s = span.split("-")[1]
            y2 = int(s) if len(s) == 4 else (y1 // 100) * 100 + int(s)
            if y2 < y1: y2 += 100
        role, _, rest = text.partition(", ")
        rest = re.sub(r",?\s*total direct costs?,?\s*\$?\s*[\d,\.]+\s*$", "", rest, flags=re.I).strip(" ,")
        rest = re.sub(r",?\s*\$\s*[\d,\.]+\s*$", "", rest).strip(" ,")
        out.append(dict(role=role, title=rest[:250], description=rest, start=y1, end=y2, kind=kind))
    return out

projs = (projects(idx("Laboratory Research Funding"), idx("Clinical Research Funding"), "laboratory")
         + projects(idx("Clinical Research Funding"), idx("Educational Funding"), "clinical")
         + projects(idx("Educational Funding"), idx("Students, Residents"), "educational"))

Path("core/data").mkdir(parents=True, exist_ok=True)
Path("core/data/cv_data.json").write_text(json.dumps(dict(publications=publications, presentations=presentations, projects=projs), indent=1, ensure_ascii=False), encoding="utf-8")
print(len(publications), {k: sum(1 for p in publications if p['kind']==k) for k in ('article','review','chapter')}, len(presentations), len(projs))
