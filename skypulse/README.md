# SkyPulse Web App (Phase 2)

`skypulse/` is the Phase 2 web application for SkyPulse, built with **Next.js App Router + Prisma + SQLite + Tailwind CSS**.

This README covers:
- what is implemented today,
- how to run locally,
- the data model and key flows,
- and minimum verification commands.

---

## 1) Implemented features

### Authentication and session

- User registration (email + password)
- Sign in / sign out
- Cookie-based session persistence
- Password hashing and verification (`pbkdf2`)
- Email verification token flow (create token, submit token, update verification state)

### User-scoped subscription management

- Create subscriptions from natural-language prompts
- Default-value fallback from user preferences (origin / max price)
- Toggle subscription active state (`isActive`)
- Delete subscriptions
- Ownership checks for subscription actions using current logged-in user

### User preferences

- `preferredOrigin`
- `preferredMaxPrice`
- `notificationEmail`

### Dashboard and analytics

- KPI cards: average price, deal count, active subscriptions
- Popular destination stats (grouped by arrival city)
- Subscription management list
- Deal card stream and email preview section

---

## 2) Tech stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Prisma 5 + SQLite
- Tailwind CSS
- OpenAI SDK (for prompt parsing and summary generation)

---

## 3) Directory overview

```text
skypulse/
├── app/                # routes and Server Actions
├── components/         # UI components (subscription form, deal card, etc.)
├── lib/                # auth, prisma client, LLM service, flight service
├── prisma/             # schema and local sqlite files
├── public/             # static assets (including grid background)
└── README.md
```

---

## 4) Local setup

### 4.1 Install dependencies

```bash
cd skypulse
npm install
```

### 4.2 Configure environment variables

Create `skypulse/.env`:

```env
DATABASE_URL="file:./prisma/dev.db"
OPENAI_API_KEY="sk-..."
```

> `OPENAI_API_KEY` is recommended. Without it, LLM-related behavior may run in fallback/default mode for local debugging.

### 4.3 Initialize database schema

```bash
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
```

### 4.4 Start development server

```bash
npm run dev
```

Open: <http://localhost:3000>

---

## 5) Quality checks and build

```bash
npm run lint
DATABASE_URL='file:./prisma/dev.db' npm run build
```

Optional (regenerate Prisma client):

```bash
npx prisma generate
```

---

## 6) Data model summary (Prisma)

Core models:

- `User`
  - email, password hash, verification state
  - preference fields: `preferredOrigin`, `preferredMaxPrice`, `notificationEmail`
- `VerificationToken`
  - linked to user, includes token and expiration
- `Subscription`
  - owned by `userId`
  - stores prompt + structured filters
- `Deal`
  - linked to subscription
  - stores price, airline, dates, booking link, and summary reason

Relationship highlights:

- `User -> Subscription` cascade delete
- `User -> VerificationToken` cascade delete
- `Subscription -> Deal` cascade delete

---

## 7) Core flow (high level)

1. User registration creates a `User` and a `VerificationToken`.
2. Successful sign-in sets session cookie.
3. Subscription creation flow:
   - parse user prompt,
   - create subscription,
   - query deals and generate summaries,
   - persist deals.
4. Dashboard load aggregates subscriptions and deals for current user and computes metrics.

---

## 8) FAQ

### Q1: Database error on startup?
Run:

```bash
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
```

### Q2: Can I run without `OPENAI_API_KEY`?
Yes. The app runs, but LLM-related output quality and behavior may be degraded.

### Q3: Why is dashboard empty?
Dashboard data is user-scoped. Register/sign in first, then create a subscription under that account.
