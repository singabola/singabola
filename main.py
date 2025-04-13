# SingaBola Core Game Logic
# Created and owned by Elias Lye © 2025
# All rights reserved. Do not copy, reproduce, or redistribute this game without written permission from Elias Lye.
# This script is protected under intellectual property law.

from flask import Flask, render_template, request, redirect, url_for, session
import random
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secure_singabola_key'

# --- Simple User Store (in-memory for demo) ---
users = {}

# --- Fictional SPL-Inspired Clubs ---
clubs = [
    {"name": "Albirex Phoenix", "rating": 78},
    {"name": "Lion City Kings", "rating": 76},
    {"name": "Tampines Thunder", "rating": 75},
    {"name": "Hougang Hunters", "rating": 72},
    {"name": "Geylang Griffins", "rating": 70},
    {"name": "Balestier Bengals", "rating": 68},
    {"name": "Young Serpents", "rating": 66},
    {"name": "Tanjong Tigers", "rating": 65},
    {"name": "Brunei Hornets", "rating": 67}
]

# --- Youth Player Class ---
class YouthPlayer:
    def __init__(self, name):
        self.name = name
        self.club = random.choice(clubs)["name"]
        self.stats = {
            "speed": random.randint(40, 60),
            "passing": random.randint(40, 60),
            "shooting": random.randint(40, 60),
            "stamina": random.randint(40, 60)
        }
        self.credits = 0
        self.training_sessions = 0
        self.matches_played = 0
        self.goals_scored = 0
        self.injured = False
        self.injury_weeks = 0

    def apply_credits(self, area, points):
        if self.credits >= points:
            self.stats[area] += points
            self.credits -= points
            self.training_sessions += 1
            return True
        return False

    def earn_credits(self, amount):
        self.credits += amount

    def recover(self):
        if self.injured:
            self.injury_weeks -= 1
            if self.injury_weeks <= 0:
                self.injured = False

    def participate_in_match(self):
        if self.injured:
            return False
        self.matches_played += 1
        if random.randint(1, 100) <= 5:
            self.injured = True
            self.injury_weeks = random.randint(1, 3)
            return "Injured"
        if random.randint(0, 100) < self.stats["shooting"]:
            self.goals_scored += 1
            return True
        return False

    def display(self):
        return {
            "name": self.name,
            "club": self.club,
            "stats": self.stats,
            "credits": self.credits,
            "training_sessions": self.training_sessions,
            "matches_played": self.matches_played,
            "goals_scored": self.goals_scored,
            "injured": self.injured,
            "injury_weeks": self.injury_weeks
        }

# --- Global Store for Players Per User ---
youth_rosters = {}

# --- Authentication Routes ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email not in users:
            users[email] = generate_password_hash(password)
            youth_rosters[email] = [YouthPlayer("Zul Azri"), YouthPlayer("Irfan Latif"), YouthPlayer("Marcus Tan")]
            session["user"] = email
            return redirect(url_for("home"))
        else:
            return "User already exists."
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and check_password_hash(users[email], password):
            session["user"] = email
            return redirect(url_for("home"))
        return "Invalid credentials."
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# --- Game Logic Routes ---
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    return render_template("index.html", roster=[p.display() for p in youth_rosters[user]])

@app.route("/train", methods=["POST"])
def train():
    user = session["user"]
    name = request.form["name"]
    area = request.form["area"]
    amount = int(request.form["amount"])
    for player in youth_rosters[user]:
        if player.name == name:
            player.apply_credits(area, amount)
    return redirect(url_for("home"))

@app.route("/simulate")
def simulate():
    user = session["user"]
    for player in youth_rosters[user]:
        player.recover()
        player.participate_in_match()
    return redirect(url_for("home"))

@app.route("/earn", methods=["POST"])
def earn():
    user = session["user"]
    name = request.form["name"]
    action = request.form["action"]
    credit_map = {
        "credits_school": 10,
        "credits_women": 15,
        "credits_interview": 20
    }
    credit_award = credit_map.get(action, 0)
    for player in youth_rosters[user]:
        if player.name == name:
            player.earn_credits(credit_award)
    return redirect(url_for("home"))

@app.route("/save")
def save():
    user = session["user"]
    with open(f"save_{user}.json", "w") as f:
        json.dump([p.display() for p in youth_rosters[user]], f, indent=4)
    return "Game saved."

@app.route("/load")
def load():
    user = session["user"]
    filename = f"save_{user}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        for i, p_data in enumerate(data):
            if i < len(youth_rosters[user]):
                youth_rosters[user][i].__dict__.update({
                    'name': p_data['name'],
                    'club': p_data['club'],
                    'stats': p_data['stats'],
                    'credits': p_data['credits'],
                    'training_sessions': p_data['training_sessions'],
                    'matches_played': p_data['matches_played'],
                    'goals_scored': p_data['goals_scored'],
                    'injured': p_data['injured'],
                    'injury_weeks': p_data['injury_weeks']
                })
    return redirect(url_for("home"))

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
