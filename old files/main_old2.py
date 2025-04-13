# SingaBola - Singapore Football Manager
# Created and owned by Elias Lye © 2025
# Full club management simulation game

from flask import Flask, render_template, request, redirect, url_for, session
import random
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'singabola_secure_key'

# --- Club & Squad Setup ---
clubs = [
    "Albirex Phoenix", "Balestier Knights", "Brunei Royals", "Geylang Griffins",
    "Hougang Hawks", "Lion City Kings", "Tampines Blaze", "Tanjong Titans", "Young Serpents"
]

positions = ["GK", "DEF", "MID", "FWD"]

# Store users, their clubs and squads
users = {}
user_clubs = {}
club_squads = {}

class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.rating = random.randint(60, 85)
        self.fitness = 100
        self.goals = 0
        self.injured = False
        self.injury_weeks = 0

    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position,
            "rating": self.rating,
            "fitness": self.fitness,
            "goals": self.goals,
            "injured": self.injured,
            "injury_weeks": self.injury_weeks
        }

def generate_squad():
    squad = []
    for i in range(20):
        name = f"Player {random.randint(100, 999)}"
        pos = random.choice(positions)
        squad.append(Player(name, pos))
    return squad

def simulate_match(team):
    goals = 0
    for player in team:
        if not player.injured and player.position in ["FWD", "MID"]:
            if random.random() < player.rating / 200:
                player.goals += 1
                goals += 1
    return goals

# --- Routes ---
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    club = user_clubs.get(user)
    squad = [p.to_dict() for p in club_squads[club]]
    return render_template("index.html", user=user, club=club, squad=squad)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users:
            return "User already exists"
        users[email] = generate_password_hash(password)
        club = random.choice([c for c in clubs if c not in user_clubs.values()])
        user_clubs[email] = club
        club_squads[club] = generate_squad()
        session["user"] = email
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and check_password_hash(users[email], password):
            session["user"] = email
            return redirect(url_for("home"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/simulate")
def simulate():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    club = user_clubs[user]
    team = club_squads[club]
    score = simulate_match(team)
    return render_template("matchday.html", club=club, score=score)

# --- Run app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
