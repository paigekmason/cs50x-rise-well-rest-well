from cs50 import SQL
from datetime import date
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///risewell.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check for missing fields or invalid inputs
        if not username:
            return apology("Error: Missing field (username).", 400)

        elif not password:
            return apology("Error: Missing field (password).", 400)

        elif not confirmation:
            return apology("Error: Missing field (password confirmation).", 400)

        elif password != confirmation:
            return apology("Error: Password and confirmation do not match.", 400)

        # Attempt to add new user, apologize if username already taken
        try:
            hash = generate_password_hash(password, method='scrypt', salt_length=16)
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, hash)
            rows = db.execute(
                "SELECT * FROM users WHERE username = ?", request.form.get("username")
            )
            session["user_id"] = rows[0]["id"]
            return redirect("/")
        except:
            return apology("Error: Username taken. Please provide a different username.", 400)

    else:
        return render_template("/register.html")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Index into db for username to display
    user_data = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"]
    )
    username = user_data[0]["username"]

    # Display current date
    today = date.today()
    today_formatted = today.strftime("%B %d, %Y")

    # Index into gratitude table to display gratitude entries for current day
    gratitude_data_count = db.execute(
        "SELECT COUNT(entry) FROM gratitude WHERE user_id = ? AND date = ?", session["user_id"], today)
    gratitude_count = gratitude_data_count[0]["COUNT(entry)"]
    gratitude_entry_data = db.execute(
        "SELECT entry FROM gratitude WHERE user_id = ? AND date = ?", session["user_id"], today)
    gratitude_entries = []

    for entry in range(gratitude_count):
        gratitude_entries.append(gratitude_entry_data[entry]["entry"])

    # Index into db for list of steps for this user
    steps = []
    step_count_data = db.execute(
        "SELECT COUNT(step_name) FROM steps WHERE user_id = ?", session["user_id"])
    step_count = step_count_data[0]["COUNT(step_name)"]
    steps_data = db.execute("SELECT step_name FROM steps WHERE user_id = ?", session["user_id"])

    for step in range(step_count):
        steps.append(steps_data[step]["step_name"])

    return render_template("index.html", date=today_formatted, username=username, steps=steps, gratitude_entries=gratitude_entries)


@app.route("/evening", methods=["GET", "POST"])
@login_required
def evening():
    # Index into db for username to display
    user_data = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"]
    )
    username = user_data[0]["username"]

    # Display current date
    today = date.today()
    today_formatted = today.strftime("%B %d, %Y")

    # Index into db for list of steps for this user
    evening_steps = []
    step_count_data = db.execute(
        "SELECT COUNT(step_name) FROM evening_steps WHERE user_id = ?", session["user_id"])

    step_count = step_count_data[0]["COUNT(step_name)"]
    steps_data = db.execute(
        "SELECT step_name FROM evening_steps WHERE user_id = ?", session["user_id"])
    for step in range(step_count):
        evening_steps.append(steps_data[step]["step_name"])

    # Index into db for daily sentence for this user
    sentences = db.execute(
        "SELECT mood, sentence FROM daily_mood WHERE user_id = ? AND date = ?", session["user_id"], today)
    try:
        todays_sentence = sentences[0]["sentence"]
        todays_mood = sentences[0]["mood"]

    except:
        todays_sentence = ""
        todays_mood = ""

    return render_template("evening.html", date=today_formatted, username=username, evening_steps=evening_steps, todays_sentence=todays_sentence, todays_mood=todays_mood)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Error: Missing field (username).")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Error: Missing field (password).")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("Error: Invalid username and/or password.")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/addstep", methods=["POST"])
@login_required
def addStep():
    new_morning_step = request.form.get("new_step")
    new_evening_step = request.form.get("new_evening_step")
    if new_morning_step:
        db.execute("INSERT INTO steps (step_name, user_id) VALUES (?, ?)",
                   new_morning_step, session["user_id"])
        return redirect("/")
    if new_evening_step:
        db.execute("INSERT INTO evening_steps (step_name, user_id) VALUES (?, ?)",
                   new_evening_step, session["user_id"])
        return redirect("/evening")


@app.route("/gratitudeEntry", methods=["POST"])
@login_required
def gratitudeEntry():
    gratitude = request.form.get("gratitude_entry")
    today = date.today()

    if gratitude:
        db.execute("INSERT INTO gratitude (user_id, date, entry) VALUES (?, ?, ?)",
                   session["user_id"], today, gratitude)
        return redirect("/")


@app.route("/dailyEntry", methods=["POST"])
@login_required
def dailyEntry():
    sentence = request.form.get("sentence")
    mood = request.form.get("mood_selection")
    today = date.today()

    if sentence:
        db.execute("INSERT INTO daily_mood (user_id, date, sentence, mood) VALUES (?, ?, ?, ?)",
                   session["user_id"], today, sentence, mood)
        return redirect("/evening")
    return redirect("/evening")

