# SkillBridge Attendance API

SkillBridge is a command-line-first FastAPI backend for a prototype attendance management system. It implements JWT login, role-based access control, batch invite joins, session creation, attendance marking, summary reports, and a separate scoped token for Monitoring Officer read-only access.

## Tech Stack

- Python 3
- FastAPI
- SQLAlchemy ORM
- PostgreSQL on Railway for deployment
- SQLite for local default/test convenience
- PyJWT for JWT creation and validation
- passlib with bcrypt for password hashing
- Pydantic Settings / dotenv-style environment configuration
- pytest with FastAPI TestClient for tests
- Uvicorn as the ASGI server

## Live API Base URL

Deployment status: deployed on Railway with Railway PostgreSQL.

Live base URL: `https://web-production-b639d.up.railway.app`

The code is also deployment-ready for another Railway, Render, Fly.io, or similar environment. Set the environment variables from `.env.example`, point `DATABASE_URL` at PostgreSQL, and use this startup command:

```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

## Local Setup

From the `submission/` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m src.seed
uvicorn src.main:app --reload
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

Local API base URL:

```text
http://127.0.0.1:8000
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Environment Variables

```text
DATABASE_URL=sqlite:///./skillbridge.db
SECRET_KEY=replace-with-a-long-random-secret-at-least-32-bytes
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
MONITORING_TOKEN_EXPIRE_HOURS=1
MONITORING_API_KEY=dev-monitoring-key
```

For PostgreSQL, use a URL like:

```text
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
```

## Seeded Test Accounts

All seeded accounts use password `password123`.

| Role | Email |
| --- | --- |
| student | `student11@example.com` |
| trainer | `trainer1@example.com` |
| institution | `institution1@example.com` |
| programme_manager | `pm@example.com` |
| monitoring_officer | `monitor@example.com` |

The seed script creates 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions, and attendance records.

## Run Tests

```bash
pytest -q
```

The tests use a real temporary SQLite database through SQLAlchemy. They do not mock away the persistence layer.

## Seed Command

```bash
python -m src.seed
```

The seed is idempotent for users, batches, sessions, and attendance records. Delete `skillbridge.db` first if you want a completely clean local database.

## JWT Payloads

Standard access token, valid for 24 hours:

```json
{
  "user_id": 1,
  "role": "trainer",
  "token_type": "access",
  "iat": 1776670000,
  "exp": 1776756400
}
```

Monitoring scoped token, valid for 1 hour:

```json
{
  "user_id": 5,
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "scope": "monitoring:read",
  "iat": 1776670000,
  "exp": 1776673600
}
```

`GET /monitoring/attendance` rejects normal login tokens. It requires the scoped monitoring token returned by `POST /auth/monitoring-token`.

## Curl Examples

Set the base URL:

```bash
BASE_URL=http://127.0.0.1:8000
```

For the deployed Railway API, use:

```bash
BASE_URL=https://web-production-b639d.up.railway.app
```

The numeric IDs in the examples match a fresh local seed. On the live Railway database, demo accounts are seeded and working, but IDs may differ because deployment smoke checks can create extra rows. For live testing, use the returned IDs from create endpoints or inspect `/docs`.

### POST /auth/signup

```bash
curl -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Student","email":"demo.student@example.com","password":"password123","role":"student"}'
```

### POST /auth/login

```bash
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer1@example.com","password":"password123"}'
```

Store tokens:

```bash
TRAINER_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"trainer1@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
STUDENT_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"student11@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
INSTITUTION_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"institution1@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
PM_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"pm@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
MONITOR_LOGIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"monitor@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### POST /auth/monitoring-token

```bash
curl -X POST "$BASE_URL/auth/monitoring-token" \
  -H "Authorization: Bearer $MONITOR_LOGIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"dev-monitoring-key"}'
