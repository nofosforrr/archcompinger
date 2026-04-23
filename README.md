# archcompinger

A Mattermost bot that monitors channels for posts mentioning `@moac` and posts a reminder in the thread if no 🔍 reaction is added within 24 hours. Reminders repeat every hour until the reaction appears.

## Requirements

- Docker & Docker Compose

## Configuration

All configuration is done through environment variables. Copy the example file and fill in the values:

```bash
cp .env.example .env
```

Open `.env` and set the following variables:

| Variable | Description |
| --- | --- |
| `MATTERMOST_URL` | URL of your Mattermost instance (e.g. `http://localhost:8065`) |
| `MATTERMOST_TOKEN` | Bot account access token |
| `MATTERMOST_CHANNEL_IDS` | Comma-separated list of channel IDs to monitor |

### How to get a bot token

1. Log in to Mattermost as an admin.
2. Go to **System Console → Integrations → Bot Accounts** and enable bot accounts.
3. Go to **Integrations → Bot Accounts → Add Bot Account**, fill in a username, and click **Create Bot Account**.
4. Copy the token shown on the next screen — it is only displayed once.

### How to find a channel ID

Open the channel in Mattermost, click the channel name at the top → **View Info**. The ID appears in the URL or the info panel.

### Example `.env`

```env
MATTERMOST_URL=http://localhost:8065
MATTERMOST_TOKEN=bdq17is68pb3bmadp757c46jkh
MATTERMOST_CHANNEL_IDS=n9ng644ugfr15phcwj9u3d88sc
```

For multiple channels, separate IDs with commas and no spaces:

```env
MATTERMOST_CHANNEL_IDS=n9ng644ugfr15phcwj9u3d88sc,abc123def456ghi789jkl012mn
```

## Running with Docker

### First-time setup

Start Mattermost and Postgres, then complete the Mattermost setup wizard:

```bash
docker compose up postgres mattermost
```

Open <http://localhost:8065>, create an admin account, then follow the [configuration steps](#configuration) above to create a bot and fill in `.env`.

Start the full stack:

```bash
docker compose up -d
```

### Viewing logs

```bash
docker compose logs -f archcompinger
```

### Stopping

```bash
docker compose down
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
