import logging
import aiohttp
from typing import Any

BASE_HEADERS = {"Content-Type": "application/json"}

logger = logging.getLogger(__name__)


class MattermostClient:
    def __init__(self, url: str, token: str) -> None:
        self.base_url = url.rstrip("/") + "/api/v4"
        self.headers = {**BASE_HEADERS, "Authorization": f"Bearer {token}"}
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "MattermostClient":
        self._session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._session:
            await self._session.close()

    async def get_posts_for_channel(self, channel_id: str, page: int = 0, per_page: int = 60) -> dict:
        url = f"{self.base_url}/channels/{channel_id}/posts"
        logger.debug("GET posts channel=%s page=%d", channel_id, page)
        async with self._session.get(url, params={"page": page, "per_page": per_page}) as resp:
            resp.raise_for_status()
            data = await resp.json()
            logger.debug("Got %d posts from channel=%s", len(data.get("posts", {})), channel_id)
            return data

    async def get_reactions(self, post_id: str) -> list[dict]:
        logger.debug("GET reactions post=%s", post_id)
        async with self._session.get(f"{self.base_url}/posts/{post_id}/reactions") as resp:
            resp.raise_for_status()
            reactions = await resp.json() or []
            logger.debug("Post=%s has %d reaction(s)", post_id, len(reactions))
            return reactions

    async def get_my_user_id(self) -> str:
        async with self._session.get(f"{self.base_url}/users/me") as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["id"]

    async def ping(self) -> None:
        logger.debug("GET /system/ping")
        async with self._session.get(f"{self.base_url}/system/ping") as resp:
            resp.raise_for_status()

    async def create_post(self, channel_id: str, message: str, root_id: str = "") -> dict:
        logger.info("POST reply channel=%s root=%s", channel_id, root_id or "—")
        payload: dict = {"channel_id": channel_id, "message": message}
        if root_id:
            payload["root_id"] = root_id
        async with self._session.post(f"{self.base_url}/posts", json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