```

Store the scoped token:

```bash
MONITORING_TOKEN=$(curl -s -X POST "$BASE_URL/auth/monitoring-token" -H "Authorization: Bearer $MONITOR_LOGIN_TOKEN" -H "Content-Type: application/json" -d '{"key":"dev-monitoring-key"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### POST /batches

Trainer creates a batch for their institution:

```bash
curl -X POST "$BASE_URL/batches" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Evening Python Batch","institution_id":1}'
```

Institution creates a batch under itself:

```bash
curl -X POST "$BASE_URL/batches" \
  -H "Authorization: Bearer $INSTITUTION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Institution Created Batch"}'
```

### POST /batches/{id}/invite

Seed batch `1` is assigned to `trainer1@example.com`.

```bash
curl -X POST "$BASE_URL/batches/1/invite" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_hours":72}'
```

### POST /batches/join

Replace `<INVITE_TOKEN>` with the token returned above.

```bash
curl -X POST "$BASE_URL/batches/join" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"<INVITE_TOKEN>"}'
```

### POST /sessions

```bash
curl -X POST "$BASE_URL/sessions" \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"batch_id":1,"title":"API Practice","date":"2026-04-20","start_time":"14:00:00","end_time":"16:00:00"}'
```

### POST /attendance/mark

Attendance can only be marked during the session date and time window.

```bash
curl -X POST "$BASE_URL/attendance/mark" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":8,"status":"present"}'
```

### GET /sessions/{id}/attendance

```bash
curl "$BASE_URL/sessions/1/attendance" \
  -H "Authorization: Bearer $TRAINER_TOKEN"
```

### GET /batches/{id}/summary

```bash
curl "$BASE_URL/batches/1/summary" \
  -H "Authorization: Bearer $INSTITUTION_TOKEN"
```

### GET /institutions/{id}/summary

```bash
curl "$BASE_URL/institutions/1/summary" \
  -H "Authorization: Bearer $PM_TOKEN"
```

### GET /programme/summary

```bash
curl "$BASE_URL/programme/summary" \
  -H "Authorization: Bearer $PM_TOKEN"
```

### GET /monitoring/attendance

This must use `$MONITORING_TOKEN`, not `$MONITOR_LOGIN_TOKEN`.

```bash
curl "$BASE_URL/monitoring/attendance" \
  -H "Authorization: Bearer $MONITORING_TOKEN"
```

A non-GET request returns `405 Method Not Allowed`:

```bash
curl -X POST "$BASE_URL/monitoring/attendance"
```

## Schema Decisions

`batch_trainers` is a join table because a batch can have more than one trainer and a trainer can teach more than one batch. The session creation endpoint checks this assignment before allowing a trainer to create a session.

`batch_students` keeps enrolment separate from users because students can join multiple batches over time.

`batch_invites` stores opaque invite tokens with expiry and a `used` flag. This implementation treats invites as single-use. A trainer must be assigned to the batch before generating an invite.

Monitoring Officers use two token layers. First they log in normally and receive a standard `token_type=access` JWT. Then they exchange that token plus the environment-backed API key for a short-lived `token_type=monitoring` token scoped to `monitoring:read`. Monitoring endpoints reject standard tokens so read-only programme access is clearly separated.

## Working Status

Fully working:

- Signup and login with password hashing.
- Standard JWT auth with role in the server-validated token.
- Role checks for every protected endpoint.
- Batch creation, trainer invite creation, student invite join.
- Trainer session creation with assignment check.
- Student attendance marking with enrolment and active-session checks.
- Batch, institution, programme, session, and monitoring attendance reads.
- Monitoring Officer scoped token flow.
- Seed script and pytest suite.

Partially done:

- PostgreSQL is supported through `DATABASE_URL`, but this local submission uses SQLite by default.
- Tables are created at startup for simplicity. This is acceptable for a prototype but not enough for production schema migrations.

Skipped:

- Alembic migrations.
- Trainer assignment management endpoint. Seed data and trainer-created batches cover assigned trainers.
- Refresh tokens and token blacklist storage.

One thing I would do differently with more time:

- Add Alembic migrations early instead of relying on startup table creation. It is fine for this prototype, but migrations would make deployed schema changes safer and easier to review.

## Security Notes

Current security issue: JWTs are stateless and cannot be revoked before expiry. If a token leaks, it remains usable until `exp`.

With more time, I would add a `jti` claim, store active token IDs in Redis or PostgreSQL, and check that store on protected requests. Logout, account disablement, and key compromise response would add token IDs to a denylist until expiry.

For token rotation in a real deployment, I would keep short-lived access tokens, add refresh tokens stored server-side with rotation, and version signing keys with a `kid` header. During key rotation, the API would accept the previous key for a short grace period, issue new tokens with the new key, then retire the old key.

## Deployment Notes

Render example:

```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

Set these platform secrets:

```text
DATABASE_URL=<managed PostgreSQL URL>
SECRET_KEY=<strong random secret>
MONITORING_API_KEY=<strong random API key>
```

The repository includes a `Procfile` for platforms that detect it:

```text
web: uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

After deploy, run the seed command once from the platform shell if available:

```bash
python -m src.seed
```

If platform shell access is unavailable, seed locally against the managed PostgreSQL URL by setting `DATABASE_URL` in `.env` and running the same command.
