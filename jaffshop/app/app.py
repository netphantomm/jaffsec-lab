from pathlib import Path
import sqlite3

from flask import (
    Flask,
    jsonify,
    render_template_string,
    request,
    session,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "localhost-dev-secret-change-me"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DB_PATH = Path(__file__).parent / "jaffshop.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Existing products table for the SQL injection lab.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    """)

    # Users for authentication and access-control labs.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    # Every order belongs to one user.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            total INTEGER NOT NULL CHECK (total >= 0),
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Seed products only when the table is empty.
    cur.execute("SELECT COUNT(*) AS count FROM products")
    if cur.fetchone()["count"] == 0:
        cur.executemany("""
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        """, [
            (
                "Kali Hoodie",
                "Black hoodie for lab hackers",
                49,
            ),
            (
                "JaffSec Mug",
                "Coffee mug for debugging nights",
                15,
            ),
            (
                "Packet Sniffer Sticker",
                "Cybersecurity sticker pack",
                5,
            ),
            (
                "Binary Autopsy Notebook",
                "Notebook for reverse engineering notes",
                12,
            ),
        ])

    # Create two test users.
    cur.executemany("""
        INSERT OR IGNORE INTO users (
            username,
            password_hash,
            display_name,
            role
        )
        VALUES (?, ?, ?, ?)
    """, [
        (
            "alice",
            generate_password_hash("AlicePass123!"),
            "alice",
            "user",
        ),
        (
            "bob",
            generate_password_hash("BobPass123!"),
            "bob",
            "user",
        ),
    ])

    # Resolve their real database IDs instead of assuming 1 and 2.
    user_rows = cur.execute("""
        SELECT id, username
        FROM users
        WHERE username IN (?, ?)
    """, ("alice", "bob")).fetchall()

    user_ids = {
        row["username"]: row["id"]
        for row in user_rows
    }

    # Create one owned order per user.
    cur.execute("SELECT COUNT(*) AS count FROM orders")
    if cur.fetchone()["count"] == 0:
        cur.executemany("""
            INSERT INTO orders (user_id, item_name, total, status)
            VALUES (?, ?, ?, ?)
        """, [
            (
                user_ids["alice"],
                "Kali Hoodie",
                49,
                "paid",
            ),
            (
                user_ids["bob"],
                "Binary Autopsy Notebook",
                12,
                "paid",
            ),
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

    products = conn.execute("""
        SELECT id, name, description, price
        FROM products
    """).fetchall()

    if q and mode == "vulnerable":
        # Intentionally vulnerable for localhost lab learning.
        executed_query = (
            "SELECT id, name, description, price "
            "FROM products "
            f"WHERE name LIKE '%{q}%'"
        )

        rows = conn.execute(executed_query).fetchall()
        results = [dict(row) for row in rows]
        status = "VULNERABLE SEARCH"

    elif q and mode == "safe":
        # Fixed version: parameterized SQL query.
        executed_query = (
            "SELECT id, name, description, price "
            "FROM products "
            "WHERE name LIKE ?"
        )

        rows = conn.execute(
            executed_query,
            (f"%{q}%",),
        ).fetchall()

        results = [dict(row) for row in rows]
        status = "SAFE SEARCH"

    conn.close()

    return render_template_string(
        """
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

        code,
        pre {
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

        <p class="hint">
            Этот поиск специально уязвим.
            Он вставляет твой ввод прямо в SQL.
        </p>

        <form method="get" action="/">
            <input
                type="hidden"
                name="mode"
                value="vulnerable"
            >

            <input
                name="q"
                placeholder="try: hoodie or nonexistent' OR 1=1--"
                value="{{ q }}"
            >

            <button class="danger" type="submit">
                Search vulnerable
            </button>
        </form>
    </div>

    <div class="box">
        <h2>2. Safe Search</h2>

        <p class="hint">
            Этот поиск исправлен.
            Он использует parameterized query.
        </p>

        <form method="get" action="/">
            <input
                type="hidden"
                name="mode"
                value="safe"
            >

            <input
                name="q"
                placeholder="try: hoodie or nonexistent' OR 1=1--"
                value="{{ q }}"
            >

            <button class="safe" type="submit">
                Search safe
            </button>
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
        """,
        products=products,
        q=q,
        mode=mode,
        results=results,
        executed_query=executed_query,
        status=status,
    )


@app.route("/api/products")
def api_products():
    conn = get_db()

    rows = conn.execute("""
        SELECT id, name, description, price
        FROM products
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.route("/api/search")
def vulnerable_search():
    q = request.args.get("q", "")

    sql = (
        "SELECT id, name, description, price "
        "FROM products "
        f"WHERE name LIKE '%{q}%'"
    )

    conn = get_db()
    rows = conn.execute(sql).fetchall()
    conn.close()

    return jsonify({
        "warning": "VULNERABLE_ENDPOINT_FOR_LOCALHOST_LAB_ONLY",
        "query": sql,
        "results": [
            dict(row)
            for row in rows
        ],
    })


@app.route("/api/search_safe")
def safe_search():
    q = request.args.get("q", "")

    sql = (
        "SELECT id, name, description, price "
        "FROM products "
        "WHERE name LIKE ?"
    )

    conn = get_db()

    rows = conn.execute(
        sql,
        (f"%{q}%",),
    ).fetchall()

    conn.close()

    return jsonify({
        "status": "SAFE_ENDPOINT",
        "query": sql,
        "results": [
            dict(row)
            for row in rows
        ],
    })



@app.get("/api/orders/<int:order_id>")
def get_order(order_id):
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    conn = get_db()

    # Intentionally vulnerable:
    # order_id is checked, but ownership is not.
    order = conn.execute("""
        SELECT id, user_id, item_name, total, status
        FROM orders
        WHERE id = ?
    """, (order_id,)).fetchone()

    conn.close()

    if order is None:
        return jsonify({
            "error": "order_not_found",
        }), 404

    return jsonify({
        "mode": "vulnerable",
        "authenticated_user_id": current_user_id,
        "order": dict(order),
    })



@app.route("/orders-lab")
def orders_lab():
    return render_template_string("""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>JaffShop — Orders Lab</title>

    <style>
        :root {
            color-scheme: dark;
            --background: #09090b;
            --panel: #18181b;
            --panel-soft: #202024;
            --border: #34343a;
            --text: #f4f4f5;
            --muted: #a1a1aa;
            --accent: #22c55e;
            --accent-hover: #16a34a;
            --danger: #f87171;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
            color: var(--text);
            background:
                radial-gradient(
                    circle at top,
                    #163221 0,
                    var(--background) 38%
                );
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        .shell {
            width: min(960px, calc(100% - 32px));
            margin: 0 auto;
            padding-bottom: 64px;
        }

        nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 24px 0;
        }

        .brand {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .lab-badge {
            padding: 7px 11px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--muted);
            background: rgba(24, 24, 27, 0.8);
            font-size: 13px;
        }

        .hero {
            padding: 56px 0 32px;
        }

        .eyebrow {
            color: var(--accent);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 12px;
        }

        h1 {
            max-width: 720px;
            margin: 14px 0 16px;
            font-size: clamp(40px, 7vw, 72px);
            line-height: 0.98;
            letter-spacing: -0.045em;
        }

        .lead {
            max-width: 650px;
            margin: 0;
            color: var(--muted);
            font-size: 18px;
            line-height: 1.7;
        }

        .grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(280px, 0.72fr);
            gap: 20px;
            margin-top: 30px;
        }

        .panel {
            border: 1px solid var(--border);
            border-radius: 20px;
            background: rgba(24, 24, 27, 0.92);
            padding: 24px;
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
        }

        .panel h2 {
            margin: 0 0 8px;
            font-size: 20px;
        }

        .hint {
            margin: 0 0 22px;
            color: var(--muted);
            line-height: 1.55;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 700;
        }

        .search-row {
            display: flex;
            gap: 10px;
        }

        input {
            width: 100%;
            min-width: 0;
            padding: 13px 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            outline: none;
            color: var(--text);
            background: var(--panel-soft);
            font: inherit;
        }

        input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.14);
        }

        button {
            flex: 0 0 auto;
            border: 0;
            border-radius: 12px;
            padding: 0 18px;
            background: var(--accent);
            color: #031108;
            font: inherit;
            font-weight: 800;
            cursor: pointer;
        }

        button:hover {
            background: var(--accent-hover);
            color: white;
        }

        .request-preview {
            margin-top: 18px;
            padding: 13px 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #050505;
            color: #86efac;
            font-family: "JetBrains Mono", monospace;
            font-size: 13px;
            overflow-wrap: anywhere;
        }

        .status {
            min-height: 24px;
            margin-top: 18px;
            color: var(--muted);
        }

        .status.error {
            color: var(--danger);
        }

        .order-card {
            margin-top: 18px;
            padding: 20px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--panel-soft);
        }

        .hidden {
            display: none;
        }

        .order-header {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 20px;
        }

        .order-number {
            color: var(--muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .order-title {
            margin-top: 5px;
            font-size: 24px;
            font-weight: 800;
        }

        .status-pill {
            align-self: flex-start;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.14);
            color: #86efac;
            font-size: 13px;
            font-weight: 700;
        }

        .details {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }

        .detail {
            padding: 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #151518;
        }

        .detail-label {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .detail-value {
            margin-top: 6px;
            font-size: 18px;
            font-weight: 750;
        }

        pre {
            min-height: 310px;
            margin: 0;
            padding: 18px;
            border-radius: 14px;
            overflow: auto;
            background: #050505;
            color: #86efac;
            font-family: "JetBrains Mono", monospace;
            font-size: 13px;
            line-height: 1.6;
        }

        @media (max-width: 760px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .search-row {
                flex-direction: column;
            }

            button {
                min-height: 46px;
            }
        }
    </style>
</head>

<body>
    <div class="shell">
        <nav>
            <a class="brand" href="/">JAFFSHOP</a>
            <span class="lab-badge">LOCALHOST LAB</span>
        </nav>

        <section class="hero">
            <div class="eyebrow">Access Control Laboratory</div>

            <h1>Order Object Viewer</h1>

            <p class="lead">
                Enter an order identifier and observe how the browser
                requests an object from the JaffShop API.
            </p>
        </section>

        <main class="grid">
            <section class="panel">
                <h2>Load an order</h2>

                <p class="hint">
                    The browser sends a GET request to the API.
                    Later we will add authentication and ownership checks.
                </p>

                <label for="order-id">Order ID</label>

                <div class="search-row">
                    <input
                        id="order-id"
                        type="number"
                        min="1"
                        value="1"
                        autocomplete="off"
                    >

                    <button id="load-order" type="button">
                        Load order
                    </button>
                </div>

                <div id="request-preview" class="request-preview">
                    GET /api/orders/1
                </div>

                <div id="request-status" class="status">
                    Ready.
                </div>

                <article id="order-card" class="order-card hidden">
                    <div class="order-header">
                        <div>
                            <div class="order-number">
                                Order <span id="order-id-value"></span>
                            </div>

                            <div
                                id="order-item"
                                class="order-title"
                            ></div>
                        </div>

                        <div
                            id="order-status"
                            class="status-pill"
                        ></div>
                    </div>

                    <div class="details">
                        <div class="detail">
                            <div class="detail-label">Owner ID</div>
                            <div
                                id="order-owner"
                                class="detail-value"
                            ></div>
                        </div>

                        <div class="detail">
                            <div class="detail-label">Total</div>
                            <div
                                id="order-total"
                                class="detail-value"
                            ></div>
                        </div>
                    </div>
                </article>
            </section>

            <aside class="panel">
                <h2>Raw API response</h2>

                <p class="hint">
                    This is the JSON returned by the server.
                </p>

                <pre id="raw-response">No response yet.</pre>
            </aside>
        </main>
    </div>

    <script>
        const orderInput = document.querySelector("#order-id");
        const loadButton = document.querySelector("#load-order");
        const preview = document.querySelector("#request-preview");
        const statusBox = document.querySelector("#request-status");
        const card = document.querySelector("#order-card");
        const rawResponse = document.querySelector("#raw-response");

        function updatePreview() {
            const orderId = orderInput.value || "{id}";
            preview.textContent = `GET /api/orders/${orderId}`;
        }

        async function loadOrder() {
            const orderId = orderInput.value.trim();

            if (!orderId) {
                statusBox.textContent = "Enter an order ID.";
                statusBox.className = "status error";
                return;
            }

            statusBox.textContent = "Sending request...";
            statusBox.className = "status";
            card.classList.add("hidden");
            rawResponse.textContent = "Loading...";

            try {
                const response = await fetch(
                    `/api/orders/${encodeURIComponent(orderId)}`,
                    {
                        method: "GET",
                        headers: {
                            "Accept": "application/json"
                        }
                    }
                );

                const data = await response.json();

                rawResponse.textContent = JSON.stringify(
                    data,
                    null,
                    2
                );

                if (!response.ok) {
                    throw new Error(
                        data.error || `HTTP ${response.status}`
                    );
                }

                document.querySelector("#order-id-value").textContent =
                    data.id;

                document.querySelector("#order-item").textContent =
                    data.item_name;

                document.querySelector("#order-owner").textContent =
                    data.user_id;

                document.querySelector("#order-total").textContent =
                    `$${data.total}`;

                document.querySelector("#order-status").textContent =
                    data.status;

                card.classList.remove("hidden");

                statusBox.textContent =
                    `HTTP ${response.status}: order loaded successfully.`;

                statusBox.className = "status";
            } catch (error) {
                statusBox.textContent = `Request failed: ${error.message}`;
                statusBox.className = "status error";
            }
        }

        orderInput.addEventListener("input", updatePreview);
        loadButton.addEventListener("click", loadOrder);

        orderInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                loadOrder();
            }
        });

        updatePreview();
    </script>
