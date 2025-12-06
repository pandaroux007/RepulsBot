# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
import os
import sys

CMD_PREFIX = '!'

_current_dir = os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0])))
load_dotenv(os.path.join(_current_dir, ".env"))

ENV = os.getenv("ENV", "prod")
ENV_DEV_MODE = "dev"

class PrivateData:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
    API_TOKEN = os.getenv("API_TOKEN")

# https://support.discord.com/hc/en-us/community/posts/4407711130775-Mention-format-for-slash-commands
# ----------------------------------------- IDs ----------------------------------------
#           DEV bot and server IDs           |           OFFICIAL bot and server IDs   |
# --------------------------------------------------------------------------------------
class ServerChannelID:
    BOTLOG = 1399029942221799475             if ENV == ENV_DEV_MODE else 1399017426880041141
    MODLOG = 1403797711764852756             if ENV == ENV_DEV_MODE else 1044053262975893514
    RULES = 1389989335318794420              if ENV == ENV_DEV_MODE else 758364818348048444
    WELCOME = 1446881118061072467            if ENV == ENV_DEV_MODE else 665786571424923648
    FEATURED_VIDEO = 1427982134857043990     if ENV == ENV_DEV_MODE else ...
    SHARED_VIDEO = 1370706473155563581       if ENV == ENV_DEV_MODE else 800108276004028446
    TICKETS_CATEGORY = 1390286889830842470   if ENV == ENV_DEV_MODE else 1398622102713667605

class ServerRoleID: # "<@&role_id>"
    YOUTUBER = 1381223948854759494           if ENV == ENV_DEV_MODE else 781295509331116054
    STREAMER = 1381223990349004850           if ENV == ENV_DEV_MODE else 781295771894153266
    ADMIN = 1376617317382754456              if ENV == ENV_DEV_MODE else 800091356974022677
    TRUSTED = 1381224331685920930            if ENV == ENV_DEV_MODE else 910540568164188252
    DEVELOPER = 1381224153478336553          if ENV == ENV_DEV_MODE else 682090620726411304
    CONDUCTOR = 1388550692213362879          if ENV == ENV_DEV_MODE else 1317870046726324284
    SWATTEAM = 1388550925353877685           if ENV == ENV_DEV_MODE else 862318347542724679
    CONTRIBUTOR = 1388551885476204655        if ENV == ENV_DEV_MODE else 850775875821109298
    ESPORTS_ORGANIZER = 1388880454479904808  if ENV == ENV_DEV_MODE else 1371212276421496925
    CLAN_LEADER = 1394988076551635014        if ENV == ENV_DEV_MODE else 850917985429880863
    MUTED = 1420425892429168821              if ENV == ENV_DEV_MODE else 805854637126713394
    TICKET_HELPER = 1420425652221251585      if ENV == ENV_DEV_MODE else 1399022819861336194

AUTHORISED_ROLES = {
    ServerRoleID.ADMIN,
    ServerRoleID.DEVELOPER
}

# these IDs do not change
class RepulsTeamMemberID: # "<@member_id>"
    # GRAPHIC_DESIGNER = 896507294983020574 # caracal
    MAIN_DEVELOPER = 213028561584521216 # docski
    BOT_DEVELOPER = 1329483867937050652 # pandaroux007

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
    NO_ENTRY = '\u26D4' # :no_entry:
    UP_ARROW = '\u2B06' # :up_arrow:
    OFFLINE = '\U0001F534' # :red_circle:
    ONLINE = '\U0001F7E2' # :green_circle:

class BotInfo:
    VERSION = "1.5.0-beta"
    GITHUB = "https://github.com/pandaroux007/RepulsBot"
    DESCRIPTION = """
    Hey there! :waving_hand:
    It's me, {name}, the official Discord bot for [this server]({server})! If you need anything, use my help command to see what I can do!
    If you don't feel like chatting with our amazing community, you can always play a game of [repuls.io]({game}) :wink:
    """

class Links:
    WIKI = "https://repulsio.fandom.com/wiki/Repuls.io_Wiki"
    PRIVACY = "https://docskigames.com/privacy/"
    GAME = "https://repuls.io/"
    MAIN_SERVER = "https://discord.com/invite/2YKgx2HSfR"
    RWNC_SERVER = "https://discord.com/invite/YzfQndsdn3"
    CLEAR_DATA_TUTORIAL = "https://github.com/pandaroux007/RepulsBot/wiki/Troubleshoot-game-loading-issues"

ASK_HELP = "\n**Ask an administrator for help!**"
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"