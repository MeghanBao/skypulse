# SkyPulse

SkyPulse is a flight-deal discovery and subscription system with two runnable services:

- `skypulse/`: Next.js 16 + Prisma web dashboard (Phase 2 core)
- `skypulse-email/`: Python email parsing, matching, and monitoring service

> The repository is currently centered on **Phase 2 web capabilities**, so this README focuses on what is implemented now, how to run it, and how to verify it.

---

## 1) Current implementation status

### Web app (`skypulse/`)

- Authentication and user management
  - Register / sign in / sign out
  - Cookie-based session handling
  - Password hashing and verification (`pbkdf2`)
  - Email verification token model and flow
- Subscription management (user-isolated)
  - Create subscriptions from natural-language prompts
  - Pause/activate subscriptions
  - Delete subscriptions
  - Ownership checks enforced via `userId`
- User preferences
  - `preferredOrigin`
  - `preferredMaxPrice`
  - `notificationEmail`
- Dashboard analytics
  - Total deal frequency
  - Average deal price
  - Active subscription count
  - Destination distribution
  - Deal cards + email preview feed

### Email service (`skypulse-email/`)

- Parsing and matching modules (`parsers/`, `matching/`)
- Reliability and monitoring utilities (`monitoring/health.py`, `monitoring/metrics.py`, `monitoring/retry.py`)
- SQLite local database and runnable service entry (`main.py`)

---

## 2) Repository structure

```text
skypulse/
├── skypulse/               # Next.js + Prisma web app (Phase 2)
├── skypulse-email/         # Python email service
├── PHASE2.md               # Historical phase planning doc (contains outdated plan items)
└── README.md               # Repository overview (this file)
```

---

## 3) Quick start

### 3.1 Run the web app (recommended first)

```bash
cd skypulse
npm install
```

Create `skypulse/.env`:

```env
DATABASE_URL="file:./prisma/dev.db"
OPENAI_API_KEY="sk-..."
```

Initialize database and start dev server:

```bash
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
npm run dev
```

Open: <http://localhost:3000>

---

### 3.2 Run the email service

```bash
cd skypulse-email
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 4) Verification commands

### Web app

```bash
cd skypulse
npm run lint
DATABASE_URL='file:./prisma/dev.db' npm run build
```

### Prisma (optional)

```bash
cd skypulse
npx prisma generate
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
```

---

## 5) Environment variables

### `skypulse/.env`

- `DATABASE_URL`: Prisma database connection string (SQLite file by default).
- `OPENAI_API_KEY`: Enables LLM-powered parsing/summarization.
  - If missing, parts of the LLM flow may fall back to default/mock behavior for local development.

---

## 6) Notes and boundaries

- `PHASE2.md` includes historical planning and targets; it does **not** fully represent the current implementation.
- For web-app-specific details (features, models, workflows), see `skypulse/README.md`.
