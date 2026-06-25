 JaffSec Lab

JaffSec Lab is my personal cybersecurity portfolio project focused on Web/AppSec and Reverse Engineering.

The goal is to turn each learned vulnerability into a portfolio artifact:

- vulnerable code
- localhost exploit scenario
- secure fix
- clinic-style writeup
- reusable payload pattern

## Current MVP

JaffShop: vulnerable Flask e-commerce lab.

First case:
- SQLi in product search endpoint `/api/search?q=`
## Current Module

### JaffShop: SQL Injection Search Lab

JaffShop is a small local Flask + SQLite web application.

Current feature:

- product list
- vulnerable product search
- safe product search

The goal of this module is to demonstrate the difference between unsafe SQL string interpolation and safe parameterized queries.

## How to Run

From the project root:

```bash
python3 jaffshop/app/app.py

Open in browser:

http://127.0.0.1:5000/

Browser Tests
1. Normal Search

In Vulnerable Search, enter:

hoodie

Expected result:

Kali Hoodie

2. No Results

In Vulnerable Search, enter:

nonexistent

Expected result:

No results.

3. SQL Injection Demo

In Vulnerable Search, enter:

nonexistent' OR 1=1--

Expected result:

All products are returned.

Why:

The vulnerable endpoint inserts user input directly into the SQL query.
4. Safe Search

In Safe Search, enter the same input:

nonexistent' OR 1=1--

Expected result:

No results.

Why:

The safe endpoint uses a parameterized SQL query, so the input is treated as data, not SQL logic.
Vulnerable Code Pattern

sql = f"SELECT id, name, description, price FROM products WHERE name LIKE '%{q}%'"

Secure Code Pattern

sql = "SELECT id, name, description, price FROM products WHERE name LIKE ?"
rows = conn.execute(sql, (f"%{q}%",)).fetchall()

Scope

This project is for localhost / lab / educational use only.
MD


