from flask import Flask, request, jsonify, render_template_string
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
    q = request.args.get("q", "")
    mode = request.args.get("mode", "")
    results = []
    executed_query = ""
    status = "No search yet"

    conn = get_db()

    products = conn.execute(
        "SELECT id, name, description, price FROM products"
    ).fetchall()

    if q and mode == "vulnerable":
        # Intentionally vulnerable for localhost lab learning.
        executed_query = f"SELECT id, name, description, price FROM products WHERE name LIKE '%{q}%'"
        rows = conn.execute(executed_query).fetchall()
        results = [dict(row) for row in rows]
        status = "VULNERABLE SEARCH"

    elif q and mode == "safe":
        # Fixed version: parameterized query.
        executed_query = "SELECT id, name, description, price FROM products WHERE name LIKE ?"
        rows = conn.execute(executed_query, (f"%{q}%",)).fetchall()
        results = [dict(row) for row in rows]
        status = "SAFE SEARCH"

    conn.close()

    return render_template_string("""
<!doctype html>
<html>
<head>
    <title>JaffShop - SQLi Lab</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: #eee;
            margin: 40px;
        }
        .box {
            background: #1c1c1c;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            border: 1px solid #333;
        }
        input {
            padding: 10px;
            width: 420px;
            background: #222;
            color: #fff;
            border: 1px solid #555;
            border-radius: 5px;
        }
        button {
            padding: 10px 15px;
            margin-left: 10px;
            border: 0;
            border-radius: 5px;
            cursor: pointer;
        }
        .danger {
            background: #b91c1c;
            color: white;
        }
        .safe {
            background: #15803d;
            color: white;
        }
        code, pre {
            background: #000;
            color: #00ff88;
            padding: 10px;
            display: block;
            white-space: pre-wrap;
            border-radius: 5px;
        }
        .product {
            padding: 10px;
            border-bottom: 1px solid #333;
        }
        .hint {
            color: #aaa;
        }
    </style>
</head>
<body>

<h1>JaffShop — SQL Injection Lab</h1>
<p class="hint">Localhost educational lab only.</p>

<div class="box">
    <h2>Products</h2>
    {% for p in products %}
        <div class="product">
            <b>{{ p["name"] }}</b> — ${{ p["price"] }}<br>
            <span class="hint">{{ p["description"] }}</span>
        </div>
    {% endfor %}
</div>

<div class="box">
    <h2>1. Vulnerable Search</h2>
    <p class="hint">Этот поиск специально уязвим. Он вставляет твой ввод прямо в SQL.</p>

    <form method="get" action="/">
        <input type="hidden" name="mode" value="vulnerable">
        <input name="q" placeholder="try: hoodie or nonexistent' OR 1=1--" value="{{ q }}">
        <button class="danger" type="submit">Search vulnerable</button>
    </form>
</div>

<div class="box">
    <h2>2. Safe Search</h2>
    <p class="hint">Этот поиск исправлен. Он использует parameterized query.</p>

    <form method="get" action="/">
        <input type="hidden" name="mode" value="safe">
        <input name="q" placeholder="try: hoodie or nonexistent' OR 1=1--" value="{{ q }}">
        <button class="safe" type="submit">Search safe</button>
    </form>
</div>

<div class="box">
    <h2>Search Status</h2>
    <p><b>{{ status }}</b></p>

    <h3>Your input:</h3>
    <code>{{ q }}</code>

    <h3>SQL query:</h3>
    <pre>{{ executed_query }}</pre>

    <h3>Results:</h3>
    {% if results %}
        {% for r in results %}
            <div class="product">
                <b>{{ r["name"] }}</b> — ${{ r["price"] }}<br>
                <span class="hint">{{ r["description"] }}</span>
            </div>
        {% endfor %}
    {% else %}
        <p class="hint">No results.</p>
    {% endif %}
</div>

</body>
</html>
    """, products=products, q=q, mode=mode, results=results, executed_query=executed_query, status=status)


@app.route("/api/products")
def api_products():
    conn = get_db()
    rows = conn.execute("SELECT id, name, description, price FROM products").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/search")
def vulnerable_search():
    q = request.args.get("q", "")
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
