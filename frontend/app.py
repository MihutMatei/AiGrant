from flask import Flask, request, session, redirect, url_for, jsonify, render_template

app = Flask(__name__, template_folder="../templates/", static_folder="../public/")
app.secret_key = "replace_this_with_a_secure_random_key"

# Mock user database (replace with real DB later)
USERS = {
    "demo@example.com": {
        "password": "password123",
        "name": "Demo User",
        "email": "demo@example.com",
        "cui": "12345678",
        "numar_angajati": 50,
    }
}

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
    if "user" in session:
        return redirect(url_for("account"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Show login page
        return render_template("login.html")

    # POST: handle login
    email = request.form.get("email")
    password = request.form.get("password")

    user = USERS.get(email)

    if not user or user["password"] != password:
        # Invalid login, show error
        return render_template("login.html", error="Invalid email or password")

    # Successful login
    session["user"] = email
    return redirect(url_for("account"))


@app.route("/account", methods=["GET", "POST"])
def account():
    if "user" not in session:
        return redirect(url_for("login"))

    user = USERS[session["user"]]

    if request.method == "POST":
        # Update CUI and Numar de angajati
        cui = request.form.get("cui")
        numar_angajati = request.form.get("numar_angajati")

        user["cui"] = cui
        try:
            user["numar_angajati"] = int(numar_angajati)
        except ValueError:
            user["numar_angajati"] = 0

        message = "Changes saved successfully!"
        return render_template("account.html", user=user, message=message)

    return render_template("account.html", user=user)


@app.route("/grants")
def grants():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("grants.html", grants=GRANTS)


@app.route("/grants/<int:grant_id>")
def grant_detail(grant_id):
    grant = next((g for g in GRANTS if g["id"] == grant_id), None)
    if not grant:
        return "Grant not found", 404
    return render_template("grant_detail.html", grant=grant)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