# Delete steps from gratitude, morning routine, or evening routine


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    gratitude_delete = request.form.get("delete_gratitude")
    morning_step_delete = request.form.get("delete_step")
    evening_step_delete = request.form.get("delete_evening_step")
    today = date.today()

    if gratitude_delete:
        db.execute("DELETE FROM gratitude WHERE user_id = ? AND entry = ? AND date = ?",
                   session["user_id"], gratitude_delete, today)
        return redirect("/")

    if morning_step_delete:
        db.execute("DELETE FROM steps WHERE user_id = ? AND step_name = ?",
                   session["user_id"], morning_step_delete)
        return redirect("/")

    if evening_step_delete:
        db.execute("DELETE FROM evening_steps WHERE user_id = ? AND step_name = ?",
                   session["user_id"], evening_step_delete)
        return redirect("/evening")

    return redirect("/")


@app.context_processor
def inject_user():
    return {'username': session.get('username')}


# Add a page where you can review previous mood and sentences (in a table)
@app.route("/dailyHistory", methods=["GET"])
@login_required
def dailyHistory():
    # Index into db for username to display
    user_data = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"]
    )
    username = user_data[0]["username"]

    number_entries = db.execute(
        "SELECT COUNT(sentence) FROM daily_mood WHERE user_id = ?", session["user_id"])
    entry_count = number_entries[0]["COUNT(sentence)"]
    entry_data = db.execute(
        "SELECT date, sentence, mood FROM daily_mood WHERE user_id = ?", session["user_id"])
    entries = []

    for i in range(entry_count):
        date = entry_data[i]["date"]
        sentence = entry_data[i]["sentence"]
        mood = entry_data[i]["mood"]
        entry = {"date": date, "sentence": sentence, "mood": mood}
        entries.append(entry)

    return render_template("dailyHistory.html", entries=entries, username=username)

# Add a page where you can review previous gratitude entries


@app.route("/gratitudeHistory", methods=["GET"])
@login_required
def gratitudeHistory():
    # Index into db for username to display
    user_data = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"]
    )
    username = user_data[0]["username"]

    number_entries = db.execute(
        "SELECT COUNT(entry) FROM gratitude WHERE user_id = ?", session["user_id"])
    entry_count = number_entries[0]["COUNT(entry)"]
    entry_data = db.execute(
        "SELECT date, entry FROM gratitude WHERE user_id = ?", session["user_id"])
    entries = []

    for i in range(entry_count):
        date = entry_data[i]["date"]
        entry = entry_data[i]["entry"]
        gratitude_entry = {"date": date, "entry": entry}
        entries.append(gratitude_entry)

    return render_template("gratitudeHistory.html", entries=entries, username=username)

# Change username/password


@app.route("/resetPassword", methods=["POST"])
@login_required
def resetPassword():
    # For display in top corner
    users = db.execute(
        "SELECT username, hash FROM users WHERE id = ?", session["user_id"]
    )
    username = users[0]["username"]

    old_password = request.form.get("old_password")
    old_confirmation = request.form.get("old_confirmation")
    new_password = request.form.get("new_password")
    new_confirmation = request.form.get("new_confirmation")

    # Query database for current hash
    rows = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

    # Check for missing fields
    if not old_password or not old_confirmation or not new_password or not new_confirmation:
        return apology("Missing fields.", username=username)

        # Check for password confirmations
    elif old_password != old_confirmation:
        return apology("Old password does not match confirmation.", username=username)

    elif new_password != new_confirmation:
        return apology("New password does not match confirmation.", username=username)

    elif not check_password_hash(rows[0]["hash"], old_password):
        return apology("Old password is incorrect.", username=username)

    else:
        new_hash = generate_password_hash(new_password, method='scrypt', salt_length=16)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])
        return redirect("/")


@app.route("/resetUsername", methods=["POST"])
@login_required
def resetUsername():
    current_username = request.form.get("current_username")
    new_username = request.form.get("new_username")
    password = request.form.get("password")

    # For display in top corner
    users = db.execute(
        "SELECT username, hash FROM users WHERE id = ?", session["user_id"]
    )
    username = users[0]["username"]

    rows = db.execute(
        "SELECT * FROM users WHERE username = ?", new_username)

    # Check for missing fields
    if not current_username or not new_username or not password:
        return apology("Error: Missing fields.", username=username)

    # Check for valid current credentials
    if (current_username != username) or not check_password_hash(users[0]["hash"], password):
        return apology("Error: Invalid username or password.", username=username)

    # Query database for new username to check if already taken
    elif len(rows) == 1:
        return apology("Error: Username taken. Please choose a new username.", username=username)

    else:
        db.execute("UPDATE users SET username = ? WHERE id = ?", new_username, session["user_id"])
        return redirect("/")


@app.route("/resetLogin", methods=["GET"])
@login_required
def resetLogin():
    users = db.execute(
        "SELECT username, hash FROM users WHERE id = ?", session["user_id"]
    )
    username = users[0]["username"]
    return render_template("resetLogin.html", username=username)
