# Mass Assignment in JaffShop Profile API

## Context

- Application: JaffShop
- Environment: Flask + SQLite on localhost
- Scope: authorized educational laboratory

## Actors

- Alice: normal user
- Bob: normal user

## Sensitive property

`role` controls access to administrative functionality.

Normal value:

```text
user
```

Privileged value:

```text
admin
```

## Affected endpoint

```http
PATCH /api/profile
Content-Type: application/json
```

## Authentication baseline

Alice was authenticated successfully.

Before testing:

```json
{
  "display_name": "alice",
  "role": "user",
  "username": "alice"
}
```

## Vulnerable request

```http
PATCH /api/profile
Content-Type: application/json
```

```json
{
  "display_name": "Alice Admin",
  "role": "admin"
}
```

## Actual vulnerable behavior

The server accepted both properties and changed Alice's role:

```json
{
  "display_name": "Alice Admin",
  "role": "admin"
}
```

Alice then accessed:

```http
GET /api/admin
```

Result:

```text
HTTP 200
admin_access_granted
```

## Expected behavior

A normal user may update `display_name`, but must not be able to update:

- `role`
- `id`
- `username`
- `password_hash`

## Root cause

The vulnerable endpoint reads the sensitive `role` property from the
client-controlled JSON body and writes it to the database.

Authentication identifies Alice, but property-level authorization does not
verify whether Alice may modify `role`.

## Security fix

The safe endpoint uses an allowlist:

```python
allowed_fields = {"display_name"}
```

Any property outside the allowlist is rejected before executing SQL.

## Safe retest

Attempt:

```json
{
  "display_name": "Alice Admin",
  "role": "admin"
}
```

Result:

```text
HTTP 400
forbidden_profile_fields
role
```

Administrative access after the rejected request:

```text
HTTP 403
admin_required
```

A legitimate update still succeeds:

```json
{
  "display_name": "Alice Smith"
}
```

Final profile:

```json
{
  "display_name": "Alice Smith",
  "role": "user",
  "username": "alice"
}
```

## Impact

An authenticated attacker could promote their own account to an
administrative role and access privileged application functionality.

## Conclusion

Authentication answers:

> Who is the user?

Property-level authorization answers:

> Which fields may this user modify?

The safe implementation allows ordinary profile changes while protecting
security-sensitive properties.
