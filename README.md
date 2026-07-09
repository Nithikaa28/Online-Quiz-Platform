# Online Quiz Platform (Flask)

A modern interactive quiz platform with authentication, score tracking, and skill analysis.

## Features

- User registration and login/logout
- Interactive quiz interface
- Confidence-based answering with transparent weighted scoring:
  - Low: +1 correct / 0 wrong
  - Medium: +2 correct / -1 wrong
  - High: +3 correct / -2 wrong
- Deterministic adaptive difficulty flow (easy/medium/hard ordering from recent accuracy)
- Weak-topic “Focus Areas” with concise recommendations
- Streak + mastery indicators on dashboard and result screens
- Modern light-theme UI with Inter + Poppins typography

## Tech Stack

- Python
- Flask
- SQLAlchemy
- SQLite
- HTML/CSS/JS

## Run locally

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Notes

- Update `SECRET_KEY` in `app.py` before production use.
- Database file (`quiz.db`) is auto-created on first run.
- Existing databases are automatically upgraded with new attempt columns on app startup.
