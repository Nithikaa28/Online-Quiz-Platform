# Online Quiz Platform (Flask)

A modern interactive quiz platform with authentication, score tracking, and skill analysis.

## Features

- User registration and login/logout
- Interactive quiz interface
- Score tracking dashboard
- Topic-wise skill analysis
- Modern UI/UX with aesthetic fonts and color palette

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
