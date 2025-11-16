from flask import Flask, request, session, redirect, url_for, render_template
import sys
import requests
import feedparser
import re
import json
import os
import copy

app = Flask(__name__, template_folder="../templates/", static_folder="../public/")
app.secret_key = "replace_this_with_a_secure_random_key"

# fișierul de output pentru formular
USERS_FILE = "form_output.json"

# Default mock user database
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


# ------------------- Helper -------------------
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
        return render_template("demo.html", user=user, grants=GRANTS)
    else:
        return redirect(url_for("grants"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    user = USERS.get(email)

    if not user or user.get("password") != password:
        return render_template("login.html", error="Invalid email or password")

    # Store only email in session
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

        save_users()

        if action == "find_grants":
            return redirect(url_for("grants"))

        message = "Changes saved successfully!"
        return render_template("account.html", user=user, message=message)

    return render_template("account.html", user=user)


@app.route("/grants")
def grants():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    sorted_grants = sorted(
        GRANTS,
        key=lambda g: (
            not g["eligibility"],
            -g["sum_eur"],
            len(g["required_documents"]),
        ),
    )
    return render_template("grants.html", grants=sorted_grants, user=user)


@app.route("/grants/<int:grant_id>")
def grant_detail(grant_id):
    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if not grant:
        return "Grant not found", 404
    user = get_current_user()
    return render_template("grant_detail.html", grant=grant, user=user)


@app.route("/grants/<int:grant_id>/documents")
def grant_documents(grant_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if not grant:
        return "Grant not found", 404

    return render_template("generate_documents.html", grant=grant, user=user)


if __name__ == "__main__":
    app.run(debug=True)
