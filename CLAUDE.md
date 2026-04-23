# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`archcompinger` is a Mattermost bot written in Python. It polls configured channels once an hour, finds root posts that mention `@moac`, and posts a reminder comment on any thread that has not received a 🔍 (`mag`) reaction within 24 hours.

## Running with Docker

### First-time setup

1. Start Mattermost and Postgres:

   ```bash
   docker compose up postgres mattermost
   ```

2. Open <http://localhost:8065>, complete the setup wizard, create an admin account.
3. Go to **System Console → Integrations → Bot Accounts**, enable bot accounts, create a bot, and copy its token.
4. Copy `.env.example` to `.env` and fill in `MATTERMOST_TOKEN` and `MATTERMOST_CHANNEL_IDS`.
5. Start everything:

   ```bash
   docker compose up -d
   ```

### Subsequent starts

```bash
docker compose up -d
docker compose logs -f archcompinger
```

### Rebuild after code changes

```bash
docker compose build archcompinger && docker compose up -d archcompinger
```

## Running locally (without Docker)

```bash
poetry install
cp .env.example .env  # fill in values
poetry run archcompinger
```

Lint:

```bash
poetry run ruff check .
poetry run ruff format .
```

## Architecture

Three modules, each with a single responsibility:

- **`archcompinger/client.py`** — thin `aiohttp` wrapper around the Mattermost REST API (`/api/v4`). Manages a single `ClientSession` via async context manager.
- **`archcompinger/checker.py`** — polling logic. Fetches posts, filters root posts mentioning `@moac` that are older than 24 h and lack the `mag` reaction, then posts a reply.
- **`archcompinger/main.py`** — entry point. Loads `.env`, waits for Mattermost to be reachable, then runs `check_all_channels` in a `while True / asyncio.sleep(3600)` loop.

## Key Details

- Mattermost timestamps (`create_at`) are in **milliseconds**.
- The lens emoji name in the Mattermost API is `mag` (not `mag_right` or `lens`).
- The bot only inspects **root posts** (posts where `root_id` is empty); replies are skipped.
- In Docker, `MATTERMOST_URL` is set to `http://mattermost:8065` (internal service name) by `docker-compose.yml`. The `.env` file provides only `MATTERMOST_TOKEN` and `MATTERMOST_CHANNEL_IDS`.
- Pagination is not yet implemented — `get_posts_for_channel` fetches one page (60 posts). Add pagination if channels are high-volume.
