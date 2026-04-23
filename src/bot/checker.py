import logging
import time

from bot.client import MattermostClient

LENS_EMOJI = "mag"  # Mattermost emoji name for 🔍
MOAC_MENTION = "@moac"
THRESHOLD_SECONDS = 15   # 24 * 3600 in production
REMIND_INTERVAL = 20     # 3600 in production
REMINDER_MESSAGE = "@moac This thread has not been reviewed yet (no 🔍 reaction after 24 hours)."

logger = logging.getLogger(__name__)


async def check_channel(client: MattermostClient, channel_id: str, bot_user_id: str) -> None:
    """Check a single channel for unreviewed @moac threads and send reminders.

    A thread is eligible for a reminder when all of the following are true:
    - The root post mentions ``@moac``.
    - The root post is older than ``THRESHOLD_SECONDS``.
    - The root post has no 🔍 (``mag``) reaction.
    - At least ``REMIND_INTERVAL`` seconds have passed since the bot's last reminder in that thread.
    """
    data = await client.get_posts_for_channel(channel_id)
    posts: dict = data.get("posts", {})
    now = time.time()

    # For each root post, find the timestamp of the bot's most recent reminder reply
    last_reminded: dict[str, float] = {}
    for p in posts.values():
        root_id = p.get("root_id")
        if root_id and p.get("user_id") == bot_user_id:
            ts = p.get("create_at", 0) / 1000
            if ts > last_reminded.get(root_id, 0):
                last_reminded[root_id] = ts

    moac_posts = [
        (pid, p) for pid, p in posts.items()
        if not p.get("root_id") and MOAC_MENTION in p.get("message", "")
    ]
    logger.info("Channel=%s: %d total posts, %d mention %s", channel_id, len(posts), len(moac_posts), MOAC_MENTION)

    for post_id, post in moac_posts:
        age_seconds = now - post.get("create_at", 0) / 1000
        if age_seconds < THRESHOLD_SECONDS:
            logger.info("Post=%s age=%.0fs — too recent, skipping", post_id, age_seconds)
            continue

        reactions = await client.get_reactions(post_id)
        has_lens = any(r.get("emoji_name") == LENS_EMOJI for r in reactions)
        if has_lens:
            logger.info("Post=%s age=%.0fs — has 🔍, skipping", post_id, age_seconds)
            continue

        since_last = now - last_reminded.get(post_id, 0)
        if since_last < REMIND_INTERVAL:
            logger.info("Post=%s — reminded %.0fs ago, next in %.0fs", post_id, since_last, REMIND_INTERVAL - since_last)
            continue

        logger.info("Post=%s age=%.0fs — no 🔍, sending reminder", post_id, age_seconds)
        await client.create_post(channel_id, REMINDER_MESSAGE, root_id=post_id)


async def check_all_channels(client: MattermostClient, channel_ids: list[str], bot_user_id: str) -> None:
    """Run ``check_channel`` for every channel in the list, logging but not re-raising per-channel errors."""
    for channel_id in channel_ids:
        try:
            await check_channel(client, channel_id, bot_user_id)
        except Exception:
            logger.exception("Failed to check channel=%s", channel_id)
