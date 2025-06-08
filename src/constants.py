VOTE_HOURS = 48

# regex for youtube links
import re
# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'((?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?[\w\-]+(?:\S+)?)',
    re.IGNORECASE
)

# ------------------------------------- IDs
# roles and channels
#     -----    test server IDs   -----     /    -----   real server IDs
STATUS_CHANNEL_ID = 1370716216863227924    # 849711794032214087 (info channel)
VIDEO_CHANNEL_ID = 1370706473155563581     # 800108276004028446

YOUTUBER_ROLE_ID = 1381223948854759494     # 781295509331116054
STREAMER_ROLE_ID = 1381223990349004850     # 781295771894153266
ADMIN_ROLE_ID = 1376617317382754456        # 800091356974022677
TRUSTED_ROLE_ID = 1381224331685920930      # 910540568164188252
DEVELOPER_ROLE_ID = 1381224153478336553    # 682090620726411304

# ------------------------------------- emojis
# custom bot emojis ("<:emiji_name:emoji_id>")
CONNECTE_EMOJI_ID = 1376214233041080410
DECONNECTE_EMOJI_ID = 1376214242424000583
LOADER_EMOJI_ID = 1376135761757470791
RC_EMOJI_ID = 1376135351353086002
RANK_EMOJI_ID = 1376135312669151232
ESPORTS_EMOJI_ID = 1376135172034007102
RWNC_EMOJI_ID = 1376135129960939575
REPULS_EMOJI_ID = 1376134874595065906

# default emojis
CHECK = ":white_check_mark:"
ERROR = ":x:"
VALIDATION_UNICODE = "✅"

# ------------------------------------- constants texts and links
# links
ENDPOINT_URL = "" # nothing for now
REPULS_PRIVACY_LINK = "https://docskigames.com/privacy/"
REPULS_LINK = "https://repuls.io/"
DISCORD_INVITE_LINK = "https://discord.com/invite/2YKgx2HSfR"
DISCORD_YOUTUBE_CHANNEL_LINK = f"https://discord.com/channels/1370706439491817563/{VIDEO_CHANNEL_ID}" # f"https://discord.com/channels/603655329120518223/{VIDEO_CHANNEL}"

# texts
FOOTER_EMBED = "repuls.io is developed with ♥️ by docski"
REPULS_DESCRIPTION = f"""
[Repuls.io]({REPULS_LINK}) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!\n
Tired of the same run, aim, shoot gameplay that every shooter does??! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech!! THATS the repuls experience son!
"""
BOT_DESCRIPTION = """
Hey there! :waving_hand:
It's me, {name}, the official Discord bot for [this server]({server})! If you need help, type "!help" or help command to see what I can do!\n
If you don't feel like chatting with our amazing community, you can always play a game of [repuls.io]({game}) :wink:
"""

# cogs name
EVENT_COG = "event_cog"
VOTE_COG = "vote_cog"
SERVER_COG = "server_cog"
ABOUT_COG = "about_cog"