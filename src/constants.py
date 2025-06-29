# https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
from dotenv import load_dotenv
import os, sys

_current_dir = os.path.dirname(os.path.abspath(os.path.realpath(sys.argv[0])))
load_dotenv(os.path.join(_current_dir, ".env"))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
API_TOKEN = os.getenv("API_TOKEN")

# regex for youtube links
import re
# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'((?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?[\w\-]+(?:\S+)?)',
    re.IGNORECASE
)

# ------------------------------------- IDs
# roles and channels ("<@&role_id>")
#     -----    test server IDs   -----     /    -----   real server IDs
STATUS_CHANNEL_ID = 1370716216863227924    # 849711794032214087 (info channel)
VIDEO_CHANNEL_ID = 1370706473155563581     # 800108276004028446

YOUTUBER_ROLE_ID = 1381223948854759494     # 781295509331116054
STREAMER_ROLE_ID = 1381223990349004850     # 781295771894153266
ADMIN_ROLE_ID = 1376617317382754456        # 800091356974022677
TRUSTED_ROLE_ID = 1381224331685920930      # 910540568164188252
DEVELOPER_ROLE_ID = 1381224153478336553    # 682090620726411304
CONDUCTOR_ROLE_ID = 1388550692213362879    # 1317870046726324284
SWATTEAM_ROLE_ID = 1388550925353877685     # 862318347542724679
CONTRIBUTOR_ROLE_ID = 1388551885476204655  # 850775875821109298

# custom bot emojis ("<:emiji_name:emoji_id>")
CONNECTE_EMOJI_ID = 1376214233041080410
DECONNECTE_EMOJI_ID = 1376214242424000583
LOADER_EMOJI_ID = 1376135761757470791
RC_EMOJI_ID = 1376135351353086002
RANK_EMOJI_ID = 1376135312669151232
ESPORTS_EMOJI_ID = 1376135172034007102
RWNC_EMOJI_ID = 1376135129960939575
REPULS_EMOJI_ID = 1376134874595065906

# members
GRAPHIC_DESIGNER_ID = 896507294983020574 # caracal
MAIN_DEVELOPER_ID = 213028561584521216 # docski

# default emojis
CHECK = ":white_check_mark:"
WARN = ":warning:"
ERROR = ":no_entry:"
VALIDATION_UNICODE = "✅"

# ------------------------------------- constants texts and links
# links
REPULS_WIKI_LINK = "https://repulsio.fandom.com/wiki/Repuls.io_Wiki"
REPULS_PRIVACY_LINK = "https://docskigames.com/privacy/"
REPULS_LINK = "https://repuls.io/"
DISCORD_INVITE_LINK = "https://discord.com/invite/2YKgx2HSfR"
CLEAR_DATA_TUTORIAL = "https://its.uiowa.edu/services/how-clear-cache-and-cookies-your-web-browser"

# texts (and bot info)
ASK_HELP = "\n**Ask an administrator for help!**"
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"
REPULS_DESCRIPTION = f"""
[Repuls.io]({REPULS_LINK}) is the future of browser games.
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
BOT_NAME = "RepulsBot"
BOT_VERSION = "0.1.9"
BOT_LINK = "https://github.com/pandaroux007/RepulsBot"
BOT_DESCRIPTION = """
Hey there! :waving_hand:
It's me, {name}, the official Discord bot for [this server]({server})! If you need help, type "!help" or help command to see what I can do!\n
If you don't feel like chatting with our amazing community, you can always play a game of [repuls.io]({game}) :wink:
"""
BOT_PREFIX = '!'
VOTE_HOURS = 48

# cogs name
EVENT_COG = "event_cog"
VOTE_COG = "vote_cog"
SERVER_COG = "server_cog"
ABOUT_COG = "about_cog"