import aiohttp
import datetime
# bot file
from data.constants import PrivateData

class PublicAPI:
    CCU = "https://stats.docskigames.com/api/ccu-current"
    SERVERS = "https://regions.docskigames.com/getServers"
    FEATURED_VIDEO = "https://community.docskigames.com/api/feature-video"
    LEADERBOARD = "https://leaderboards.docskigames.com/api/getScore"

"""
For contributors interested in improving API support,
here is some useful documentation to understand asynchronous HTTP clients.
- https://apidog.com/blog/aiohttp-request/
- https://docs.aiohttp.org/en/stable/client_quickstart.html
"""
class VideoSystemAPI:
    @staticmethod
    async def send_video_to_endpoint(video_url: str) -> int | str:
        payload = {"video_url": video_url}
        headers = {
            "Authorization": f"Bearer {PrivateData.API_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(PrivateData.API_ENDPOINT_URL, json=payload, headers=headers) as resp:
                    return resp.status
        except Exception:
            return "unknown"

    @staticmethod
    async def get_website_featured_video() -> tuple[str | None, datetime.datetime | None]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PublicAPI.FEATURED_VIDEO) as resp:
                    data = await resp.json()
                    video_url = data.get("video_url", None)
                    updated_str = data.get("updatedAt", None)
                    updated_at_dt = datetime.datetime.fromisoformat(updated_str) if updated_str else None
                    return video_url, updated_at_dt
        except Exception:
            return None, None