</body>
</html>
    """)

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "error": "username_and_password_required",
        }), 400

    conn = get_db()

    user = conn.execute("""
        SELECT id, username, password_hash
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if user is None:
        return jsonify({
            "error": "invalid_credentials",
        }), 401

    if not check_password_hash(
        user["password_hash"],
        password,
    ):
        return jsonify({
            "error": "invalid_credentials",
        }), 401

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "status": "logged_in",
        "user": {
            "id": user["id"],
            "username": user["username"],
        },
    })

@app.get("/api/me")
def current_user():
    user_id = session.get("user_id")
    username = session.get("username")

    if user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    return jsonify({
        "id": user_id,
        "username": username,
    })

@app.get("/api/orders-safe/<int:order_id>")
def get_order_safe(order_id):
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    conn = get_db()

    order = conn.execute("""
        SELECT id, user_id, item_name, total, status
        FROM orders
        WHERE id = ?
          AND user_id = ?
    """, (
        order_id,
        current_user_id,
    )).fetchone()

    conn.close()

    if order is None:
        return jsonify({
            "error": "order_not_found",
        }), 404

    return jsonify({
        "mode": "safe",
        "authenticated_user_id": current_user_id,
        "order": dict(order),
    }), 200
@app.get("/profile-lab")
def profile_lab():
    return render_template_string("""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>JaffShop — Profile Security Lab</title>

    <style>
        :root {
            color-scheme: dark;
            --background: #09090b;
            --panel: #18181b;
            --border: #34343a;
            --text: #f4f4f5;
            --muted: #a1a1aa;
            --accent: #22c55e;
            --danger: #ef4444;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family:
                Inter,
                system-ui,
                sans-serif;
            color: var(--text);
            background: var(--background);
        }

        .shell {
            width: min(960px, calc(100% - 32px));
            margin: 0 auto;
            padding: 32px 0 64px;
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 48px;
        }

        .brand {
            color: var(--text);
            font-weight: 800;
            text-decoration: none;
        }

        .badge {
            padding: 7px 11px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--muted);
            font-size: 13px;
        }

        h1 {
            margin: 0 0 14px;
            font-size: clamp(38px, 7vw, 68px);
            line-height: 1;
        }

        .lead {
            max-width: 680px;
            margin-bottom: 32px;
            color: var(--muted);
            line-height: 1.7;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 20px;
        }

        .panel {
            padding: 24px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: var(--panel);
        }

        .panel h2 {
            margin-top: 0;
        }

        .button-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        button {
            min-height: 44px;
            padding: 0 16px;
            border: 0;
            border-radius: 10px;
            background: var(--accent);
            color: #041108;
            font: inherit;
            font-weight: 800;
            cursor: pointer;
        }

        button.secondary {
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
        }

        .status {
            min-height: 24px;
            margin-top: 18px;
            color: var(--muted);
        }

        pre {
            min-height: 260px;
            margin: 0;
            padding: 18px;
            overflow: auto;
            border-radius: 12px;
            background: #050505;
            color: #86efac;
            font-size: 13px;
            line-height: 1.6;
        }

       label {
    display: block;
    margin: 16px 0 8px;
    font-size: 14px;
    font-weight: 700;
}

input {
    width: 100%;
    min-height: 44px;
    padding: 0 13px;
    border: 1px solid var(--border);
    border-radius: 10px;
    outline: none;
    background: #202024;
    color: var(--text);
    font: inherit;
}

input:focus {
    border-color: var(--accent);
}

button.danger {
    background: var(--danger);
    color: white;
}

.update-buttons {
    margin-top: 20px;
}

.full-width {
    grid-column: 1 / -1;
}

@media (max-width: 720px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
    </style>
</head>

<body>
    <div class="shell">
        <nav>
            <a class="brand" href="/">JAFFSHOP</a>
            <span class="badge">LOCALHOST LAB</span>
        </nav>

        <h1>Profile Security Lab</h1>

        <p class="lead">
            Authenticate as a test user and inspect the profile properties
            returned by the API.
        </p>

        <main class="grid">
    <section class="panel">
        <h2>1. Session</h2>

        <div class="button-row">
            <button id="login-alice" type="button">
                Login as Alice
            </button>

            <button id="login-bob" type="button">
                Login as Bob
            </button>

            <button
                id="load-profile"
                class="secondary"
                type="button"
            >
                Load profile
            </button>
        </div>

        <div id="status" class="status">
            Not authenticated.
        </div>
    </section>

    <section class="panel">
        <h2>2. Profile update</h2>

        <label for="display-name">Display name</label>

        <input
            id="display-name"
            type="text"
            value="Alice Admin"
            autocomplete="off"
        >

        <label for="role">Role</label>

        <input
            id="role"
            type="text"
            value="admin"
            autocomplete="off"
        >

        <div class="button-row update-buttons">
            <button
                id="update-vulnerable"
                class="danger"
                type="button"
            >
                Vulnerable PATCH
            </button>

            <button
                id="update-safe"
                type="button"
            >
                Safe PATCH
            </button>

            <button
                id="check-admin"
                class="secondary"
                type="button"
            >
                Check admin access
            </button>
        </div>
    </section>

    <section class="panel full-width">
        <h2>Raw API response</h2>
        <pre id="raw-response">No response yet.</pre>
    </section>
</main>
    </div>

    <script>
        const statusBox = document.querySelector("#status");
        const rawResponse = document.querySelector("#raw-response");

        async function showResponse(response) {
            const data = await response.json();

            rawResponse.textContent = JSON.stringify(
                data,
                null,
                2
            );

            statusBox.textContent = `HTTP ${response.status}`;

            return data;
        }

        async function login(username, password) {
            statusBox.textContent = `Logging in as ${username}...`;

            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    username,
                    password
                })
            });

            await showResponse(response);
        }

        async function loadProfile() {
            statusBox.textContent = "Loading profile...";

            const response = await fetch("/api/profile", {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            });

            await showResponse(response);
        }

        document
            .querySelector("#login-alice")
            .addEventListener("click", () => {
                login("alice", "AlicePass123!");
            });

        document
            .querySelector("#login-bob")
            .addEventListener("click", () => {
                login("bob", "BobPass123!");
            });

        document
            .querySelector("#load-profile")
            .addEventListener("click", loadProfile);
    async function updateProfile(endpoint) {
    const displayName =
        document.querySelector("#display-name").value;

    const role =
        document.querySelector("#role").value;

    statusBox.textContent = `Sending PATCH ${endpoint}...`;

    const response = await fetch(endpoint, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            display_name: displayName,
            role: role
        })
    });

    await showResponse(response);
}

async function checkAdminAccess() {
    statusBox.textContent = "Checking admin access...";

    const response = await fetch("/api/admin", {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    });

    await showResponse(response);
}

document
    .querySelector("#update-vulnerable")
    .addEventListener("click", () => {
        updateProfile("/api/profile");
    });

document
    .querySelector("#update-safe")
    .addEventListener("click", () => {
        updateProfile("/api/profile-safe");
    });

document
    .querySelector("#check-admin")
    .addEventListener("click", checkAdminAccess);
</script>
</body>
</html>
    """)

