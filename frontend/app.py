from flask import Flask, request, session, redirect, url_for, render_template, send_from_directory
import sys
import requests
import feedparser
import re
import json
import os
import copy
from datetime import datetime
import subprocess

app = Flask(__name__, template_folder="../templates/", static_folder="../public/")
app.secret_key = "replace_this_with_a_secure_random_key"

# bază pentru path-uri relative
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "form_output.json")
REQUEST_SCRIPT = os.path.join(BASE_DIR, "..", "input", "request.py")
MATCH_SCRIPT = os.path.join(BASE_DIR, "..", "rag", "run_match_opp.py")

# fișierul cu descrierile oficiale ale oportunităților
SOURCES_PATH = os.path.join(BASE_DIR, "..", "data", "opportunities", "sources.json")


# ------------------- USERS & PERSISTENȚĂ -------------------

# Default mock user database
DEFAULT_USERS = {
    "demo@example.com": {
        "password": "password123",
        "name": "Demo Company",
        "email": "demo@example.com",
        "cui": "12345678",
        "numar_angajati": 50,
        "varsta_dezvoltator": 30,
        "additional_info_1": "",
        "additional_info_2": "",
        "additional_info_3": "",
        "additional_info_4": "",
        "additional_info_5": "",
        "additional_info_6": "",
    }
}


def load_users():
    users = copy.deepcopy(DEFAULT_USERS)
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("data"), dict):
                    saved = data["data"]
                    demo = users.get("demo@example.com", {})
                    for k, v in saved.items():
                        if k in demo and k != "password":
                            demo[k] = v
        except (json.JSONDecodeError, OSError):
            pass
    return users


def save_users():
    user = USERS.get("demo@example.com", {})
    safe_data = {k: v for k, v in user.items() if k != "password"}
    payload = {"data": safe_data}
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


USERS = load_users()

# fallback grants hardcodate – doar dacă nu avem JSON-uri
GRANTS = [
    {
        "id": 1,
        "title": "Innovation Grant",
        "requirements": [
            "Company registered > 1 year",
            "At least 3 employees",
            "Innovation project proposal",
        ],
        "met_requirements": ["Company registered > 1 year", "At least 3 employees"],
        "unmet_requirements": ["Innovation project proposal"],
        "sum_eur": 50000,
        "description": "Supports innovative projects in tech and software.",
        "required_documents": [
            "Business plan",
            "Financial statement",
            "Project proposal",
        ],
        "eligibility": False,
    },
    {
        "id": 2,
        "title": "Research Support",
        "requirements": [
            "Company must have at least 5 employees",
            "Annual revenue > 100k€",
        ],
        "met_requirements": [],
        "unmet_requirements": [
            "Company must have at least 5 employees",
            "Annual revenue > 100k€",
        ],
        "sum_eur": 20000,
        "description": "Provides funding for academic and industry research projects.",
        "required_documents": ["Research proposal", "Team CVs", "Budget breakdown"],
        "eligibility": False,
    },
    {
        "id": 3,
        "title": "Green Energy Fund",
        "requirements": [
            "Project reduces carbon footprint",
            "Company has experience in energy sector",
        ],
        "met_requirements": [
            "Project reduces carbon footprint",
            "Company has experience in energy sector",
        ],
        "unmet_requirements": [],
        "sum_eur": 75000,
        "description": "Grants for companies developing green energy solutions.",
        "required_documents": [
            "Project plan",
            "Environmental impact study",
            "Budget sheet",
        ],
        "eligibility": True,
    },
]


# ------------------- SOURCES & MATCHING HELPERS -------------------

def run_request_script():
    """
    Pornește scriptul ../input/request.py într-un proces separat.
    Scriptul poate folosi form_output.json ca input.
    """
    if not os.path.exists(REQUEST_SCRIPT):
        print(f"request.py not found at {REQUEST_SCRIPT}")
        return

    try:
        # rulează cu același interpreter de Python ca aplicația Flask
        subprocess.Popen([sys.executable, REQUEST_SCRIPT])
    except Exception as e:
        print(f"Error starting request.py: {e}")

