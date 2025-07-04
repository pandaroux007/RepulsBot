# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
import os
import sys

CMD_PREFIX = '!'

_current_dir = os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0])))
load_dotenv(os.path.join(_current_dir, ".env"))

class PrivateData:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
    API_TOKEN = os.getenv("API_TOKEN")

# https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
# ------------------------------------- cogs
class CogsNames:
    EVENT = "event_cog"
    VOTE = "vote_cog"
    SERVER = "server_cog"
    ABOUT = "about_cog"
    TICKETS = "tickets_cog"

COGS_LIST = [
    CogsNames.EVENT,
    CogsNames.SERVER,
    CogsNames.ABOUT,
    CogsNames.VOTE,
    CogsNames.TICKETS
]

# ------------------------------------- IDs
class ServerChannelIDs:
    RULES = 1389989335318794420  # 758364818348048444
    STATUS = 1370716216863227924 # 849711794032214087 (info channel)
    VIDEO = 1370706473155563581  # 800108276004028446

class ServerRoleIDs: # "<@&role_id>"
    YOUTUBER = 1381223948854759494          # 781295509331116054
    STREAMER = 1381223990349004850          # 781295771894153266
    ADMIN = 1376617317382754456             # 800091356974022677
    TRUSTED = 1381224331685920930           # 910540568164188252
    DEVELOPER = 1381224153478336553         # 682090620726411304
    CONDUCTOR = 1388550692213362879         # 1317870046726324284
    SWATTEAM = 1388550925353877685          # 862318347542724679
    CONTRIBUTOR = 1388551885476204655       # 850775875821109298
    ESPORTS_ORGANIZER = 1388880454479904808 # 1371212276421496925

class CustomEmojisIDs: # "<:emiji_name:emoji_id>"
    CONNECTE = 1376214233041080410
    DECONNECTE = 1376214242424000583
    LOADER = 1376135761757470791
    RC = 1376135351353086002
    RANK = 1376135312669151232
    ESPORTS = 1376135172034007102
    RWNC = 1376135129960939575
    REPULS = 1376134874595065906

class RepulsTeamMembersIDs: # "<@member_id>"
    GRAPHIC_DESIGNER = 896507294983020574 # caracal
    MAIN_DEVELOPER = 213028561584521216 # docski

class IDs:
    serverChannel = ServerChannelIDs
    serverRoles = ServerRoleIDs
    customEmojis = CustomEmojisIDs
    repulsTeam = RepulsTeamMembersIDs

# ------------------------------------- texts and links
class DefaultEmojis:
    CHECK = "✅" # :white_check_mark:
    WARN = "⚠️" # :warning:

class BotInfo():
    NAME = "RepulsBot"
    VERSION = "0.1.9"
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
FEATURED_VIDEO_MSG = """
*(And you, do you want your video to appear on the game's main page? Then hurry up and post the link here,
and cross your fingers that the community votes for your message with the reaction {reaction} just below!*
***I come and check the best video every {time} hours, you have every chance!***)
"""
REPULS_WIKI_DESCRIPTION = """
Do you love repuls.io but don't know how the game works, what maps, weapons, top players, game modes, etc. are?\n
Then you'll find everything you need on the official Wiki!
"""
OPEN_TICKET_MSG = """
Need help? Simply click on the type of ticket you want to open **in the selector below**, fill up the information needed and **send** (send your images and video after creating the ticket).\n
It will create a private channel between you and **the moderation team**. This way, you can make a report, request a role, or anything else.
**Only create a ticket if absolutely necessary. Check if the answer to your question is not in the two server FAQs! To report a game bug, you can use the channel https://discord.com/channels/603655329120518223/1076163933213311067 !**
"""