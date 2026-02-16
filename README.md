# SkyPulse

SkyPulse is an intelligent flight-deal system with two parts:

- `skypulse/`: Next.js web app (Phase 2 dashboard)
- `skypulse-email/`: Python email processing and monitoring service

---

## Current Phase 2 status (web app)

Implemented in `skypulse/`:

- Auth and user management
  - Register / Sign in / Sign out
  - Cookie-based session
  - Email verification token model + flow
- Subscription management
  - Create subscription from natural-language prompt
  - Pause/activate subscription
  - Delete subscription
  - User ownership enforced
- Settings and preferences
  - Default origin
  - Default max budget
  - Notification email
- Dashboard and analytics
  - Deal frequency
  - Average price
  - Active subscriptions
  - Destination trend bars
  - Deal + email preview feed

---

## Repository structure

```text
skypulse/
├── skypulse/           # Next.js + Prisma web app
├── skypulse-email/     # Python email service
├── PHASE2.md           # phase planning doc
└── README.md
```

---

## Quick start

### 1) Web app (`skypulse/`)

```bash
cd skypulse
npm install
```

Create `.env`:

```env
DATABASE_URL="file:./prisma/dev.db"
OPENAI_API_KEY="sk-..."
```

Sync database and run:

```bash
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
npm run dev
```

Open: http://localhost:3000

### 2) Email service (`skypulse-email/`)

```bash
cd skypulse-email
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Verification commands

Web app:

```bash
cd skypulse
npm run lint
DATABASE_URL='file:./prisma/dev.db' npm run build
```

---

## Notes

- If `OPENAI_API_KEY` is missing, parts of the LLM behavior may fall back to mock/default responses for local development.
- The email service includes monitoring utilities under `skypulse-email/monitoring` (health checks, metrics, retries).
