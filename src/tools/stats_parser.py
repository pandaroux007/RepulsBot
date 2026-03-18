import json
import aiohttp
from datetime import datetime
import re
from io import BytesIO
from PIL import (
    Image,
    ImageDraw
)

# bot files
from data.constants import DefaultEmojis
from tools.utils import GamePlaylist
from tools.api_client import (
    PublicAPI,
    PlayFabAPI,
    PlayFabClient
)

# ---------------------------------- basic information function (game version, list of available regions)
async def fetch_game_version(playfab_connection: PlayFabClient) -> str | None:
    """
    returns the formatted game version: v + MajorGameVersion.MinorGameVersion.ClientVersion
    """
    data = await playfab_connection.call_client_api(PlayFabAPI.GET_GAME_VERSION, { "Keys": ["GameInfo"] })
    if not data:
        return None
    game_version = json.loads(data["data"]["Data"]["GameInfo"])["GameVersion"]
    return game_version

async def fetch_regions_list() -> list[str]:
    """
    returns a list of available region **names** (nothing else)
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(PublicAPI.REGIONS) as resp_servers:
            data: dict = await resp_servers.json()
            servers = data.get("regionList", [])

    regions: list[str] = [region["region"] for region in servers]
    return regions

# ---------------------------------- game ccu and server status
class GameServerRegion:
    def __init__(self, name: str, players: dict[GamePlaylist, int] | None = None):
        self.name: str = name
        self.players: dict[GamePlaylist, int] = players or {}
        self.status: str = "unknown"

    @property
    def total(self) -> int:
        return sum(self.players.values())

    def get(self, playlist: GamePlaylist) -> int:
        return self.players.get(playlist, 0)

async def fetch_server_stats() -> tuple[str | None, list[GameServerRegion], GameServerRegion] | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PublicAPI.CCU) as resp_ccu:
                ccu: dict = await resp_ccu.json()

        regions = await fetch_regions_list()
    except Exception:
        return None

    updated_at: str = ccu.get("timestamp", None)
    region_dict: dict = ccu.get("perRegion", {})
    global_dict: dict = ccu.get("global", {})

    global_players: dict[GamePlaylist, int] = {}
    for pl in GamePlaylist:
        global_players[pl] = global_dict.get(pl.code, 0)
    global_stats = GameServerRegion(name="GLOBAL", players=global_players)

    regions_ping: dict[str, str] = {
        name: PublicAPI.REGION_PING.format(region=name)
        for name in regions
    }

    region_stats: list[GameServerRegion] = []
    for region_name, region_data in region_dict.items():
        players: dict[GamePlaylist, int] = {}
        for pl in GamePlaylist:
            players[pl] = region_data.get(pl.code, 0)

        region = GameServerRegion(name=region_name, players=players)

        ping_url = regions_ping.get(region_name)
        if ping_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(ping_url, timeout=3) as resp_ping:
                        if resp_ping.status == 200:
                            data = await resp_ping.json(content_type=None)
                            if isinstance(data, dict) and data.get("status") == "ok":
                                region.status = DefaultEmojis.ONLINE
                            else:
                                region.status = "🟡 Down"
                        else:
                            region.status = f"{DefaultEmojis.OFFLINE} Unavailable"
            except Exception:
                region.status = f"{DefaultEmojis.ERROR} Error"

        region_stats.append(region)

    return updated_at, region_stats, global_stats

# ---------------------------------- retrieves information from ongoing games
class GameInProgress:
    def __init__(self, name: str, map: str, mode: str, players: int, max_players: int, port: int):
        self.name: str = name
        self.map: str = map
        self.mode: str = mode
        self.web_port: int = port
        self._players: int = players
        self._max_players: int = max_players
        
    @property
    def players(self) -> str:
        return f"{self._players}/{self._max_players}"
    
    @property
    def is_full(self) -> bool:
        return self._players == self._max_players
    
    @property
    def is_empty(self) -> bool:
        return self._players == 0

async def fetch_games_list(region: str) -> dict[GamePlaylist, list[GameInProgress]] | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PublicAPI.GET_GAME_LIST.format(region=region)) as resp:
                data: dict = await resp.json()
                game_list: dict = data.get("serverList", {})
    except Exception:
        return None

    result: dict[GamePlaylist, list[GameInProgress]] = {}
    for game in game_list:
        playlist = GamePlaylist.from_code(game["playlist"])
        result.setdefault(playlist, []).append(GameInProgress(
            name=game["gameId"],
            map=game["gameMap"],
            mode=game["gameMode"],
            players=game["playerCount"],
            max_players=game["maxPlayers"],
            port=int(game["webPort"])
        ))

    return result or None

# ---------------------------------- Player Analysis
PLAYER_XP_LEVELS = [ # AUTOGENERATED FROM XpManager – DO NOT HAND EDIT
    1000,   1757,   3982,   7601,   12544,  18738,  26111,  34591,  44107,  54587,
    65957,  78148,  91086,  104699, 118917, 133666, 148875, 164471, 180384, 196541,
    212870, 229299, 245756, 262170, 278467, 294578, 310428, 325947, 341063, 355703,
    369796, 383269, 396052, 408071, 419255, 429532, 438830, 447077, 454201, 460130,
    464793, 468214, 471127, 473721, 476027, 478072, 479886, 481497, 482935, 484228,
    485405, 486496, 487528, 488532, 489535, 490567, 491656, 492833, 494124, 495560,
    497170, 498981, 501024, 503327, 505918, 508828, 512084, 515716, 519752, 524222,
    529154, 534577, 540520, 547013, 554083, 561761, 570074, 579052, 588723, 599117,
    610262, 622188, 634923, 648496, 662936, 678272, 694533, 711747, 729944, 749153,
    769402, 790721, 813138, 836682, 861382, 887267, 914366, 942708, 972322, 1000000
]

WEAPON_PARSING_TABLE = {
    "crifle": "Combat Rifle",
    "arifle": "Assault Rifle",
    "brifle": "Burst Rifle",
    "pBlaster": "Plasma Blaster",
    "pRocket": "Pocket Rocket",
    "mechProj": "Mech",
    "dBarrel": "Double Barrel"
}

class PlayerProfile:
    def __init__(self, name: str, playfab_id: str):
        # Account information
        self.display_name: str = name
        self.username: str = None
        self.playfab_id: str = playfab_id
        self.created: datetime = None
        self.last_login: datetime = None
        self.repuls_account: bool = True
        self.is_admin: bool = False
        self.is_banned: bool = False
        self._clan: str = None
        # Avatar
        self.primary_color: str | None = None
        self.secondary_color: str | None = None
        self.color_theme: tuple[BytesIO, str] | None = None
        self._avatar_mods: list[str] = []
        # Player statistics
        self.level: int = 0
        self.xp: int = 0
        self.matches: int = 0
        self.wins: int = 0
        self.kills: int = 0
        self.deaths: int = 0
        self.flags: int = 0
        self.skulls: int = 0
        self.winstreak: int = 0
        self._best_weapons: dict[str, int] = {}
        # kills statistics
        self.vehicle_kills: int = 0
        self.headshot: int = 0
        self.double_kill: int = 0
        self.triple_kill: int = 0
        self.quad_kill: int = 0
        self.mega_kill: int = 0
        self.ultra_kill: int = 0
        self.monster_kill: int = 0
        self.killing_spree: int = 0
        self.dominating: int = 0
        self.unstoppable: int = 0
        self.godlike: int = 0
        self.assist: int = 0

    @property
    def name(self) -> str:
        return self.display_name if self.display_name.lower() != "none" else self.username if self.username else "*Unknown*"

    @property
    def kd_ratio(self) -> float:
        if not self.kills or not self.deaths:
            return 0.0
        return round(self.kills / max(1, self.deaths), 2)

    @property
    def win_ratio(self) -> str:
        return f"{self.wins / max(1, self.matches) * 100:.1f}%"
    
    @property
    def clan(self) -> str | None:
        if not self._clan:
            return None
        match = re.search(r"<color=#[0-9a-fA-F]{6}>\[\s*(.*?)\s*\]<\/color>", self._clan)
        return match.group(1) if match else None

    def xp_progress(self, width: int = 20) -> str:
        if self.level >= len(PLAYER_XP_LEVELS):
            return f"{self.xp} XP"

        xp_for_next_level = PLAYER_XP_LEVELS[self.level]
        progress_ratio = min(self.xp / xp_for_next_level, 1.0)
        filled_length = int(progress_ratio * width)
        bar = "█" * filled_length + "░" * (width - filled_length)

        return f"|{bar}| {self.xp:,}/{xp_for_next_level:,} XP"

    @property
    def best_weapons(self) -> str | None:
        weapons_text: list[str] = []
        for weapon, count in self._best_weapons.items():
            if len(weapon) == 3:
                weapon = weapon.upper()
            elif weapon in WEAPON_PARSING_TABLE:
                weapon = WEAPON_PARSING_TABLE.get(weapon)
            weapons_text.append(f"> **{weapon.replace('_', ' ').title()}**: {count:,}")
        return '\n'.join(weapons_text) if weapons_text else None
    
    @property
    def avatar_mods(self) -> str | None:
        mods_text: list[str] = []
        for mod in self._avatar_mods:
            mod = mod.strip()
            if not mod:
                continue
            if "none" not in mod or "unknown" not in mod:
                mods_text.append(f"> - **{mod.removeprefix("mod_").replace('_', ' ').title()}**") 
        return '\n'.join(mods_text) if mods_text else None

async def fetch_player(playfab_connection: PlayFabClient, name: str) -> PlayerProfile | None:
    # https://learn.microsoft.com/en-us/rest/api/playfab/client/account-management/get-account-info?view=playfab-rest
    profile = await playfab_connection.call_client_api(PlayFabAPI.SEARCH_PLAYER, {"TitleDisplayName": name})
    if not profile:
        profile = await playfab_connection.call_client_api(PlayFabAPI.SEARCH_PLAYER, {"Username": name})
        if not profile:
            return None
    target_player_id: str = profile["data"]["AccountInfo"]["PlayFabId"]

    player_data = await playfab_connection.call_client_api(PlayFabAPI.GET_PLAYER_DATA, {
        "FunctionName": "getRemoteUserProfile",
        "FunctionParameter": {
            "remoteId": target_player_id
        }
    })

    result = player_data["data"]["FunctionResult"]
    logs = player_data["data"]["Logs"]

    profile = PlayerProfile(name=str(result["DisplayName"]), playfab_id=target_player_id)

    if logs:
        try:
            log_data = dict(json.loads(logs[0]["Message"]))
            info_payload = dict(log_data["InfoResultPayload"]["AccountInfo"])

            profile.username = info_payload.get("Username")
            profile.repuls_account = not bool(info_payload.get("GoogleInfo"))
            profile.created = datetime.fromisoformat(info_payload["Created"])
            profile.last_login = datetime.fromisoformat(info_payload["TitleInfo"]["LastLogin"])
            profile.is_banned = bool(info_payload["TitleInfo"]["isBanned"])
        except Exception:
            pass

    try:
        properties = dict(json.loads(result["UserReadOnlyData"]["Properties"]["Value"]))

        profile.level = properties.get("Level", 0)
        profile.xp = properties.get("Experience", 0)
        profile.is_admin = bool(properties.get("isAdmin", False))
        profile._clan = properties.get("verificationProperties", None)

        achievements = {item["Id"]: item["count"] for item in properties.get("achievementProgressions", [])}
        profile.kills = achievements.get("kills", 0)
        profile.deaths = achievements.get("deaths", 0)
        profile.matches = achievements.get("games", 0)
        profile.wins = achievements.get("wins", 0)
        profile.flags  = achievements.get("flags", 0)
        profile.skulls = achievements.get("skulls", 0)
        profile.winstreak = achievements.get("winstreak", 0)
        profile.vehicle_kills = achievements.get("vehKills", 0)
        profile.headshot = achievements.get("headshot", 0)
        profile.double_kill = achievements.get("kchain_x2", 0)
        profile.triple_kill = achievements.get("kchain_x3", 0)
        profile.quad_kill = achievements.get("kchain_x4", 0)
        profile.mega_kill = achievements.get("kchain_x5", 0)
        profile.ultra_kill = achievements.get("kchain_x6", 0)
        profile.monster_kill = achievements.get("kchain_x7", 0)
        profile.killing_spree = achievements.get("killStreak_x4", 0)
        profile.dominating = achievements.get("killStreak_x6", 0)
        profile.unstoppable = achievements.get("killStreak_x8", 0)
        profile.godlike = achievements.get("killStreak_x10", 0)
        profile.assist = achievements.get("assist", 0)

        kill_stats = {str(stat["Id"]).lower(): stat["count"] for stat in properties.get("killStats", [])}
        profile._best_weapons = dict(sorted(kill_stats.items(), key=lambda item: item[1], reverse=True)[:5])

        avatar = dict(json.loads(result["UserData"]["Loadout"]["Value"]))
        profile._avatar_mods = [str(mod) for mod in avatar.get("avatarMods", [])]
        if avatar.get("color_pri", None):
            profile.primary_color = f"#{avatar["color_pri"]}"
        if avatar.get("color_sec", None):
            profile.secondary_color = f"#{avatar["color_sec"]}"

        if profile.primary_color and profile.secondary_color:
            buffer = BytesIO()
            image = Image.new("RGB", (60, 60), color=profile.secondary_color)
            draw = ImageDraw.Draw(image)
            draw.polygon(((0, 0), (0, 60), (60, 0)), fill=profile.primary_color)
            image.save(buffer, format='PNG')
            buffer.seek(0)
            profile.color_theme = (buffer, f"{profile.primary_color}|{profile.secondary_color}.png")
    except Exception:
        pass

    return profile