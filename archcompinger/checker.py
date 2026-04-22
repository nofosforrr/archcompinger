import logging
import time

from archcompinger.client import MattermostClient

LENS_EMOJI = "mag"  # Mattermost emoji name for 🔍
MOAC_MENTION = "@moac"
THRESHOLD_SECONDS = 15  # 24 * 3600 in production
REMINDER_MESSAGE = "@moac This thread has not been reviewed yet (no 🔍 reaction after 24 hours)."

logger = logging.getLogger(__name__)


async def check_channel(client: MattermostClient, channel_id: str, bot_user_id: str) -> None:
    data = await client.get_posts_for_channel(channel_id)
    posts: dict = data.get("posts", {})
    now = time.time()

    # Build a set of root_ids that the bot has already replied to
    already_replied = {
        p["root_id"] for p in posts.values()
        if p.get("root_id") and p.get("user_id") == bot_user_id
    }

    moac_posts = [
        (pid, p) for pid, p in posts.items()
        if not p.get("root_id") and MOAC_MENTION in p.get("message", "")
    ]
    logger.info("Channel=%s: %d total posts, %d mention %s", channel_id, len(posts), len(moac_posts), MOAC_MENTION)

    for post_id, post in moac_posts:
        if post_id in already_replied:
            logger.info("Post=%s — already reminded, skipping", post_id)
            continue

        age_seconds = now - post.get("create_at", 0) / 1000
        if age_seconds < THRESHOLD_SECONDS:
            logger.info("Post=%s age=%.0fs — too recent, skipping", post_id, age_seconds)
            continue

        reactions = await client.get_reactions(post_id)
        has_lens = any(r.get("emoji_name") == LENS_EMOJI for r in reactions)
        if has_lens:
            logger.info("Post=%s age=%.0fs — has 🔍, skipping", post_id, age_seconds)
            continue

        logger.info("Post=%s age=%.0fs — no 🔍, sending reminder", post_id, age_seconds)
        await client.create_post(channel_id, REMINDER_MESSAGE, root_id=post_id)


async def check_all_channels(client: MattermostClient, channel_ids: list[str], bot_user_id: str) -> None:
    for channel_id in channel_ids:
        try:
            await check_channel(client, channel_id, bot_user_id)
        except Exception:
            logger.exception("Failed to check channel=%s", channel_id)
