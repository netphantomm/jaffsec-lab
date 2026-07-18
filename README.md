# JaffSec Lab

JaffSec Lab is a localhost cybersecurity portfolio project focused on
Web and API Application Security.

The project turns each studied vulnerability into a reproducible portfolio
artifact:

- intentionally vulnerable code;
- localhost attack scenario;
- secure implementation;
- vulnerable-versus-safe comparison;
- clinic-style case study;
- reusable security pattern.

> This repository is intentionally vulnerable and must only be used in a
> localhost, laboratory, CTF, or otherwise authorized environment.

## Current Labs

### 1. SQL Injection — Product Search

Demonstrates the difference between unsafe SQL string interpolation and
parameterized queries.

| Component | Endpoint |
|---|---|
| Browser lab | `/` |
| Vulnerable API | `GET /api/search?q=` |
| Safe API | `GET /api/search_safe?q=` |

Case study:

- [SQL Injection Search Case](case-files/appsec-clinic/sqli-search-case.md)

Additional materials:

- [SQL Injection Explanation](docs/sqli-search-explanation.md)
- [SQL Injection Context Pattern](payload-pattern-bible/web/sqli-search-context.md)

---

### 2. IDOR / BOLA — Order Ownership

Demonstrates broken object-level authorization.

An authenticated user can request an order by its identifier. The vulnerable
endpoint verifies that the order exists but does not verify that the
authenticated user owns it.

| Component | Endpoint |
|---|---|
| Browser lab | `/orders-lab` |
| Vulnerable API | `GET /api/orders/<order_id>` |
| Safe API | `GET /api/orders-safe/<order_id>` |

The safe implementation includes both the object identifier and the
authenticated user identifier in the database query.

Case study:

- [IDOR Orders Case](case-files/appsec-clinic/idor-orders-case.md)

---

### 3. Mass Assignment — Profile Role Escalation

Demonstrates broken object-property authorization and vertical privilege
escalation.

The vulnerable profile endpoint accepts the sensitive `role` property from a
client-controlled JSON body. A normal user can change their role from `user`
to `admin` and access administrative functionality.

| Component | Endpoint |
|---|---|
| Browser lab | `/profile-lab` |
| Read profile | `GET /api/profile` |
| Vulnerable update | `PATCH /api/profile` |
| Safe update | `PATCH /api/profile-safe` |
| Impact verification | `GET /api/admin` |

The safe implementation uses an explicit allowlist:

```python
allowed_fields = {"display_name"}
```

Case study:

- [Mass Assignment Profile Case](case-files/appsec-clinic/mass-assignment-profile-case.md)

## Technology Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Git and GitHub

## Project Structure

```text
jaffsec-lab/
├── README.md
├── jaffshop/
│   └── app/
│       └── app.py
├── case-files/
│   └── appsec-clinic/
│       ├── sqli-search-case.md
│       ├── idor-orders-case.md
│       └── mass-assignment-profile-case.md
├── docs/
│   └── sqli-search-explanation.md
└── payload-pattern-bible/
    └── web/
        └── sqli-search-context.md
```

## How to Run

Clone the repository and enter the project directory:

```bash
git clone https://github.com/netphantomm/jaffsec-lab.git
cd jaffsec-lab
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Start JaffShop:

```bash
python3 jaffshop/app/app.py
```

Open the labs:

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/orders-lab
http://127.0.0.1:5000/profile-lab
```

## Test Accounts

The application creates two local test accounts:

| Username | Password | Initial role |
|---|---|---|
| `alice` | `AlicePass123!` | `user` |
| `bob` | `BobPass123!` | `user` |

These credentials are only for the local educational application.

## Security Method

Each lab follows the same workflow:

1. Establish an authenticated baseline.
2. Identify the controlled input.
3. Identify the protected object or property.
4. Send the vulnerable request.
5. Verify the security impact.
6. Implement a server-side fix.
7. Repeat the same test against the safe implementation.
8. Document the root cause, impact, and remediation.

## Current Focus

The current portfolio track is Web and API Application Security:

- HTTP and sessions;
- authentication;
- access control;
- IDOR / BOLA;
- property-level authorization;
- SQL injection;
- secure server-side validation;
- vulnerable-versus-safe API design.

## Legal Scope

This project is for:

- localhost laboratories;
- educational use;
- CTF environments;
- explicitly authorized security testing.

It must not be used against third-party systems without permission.
