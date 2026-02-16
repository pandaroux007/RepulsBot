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

# ---------------------------------- ccu
class GameServerRegion:
    def __init__(self, name: str, wf: int, hc: int, cs: int, cm: int):
        self.name: str = name
        self.warfare: int = wf
        self.hardcore: int = hc
        self.casual: int = cs
        self.customs: int = cm
        self.status: str = "unknown"

    @property
    def total(self) -> int:
        return self.warfare + self.hardcore + self.casual + self.customs

async def fetch_stats() -> tuple[str | None, list[GameServerRegion], GameServerRegion]:
    async with aiohttp.ClientSession() as session:
        async with session.get(PublicAPI.CCU) as resp_ccu:
            ccu: dict = await resp_ccu.json()

        async with session.get(PublicAPI.SERVERS) as resp_servers:
            servers_payload: dict = await resp_servers.json()

    updated_at: str = ccu.get("timestamp", None)
    region_dict: dict = ccu.get("perRegion", {})
    global_dict: dict = ccu.get("global", {})

    global_stats = GameServerRegion(
        name="GLOBAL",
        wf=global_dict.get("wf", 0),
        hc=global_dict.get("hc", 0),
        cs=global_dict.get("cs", 0),
        cm=global_dict.get("cm", 0)
    )

    regions_ping: dict[str, str] = {
        entry["region"]: entry["pingAddress"]
        for entry in servers_payload.get("regionList", [])
    }

    region_stats: list[GameServerRegion] = []
    for region_name, region_data in region_dict.items():
        region = GameServerRegion(
            name=region_name,
            wf=region_data.get("wf", 0),
            hc=region_data.get("hc", 0),
            cs=region_data.get("cs", 0),
            cm=region_data.get("cm", 0)
        )

        ping_url = regions_ping.get(region_name)
        if ping_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(ping_url, timeout=3) as resp_ping:
                        if resp_ping.status == 200:
                            data = await resp_ping.json(content_type=None)
                            if isinstance(data, dict) and data.get("status") == "ok":
                                region.status = "ok"
                            else:
                                region.status = "down"
                        else:
                            region.status = "unavailable"
            except Exception:
                region.status = "error"
        
        region_stats.append(region)

    return updated_at, region_stats, global_stats