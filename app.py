from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text

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
    raw_score = db.Column(db.Integer, nullable=False, default=0)
    confidence_score = db.Column(db.Integer, nullable=False, default=0)
    max_confidence_score = db.Column(db.Integer, nullable=False, default=0)
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
        "difficulty": "easy",
        "question": "What is the output type of: type([1,2,3])?",
        "options": ["tuple", "list", "dict", "set"],
        "answer": "list",
    },
    {
        "id": 2,
        "topic": "Flask",
        "difficulty": "medium",
        "question": "Which method is used to define a route in Flask?",
        "options": ["@app.route()", "@route.path()", "@flask.url()", "@map.route()"],
        "answer": "@app.route()",
    },
    {
        "id": 3,
        "topic": "HTML",
        "difficulty": "easy",
        "question": "Which tag is used for the largest heading?",
        "options": ["<h6>", "<heading>", "<h1>", "<head>"],
        "answer": "<h1>",
    },
    {
        "id": 4,
        "topic": "CSS",
        "difficulty": "medium",
        "question": "Which CSS property changes text color?",
        "options": ["font-color", "color", "text-style", "text-color"],
        "answer": "color",
    },
    {
        "id": 5,
        "topic": "JavaScript",
        "difficulty": "hard",
        "question": "Which keyword declares a block-scoped variable?",
        "options": ["var", "const", "both let and const", "global"],
        "answer": "both let and const",
    },
]

CONFIDENCE_SCORING = {
    "low": {"correct": 1, "wrong": 0, "label": "Low"},
    "medium": {"correct": 2, "wrong": -1, "label": "Medium"},
    "high": {"correct": 3, "wrong": -2, "label": "High"},
}

DIFFICULTY_PRIORITY = {
    "easy": ["easy", "medium", "hard"],
    "medium": ["medium", "easy", "hard"],
    "hard": ["hard", "medium", "easy"],
}

SCHEMA_READY = False


def ensure_quiz_attempt_columns():
    if not inspect(db.engine).has_table("quiz_attempt"):
        return

    existing_columns = {col["name"] for col in inspect(db.engine).get_columns("quiz_attempt")}
    required_columns = {
        "raw_score": "ALTER TABLE quiz_attempt ADD COLUMN raw_score INTEGER NOT NULL DEFAULT 0",
        "confidence_score": "ALTER TABLE quiz_attempt ADD COLUMN confidence_score INTEGER NOT NULL DEFAULT 0",
        "max_confidence_score": "ALTER TABLE quiz_attempt ADD COLUMN max_confidence_score INTEGER NOT NULL DEFAULT 0",
    }

    schema_updated = False
    for column_name, alter_sql in required_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(alter_sql))
            schema_updated = True

    if schema_updated:
        db.session.execute(text("UPDATE quiz_attempt SET raw_score = score WHERE raw_score = 0 AND score > 0"))
        db.session.execute(
            text(
                "UPDATE quiz_attempt "
                "SET max_confidence_score = CASE WHEN total > 0 THEN total * 3 ELSE 0 END "
                "WHERE max_confidence_score = 0"
            )
        )
    db.session.commit()


@app.before_request
def ensure_schema_ready():
    global SCHEMA_READY
    if SCHEMA_READY:
        return
    ensure_quiz_attempt_columns()
    SCHEMA_READY = True


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


def attempt_raw_score(attempt):
    return attempt.raw_score if attempt.raw_score else attempt.score


def confidence_points(is_correct, confidence_level):
    confidence_level = (confidence_level or "low").lower()
    rule = CONFIDENCE_SCORING.get(confidence_level, CONFIDENCE_SCORING["low"])
    return rule["correct"] if is_correct else rule["wrong"]


def select_target_difficulty(recent_accuracy):
    if recent_accuracy is None:
        return "medium"
    if recent_accuracy < 50:
        return "easy"
    if recent_accuracy > 80:
        return "hard"
    return "medium"


def sort_questions_by_target(questions, target_difficulty):
    priority = DIFFICULTY_PRIORITY[target_difficulty]
    grouped_questions = {tier: [] for tier in priority}
    for question in questions:
        difficulty = question.get("difficulty", "medium").lower()
        grouped_questions.setdefault(difficulty, []).append(question)

    ordered_questions = []
    for tier in priority:
        ordered_questions.extend(sorted(grouped_questions.get(tier, []), key=lambda q: q["id"]))
    return ordered_questions, priority


