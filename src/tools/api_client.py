from discord.ext import commands
import aiohttp
import datetime
import json
# bot files
from data.constants import (
    PrivateData,
    DefaultEmojis
)

from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class PublicAPI:
    CCU = "https://stats.docskigames.com/api/ccu-current"
    SERVERS = "https://regions.docskigames.com/getServers"
    FEATURED_VIDEO = "https://community.docskigames.com/api/feature-video"
    LEADERBOARD = "https://leaderboards.docskigames.com/api/getScore"

# ---------------------------------- video system
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
            "Authorization": f"Bearer {PrivateData.VIDEO_ENDPOINT_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(PrivateData.VIDEO_ENDPOINT_URL, json=payload, headers=headers) as resp:
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

# ---------------------------------- playfab connexion
class PlayFabAPI:
    TITLE_ID = "df3ef"
    BASE_URL = f"https://{TITLE_ID}.playfabapi.com/Client"
    LOGIN = f"{BASE_URL}/LoginWithPlayFab"
    GET_GAME_VERSION = f"{BASE_URL}/GetTitleData"
    SEARCH_PLAYER = f"{BASE_URL}/GetAccountInfo"
    GET_PLAYER_DATA = f"{BASE_URL}/ExecuteCloudScript"

class PlayFab():
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._playfab_id: str | None = None
        self._session_token: str | None = None
        self._token_expiration: datetime.datetime | None = None

    async def _handle_api_error(self, error: dict, api: str) -> None:
        await log(
            bot=self._bot, type=BOTLOG, color=LogColor.RED,
            title=f"{DefaultEmojis.ERROR} An error occurred while attempting to connect to PlayFab.",
            msg=(
                f"Attempting to connect to: `...{api[-25:]}`\n"
                f"Code: {error["code"]} ({error["status"]}) | Error `{error["error"]}` ({error["errorCode"]})\n"
                f"**Error message**:\n```\n{error["errorMessage"]}\n```"
            )
        )

    def _is_token_valid(self) -> bool:
        if not self._session_token or not self._token_expiration:
            return False
        return datetime.datetime.now(datetime.timezone.utc) <= self._token_expiration

    async def _login(self) -> bool:
        # https://learn.microsoft.com/en-us/rest/api/playfab/client/authentication/login-with-playfab?view=playfab-rest
        payload = {
            "Password": PrivateData.PLAYFAB_PASSWORD,
            "TitleId": PlayFabAPI.TITLE_ID,
            "Username": PrivateData.PLAYFAB_USERNAME
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(PlayFabAPI.LOGIN, json=payload, timeout=5) as resp:
                    data = await resp.json()
                    if data["code"] != 200:
                        await self._handle_api_error(data, PlayFabAPI.LOGIN)
                        return False
                    self._playfab_id = data["data"]["PlayFabId"]
                    self._session_token = data["data"]["SessionTicket"]
                    self._token_expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=40) # 45mn with a margin of 5mn
                    await log(
                        bot=self._bot, type=BOTLOG, color=LogColor.GREEN,
                        title="🌐 PlayFab login successful",
                        msg="The bot successfully logged into the PlayFab service"
                    )
                    return True
        except Exception:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Connection to PlayFab failed",
                msg="An error occurred while attempting to connect to PlayFab. The service may be unavailable?"
            )
            return False

    # ---------------------------------- public methods
    async def call_client_api(self, url: str, body: dict) -> dict | None:
        if not self._is_token_valid():
            if not await self._login():
                return None

        headers = {
            "X-Authorization": self._session_token,
            "Content-Type": "application/json",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, headers=headers) as resp:
                    data = await resp.json()
                    if data["code"] != 200:
                        await self._handle_api_error(data, url)
                        return None
                    return data
        except Exception:
            return None

# ---------------------------------- stats
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

class InfoSystemAPI():
    @staticmethod
    async def fetch_servers() -> tuple[str | None, list[GameServerRegion], GameServerRegion]:
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
    
    @staticmethod
    async def fetch_game_version(playfab_connection: PlayFab) -> str | None:
        data = await playfab_connection.call_client_api(PlayFabAPI.GET_GAME_VERSION, { "Keys": ["GameInfo"] })
        if not data:
            return None
        title_data = data["data"]["Data"]
        game_version = json.loads(title_data["GameInfo"])["GameVersion"]
        return game_version