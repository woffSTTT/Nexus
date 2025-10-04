from flask import Flask, redirect, request, session, render_template
import requests, os, json

app = Flask(__name__)
app.secret_key = "supersegreto"

with open("config.json") as f:
    config = json.load(f)

DISCORD_API = "https://discord.com/api"

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    stats = {"BAN": 0, "KICK": 0, "MUTE": 0, "WARN": 0}
    log_path = "logs/moderation.log"
    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                for key in stats:
                    if key in line:
                        stats[key] += 1
    return render_template("dashboard.html", user=session["user"], stats=stats)

@app.route("/login")
def login():
    return redirect(f"{DISCORD_API}/oauth2/authorize?client_id={config['client_id']}&redirect_uri={config['redirect_uri']}&response_type=code&scope=identify")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config["redirect_uri"],
        "scope": "identify"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers)
    access_token = r.json().get("access_token")
    user = requests.get(f"{DISCORD_API}/users/@me", headers={"Authorization": f"Bearer {access_token}"}).json()
    session["user"] = user
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