@app.get("/api/profile")
def get_profile():
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    conn = get_db()

    user = conn.execute("""
        SELECT id, username, display_name, role
        FROM users
        WHERE id = ?
    """, (current_user_id,)).fetchone()

    conn.close()

    if user is None:
        session.clear()

        return jsonify({
            "error": "user_not_found",
        }), 404

    return jsonify({
        "profile": dict(user),
    }), 200

@app.patch("/api/profile")
def update_profile_vulnerable():
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    data = request.get_json(silent=True) or {}

    display_name = data.get("display_name")
    role = data.get("role")

    if display_name is None or role is None:
        return jsonify({
            "error": "display_name_and_role_required",
        }), 400

    conn = get_db()

    # Intentionally vulnerable:
    # the client is allowed to update the sensitive role field.
    conn.execute("""
        UPDATE users
        SET display_name = ?,
            role = ?
        WHERE id = ?
    """, (
        display_name,
        role,
        current_user_id,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "mode": "vulnerable",
        "updated_fields": {
            "display_name": display_name,
            "role": role,
        },
    }), 200


@app.get("/api/admin")
def admin_panel():
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    conn = get_db()

    user = conn.execute("""
        SELECT id, username, role
        FROM users
        WHERE id = ?
    """, (current_user_id,)).fetchone()

    conn.close()

    if user is None:
        session.clear()

        return jsonify({
            "error": "user_not_found",
        }), 404

    if user["role"] != "admin":
        return jsonify({
            "error": "admin_required",
            "current_role": user["role"],
        }), 403

    return jsonify({
        "message": "admin_access_granted",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }), 200


@app.patch("/api/profile-safe")
def update_profile_safe():
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "authentication_required",
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "json_object_required",
        }), 400

    allowed_fields = {"display_name"}
    received_fields = set(data.keys())
    forbidden_fields = sorted(received_fields - allowed_fields)

    if forbidden_fields:
        return jsonify({
            "error": "forbidden_profile_fields",
            "fields": forbidden_fields,
        }), 400

    display_name = data.get("display_name")

    if not isinstance(display_name, str) or not display_name.strip():
        return jsonify({
            "error": "valid_display_name_required",
        }), 400

    display_name = display_name.strip()

    conn = get_db()

    conn.execute("""
        UPDATE users
        SET display_name = ?
        WHERE id = ?
    """, (
        display_name,
        current_user_id,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "mode": "safe",
        "updated_fields": {
            "display_name": display_name,
        },
    }), 200


if __name__ == "__main__":
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