def run_match_opp(cui: str):
    """
    Rulează modulul rag.run_match_opp cu:
      python -m rag.run_match_opp --cif <cui> --top-k 5

    Structură așteptată:
      <project_root>/
        rag/
          __init__.py
          run_match_opp.py
          recommendation.py
        frontend/
          app.py  (acest fișier)
    """
    if not cui:
        return

    # verificăm dacă există fișierul cu firma: ../data/firms/<cui>.json
    cui_json = os.path.join(BASE_DIR, "..", "data", "firms", f"{cui}.json")
    if not os.path.exists(cui_json):
        print(f"[run_match_opp] {cui_json} not found, skipping.")
        return

    # root-ul proiectului (un nivel mai sus de frontend/)
    project_root = os.path.join(BASE_DIR, "..")

    rag_folder = os.path.join(project_root, "rag")
    if not os.path.exists(rag_folder):
        print(f"[run_match_opp] rag folder not found at {rag_folder}")
        return

    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "rag.run_match_opp",   # 👈 modulul, cu doi de p
                "--cif",
                str(cui),
                "--top-k",
                "5",
            ],
            cwd=project_root,          # rulează din root-ul proiectului
        )
        print(f"[run_match_opp] Started rag.run_match_opp for CUI={cui}")
    except Exception as e:
        print(f"[run_match_opp] Error starting rag.run_match_opp: {e}")


def load_sources():
    """Încarcă ../data/opportunities/sources.json."""
    if not os.path.exists(SOURCES_PATH):
        print(f"Warning: sources.json not found at {SOURCES_PATH}")
        return {}
    try:
        with open(SOURCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sources.json:", e)
        return {}


SOURCES = load_sources()

def parse_date_to_dateobj(raw):
    """
    Primește string de dată (ex: '2025-11-07', '2026-01-12T17:00:00+01:00')
    și întoarce un datetime.date sau None.
    """
    if not raw or not isinstance(raw, str):
        return None

    s = raw.strip()
    if s.lower() == "continuous":
        return None

    # Încercăm ISO full (inclusiv cu offset)
    try:
        # fromisoformat știe și de 'YYYY-MM-DD' și de 'YYYY-MM-DDTHH:MM:SS+HH:MM'
        dt = datetime.fromisoformat(s.replace("Z", ""))
        return dt.date()
    except ValueError:
        pass

    # Încercăm doar primele 10 caractere (YYYY-MM-DD)
    try:
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.date()
    except ValueError:
        return None


def format_dmy(date_obj):
    """Formatăm data în stil european: zi.lună.an (ex: 07.11.2025)."""
    if not date_obj:
        return ""
    return date_obj.strftime("%d.%m.%Y")



def find_source_by_id(grant_id: str):
    """Caută grantul după id în `grants`, `vcs`, `accelerators` din sources.json."""
    data = SOURCES or {}
    for key in ("grants", "vcs", "accelerators"):
        for item in data.get(key, []):
            if str(item.get("id")) == str(grant_id):
                return item
    return None


def load_match_opportunities(cui: str):
    """
    Încărcă ../outputs/<cui>/match_opportunities.json.

    Returnează:
      - None  -> fișierul NU există (show loading page)
      - []    -> fișierul există dar nu are rezultate / e gol
      - [..]  -> listă de match-uri valide
    """
    if not cui:
        return None

    path = os.path.join(BASE_DIR, "..", "outputs", str(cui), "match_opportunities.json")
    if not os.path.exists(path):
        # fișierul nu există încă -> vrem pagina de loading
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"Error loading match_opportunities for CUI {cui}: {e}")
        # considerăm că fișierul e stricat, tratăm ca și cum nu ar avea rezultate
        return []


