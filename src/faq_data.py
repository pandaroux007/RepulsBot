from constants import (
    BotInfo as bot,
    Links as links,
    DefaultEmojis,
    IDs
)

# ---------------------------------- faq base class
class FAQBase:
    faq_id: str
    faq_data: list

    @classmethod
    def get_id(cls) -> str:
        return cls.faq_id

    @classmethod
    def get_data(cls) -> list:
        return cls.faq_data

# ---------------------------------- faq content
class ServerFAQ(FAQBase):
    faq_id = "server_faq_select"
    faq_data = [
        {
            "question": "How to report a bug ?",
            "answer": f"If this is a RepulsBot bug, then you can create an issue [on github]({bot.GITHUB}/issues) (just make sure it's actually a bug first). Otherwise, if the bug is coming from the game, then you can create a topic [in this channel](https://discord.com/channels/603655329120518223/1076163933213311067) or in [this one](https://discord.com/channels/603655329120518223/1349635397155684446) for bugs related to v2 of the netcode. Videos and screenshots are welcome."
        },
        {
            "question": "How to post a youtube video ?",
            "answer": f"To post a YouTube video, you must have the <@&{IDs.serverRoles.YOUTUBER}> role. Then, simply post your video along with a simple description in the  channel. A moderator will have to add the {DefaultEmojis.CHECK} reaction if your video is valid."
        },
        {
            "question": "How to get a role ?",
            "answer": f"""
- To become a <@&{IDs.serverRoles.YOUTUBER}> or a <@&{IDs.serverRoles.STREAMER}>, please read this message https://discord.com/channels/603655329120518223/800107070614405120/1389262601740877925 and follow the instructions.
- To become a <@&{IDs.serverRoles.CLAN_LEADER}>, simply have a clan of at least 10 members (they can play as guests and without discord). See https://discord.com/channels/603655329120518223/1395002152933396603 for details.
- To become a <@&{IDs.serverRoles.CONTRIBUTOR}>, you must donate to the game in some way. Please contact docski in DM for this, the admins will not grant this role.
- *Staff doesn't offer the <@&{IDs.serverRoles.SWATTEAM}>, or <@&{IDs.serverRoles.CONDUCTOR}> roles.*. Don't beg for the <@&{IDs.serverRoles.TRUSTED}> or <@&{IDs.serverRoles.ADMIN}> roles either; they are only granted if administrators deem it appropriate.
"""
        },
        {
            "question": "I would like to report someone.",
            "answer": "To report abuse in game chat, a hacker, or a Discord user, create an appropriate ticket, via the following message: https://discord.com/channels/603655329120518223/1398612579034595358. Make sure your report **includes evidence, such as a screenshot or video!**"
        },
        {
            "question": "When will the next update be ?",
            "answer": f"""
The [repuls.io]({links.GAME}) game is currently being rewritten. The current game code needs to be rewritten for greater stability and to accommodate more players in future seasons.\n
This code rewrite, called `R2` or `netcode v2`, will also add the basis for numerous bug fixes, as well as new features (training bots, tanks, new mechs, etc.), and new servers (e.g., in Asia).\n
Although we don't have the exact date for the next update, you can already test it in the beta! Any bugs discovered save time for <@{IDs.repulsTeam.MAIN_DEVELOPER}>, so report them here: https://discord.com/channels/603655329120518223/1349635397155684446\n
"""
        },
        {
            "question": "How can I suggest new ideas for the game ?",
            "answer": """
                You can suggest new ideas for Repuls on the forum https://discord.com/channels/603655329120518223/1079019183637016576 by creating a post introducing your idea.\n
                **Use the pinned forum guidelines to structure your idea. Make sure to include as much detail as possible for easy understanding.**\n
                To create new textures or assets (helmets, weapons...), please visit the forum https://discord.com/channels/603655329120518223/1240802379943641129 and follow the instructions.
            """
        },
    ]

class GameFAQ(FAQBase):
    faq_id = "game_faq_select"
    faq_data = [
        {
            "question": "Where can I get 3D assets of the game?",
            "answer": f"To prevent 3D assets in REPULS from being stolen, please join [the RWNC server]({links.RWNC_SERVER}) for access to certain models."
        },
        {
            "question": "Why is the game not working/loading ?",
            "answer": f"Your browser may have cached the game code. Clear your cache and cookies [as instructed here]({links.CLEAR_DATA_TUTORIAL}), and try launching [repuls.io]({links.GAME}) again."
        },
        {
            "question": "How do I reset my password ?",
            "answer": f"To reset your password, you cannot do so through the game UI. Please send a direct message with your account name and the new password you wish to use to <@{IDs.repulsTeam.MAIN_DEVELOPER}>. Once done, remember to delete your messages."
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
*If you don't have a clan but still want to play, you can become a free agent (free agents are players hired by participating clans).*
"""
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
To host your own tournaments, they must be approved by staff. Send a DM to an <@&{IDs.serverRoles.ESPORTS_ORGANIZER}> with your plan, rules, and projected size.
"""
        },
    ]