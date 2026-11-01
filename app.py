from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = 'library.db'

# 1. Helper function to connect to SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name (e.g., book['title'])
    return conn

# 2. Initialize the Database table if it doesn't exist
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,         -- 'Physical' or 'Online'
            link TEXT                   -- URL if it's an online book
        )
    ''')
    conn.commit()
    conn.close()

# 3. Route to serve the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# 4. API Route: GET all books from SQLite
@app.route('/api/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    # Convert SQLite rows into a JSON list
    return jsonify([dict(book) for book in books])

# 5. API Route: POST (Add) a new book into SQLite
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, category, type, link) VALUES (?, ?, ?, ?)',
        (data['title'], data['category'], data['type'], data.get('link', ''))
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book added successfully!'}), 201

if __name__ == '__main__':
    init_db()  # Create database table when app starts
    app.run(debug=True)