def build_list_grants_from_matches(matches):
    """
    Pentru pagina /grants: mapăm direct din match_opportunities.json:

      - eligibility        ← fieldul m["eligibility"] (bool)
      - grant name         ← m["title"]
      - funding value      ← m["funding"] (raw) + sum_eur numeric pentru sortare
      - key requirements   ← m["eligibility_criteria"]
      - number_of_docs     ← m["number_of_docs"]
      - application_period ← cel mai vechi → cel mai nou din m["deadlines"], în format zi.lună.an
    """
    grants = []
    for m in matches:
        # eligibility direct din JSON
        eligibility = bool(m.get("eligibility", False))

        # funding: raw + numeric pentru sortare
        funding_raw = m.get("funding")
        if isinstance(funding_raw, (int, float)):
            sum_eur = float(funding_raw)
        else:
            sum_eur = 0.0  # pentru sortare; la afișare poți folosi funding_raw direct

        # number of required documents
        num_docs = m.get("number_of_docs")
        try:
            num_docs_int = int(num_docs) if num_docs is not None else 0
        except (TypeError, ValueError):
            num_docs_int = 0

        # application period din deadlines: cea mai veche → cea mai nouă
        deadlines = m.get("deadlines") or []
        date_objs = []
        for d in deadlines:
            dt = parse_date_to_dateobj(d.get("date"))
            if dt:
                date_objs.append(dt)

        application_period = ""
        if date_objs:
            start = min(date_objs)
            end = max(date_objs)
            if start == end:
                application_period = format_dmy(start)
            else:
                application_period = f"{format_dmy(start)} → {format_dmy(end)}"

        requirements = m.get("eligibility_criteria") or []

        grants.append(
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "description": None,
                "requirements": requirements,
                "met_requirements": [],
                "unmet_requirements": requirements,
                "sum_eur": sum_eur,
                "funding_raw": funding_raw,
                "required_documents": [f"Document {i+1}" for i in range(num_docs_int)],
                "eligibility": eligibility,
                "application_period": application_period,
                "semantic_score": m.get("semantic_score"),
                "source_url": m.get("source_url"),
                "type": m.get("type"),
            }
        )

    return grants


def pick_application_form_link(source: dict):
    """
    Ia linkul de application form din diverse câmpuri posibile.
    Fallback la source_url dacă nu găsim altceva.
    """
    if not source:
        return None
    return (
        source.get("application_form_url")
        or source.get("application_url")
        or source.get("application_link")
        or source.get("apply_url")
        or source.get("funding_call_url")
        or source.get("source_url")
    )


def build_grant_from_source_and_match(source, match):
    """
    Pentru pagina fiecărui grant:
      - document names          ← source["required_documents"]
      - reqs                    ← source["eligibility_criteria"] (sau similar)
      - grant name              ← source["title"] / "name"
      - grant funding value     ← source["funding_max"] / "funding" / "cash_stipend"
      - application form link   ← diverse câmpuri application_* / source_url
      - perioada aplicare       ← cel mai vechi → cel mai nou din source["deadlines"], zi.lună.an
    """
    # requirements
    requirements = (
        source.get("eligibility_criteria")
        or source.get("eligibility_criteria_short")
        or []
    )
    if requirements is None:
        requirements = []

    # document names
    required_documents = source.get("required_documents") or []

    # funding value
    sum_eur = 0.0
    funding_max = source.get("funding_max")
    funding_field = source.get("funding")
    cash_stipend = source.get("cash_stipend")

    if isinstance(funding_max, (int, float)):
        sum_eur = float(funding_max)
    elif isinstance(funding_field, (int, float)):
        sum_eur = float(funding_field)
    elif isinstance(cash_stipend, (int, float)):
        sum_eur = float(cash_stipend)

    # perioada aplicare din deadlines sau câmpuri text
    application_period = ""
    deadlines = source.get("deadlines") or []
    date_objs = []
    for d in deadlines:
        dt = parse_date_to_dateobj(d.get("date"))
        if dt:
            date_objs.append(dt)

    if date_objs:
        start = min(date_objs)
        end = max(date_objs)
        if start == end:
            application_period = format_dmy(start)
        else:
            application_period = f"{format_dmy(start)} → {format_dmy(end)}"
    else:
        # fallback pe câmpuri text, fără oră
        raw_period = (
            source.get("application_period")
            or source.get("application_period_text")
            or source.get("deadline")
            or source.get("call_deadline")
            or ""
        )
        application_period = raw_period

    # eligibility & semantic_score din match_opps
    semantic_score = None
    eligibility = False
    match_reasons = []
    if match:
        semantic_score = match.get("semantic_score")
        match_reasons = match.get("match_reasons") or []
        eligibility = bool(match.get("eligibility", False))

    if eligibility and requirements:
        met_requirements = requirements
        unmet_requirements = []
    else:
        met_requirements = []
        unmet_requirements = requirements

    title = source.get("title") or source.get("name") or "Untitled"
    description = source.get("summary") or ""

    application_form_url = pick_application_form_link(source)

    return {
        "id": source.get("id"),
        "title": title,
        "description": description,
        "requirements": requirements,
        "met_requirements": met_requirements,
        "unmet_requirements": unmet_requirements,
        "sum_eur": sum_eur,
        "required_documents": required_documents,
        "eligibility": eligibility,
        "application_period": application_period,
        "semantic_score": semantic_score,
        "match_reasons": match_reasons,
        "application_form_url": application_form_url,
        "source_url": application_form_url or source.get("source_url"),
    }