def adapt_questions_for_user(user):
    attempts = (
        QuizAttempt.query.filter_by(user_id=user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(3)
        .all()
    )
    recent_accuracy = None
    if attempts:
        total_accuracy = 0
        for attempt in attempts:
            raw_score = attempt_raw_score(attempt)
            accuracy = (raw_score / attempt.total) * 100 if attempt.total else 0
            total_accuracy += accuracy
        recent_accuracy = total_accuracy / len(attempts)

    target_difficulty = select_target_difficulty(recent_accuracy)
    ordered_questions, priority = sort_questions_by_target(QUESTIONS, target_difficulty)

    adaptive_meta = {
        "recent_accuracy": round(recent_accuracy, 2) if recent_accuracy is not None else None,
        "target_difficulty": target_difficulty.title(),
        "difficulty_flow": " → ".join(tier.title() for tier in priority),
    }
    return ordered_questions, adaptive_meta


def calculate_streak_and_mastery(attempts):
    if not attempts:
        return 0, 0

    accuracies = []
    streak = 0
    for attempt in attempts:
        raw_score = attempt_raw_score(attempt)
        accuracy = (raw_score / attempt.total) * 100 if attempt.total else 0
        accuracies.append(accuracy)

        if accuracy >= 70:
            streak += 1
        else:
            break

    mastery = round(sum(accuracies[:5]) / min(len(accuracies), 5), 2)
    return streak, mastery


def get_focus_areas(user_id, limit=3):
    performances = TopicPerformance.query.filter_by(user_id=user_id).all()
    weak_topics = []
    for p in performances:
        total = p.correct + p.wrong
        if total == 0:
            continue
        accuracy = round((p.correct / total) * 100, 2)
        if accuracy < 75 or p.wrong > p.correct:
            recommendation = (
                "Review fundamentals and solve two targeted practice questions."
                if accuracy < 60
                else "Do one revision pass and retake a focused mini-quiz."
            )
            weak_topics.append(
                {
                    "topic": p.topic,
                    "accuracy": accuracy,
                    "correct": p.correct,
                    "wrong": p.wrong,
                    "recommendation": recommendation,
                }
            )

    weak_topics.sort(key=lambda row: (row["accuracy"], -row["wrong"]))
    return weak_topics[:limit]


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
    best_score = max([attempt_raw_score(a) for a in attempts], default=0)
    total_attempts = len(attempts)
    current_streak, mastery = calculate_streak_and_mastery(attempts)
    focus_areas = get_focus_areas(user.id, limit=3)

    return render_template(
        "dashboard.html",
        user=user,
        attempts=attempts,
        best_score=best_score,
        total_attempts=total_attempts,
        current_streak=current_streak,
        mastery=mastery,
        focus_areas=focus_areas,
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not login_required():
        flash("Please login to attempt quiz.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        user = current_user()
        score = 0
        confidence_score = 0
        total = len(QUESTIONS)
        max_confidence_score = total * CONFIDENCE_SCORING["high"]["correct"]
        confidence_breakdown = []
        topic_snapshot = {}

        for q in QUESTIONS:
            selected = request.form.get(f"q_{q['id']}")
            confidence_level = request.form.get(f"confidence_{q['id']}", "low").lower()
            is_correct = selected == q["answer"]
            if is_correct:
                score += 1
            points = confidence_points(is_correct, confidence_level)
            confidence_score += points
            upsert_topic_performance(user.id, q["topic"], is_correct)
            topic_summary = topic_snapshot.setdefault(q["topic"], {"correct": 0, "wrong": 0})
            if is_correct:
                topic_summary["correct"] += 1
            else:
                topic_summary["wrong"] += 1
            confidence_breakdown.append(
                {
                    "question": q["question"],
                    "topic": q["topic"],
                    "difficulty": q.get("difficulty", "medium").title(),
                    "selected": selected or "Not Answered",
                    "correct_answer": q["answer"],
                    "is_correct": is_correct,
                    "confidence": CONFIDENCE_SCORING.get(confidence_level, CONFIDENCE_SCORING["low"])["label"],
                    "points": points,
                }
            )

        attempt = QuizAttempt(
            user_id=user.id,
            score=score,
            total=total,
            raw_score=score,
            confidence_score=confidence_score,
            max_confidence_score=max_confidence_score,
        )
        db.session.add(attempt)
        db.session.commit()
        session["latest_result"] = {
            "attempt_id": attempt.id,
            "confidence_breakdown": confidence_breakdown,
            "topic_snapshot": topic_snapshot,
        }

        return redirect(url_for("result", attempt_id=attempt.id))

    user = current_user()
    questions, adaptive_meta = adapt_questions_for_user(user)
    return render_template("quiz.html", user=user, questions=questions, adaptive_meta=adaptive_meta)


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
    confidence_percentage = round(
        (attempt.confidence_score / attempt.max_confidence_score) * 100, 2
    ) if attempt.max_confidence_score else 0
    latest_result = session.get("latest_result", {})
    confidence_breakdown = latest_result.get("confidence_breakdown", []) if latest_result.get("attempt_id") == attempt.id else []
    topic_snapshot = latest_result.get("topic_snapshot", {}) if latest_result.get("attempt_id") == attempt.id else {}

    user_attempts = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.created_at.desc()).all()
    current_streak, mastery = calculate_streak_and_mastery(user_attempts)
    focus_areas = get_focus_areas(user.id, limit=3)

    return render_template(
        "result.html",
        user=user,
        attempt=attempt,
        percentage=percentage,
        confidence_percentage=confidence_percentage,
        confidence_breakdown=confidence_breakdown,
        topic_snapshot=topic_snapshot,
        current_streak=current_streak,
        mastery=mastery,
        focus_areas=focus_areas,
        confidence_scoring=CONFIDENCE_SCORING,
    )


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

    focus_areas = get_focus_areas(user.id, limit=5)

    return render_template("analysis.html", user=user, analysis_data=analysis_data, focus_areas=focus_areas)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_quiz_attempt_columns()
    app.run(debug=True)
