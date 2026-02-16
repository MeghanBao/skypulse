# SkyPulse Web App (Phase 2)

SkyPulse is an AI-powered flight-deal dashboard built with Next.js + Prisma.

## What is implemented in Phase 2

- User registration, sign-in, sign-out, and session cookie auth
- Email verification flow (token-based)
- User-scoped subscriptions (create, pause/activate, delete)
- User preference settings (default origin, max budget, notification email)
- Dashboard analytics (deal count, average price, active subscriptions, destination trends)
- Deal cards and email preview section

## Tech Stack

- Next.js (App Router)
- TypeScript
- Prisma + SQLite
- Tailwind CSS
- OpenAI API (for parsing and summary generation)

## Prerequisites

- Node.js 18+
- npm
- OpenAI API key (optional for local mock behavior)

## Setup

```bash
cd skypulse
npm install
```

Create `.env` in `skypulse/`:

```env
DATABASE_URL="file:./prisma/dev.db"
OPENAI_API_KEY="sk-..."
```

Initialize database schema:

```bash
DATABASE_URL='file:./prisma/dev.db' npx prisma db push
```

## Run

```bash
npm run dev
```

Open http://localhost:3000

## Quality checks

```bash
npm run lint
DATABASE_URL='file:./prisma/dev.db' npm run build
```

## Key folders

- `app/` - pages and server actions
- `components/` - UI components
- `lib/` - prisma client, auth helper, LLM integrations
- `prisma/` - schema and local sqlite db
- `public/` - static assets