# ------------------- Helper user curent -------------------

def get_current_user():
    """Return the user dict from session email, or None."""
    email = session.get("user")
    if email:
        return USERS.get(email)
    return None


# ------------------- Routes -------------------

@app.route("/")
def index():
    feed_url = 'https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/grantTenders-rss.xml'
    items = []

    try:
        r = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:10]:
            description_html = entry.get('description', '')
            deadline_match = re.search(r'<b>Deadline</b>:\s*(.*?)<br/>', description_html)
            deadline = deadline_match.group(1).strip() if deadline_match else 'No deadline'
            items.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'pubDate': entry.get('published', ''),
                'deadline': deadline
            })
    except Exception as e:
        print("Error fetching EU grants:", e)

    user = get_current_user()
    return render_template("index.html", user=user, grants=items)


@app.route("/demo")
def demo():
    user = get_current_user()
    if not user:
        # demo folosește GRANTS hardcodate
        return render_template("demo.html", user=user, grants=GRANTS)
    else:
        return redirect(url_for("grants"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        email = request.args.get("email")
        password = request.args.get("password")

        # If both were provided, try to auto-login
        if email and password:
            user = USERS.get(email)
            if user and user.get("password") == password:
                session["user"] = email
                return redirect(url_for("index"))

        # Otherwise show the login form normally
        return render_template("login.html", error=None)

    email = request.form.get("email")
    password = request.form.get("password")
    user = USERS.get(email)

    if not user or user.get("password") != password:
        return render_template("login.html", error="Invalid email or password")

    session["user"] = email
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/account", methods=["GET", "POST"])
def account():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")
        user["cui"] = request.form.get("cui", "").strip()

        try:
            user["numar_angajati"] = int(request.form.get("numar_angajati", "0"))
        except ValueError:
            user["numar_angajati"] = 0

        try:
            user["varsta_dezvoltator"] = int(request.form.get("varsta_dezvoltator", "0"))
        except ValueError:
            user["varsta_dezvoltator"] = None

        for i in range(1, 7):
            key = f"additional_info_{i}"
            user[key] = request.form.get(key, "").strip()

        # salvăm profilul în form_output.json
        save_users()

        # rulează request.py (pipeline-ul ăla inițial)
        run_request_script()

        # dacă user-ul a apăsat "Find grants", rulăm și matcher-ul RAG
        if action == "find_grants":
            run_match_opp(user.get("cui"))
            return redirect(url_for("grants"))

        message = "Changes saved successfully!"
        return render_template("account.html", user=user, message=message)
    return render_template("account.html", user=user)


@app.route("/grants")
def grants():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    cui = user.get("cui")

    # la fiecare acces la /grants, dacă avem <cui>.json,
    # pornim scriptul de matching cu RAG
    run_match_opp(cui)

    matches = load_match_opportunities(cui)

    # match_opportunities.json nu există încă -> pagina de loading
    if matches is None:
        return render_template("grants_loading.html", user=user)

    if matches:
        list_grants = build_list_grants_from_matches(matches)
        sorted_grants = sorted(
            list_grants,
            key=lambda g: (
                not g["eligibility"],
                -g["sum_eur"],
                len(g["required_documents"]),
            ),
        )
    else:
        # fallback demo
        sorted_grants = sorted(
            GRANTS,
            key=lambda g: (
                not g["eligibility"],
                -g["sum_eur"],
                len(g["required_documents"]),
            ),
        )

    return render_template("grants.html", grants=sorted_grants, user=user)


@app.route("/grants/<grant_id>")
def grant_detail(grant_id):
    user = get_current_user()

    cui = user.get("cui") if user else None
    matches = load_match_opportunities(cui) if cui else []
    match = next((m for m in matches if str(m.get("id")) == str(grant_id)), None)

    source = find_source_by_id(grant_id)
    grant = None

    if source:
        grant = build_grant_from_source_and_match(source, match)
    else:
        # fallback: dacă id-ul e numeric, căutăm în GRANTS hardcodate
        try:
            numeric_id = int(grant_id)
        except ValueError:
            numeric_id = None
        if numeric_id is not None:
            grant = next((g for g in GRANTS if g["id"] == numeric_id), None)

    if not grant:
        return "Grant not found", 404

    return render_template("grant_detail.html", grant=grant, user=user)


@app.route("/grants/<grant_id>/documents")
def grant_documents(grant_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    cui = user.get("cui")

    # încercăm să reconstruim grant-ul ca înainte
    matches = load_match_opportunities(cui) if cui else []
    match = next((m for m in matches if str(m.get("id")) == str(grant_id)), None)

    source = find_source_by_id(grant_id)
    grant = None

    if source:
        grant = build_grant_from_source_and_match(source, match)
    else:
        try:
            numeric_id = int(grant_id)
        except ValueError:
            numeric_id = None
        if numeric_id is not None:
            grant = next((g for g in GRANTS if g["id"] == numeric_id), None)

    if not grant:
        return "Grant not found", 404

    # 🟦 AICI construim lista de documente din folderul ../data/generated/<cui>
    documents = []
    if cui:
        gen_dir = os.path.join(BASE_DIR, "..", "data", "generated", str(cui))
        if os.path.isdir(gen_dir):
            for filename in sorted(os.listdir(gen_dir)):
                # vrem doar PDF-uri
                if not filename.lower().endswith(".pdf"):
                    continue

                # numele afișat în UI – dacă vrei poți să-l "prettify"
                display_name = filename  # sau fă replace("_", " ") etc.

                documents.append(
                    {
                        "name": display_name,
                        "has_file": True,
                        "filename": filename,
                        "download_url": url_for(
                            "download_generated", cui=cui, filename=filename
                        ),
                    }
                )

    # fallback: dacă nu avem nimic generat, folosim totuși required_documents ca listă de "pending"
    if not documents:
        doc_names = grant.get("required_documents") or []
        for doc_name in doc_names:
            documents.append(
                {
                    "name": doc_name,
                    "has_file": False,
                    "filename": None,
                    "download_url": None,
                }
            )

    return render_template("generate_documents.html", grant=grant, user=user, documents=documents)

@app.route("/generated/<cui>/<path:filename>")
def download_generated(cui, filename):
    gen_dir = os.path.join(BASE_DIR, "..", "data", "generated", str(cui))
    full_path = os.path.join(gen_dir, filename)

    if not os.path.exists(full_path):
        return "File not found", 404

    return send_from_directory(gen_dir, filename, as_attachment=True)
    

if __name__ == "__main__":
    app.run(debug=True)
