# SQLi Search Explanation

## What this module demonstrates

This module shows the difference between:

- vulnerable SQL query construction
- safe parameterized SQL query

The vulnerable endpoint is:

```http
GET /api/search?q=

The safe endpoint is:

GET /api/search_safe?q=

Normal behavior

When the user searches:

hoodie

The app searches products by name and returns matching products.
Vulnerable code

q = request.args.get("q", "")
sql = f"SELECT id, name, description, price FROM products WHERE name LIKE '%{q}%'"

The problem is that user input is inserted directly into the SQL query.
Why this is dangerous

The user controls q.

So if the user enters:

nonexistent' OR 1=1--

the SQL logic can be changed.

Instead of searching only for a product name, the query can be forced to return all rows.
Safe code

sql = "SELECT id, name, description, price FROM products WHERE name LIKE ?"
rows = conn.execute(sql, (f"%{q}%",)).fetchall()

Here the input is treated as data, not SQL code.
Main lesson

Never build SQL queries by inserting user input directly into the query string.

Use parameterized queries.
