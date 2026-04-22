import asyncio
import logging
import os

from dotenv import load_dotenv

from archcompinger.checker import check_all_channels
from archcompinger.client import MattermostClient

load_dotenv()

POLL_INTERVAL = 30  # seconds (use 3600 in production)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _config() -> tuple[str, str, list[str]]:
    url = os.environ["MATTERMOST_URL"]
    token = os.environ["MATTERMOST_TOKEN"]
    channel_ids = os.environ["MATTERMOST_CHANNEL_IDS"].split(",")
    return url, token, channel_ids


async def _wait_for_mattermost(url: str, token: str) -> None:
    for attempt in range(10):
        try:
            async with MattermostClient(url, token) as client:
                await client.ping()
            logger.info("Connected to Mattermost.")
            return
        except Exception:
            wait = 10 * (attempt + 1)
            logger.warning("Mattermost not ready (attempt %d/10), retrying in %ds...", attempt + 1, wait)
            await asyncio.sleep(wait)
    raise RuntimeError("Could not connect to Mattermost after 10 attempts.")


async def _loop() -> None:
    url, token, channel_ids = _config()
    await _wait_for_mattermost(url, token)
    async with MattermostClient(url, token) as client:
        bot_user_id = await client.get_my_user_id()
    logger.info("Bot user_id=%s", bot_user_id)
    while True:
        logger.info("Starting poll cycle.")
        async with MattermostClient(url, token) as client:
            await check_all_channels(client, channel_ids, bot_user_id)
        logger.info("Poll cycle done. Sleeping for %ds.", POLL_INTERVAL)
        await asyncio.sleep(POLL_INTERVAL)


def run() -> None:
    """Entry point. Starts the bot and runs the polling loop until interrupted."""
    asyncio.run(_loop())


if __name__ == "__main__":
    run()
