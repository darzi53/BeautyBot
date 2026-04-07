# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the bot

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in the token
cp .env.example .env

# Run
python -m bot.main
```

## Architecture

`bot/` is the main package. Entry point is `bot/main.py` which wires everything together.

- **config.py** — `Settings` via pydantic-settings, reads `.env`. Import `settings` singleton.
- **database/engine.py** — async SQLAlchemy engine + `async_session_maker`. `create_tables()` runs on startup.
- **database/models.py** — SQLAlchemy ORM models with `Base`.
- **middlewares/db.py** — `DbSessionMiddleware` injects `session: AsyncSession` into every handler via `data["session"]`.
- **handlers/** — each file creates its own `Router` and registers it in `main.py` via `dp.include_router()`. `common.py` must always be included **last** (fallback).
- **keyboards/** — keyboard builders return `InlineKeyboardMarkup` / `ReplyKeyboardMarkup`.

## Adding a new handler

1. Create `bot/handlers/my_feature.py` with `router = Router()`.
2. Add `dp.include_router(my_feature.router)` in `main.py` **before** `common.router`.
3. Accept `session: AsyncSession` as a parameter if DB access is needed.

## Database

SQLite by default (`beautybot.db`). To switch to PostgreSQL, change `DATABASE_URL` in `.env` to `postgresql+asyncpg://...` and add `asyncpg` to requirements. Migrations via Alembic (run `alembic init migrations` to initialize).

## Obsidian Sync

After every meaningful change to the project (new feature, new handler, schema change, refactor, etc.), update the Obsidian note at:

`C:/Programmer Shit/Obsidian/XOLOD/Projects/BeautyBot.md`

Add an entry to the **Changelog** section at the bottom of that note in the following format:

```
### YYYY-MM-DD — <short description>
- <what was changed and why>
```

Use the obsidian-helper agent for this.
