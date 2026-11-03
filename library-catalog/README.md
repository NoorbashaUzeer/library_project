# College Library Catalog & Availability Checker

Flask + SQLite + HTML/CSS/Vanilla JS. Catalog only — no online borrowing.

## Run
```bash
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. `library.db` is created automatically with sample books.

Librarian login: **admin / admin123** (at /login).

## Structure
```
app.py              Flask app, SQLite setup, REST API, librarian auth
templates/          index.html (catalog), login.html, dashboard.html
static/             style.css, app.js (catalog), dashboard.js (librarian)
```

## REST API
| Method | Endpoint | Access |
|---|---|---|
| GET | /api/books (optional `?q=` & `?category=`) | Public |
| GET | /api/books/<id> | Public |
| POST | /api/books | Librarian |
| PUT | /api/books/<id> | Librarian |
| DELETE | /api/books/<id> | Librarian |
| GET | /api/categories | Public |

Availability is stored as `total_copies` / `available_copies` and returned as
"3 of 3 on the shelf" or "Out of Stock".
