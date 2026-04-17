"""
For contributors interested in improving API support,
here is some useful documentation to understand asynchronous HTTP clients.
- https://apidog.com/blog/aiohttp-request/
- https://docs.aiohttp.org/en/stable/client_quickstart.html
"""

from discord.ext import commands
import aiohttp
import datetime
# bot files
from data.constants import (
    PrivateData,
    DefaultEmojis,
    GameUrl
)

from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class PublicAPI:
    CCU = "https://stats.docskigames.com/api/ccu-current"
    FEATURED_VIDEO = "https://community.docskigames.com/api/feature-video"
    # LEADERBOARD = "https://leaderboards.docskigames.com/api/getScore"
    BUILD = f"{GameUrl.GAME}/StreamingAssets/aa/settings.json"
    BETA_BUILD = f"{GameUrl.GAME}/beta/StreamingAssets/aa/settings.json"
    # GAME_CHAT = "wss://chat.docskigames.com/socket"
    REGIONS = "https://regions.docskigames.com/getServers"
    REGION_PING = "https://rep.{region}.docskigames.com/ping"
    GET_GAME_LIST = "https://rep.{region}.docskigames.com/serverList"

class PlayFabAPI:
    TITLE_ID = "df3ef"
    BASE_URL = f"https://{TITLE_ID}.playfabapi.com/Client"
    LOGIN = f"{BASE_URL}/LoginWithPlayFab"

    GET_GAME_VERSION = f"{BASE_URL}/GetTitleData"
    SEARCH_PLAYER = f"{BASE_URL}/GetAccountInfo"
    GET_PLAYER_DATA = f"{BASE_URL}/ExecuteCloudScript"
    # GET_CATALOG = f"{BASE_URL}/GetCatalogItems"

# ---------------------------------- video system
class VideoSystemClient:
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
class PlayFabClient():
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._playfab_id: str | None = None
        self._session_token: str | None = None
        self._token_expiration: datetime.datetime | None = None

    async def _handle_api_error(self, error: dict, api: str) -> None:
        if error["errorCode"] != 1001: # AccountNotFound
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} An error occurred while attempting to connect to PlayFab.",
                msg=(
                    f"Attempting to connect to: `...{api[-25:]}`\n"
                    f"Code: {error.get("code")} ({error.get("status")}) | Error `{error.get("error")}` ({error.get("errorCode")})\n"
                    f"**Error message**:\n```\n{error.get("errorMessage")}\n```\n"
                    f"**Details**:\n```\n{error.get("errorDetails")}\n```"
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
    async def call_client_api(self, url: str, body: dict = {}) -> dict | None:
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
        
    async def get_token(self) -> str | None:
        if not self._is_token_valid():
            if not await self._login():
                return None
        return self._session_token