import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.secret_key = "special-topics-demo"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "special_topics.db")
XSS_DIR = os.path.join(BASE_DIR, "xss_phishing_site")

last_query = {
    "text": "",
    "rows": 0,
}

login_result = {
    "status": "idle",
    "headline": "Awaiting login attempt",
    "detail": "Once you try to log in, the simulated secure screen below will reflect how the system responds.",
    "rows": [],
}

PAYLOAD_EXAMPLES = [
    {
        "title": "Classic bypass",
        "username": "' OR 1=1 --",
        "password": "(anything)",
        "effect": "Returns every user because condition is always true."
    },
    {
        "title": "Grab first account",
        "username": "' OR 1=1 LIMIT 1 --",
        "password": "",
        "effect": "Pulls only the first row, often the admin."
    },
    {
        "title": "Comment out password",
        "username": "' OR '1'='1",
        "password": "' OR '1'='1' --",
        "effect": "Breaks out of password clause and short-circuits authentication."
    },
    {
        "title": "Targeted username",
        "username": "admin' --",
        "password": "",
        "effect": "Forces query to only check username and ignores password entirely."
    },
]

SAMPLE_USERS = [
    ("admin", "admin123"),
    ("professor", "gradeA!"),
    ("student", "pa55word"),
    ("analyst", "sup3rSecret"),
    ("it_support", "Ticket#1042"),
    ("guest", "guest"),
    ("auditor", "Controls2024"),
    ("developer", "dev_pass!"),
    ("finance_mgr", "Ledger$ecure"),
    ("intern", "summer2024"),
    ("researcher", "dataLove"),
    ("principal", "SchoolRules"),
]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        SAMPLE_USERS,
    )
    conn.commit()
    conn.close()

def fetch_users():
    conn = get_db_connection()
    users = conn.execute("SELECT username, password FROM users ORDER BY id").fetchall()
    conn.close()
    return users

@app.route("/")
def index():
    users = fetch_users()
    return render_template(
        "index.html",
        users=users,
        last_query=last_query,
        login_result=login_result,
        payload_examples=PAYLOAD_EXAMPLES,
    )


@app.route("/xss-demo/")
def xss_demo_index():
    return send_from_directory(XSS_DIR, "index.html")


@app.route("/xss-demo")
def xss_demo_redirect():
    return redirect(url_for("xss_demo_index"))


@app.route("/xss-demo/<path:asset>")
def xss_assets(asset):
    return send_from_directory(XSS_DIR, asset)


@app.route("/xss_phishing_site/")
def legacy_xss_index():
    return send_from_directory(XSS_DIR, "index.html")


@app.route("/xss_phishing_site/<path:asset>")
def legacy_xss_assets(asset):
    return send_from_directory(XSS_DIR, asset)

@app.route("/signup", methods=["POST"])
def signup():
    global last_query
    username = request.form.get("new_username", "").strip()
    password = request.form.get("new_password", "").strip()

    if not username or not password:
        flash("Please provide both a username and password.", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        last_query = {
            "text": "INSERT INTO users (username, password) VALUES (?, ?)",
            "rows": 1,
        }
        flash("New account created safely! Now try logging in, even with malicious input.", "success")
    except sqlite3.IntegrityError:
        last_query = {
            "text": "INSERT INTO users (username, password) VALUES (?, ?)",
            "rows": 0,
        }
        flash("That username already exists.", "error")
    finally:
        conn.close()

    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    global last_query, login_result
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    vulnerable_query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password
        + "'"
    )

    conn = get_db_connection()
    rows = conn.execute(vulnerable_query).fetchall()
    conn.close()

    last_query = {
        "text": vulnerable_query,
        "rows": len(rows),
    }

    sanitized_rows = [
        {"username": row["username"], "password": row["password"]}
        for row in rows
    ]

    if rows:
        flash(
            "Login successful! Did the credentials actually exist, or did SQL injection bypass the check?",
            "success",
        )
        login_result = {
            "status": "success",
            "headline": "Access granted",
            "detail": f"The query returned {len(rows)} row(s). Sensitive data leaked below shows the risk.",
            "rows": sanitized_rows,
        }
    else:
        flash(
            "Login failed. Try a payload such as ' OR 1=1 -- in the username field to bypass the check.",
            "error",
        )
        login_result = {
            "status": "denied",
            "headline": "Access denied",
            "detail": "No rows matched the WHERE clause. Attack attempt unsuccessful this time.",
            "rows": [],
        }

    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
