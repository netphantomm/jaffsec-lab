from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "jaffshop.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) AS count FROM products")
    if cur.fetchone()["count"] == 0:
        cur.executemany("""
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        """, [
            ("Kali Hoodie", "Black hoodie for lab hackers", 49),
            ("JaffSec Mug", "Coffee mug for debugging nights", 15),
            ("Packet Sniffer Sticker", "Cybersecurity sticker pack", 5),
            ("Binary Autopsy Notebook", "Notebook for reverse engineering notes", 12),
        ])

    conn.commit()
    conn.close()


@app.route("/")
def index():
    return jsonify({
        "project": "JaffSec Lab",
        "app": "JaffShop",
        "status": "running",
        "endpoints": [
            "/api/products",
            "/api/search?q=hoodie",
            "/api/search_safe?q=hoodie"
        ]
    })


@app.route("/api/products")
def products():
    conn = get_db()
    rows = conn.execute("SELECT id, name, description, price FROM products").fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/search")
def vulnerable_search():
    q = request.args.get("q", "")

    # Intentionally vulnerable for localhost lab learning.
    sql = f"SELECT id, name, description, price FROM products WHERE name LIKE '%{q}%'"

    conn = get_db()
    rows = conn.execute(sql).fetchall()
    conn.close()

    return jsonify({
        "warning": "VULNERABLE_ENDPOINT_FOR_LOCALHOST_LAB_ONLY",
        "query": sql,
        "results": [dict(row) for row in rows]
    })


@app.route("/api/search_safe")
def safe_search():
    q = request.args.get("q", "")

    # Fixed version: parameterized query.
    sql = "SELECT id, name, description, price FROM products WHERE name LIKE ?"

    conn = get_db()
    rows = conn.execute(sql, (f"%{q}%",)).fetchall()
    conn.close()

    return jsonify({
        "status": "SAFE_ENDPOINT",
        "query": sql,
        "results": [dict(row) for row in rows]
    })


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
