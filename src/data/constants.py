# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
from pathlib import Path
import os
import discord

CMD_PREFIX = '!'
# https://discordpy.readthedocs.io/en/latest/api.html?highlight=permissions#discord.Permissions
ADMIN_CMD = discord.Permissions(administrator=True)

DISCORD_MSG_ID_REGEX = r"(\d{17,20})$"

DB_PATH = Path(__file__).parent.parent / "data" / "storage.db"

# ------------------------------------- env file's data
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(_ENV_FILE)

class PrivateData:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    VIDEO_ENDPOINT_URL = os.getenv("VIDEO_ENDPOINT_URL")
    VIDEO_ENDPOINT_TOKEN = os.getenv("VIDEO_ENDPOINT_TOKEN")
    PLAYFAB_USERNAME = os.getenv("PLAYFAB_USERNAME")
    PLAYFAB_PASSWORD = os.getenv("PLAYFAB_PASSWORD")
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
    VERIFICATION = 1489269017477779608       if _MODE == _MODE_DEV else 1483400111462551593
    ANNOUNCEMENTS = 1437510214126403584      if _MODE == _MODE_DEV else 733177088961544202
    SHARED_VIDEO = 1370706473155563581       if _MODE == _MODE_DEV else 800108276004028446
    FEATURED_VIDEO = 1427982134857043990     if _MODE == _MODE_DEV else 1458152386404159599
    TICKETS_CATEGORY = 1390286889830842470   if _MODE == _MODE_DEV else 1398622102713667605

class ServerRoleID: # "<@&role_id>"
    YOUTUBER = 1381223948854759494           if _MODE == _MODE_DEV else 781295509331116054
    STREAMER = 1381223990349004850           if _MODE == _MODE_DEV else 781295771894153266
    ADMIN = 1376617317382754456              if _MODE == _MODE_DEV else 800091356974022677
    HELPER = 1461389067043209439             if _MODE == _MODE_DEV else 1438579395492184206
    TRUSTED = 1381224331685920930            if _MODE == _MODE_DEV else 910540568164188252
    DEVELOPER = 1381224153478336553          if _MODE == _MODE_DEV else 682090620726411304
    ASTRONAUT = 1388550692213362879          if _MODE == _MODE_DEV else 1317870046726324284
    SWATTEAM = 1388550925353877685           if _MODE == _MODE_DEV else 862318347542724679
    CONTRIBUTOR = 1388551885476204655        if _MODE == _MODE_DEV else 850775875821109298
    ESPORTS_ORGANIZER = 1388880454479904808  if _MODE == _MODE_DEV else 1371212276421496925
    CLAN_LEADER = 1394988076551635014        if _MODE == _MODE_DEV else 850917985429880863
    MUTED = 1420425892429168821              if _MODE == _MODE_DEV else 805854637126713394
    TICKET_RESPONDER = 1420425652221251585   if _MODE == _MODE_DEV else 1399022819861336194

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

AUTHORIZED_ROLES = {
    ServerRoleID.ADMIN,
    ServerRoleID.DEVELOPER
}

# class grouping the different IDs
class IDs:
    serverChannel = ServerChannelID
    serverRoles = ServerRoleID
    repulsTeam = RepulsTeamMemberID

class DefaultAntiraidSettings:
    # NOTE: 1 trigger = one activation of the anti-spam system
    ANTIRAID_STATE = 1 # (0/1 = SQL boolean) antiraid enabled by default

    USER_MAX_TRIGGERS_BEFORE_MOD = 3 # maximum number of triggers before auto-moderator action
    USER_MSG_SPAM_THRESHOLD = 4 # maximum number of messages allowed within the given time
    USER_MSG_SPAM_INTERVAL_S = 2 # minimum interval in which this quantity of message is allowed

    USER_CHANNEL_SPAM_THRESHOLD = 3 # number of messages from a user across multiple channels on which to perform sampling
    USER_CHANNEL_SPAM_INTERVAL_S = USER_CHANNEL_SPAM_THRESHOLD * 4 # 3s (margin of 1s) for 1 message per channel on average * number of messages

    CHANNEL_MAX_TRIGGERS_BEFORE_LOCK = 5
    CHANNEL_LOCK_DURATION_MN = 30
    CHANNEL_SPAM_INTERVAL_S = 5
    CHANNEL_SPAM_THRESHOLD = 12

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
    CROSS = '\u274C' # :x:
    WARN = f'\u26A0{VARIATION_SELECTOR_IMG}' # :warning:
    ERROR = CROSS
    CRITICAL = '\U0001F6A8' # :police_car_light:
    INFO = f'\u2139{VARIATION_SELECTOR_IMG}' # :information_source:
    MODERATION = '\U0001f6e1' # :shield:
    NO_ENTRY = '\u26D4' # :no_entry:
    UP_ARROW = '\u2B06' # :up_arrow:
    OFFLINE = '\U0001F534' # :red_circle:
    ONLINE = '\U0001F7E2' # :green_circle:

class BotInfo:
    VERSION = "1.7.2"
    GITHUB = "https://github.com/pandaroux007/RepulsBot"
    REPORT = f"{GITHUB}/issues"

class GameUrl:
    GAME = "https://repuls.io"
    BETA = f"{GAME}/beta"
    HOME = f"{GAME}/home"
    LEADERBOARD = f"{GAME}/leaderboard"
    UPDATES = f"{GAME}/updates"
    TERMS = f"{GAME}/terms" # and https://docskigames.com/privacy/
    ESPORTS_ROADMAP = f"{GAME}/esports"
    ESPORTS_ROADMAP_IMG = f"{ESPORTS_ROADMAP}/REPULS_eSPORTS_ROADMAP.png"
    ICON = f"{GAME}/img/repuls_logo_icon.png"
    # ------------------------------------- external
    RWNC_SERVER = "https://discord.com/invite/YzfQndsdn3"
    WIKI = "https://officialrepuls.fandom.com"
    # WIKIS_LIST = [
    #     {"name": "Official Wiki", "url": WIKI},
    #     {"name": "Official Historical Wiki", "url": "https://repulsio.fandom.com"},
    #     {"name": "Unofficial Player Wiki", "url": "https://repulsplayer.fandom.com"},
    #     {"name": "Unofficial Wiki", "url": "https://repuls.fandom.com"}
    # ]

ASK_HELP = "\n**Ask an administrator for help!**"
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"