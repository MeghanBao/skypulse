# SkyPulse - Intelligent Flight Deal System

**SkyPulse** is your personal, AI-powered flight deal assistant. Instead of endless searching, simply tell SkyPulse what you're looking for (e.g., "Weekend trip to Paris under $500 next month"), and it will monitor deals, analyze them for value, and notify you with a personalized summary.

## ✨ Features

- **Natural Language Subscriptions**: No more complex forms. Just type your travel plans naturally.
- **Intelligent Recommendations**: Uses LLMs (OpenAI) to analyze flight data and explain *why* a deal is good for you.
- **Deal Dashboard**: A clean, premium interface to view your active subscriptions and recommended flights.
- **Multi-Channel Push**: (Planned) Get notified via Email, WhatsApp, or Telegram.

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- An OpenAI API Key

### Installation

1.  **Clone the repository** (or navigate to the directory):
    ```bash
    cd skypulse
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Environment Setup**:
    Create a `.env` file in the root directory:
    ```env
    DATABASE_URL="file:./dev.db"
    OPENAI_API_KEY="sk-..."
    ```

4.  **Database Setup**:
    Initialize the SQLite database:
    ```bash
    npx prisma migrate dev --name init
    ```

5.  **Run the application**:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) with your browser.

## 🛠 Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
- **Language**: TypeScript
- **Database**: SQLite with [Prisma](https://www.prisma.io/)
- **AI/LLM**: OpenAI API

## 📂 Project Structure

- `/app`: Frontend pages and API routes (Next.js App Router).
- `/lib`: Shared utilities (Database client, LLM wrapper).
- `/prisma`: Database schema and migrations.
- `/components`: Reusable UI components.

## 🤝 Contributing

This is a personal project. Feel free to fork and customize!
