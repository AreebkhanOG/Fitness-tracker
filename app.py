from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
from datetime import date, datetime
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fitness.db"

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"

QUOTES = [
    "Success starts with self-discipline.",
    "Small progress is still progress.",
    "Your body can stand almost anything. It is your mind you have to convince.",
    "The hardest part is showing up. You already did that.",
    "One healthy choice at a time.",
    "Consistency beats intensity when intensity is inconsistent.",
    "You do not have to be extreme, just consistent.",
    "A little progress each day adds up to big results.",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            water INTEGER DEFAULT 0,
            steps INTEGER DEFAULT 0,
            active_minutes INTEGER DEFAULT 0,
            calories INTEGER DEFAULT 0,
            UNIQUE(user_id, log_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            logged_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def ensure_today_log(user_id):
    today = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO daily_logs (user_id, log_date) VALUES (?, ?)",
        (user_id, today),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM daily_logs WHERE user_id = ? AND log_date = ?",
        (user_id, today),
    ).fetchone()
    conn.close()
    return row


def bmi_for(height_cm, weight_kg):
    height_m = height_cm / 100
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m * height_m), 1)


def bmi_label(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Healthy"
    if bmi < 30:
        return "Overweight"
    return "High"


@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("welcome.html")


@app.route("/setup", methods=["POST"])
def setup():
    name = request.form.get("name", "").strip()
    age = request.form.get("age", type=int)
    height = request.form.get("height", type=float)
    weight = request.form.get("weight", type=float)

    if not name or not age or not height or not weight or age <= 0 or height <= 0 or weight <= 0:
        return render_template("welcome.html", error="Please enter valid information in all fields."), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, age, height, weight, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, age, height, weight, datetime.now().isoformat(timespec="seconds")),
    )
    user_id = cursor.lastrowid
    conn.execute(
        "INSERT INTO weight_logs (user_id, weight, logged_at) VALUES (?, ?, ?)",
        (user_id, weight, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()

    session["user_id"] = user_id
    ensure_today_log(user_id)
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    daily = ensure_today_log(user["id"])
    bmi = bmi_for(user["height"], user["weight"])

    conn = get_db()
    history = conn.execute(
        "SELECT weight, logged_at FROM weight_logs WHERE user_id = ? ORDER BY id DESC LIMIT 7",
        (user["id"],),
    ).fetchall()
    conn.close()
    history = list(reversed(history))

    return render_template(
        "dashboard.html",
        user=user,
        daily=daily,
        bmi=bmi,
        bmi_label=bmi_label(bmi),
        quote=random.choice(QUOTES),
        weight_history=history,
    )


@app.route("/api/water", methods=["POST"])
def update_water():
    user = current_user()
    if not user:
        return jsonify({"error": "Not signed in"}), 401

    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "add")
    daily = ensure_today_log(user["id"])
    water = daily["water"]

    if action == "add":
        water = min(8, water + 1)
    elif action == "remove":
        water = max(0, water - 1)
    elif action == "reset":
        water = 0

    conn = get_db()
    conn.execute(
        "UPDATE daily_logs SET water = ? WHERE user_id = ? AND log_date = ?",
        (water, user["id"], date.today().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"water": water, "goal": 8, "percent": int((water / 8) * 100)})


@app.route("/api/activity", methods=["POST"])
def update_activity():
    user = current_user()
    if not user:
        return jsonify({"error": "Not signed in"}), 401

    payload = request.get_json(silent=True) or {}
    steps = max(0, int(payload.get("steps", 0)))
    active_minutes = max(0, int(payload.get("active_minutes", 0)))
    calories = max(0, int(payload.get("calories", 0)))

    ensure_today_log(user["id"])
    conn = get_db()
    conn.execute(
        """UPDATE daily_logs
           SET steps = ?, active_minutes = ?, calories = ?
           WHERE user_id = ? AND log_date = ?""",
        (steps, active_minutes, calories, user["id"], date.today().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "steps": steps, "active_minutes": active_minutes, "calories": calories})


@app.route("/api/weight", methods=["POST"])
def update_weight():
    user = current_user()
    if not user:
        return jsonify({"error": "Not signed in"}), 401

    payload = request.get_json(silent=True) or {}
    try:
        weight = float(payload.get("weight"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid weight"}), 400

    if weight <= 0:
        return jsonify({"error": "Invalid weight"}), 400

    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    conn.execute("UPDATE users SET weight = ? WHERE id = ?", (weight, user["id"]))
    conn.execute(
        "INSERT INTO weight_logs (user_id, weight, logged_at) VALUES (?, ?, ?)",
        (user["id"], weight, now),
    )
    conn.commit()
    conn.close()

    bmi = bmi_for(user["height"], weight)
    return jsonify({"ok": True, "weight": weight, "bmi": bmi, "bmi_label": bmi_label(bmi)})


@app.route("/api/quote")
def new_quote():
    return jsonify({"quote": random.choice(QUOTES)})


@app.route("/reset", methods=["POST"])
def reset_profile():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
