# SingaBola: Singapore Football Manager - Expanded
# Created and owned by Elias Lye © 2025

from flask import Flask, render_template, request, redirect, url_for, session
import json
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "singabola_secure_key"

# Load club data
with open("clubs.json", "r") as f:
    clubs_data = json.load(f)

# Load player name pool
with open("players.json", "r") as f:
    name_pool = json.load(f)

positions = ["GK", "DEF", "DEF", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD", "SUB"] * 2

# In-memory data
users = {}
user_clubs = {}
club_squads = {}
club_tactics = {}
league_table = {club["name"]: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "Pts": 0, "P": 0} for club in clubs_data}

class Player:
    def __init__(self, name, position, rating):
        self.name = name
        self.position = position
        self.rating = rating
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

def generate_name():
    return f"{random.choice(name_pool['first_names'])} {random.choice(name_pool['last_names'])}"

def generate_squad():
    squad = []
    for pos in positions[:20]:
        name = generate_name()
        rating = random.randint(60, 85)
        squad.append(Player(name, pos, rating))
    return squad

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    club = user_clubs.get(user)
    squad = [p.to_dict() for p in club_squads[club]]
    tactics = club_tactics.get(club, {"formation": "4-4-2", "style": "Balanced"})
    return render_template("index.html", user=user, club=club, squad=squad, tactics=tactics)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users:
            return "User already exists"
        users[email] = generate_password_hash(password)
        club = next((c["name"] for c in clubs_data if c["name"] not in user_clubs.values()), None)
        if not club:
            return "All clubs are taken"
        user_clubs[email] = club
        club_squads[club] = generate_squad()
        club_tactics[club] = {"formation": "4-4-2", "style": "Balanced"}
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

@app.route("/tactics", methods=["GET", "POST"])
def tactics():
    user = session["user"]
    club = user_clubs[user]
    if request.method == "POST":
        formation = request.form["formation"]
        style = request.form["style"]
        club_tactics[club] = {"formation": formation, "style": style}
        return redirect(url_for("home"))
    return render_template("tactics.html", club=club, tactics=club_tactics[club])

@app.route("/simulate")
def simulate():
    user = session["user"]
    club = user_clubs[user]
    squad = club_squads[club]
    tactics = club_tactics.get(club, {"style": "Balanced"})
    multiplier = {"Attacking": 1.2, "Balanced": 1.0, "Defensive": 0.8}.get(tactics["style"], 1.0)

    goals = 0
    commentary = []
    for p in squad:
        if not p.injured and p.position in ["MID", "FWD"]:
            chance = random.random()
            if chance < (p.rating / 200) * multiplier:
                p.goals += 1
                goals += 1
                commentary.append(f"{p.name} scores for {club}!")
            elif chance < 0.05:
                p.injured = True
                p.injury_weeks = random.randint(1, 3)
                commentary.append(f"{p.name} was injured during the match!")

    # Simulate opponent
    opponent = random.choice([c["name"] for c in clubs_data if c["name"] != club])
    opp_goals = random.randint(0, 3)
    result_text = f"{club} {goals} - {opp_goals} {opponent}"
    commentary.append("Full Time: " + result_text)

    # Update league table
    league_table[club]["GF"] += goals
    league_table[club]["GA"] += opp_goals
    league_table[club]["P"] += 1
    if goals > opp_goals:
        league_table[club]["W"] += 1
        league_table[club]["Pts"] += 3
    elif goals == opp_goals:
        league_table[club]["D"] += 1
        league_table[club]["Pts"] += 1
    else:
        league_table[club]["L"] += 1

    return render_template("matchday.html", club=club, commentary=commentary)

@app.route("/table")
def table():
    sorted_table = sorted(league_table.items(), key=lambda x: (x[1]["Pts"], x[1]["GF"] - x[1]["GA"]), reverse=True)
    return render_template("table.html", table=sorted_table)
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
