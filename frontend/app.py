from flask import Flask, request, session, redirect, url_for, jsonify, render_template
import sys
import requests
import feedparser
import re
import json
import os
import copy

app = Flask(__name__, template_folder="../templates/", static_folder="../public/")
app.secret_key = "replace_this_with_a_secure_random_key"

USERS_FILE = "users.json"

# Default mock user database (folosit dacă nu există încă users.json)
DEFAULT_USERS = {
    "demo@example.com": {
        "password": "password123",
        "name": "Demo User",
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
    """Încărcăm utilizatorii din users.json sau folosim DEFAULT_USERS dacă nu există / e corupt."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    # fallback: deep copy ca să nu stricăm DEFAULT_USERS
    return copy.deepcopy(DEFAULT_USERS)


def save_users():
    """Salvăm USERS în users.json (persistență locală)."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, ensure_ascii=False, indent=2)


# baza de date în memorie, încărcată din fișier (sau default)
USERS = load_users()

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
        "eligibility": False,  # still ineligible because not all requirements met
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


@app.route("/")
def index():
    feed_url = 'https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/grantTenders-rss.xml'
    items = []

    try:
        # Use requests with User-Agent
        r = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()  # Raise error if request failed

        # Parse RSS content
        feed = feedparser.parse(r.content)

        # Safety check
        if not hasattr(feed, 'entries') or not feed.entries:
            print("Feed is empty or cannot be parsed")
        else:
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
        items = []  # ensure items is always a list

    # pe home nu afișăm date de firmă dacă nu e logat
    user = None
    return render_template("index.html", user=user, grants=items)


@app.route("/demo")
def demo():
    user = USERS.get(session["user"]) if "user" in session else None
    return render_template("demo.html", user=user, grants=GRANTS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Show login page
        return render_template("login.html")

    # POST: handle login
    email = request.form.get("email")
    password = request.form.get("password")

    user = USERS.get(email)

    if not user or user.get("password") != password:
        # Invalid login, show error
        return render_template("login.html", error="Invalid email or password")

    # Successful login
    session["user"] = email
    return redirect(url_for("index"))


@app.route("/account", methods=["GET", "POST"])
def account():
    if "user" not in session:
        return redirect(url_for("login"))

    user = USERS.get(session["user"])
    if not user:
        # fallback: dacă pentru vreun motiv nu există, îl recreăm din default
        user = copy.deepcopy(DEFAULT_USERS["demo@example.com"])
        USERS[session["user"]] = user

    if request.method == "POST":
        action = request.form.get("action")  # ce buton a fost apăsat

        # Update CUI, Numar de angajati si varsta dezvoltator
        cui = request.form.get("cui", "").strip()
        numar_angajati = request.form.get("numar_angajati", "0")
        varsta_dezvoltator = request.form.get("varsta_dezvoltator", "")

        user["cui"] = cui

        try:
            user["numar_angajati"] = int(numar_angajati)
        except (TypeError, ValueError):
            user["numar_angajati"] = 0

        try:
            user["varsta_dezvoltator"] = int(varsta_dezvoltator)
        except (TypeError, ValueError):
            user["varsta_dezvoltator"] = None

        # Additional info 1..6
        for i in range(1, 7):
            key = f"additional_info_{i}"
            user[key] = request.form.get(key, "").strip()

        # Salvăm tot USERS în fișier pentru persistență locală
        save_users()

        # dacă a apăsat "Find grants", redirecționăm după save
        if action == "find_grants":
            return redirect(url_for("grants"))

        message = "Changes saved successfully!"
        return render_template("account.html", user=user, message=message)

    return render_template("account.html", user=user)


@app.route("/grants")
def grants():
    if "user" not in session:
        return redirect(url_for("login"))

    user = USERS.get(session["user"])

    # sortare: 1) eligibil (True) înainte, 2) sum_eur desc, 3) mai puține documente înainte
    sorted_grants = sorted(
        GRANTS,
        key=lambda g: (
            not g["eligibility"],             # False (eligibil) înainte de True (neeligibil)
            -g["sum_eur"],                    # sumă mai mare înainte
            len(g["required_documents"]),     # mai puține documente înainte
        ),
    )

    return render_template("grants.html", grants=sorted_grants, user=user)


@app.route("/grants/<int:grant_id>")
def grant_detail(grant_id):
    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if not grant:
        return "Grant not found", 404
    return render_template("grant_detail.html", grant=grant)


@app.route("/grants/<int:grant_id>/documents")
def grant_documents(grant_id):
    if "user" not in session:
        return redirect(url_for("login"))

    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if not grant:
        return "Grant not found", 404

    user = USERS.get(session["user"])
    # aici, pe viitor, vei integra backend-ul de AI care chiar generează documentele
    return render_template("generate_documents.html", grant=grant, user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
