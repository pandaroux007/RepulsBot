from constants import *

# faq s custom IDs
SERVER_FAQ_ID = "server_faq_select"
GAME_FAQ_ID = "game_faq_select"

# faq content
SERVER_FAQ = [
    {
        "question": "How to report a bug ?",
        "answer": f"If this is a RepulsBot bug, then you can create an issue [on github]({BOT_LINK}/issues) (just make sure it's actually a bug first). Otherwise, if the bug is coming from the game, then you can create a topic [in this channel](https://discord.com/channels/603655329120518223/1076163933213311067) or in [this one](https://discord.com/channels/603655329120518223/1349635397155684446) as part of the v2 of the netcode. Videos and screenshots are welcome."
    },
    {
        "question": "How to post a youtube video ?",
        "answer": f"To post a YouTube video, you must have the <@&{YOUTUBER_ROLE_ID}> role. Then, either post your link directly or use the `!addvideo` command. A moderator will have to add the {VALIDATION_UNICODE} reaction if your video is valid."
    },
    {
        "question": "How to get a role ?",
        "answer": f"""
- To become a <@&{YOUTUBER_ROLE_ID}>, you must have a channel that primarily publishes Repuls-related content and have at least 75 subscribers. Videos must be at least 720p in quality and include editing (no gameplay recordings).
- To become a <@&{STREAMER_ROLE_ID}>, you must stream repuls.io once a week.
- To become a <@&{CONTRIBUTOR_ROLE_ID}>, you must donate to the game in some way.
- To become a <@&{TRUSTED_ROLE_ID}> member, you must send at least 500 messages and be active.
- *Staff no longer offers the <@&{ADMIN_ROLE_ID}>, <@&{SWATTEAM_ROLE_ID}>, or <@&{CONDUCTOR_ROLE_ID}> roles.*"""
    },
    {
        "question": "Need help ? Ask here.",
        "answer": f"Please try asking in https://discord.com/channels/603655329120518223/603655329124712560 or in https://discord.com/channels/603655329120518223/1179111829788688434 first. If you don't get a clear answer, you can also ask <@&{ADMIN_ROLE_ID}> members"
    },
    {
        "question": "I would like to report someone.",
        "answer": "If you report someone, file it in https://discord.com/channels/603655329120518223/849701341136027669. Make sure your report **includes evidence, such as a screenshot or video!**"
    },
    {
        "question": "When will the next update be ?",
        "answer": f"""
The [repuls.io]({REPULS_LINK}) game is currently being rewritten. The current game code needs to be rewritten for greater stability and to accommodate more players in future seasons.\n
This code rewrite, called `R2` or `netcode v2`, will also add the basis for numerous bug fixes, as well as new features (training bots, tanks, new mechs, etc.), and new servers (e.g., in Asia).\n
Although we don't have the exact date for the next update, you can already test it in the beta! Any bugs discovered save time for <@{MAIN_DEVELOPER_ID}>, so report them here: https://discord.com/channels/603655329120518223/1349635397155684446\n"""
    },
    {
        "question": "How can I suggest new ideas for the game ?",
        "answer": """
You can suggest new ideas for Repuls on the forum https://discord.com/channels/603655329120518223/1079019183637016576 by creating a post introducing your idea.\n
**Use the pinned forum guidelines to structure your idea. Make sure to include as much detail as possible for easy understanding.**\n
To create new textures or assets (helmets, weapons...), please visit the forum https://discord.com/channels/603655329120518223/1240802379943641129 and follow the instructions."""
    },
]

GAME_FAQ = [
    {
        "question": "Where can I get 3D assets of the game?",
        "answer": f"To prevent 3D assets in repuls from being stolen, please send a direct message or mention to <@{GRAPHIC_DESIGNER_ID}>"
    },
    {
        "question": "Why is the game not working/loading ?",
        "answer": f"Your browser may have cached the game code. Clear your cache and cookies [as instructed here]({CLEAR_DATA_TUTORIAL}), and try launching [repuls.io]({REPULS_LINK}) again."
    },
    {
        "question": "How do I reset my password ?",
        "answer": f"To reset your password, you cannot do so through the game UI. Please send a direct message with your account name and the new password you wish to use to <@{MAIN_DEVELOPER_ID}>. Once done, remember to delete your messages."
    },
    {
        "question": "How to improve in repuls.io ?",
        "answer": """
Most active community members will be happy to answer your gameplay questions.
Here are some helpful guides to help you improve your skills:
- **Pro Guide**: https://www.youtube.com/watch?v=RssaVjnsDEk
- **B-hopping**: https://www.youtube.com/watch?v=AjgZtukUl9E"""
    },
    {
        "question": "About the Super League ?",
        "answer": """
**What is the Super League ?**
The Super League is a large clan tournament where different clans compete against each other!
**Can I participate ?**
Of course! You can participate in the Super League if you are part of a clan or have created your own.\n
*If you don't have a clan but still want to play, you can become a free agent (free agents are players hired by participating clans).*"""
    },
    {
        "question": "All about clans!",
        "answer": f"""
**Where can I join a clan ?**
You can join a clan in https://discord.com/channels/603655329120518223/1373288831058710740 (Not all clans may have posted their invitation!)\n
**What are the best clans ?**
View the top 3 clans according to the rankings https://discord.com/channels/603655329120518223/1129749085541384202 in RCC (Repuls Clan Clash)\n
**How do I become a clan leader ?**
The requirements to become a clan leader are to have at least 10 members in the in-game clan.\n
**How to host your own events/tournaments?**
To host your own tournaments, they must be approved by staff. Send a DM to an <@&{ESPORTS_ORGANIZER_ROLE_ID}> with your plan, rules, and projected size."""
    },
]