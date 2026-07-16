# IDOR / BOLA in JaffShop Order API

## Context

- Application: JaffShop
- Environment: localhost Flask + SQLite laboratory
- Scope: authorized educational testing only

## Actors

- Alice: `user_id=1`
- Bob: `user_id=2`

## Object ownership

- Order 1 belongs to Alice (`user_id=1`)
- Order 2 belongs to Bob (`user_id=2`)

## Affected endpoint

- Method: `GET`
- Path: `/api/orders/<order_id>`

## Controlled input

The client controls `order_id` in the URL path.

Example:

```http
GET /api/orders/2
```

## Authentication baseline

A request without a valid session returned:

```http
HTTP/1.1 401 UNAUTHORIZED
```

```json
{
  "error": "authentication_required"
}
```

Alice's authenticated session was confirmed through:

```http
GET /api/me
```

```json
{
  "id": 1,
  "username": "alice"
}
```

## Expected behavior

Alice should only be able to access orders owned by `user_id=1`.

When Alice requests Bob's order, the server should return `403` or `404`
without disclosing the order data.

## Actual vulnerable behavior

Alice requested:

```http
GET /api/orders/2
```

The server returned:

- Authenticated user ID: `1`
- Requested order ID: `2`
- Returned owner ID: `2`
- HTTP status: `200 OK`

The response disclosed Bob's order:

```json
{
  "authenticated_user_id": 1,
  "mode": "vulnerable",
  "order": {
    "id": 2,
    "item_name": "Binary Autopsy Notebook",
    "status": "paid",
    "total": 12,
    "user_id": 2
  }
}
```

## Root cause

The vulnerable query filters the order only by its object identifier:

```sql
SELECT id, user_id, item_name, total, status
FROM orders
WHERE id = ?
```

Authentication identifies the current user, but the query does not verify
that the requested order belongs to that user.

## Security fix

The safe query includes the authenticated user's ID in the object lookup:

```sql
SELECT id, user_id, item_name, total, status
FROM orders
WHERE id = ?
  AND user_id = ?
```

The values are:

- `order_id` from the URL path;
- `user_id` from the signed Flask session.

A client cannot select another owner by changing only the URL identifier.

## Retest matrix

| Session | Requested order | Vulnerable endpoint | Safe endpoint |
|---|---:|---|---|
| Alice (`1`) | Order 1 | `200` | `200` |
| Alice (`1`) | Order 2 | `200` — foreign object exposed | `404` |
| Bob (`2`) | Order 2 | `200` | `200` |
| Bob (`2`) | Order 1 | `200` — foreign object exposed | `404` |

## Impact

An authenticated attacker could enumerate order identifiers and access
orders belonging to other users.

Exposed information could include:

- purchased item;
- order status;
- total price;
- internal owner identifier.

In a real application, an order object might also expose addresses,
recipient details, payment metadata or other personal information.

## Conclusion

Authentication answers:

> Who is making the request?

Authorization answers:

> Is this user allowed to access this specific object?

The vulnerable endpoint authenticated Alice but did not verify that the
requested order belonged to Alice.

The safe endpoint performs object-level authorization by querying the order
using both its identifier and the authenticated user's identifier.
