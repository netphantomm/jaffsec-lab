# Weak JWT Signing Secret in JaffShop

## Context

- Application: JaffShop
- Environment: Flask + SQLite on localhost
- Scope: authorized educational laboratory
- JWT algorithm: HS256

## Actor

- Alice: normal authenticated user
- Database role: `user`

## Sensitive claim

The vulnerable JWT contains the user's authorization role:

    {
      "sub": "1",
      "username": "alice",
      "role": "user"
    }

The `role` claim controls access to administrative functionality.

## Affected endpoints

    POST /api/jwt/vulnerable/login
    GET /api/jwt/vulnerable/admin

## Authentication baseline

Alice authenticated with valid credentials and received a JWT containing
`role=user`.

Request:

    GET /api/jwt/vulnerable/admin
    Authorization: Bearer <ordinary-user-token>

Result:

    HTTP 403
    admin_required

## Vulnerable configuration

The vulnerable implementation signs and verifies JWTs using a short,
guessable HMAC secret:

    JWT_VULNERABLE_SECRET = "secret"

The administrative endpoint trusts the role contained in the JWT:

    if payload.get("role") != "admin":
        return jsonify({
            "error": "admin_required"
        }), 403

## Attack path

The JWT payload was decoded and the role was changed:

    {
      "sub": "1",
      "username": "alice",
      "role": "admin"
    }

The modified token was signed using the weak secret:

    secret

Request:

    GET /api/jwt/vulnerable/admin
    Authorization: Bearer <forged-admin-token>

## Actual vulnerable behavior

The server accepted the forged signature because the same weak secret was
used to create and verify the token.

Result:

    HTTP 200
    admin_access_granted

Response:

    {
      "message": "admin_access_granted",
      "mode": "vulnerable",
      "token_claims": {
        "sub": "1",
        "username": "alice",
        "role": "admin"
      }
    }

Alice remained a normal user in the database, but the vulnerable endpoint
trusted the forged `role=admin` claim.

## Root cause

The vulnerability consists of two related problems:

1. The HS256 signing secret is short and guessable.
2. The administrative endpoint uses the JWT role claim as its authorization
   source.

JWT payloads can be read and modified by the client. Their integrity depends
on the attacker being unable to create a valid signature.

## Security fix

The safe implementation uses a strong random secret supplied through an
environment variable:

    JAFFSHOP_JWT_SECRET

The safe JWT contains identity information but does not contain the user's
role:

    {
      "sub": "1",
      "username": "alice"
    }

The safe endpoint:

- accepts only the configured HS256 algorithm;
- validates the token signature;
- validates `exp`, `iat`, `sub`, `iss`, and `aud`;
- loads the current user role from SQLite;
- does not trust a client-controlled role claim.

## Safe retest: legitimate token

Alice received a valid safe JWT.

Request:

    GET /api/jwt/safe/admin
    Authorization: Bearer <valid-safe-token>

The signature was valid, but Alice's current database role was `user`.

Result:

    HTTP 403
    admin_required
    authorization_source: database

## Safe retest: forged token

The forged token signed with the weak secret was sent to the safe endpoint:

    GET /api/jwt/safe/admin
    Authorization: Bearer <forged-admin-token>

The safe endpoint expected a signature created with the strong environment
secret.

Result:

    HTTP 401
    invalid_token

## Verification summary

    Ordinary vulnerable JWT
    -> vulnerable admin
    -> HTTP 403

    Forged role=admin JWT signed with weak secret
    -> vulnerable admin
    -> HTTP 200

    Valid safe JWT
    -> safe admin
    -> HTTP 403

    Forged weak-secret JWT
    -> safe admin
    -> HTTP 401

## Impact

An authenticated attacker who guesses or discovers the weak signing secret
can create valid administrative JWTs and perform vertical privilege
escalation.

## Conclusion

Decoding or changing a JWT does not automatically bypass security.

The attack succeeds because the weak secret allows the attacker to generate
a signature that the vulnerable server accepts.

The safe implementation uses a strong secret, validates the token and reads
authorization data from a trusted server-side source.
