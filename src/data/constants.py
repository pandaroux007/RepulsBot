# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
from pathlib import Path
import os
import discord

CMD_PREFIX = '!'
# https://discordpy.readthedocs.io/en/latest/api.html?highlight=permissions#discord.Permissions
ADMIN_CMD = discord.Permissions(administrator=True)

DB_PATH = Path(__file__).parent.parent / "data" / "storage.db"

# ------------------------------------- env file's data
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(_ENV_FILE)

class PrivateData:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
    API_TOKEN = os.getenv("API_TOKEN")
    # 3 API keys for fallback
    YOUTUBE_KEYS = [
        os.getenv("YOUTUBE_KEY1"),
        os.getenv("YOUTUBE_KEY2"),
        os.getenv("YOUTUBE_KEY3")
    ]

_MODE = os.getenv("ENV", "prod")
_MODE_DEV = "dev"

# https://support.discord.com/hc/en-us/community/posts/4407711130775-Mention-format-for-slash-commands
# ----------------------------------------- IDs ----------------------------------------
#           DEV bot and server IDs           |           OFFICIAL bot and server IDs   |
# --------------------------------------------------------------------------------------
class ServerChannelID:
    BOTLOG = 1399029942221799475             if _MODE == _MODE_DEV else 1399017426880041141
    MODLOG = 1403797711764852756             if _MODE == _MODE_DEV else 1044053262975893514
    RULES = 1389989335318794420              if _MODE == _MODE_DEV else 758364818348048444
    WELCOME = 1446881118061072467            if _MODE == _MODE_DEV else 665786571424923648
    FEATURED_VIDEO = 1427982134857043990     if _MODE == _MODE_DEV else 1458152386404159599
    SHARED_VIDEO = 1370706473155563581       if _MODE == _MODE_DEV else 800108276004028446
    TICKETS_CATEGORY = 1390286889830842470   if _MODE == _MODE_DEV else 1398622102713667605

class ServerRoleID: # "<@&role_id>"
    YOUTUBER = 1381223948854759494           if _MODE == _MODE_DEV else 781295509331116054
    STREAMER = 1381223990349004850           if _MODE == _MODE_DEV else 781295771894153266
    ADMIN = 1376617317382754456              if _MODE == _MODE_DEV else 800091356974022677
    TRUSTED = 1381224331685920930            if _MODE == _MODE_DEV else 910540568164188252
    DEVELOPER = 1381224153478336553          if _MODE == _MODE_DEV else 682090620726411304
    ASTRONAUT = 1388550692213362879          if _MODE == _MODE_DEV else 1317870046726324284
    SWATTEAM = 1388550925353877685           if _MODE == _MODE_DEV else 862318347542724679
    CONTRIBUTOR = 1388551885476204655        if _MODE == _MODE_DEV else 850775875821109298
    ESPORTS_ORGANIZER = 1388880454479904808  if _MODE == _MODE_DEV else 1371212276421496925
    CLAN_LEADER = 1394988076551635014        if _MODE == _MODE_DEV else 850917985429880863
    MUTED = 1420425892429168821              if _MODE == _MODE_DEV else 805854637126713394
    TICKET_HELPER = 1420425652221251585      if _MODE == _MODE_DEV else 1399022819861336194

# these IDs do not change
class RepulsTeamMemberID: # "<@member_id>"
    BOT_DEVELOPER = 1329483867937050652 # pandaroux007
    MAIN_DEVELOPER = 213028561584521216 # docski

class AuthorizedServersID:
    MAIN_SERVER = 603655329120518223
    TEST_SERVER = 1370706439491817563

AUTHORISED_SERVERS = {
    AuthorizedServersID.MAIN_SERVER,
    AuthorizedServersID.TEST_SERVER
}

# class grouping the different IDs
class IDs:
    serverChannel = ServerChannelID
    serverRoles = ServerRoleID
    repulsTeam = RepulsTeamMemberID

# ------------------------------------- texts and links
"""
CONTRIBUTORS: To avoid display issues, use this variable (added after the emoji's unicode value, for example
via f-string) to ensure the emoji is displayed as an image if it defaults to text in Discord. Note that conditional
tests used to compare emojis are sensitive to this addition.
"""
# https://stackoverflow.com/questions/38100329/what-does-u-ufe0f-in-an-emoji-mean-is-it-the-same-if-i-delete-it
VARIATION_SELECTOR_IMG = '\uFE0F' # '\uFE0E' for text

class DefaultEmojis:
    CHECK = '\u2705' # :white_check_mark:
    WARN = f'\u26A0{VARIATION_SELECTOR_IMG}' # :warning:
    ERROR = '\u274C' # :x:
    CROSS = ERROR
    INFO = f'\u2139{VARIATION_SELECTOR_IMG}' # :information_source:
    NO_ENTRY = '\u26D4' # :no_entry:
    UP_ARROW = '\u2B06' # :up_arrow:
    OFFLINE = '\U0001F534' # :red_circle:
    ONLINE = '\U0001F7E2' # :green_circle:

class BotInfo:
    VERSION = "1.5.3"
    GITHUB = "https://github.com/pandaroux007/RepulsBot"
    REPORT = f"{GITHUB}/issues"

class GameUrl:
    GAME = "https://repuls.io"
    BETA = f"{GAME}/beta"
    HOME = f"{GAME}/home"
    LEADERBOARD = f"{GAME}/leaderboard"
    UPDATES = f"{GAME}/updates"
    TERMS = f"{GAME}/terms"
    ESPORTS = f"{GAME}/esports"
    ESPORTS_ROADMAP_URL = f"{GAME}/esports/REPULS_eSPORTS_ROADMAP.png"

class Links:
    # PRIVACY = "https://docskigames.com/privacy/"
    # MAIN_SERVER = "https://discord.com/invite/2YKgx2HSfR"
    RWNC_SERVER = "https://discord.com/invite/YzfQndsdn3"
    WIKI = "https://repulsio.fandom.com/wiki/Repuls.io_Wiki"
    CLEAR_DATA_TUTORIAL = "https://github.com/pandaroux007/RepulsBot/wiki/Troubleshoot-game-loading-issues"
    EXPLANATION_VIDEO_SYSTEM = "https://github.com/pandaroux007/RepulsBot/wiki/How-video-voting-works"

ASK_HELP = "\n**Ask an administrator for help!**"
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"