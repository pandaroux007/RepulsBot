# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
import os
import sys

CMD_PREFIX = '!'

_current_dir = os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0])))
load_dotenv(os.path.join(_current_dir, ".env"))

ENV = os.getenv("ENV", "prod")

class PrivateData:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
    API_TOKEN = os.getenv("API_TOKEN")

# ------------------------------------- IDs -------------------------------------
#         official bot and server IDs       |          dev bot and server IDs   |
# -------------------------------------------------------------------------------
class ServerChannelID:
    RULES = 1389989335318794420              if ENV == "dev" else 758364818348048444
    STATUS = 1370716216863227924             if ENV == "dev" else 849711794032214087
    VIDEO = 1370706473155563581              if ENV == "dev" else 800108276004028446

class ServerRoleID: # "<@&role_id>"
    YOUTUBER = 1381223948854759494           if ENV == "dev" else 781295509331116054
    STREAMER = 1381223990349004850           if ENV == "dev" else 781295771894153266
    ADMIN = 1376617317382754456              if ENV == "dev" else 800091356974022677
    TRUSTED = 1381224331685920930            if ENV == "dev" else 910540568164188252
    DEVELOPER = 1381224153478336553          if ENV == "dev" else 682090620726411304
    CONDUCTOR = 1388550692213362879          if ENV == "dev" else 1317870046726324284
    SWATTEAM = 1388550925353877685           if ENV == "dev" else 862318347542724679
    CONTRIBUTOR = 1388551885476204655        if ENV == "dev" else 850775875821109298
    ESPORTS_ORGANIZER = 1388880454479904808  if ENV == "dev" else 1371212276421496925

class CustomEmojiID: # "<:emiji_name:emoji_id>"
    CONNECTE = 1392147094281916436           if ENV == "dev" else 1376214233041080410
    DECONNECTE = 1392147110979305665         if ENV == "dev" else 1376214242424000583

# these IDs do not change
class RepulsTeamMemberID: # "<@member_id>"
    GRAPHIC_DESIGNER = 896507294983020574 # caracal
    MAIN_DEVELOPER = 213028561584521216 # docski

# class grouping the different IDs
class IDs:
    serverChannel = ServerChannelID
    serverRoles = ServerRoleID
    customEmojis = CustomEmojiID
    repulsTeam = RepulsTeamMemberID

# ------------------------------------- texts and links
class DefaultEmojis:
    CHECK = "✅" # :white_check_mark:
    WARN = "⚠️" # :warning:

class BotInfo():
    NAME = "RepulsBot"
    VERSION = "1.0.1"
    GITHUB = "https://github.com/pandaroux007/RepulsBot"
    DESCRIPTION = """
    Hey there! :waving_hand:
    It's me, {name}, the official Discord bot for [this server]({server})! If you need help, type "!help" or help command to see what I can do!\n
    If you don't feel like chatting with our amazing community, you can always play a game of [repuls.io]({game}) :wink:
    """

class Links:
    REPULS_WIKI = "https://repulsio.fandom.com/wiki/Repuls.io_Wiki"
    GAME_PRIVACY = "https://docskigames.com/privacy/"
    REPULS_GAME = "https://repuls.io/"
    DISCORD_INVITE = "https://discord.com/invite/2YKgx2HSfR"
    CLEAR_DATA_TUTORIAL = "https://its.uiowa.edu/services/how-clear-cache-and-cookies-your-web-browser"

ASK_HELP = "\n**Ask an administrator for help!**"
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"
REPULS_DESCRIPTION = f"""
[Repuls.io]({Links.REPULS_GAME}) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!\n
Tired of the same run, aim, shoot gameplay that every shooter does??! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech!! THATS the repuls experience son!
"""
REPULS_WIKI_DESCRIPTION = """
Do you love repuls.io but don't know how the game works, what maps, weapons, top players, game modes, etc. are?\n
Then you'll find everything you need on the official Wiki!
"""