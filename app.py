from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace_this_with_a_secure_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy=True)


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TopicPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    correct = db.Column(db.Integer, default=0)
    wrong = db.Column(db.Integer, default=0)


QUESTIONS = [
    {
        "id": 1,
        "topic": "Python",
        "question": "What is the output type of: type([1,2,3])?",
        "options": ["tuple", "list", "dict", "set"],
        "answer": "list",
    },
    {
        "id": 2,
        "topic": "Flask",
        "question": "Which method is used to define a route in Flask?",
        "options": ["@app.route()", "@route.path()", "@flask.url()", "@map.route()"],
        "answer": "@app.route()",
    },
    {
        "id": 3,
        "topic": "HTML",
        "question": "Which tag is used for the largest heading?",
        "options": ["<h6>", "<heading>", "<h1>", "<head>"],
        "answer": "<h1>",
    },
    {
        "id": 4,
        "topic": "CSS",
        "question": "Which CSS property changes text color?",
        "options": ["font-color", "color", "text-style", "text-color"],
        "answer": "color",
    },
    {
        "id": 5,
        "topic": "JavaScript",
        "question": "Which keyword declares a block-scoped variable?",
        "options": ["var", "const", "both let and const", "global"],
        "answer": "both let and const",
    },
]


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required():
    return "user_id" in session


def upsert_topic_performance(user_id, topic, is_correct):
    perf = TopicPerformance.query.filter_by(user_id=user_id, topic=topic).first()
    if not perf:
        perf = TopicPerformance(user_id=user_id, topic=topic, correct=0, wrong=0)
        db.session.add(perf)

    if is_correct:
        perf.correct += 1
    else:
        perf.wrong += 1


@app.route("/")
def index():
    return render_template("index.html", user=current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("register"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        hashed = generate_password_hash(password)
        user = User(name=name, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", user=current_user())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html", user=current_user())


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user = current_user()
    attempts = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.created_at.desc()).all()
    best_score = max([a.score for a in attempts], default=0)
    total_attempts = len(attempts)

    return render_template(
        "dashboard.html",
        user=user,
        attempts=attempts,
        best_score=best_score,
        total_attempts=total_attempts,
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not login_required():
        flash("Please login to attempt quiz.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        user = current_user()
        score = 0
        total = len(QUESTIONS)

        for q in QUESTIONS:
            selected = request.form.get(f"q_{q['id']}")
            is_correct = selected == q["answer"]
            if is_correct:
                score += 1
            upsert_topic_performance(user.id, q["topic"], is_correct)

        attempt = QuizAttempt(user_id=user.id, score=score, total=total)
        db.session.add(attempt)
        db.session.commit()

        return redirect(url_for("result", attempt_id=attempt.id))

    return render_template("quiz.html", user=current_user(), questions=QUESTIONS)


@app.route("/result/<int:attempt_id>")
def result(attempt_id):
    if not login_required():
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    attempt = QuizAttempt.query.get_or_404(attempt_id)
    user = current_user()

    if attempt.user_id != user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))

    percentage = round((attempt.score / attempt.total) * 100, 2)
    return render_template("result.html", user=user, attempt=attempt, percentage=percentage)


@app.route("/analysis")
def analysis():
    if not login_required():
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    user = current_user()
    performances = TopicPerformance.query.filter_by(user_id=user.id).all()

    analysis_data = []
    for p in performances:
        total = p.correct + p.wrong
        accuracy = round((p.correct / total) * 100, 2) if total else 0
        analysis_data.append(
            {
                "topic": p.topic,
                "correct": p.correct,
                "wrong": p.wrong,
                "accuracy": accuracy,
            }
        )

    analysis_data = sorted(analysis_data, key=lambda x: x["accuracy"], reverse=True)

    return render_template("analysis.html", user=user, analysis_data=analysis_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
