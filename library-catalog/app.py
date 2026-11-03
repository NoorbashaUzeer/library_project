"""College Library Catalog & Availability Checker - Flask + SQLite."""
import os
import sqlite3
from functools import wraps

from flask import (Flask, g, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-lab")

SAMPLE_BOOKS = [
    ("Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 2009, 1312,
     "Comprehensive textbook covering a broad range of algorithms in depth.", 3, 3, ""),
    ("Clean Code", "Robert C. Martin", "Computer Science", 2008, 464,
     "A handbook of agile software craftsmanship.", 2, 1, ""),
    ("Pride and Prejudice", "Jane Austen", "Literature", 1813, 432,
     "A classic novel of manners set in Regency England.", 4, 4,
     "https://www.gutenberg.org/ebooks/1342"),
    ("A Brief History of Time", "Stephen Hawking", "Science", 1988, 256,
     "From the Big Bang to black holes, an accessible look at cosmology.", 2, 0, ""),
    ("The Republic", "Plato", "Philosophy", -375, 416,
     "Socratic dialogue on justice and the ideal state.", 1, 1,
     "https://www.gutenberg.org/ebooks/1497"),
    ("Engineering Mathematics", "K. A. Stroud", "Mathematics", 2020, 1200,
     "Foundation mathematics for engineering students.", 5, 3, ""),
]


# ---------------- Database ----------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS librarians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            year INTEGER,
            pages INTEGER,
            description TEXT,
            total_copies INTEGER NOT NULL DEFAULT 0,
            available_copies INTEGER NOT NULL DEFAULT 0,
            ebook_url TEXT
        );
    """)
    if not db.execute("SELECT 1 FROM librarians").fetchone():
        db.execute("INSERT INTO librarians (username, password_hash) VALUES (?, ?)",
                   ("admin", generate_password_hash("admin123")))
    if not db.execute("SELECT 1 FROM books").fetchone():
        db.executemany("""INSERT INTO books (title, author, category, year, pages, description,
                          total_copies, available_copies, ebook_url)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", SAMPLE_BOOKS)
    db.commit()
    db.close()


def book_to_dict(row):
    d = dict(row)
    total, avail = d["total_copies"], d["available_copies"]
    d["availability"] = "Out of Stock" if avail <= 0 else f"{avail} of {total} on the shelf"
    d["in_stock"] = avail > 0
    return d


# ---------------- Auth ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("librarian"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Librarian login required"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def validate_book(data):
    required = ["title", "author", "category"]
    for field in required:
        if not str(data.get(field, "")).strip():
            return None, f"'{field}' is required"
    try:
        total = int(data.get("total_copies") or 0)
        avail = int(data.get("available_copies") or 0)
        year = int(data["year"]) if str(data.get("year", "")).strip() else None
        pages = int(data["pages"]) if str(data.get("pages", "")).strip() else None
    except (ValueError, TypeError):
        return None, "Year, pages and copies must be numbers"
    if total < 0 or avail < 0 or avail > total:
        return None, "Available copies must be between 0 and total copies"
    return {
        "title": data["title"].strip(), "author": data["author"].strip(),
        "category": data["category"].strip(), "year": year, "pages": pages,
        "description": (data.get("description") or "").strip(),
        "total_copies": total, "available_copies": avail,
        "ebook_url": (data.get("ebook_url") or "").strip(),
    }, None


# ---------------- Pages ----------------
@app.route("/")
def index():
    return render_template("index.html", logged_in=bool(session.get("librarian")))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute("SELECT * FROM librarians WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["librarian"] = username
            return redirect(url_for("dashboard"))
        error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["librarian"])


# ---------------- REST API ----------------
@app.get("/api/books")
def list_books():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql, params = "SELECT * FROM books WHERE 1=1", []
    if q:
        sql += " AND (title LIKE ? OR author LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)
    rows = get_db().execute(sql + " ORDER BY title", params).fetchall()
    return jsonify([book_to_dict(r) for r in rows])


@app.get("/api/books/<int:book_id>")
def get_book(book_id):
    row = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not row:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book_to_dict(row))


@app.post("/api/books")
@login_required
def add_book():
    book, err = validate_book(request.get_json(silent=True) or {})
    if err:
        return jsonify({"error": err}), 400
    db = get_db()
    cur = db.execute("""INSERT INTO books (title, author, category, year, pages, description,
                        total_copies, available_copies, ebook_url)
                        VALUES (:title, :author, :category, :year, :pages, :description,
                        :total_copies, :available_copies, :ebook_url)""", book)
    db.commit()
    row = db.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(book_to_dict(row)), 201


@app.put("/api/books/<int:book_id>")
@login_required
def update_book(book_id):
    book, err = validate_book(request.get_json(silent=True) or {})
    if err:
        return jsonify({"error": err}), 400
    db = get_db()
    book["id"] = book_id
    cur = db.execute("""UPDATE books SET title=:title, author=:author, category=:category,
                        year=:year, pages=:pages, description=:description,
                        total_copies=:total_copies, available_copies=:available_copies,
                        ebook_url=:ebook_url WHERE id=:id""", book)
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Book not found"}), 404
    return get_book(book_id)


@app.delete("/api/books/<int:book_id>")
@login_required
def delete_book(book_id):
    db = get_db()
    cur = db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"deleted": book_id})


@app.get("/api/categories")
def categories():
    rows = get_db().execute("SELECT DISTINCT category FROM books ORDER BY category").fetchall()
    return jsonify([r["category"] for r in rows])


init_db()

if __name__ == "__main__":
    app.run(debug=True)
