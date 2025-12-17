from constants import (
    BotInfo as bot,
    Links as links,
    IDs,
    GameUrl
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
            "answer": (
                f"If this is a RepulsBot bug, then you can create an issue [on github]({bot.GITHUB}/issues) "
                "(just make sure it's actually a bug first). Otherwise, if the bug is coming from the game, "
                "then you can create a topic [in this channel](https://discord.com/channels/603655329120518223/1076163933213311067) or in "
                "[this one](https://discord.com/channels/603655329120518223/1349635397155684446) for bugs related to v2 of the netcode. Videos and screenshots are welcome."
            )
        },
        {
            "question": "How does the YouTube video system work?",
            "answer": f"You'll find [all the details here]({links.EXPLANATION_VIDEO_SYSTEM}). Start posting your repuls videos now!"
        },
        {
            "question": "I would like to report someone.",
            "answer": (
                "To report abuse in game chat, a hacker, or a Discord user, create an appropriate ticket, "
                "via the following message: https://discord.com/channels/603655329120518223/1398612579034595358. "
                "Make sure your report **includes evidence, such as a screenshot or video!**"
            )
        },
        {
            "question": "How can I suggest new ideas for the game ?",
            "answer": (
                "You can suggest new ideas for Repuls on the forum https://discord.com/channels/603655329120518223/1079019183637016576 by creating a post introducing your idea. "
                "**Use the pinned forum guidelines to structure your idea. Make sure to include as much detail as possible for easy understanding.**\n\n"
                "To create new textures or assets (helmets, weapons...), please visit the forum https://discord.com/channels/603655329120518223/1240802379943641129 and follow the instructions."
            )
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
            "answer": (
                "Your browser may have cached the game code. Clear your cache and cookies [as instructed "
                f"here]({links.CLEAR_DATA_TUTORIAL}), and try launching [repuls.io]({GameUrl.GAME}) again."
            )
        },
        {
            "question": "How do I reset my password ?",
            "answer": (
                f"To reset your password, you cannot do so through the game UI. Please send a direct message with your "
                f"account name and the new password you wish to use to <@{IDs.repulsTeam.MAIN_DEVELOPER}>. Once done, remember to delete your messages."
            )
        },
        {
            "question": "How to improve in repuls.io ?",
            "answer": (
                "Most active community members will be happy to answer your gameplay questions."
                "Here are some helpful guides to help you improve your skills:"
                "- **Pro Guide**: https://www.youtube.com/watch?v=RssaVjnsDEk"
                "- **B-hopping**: https://www.youtube.com/watch?v=AjgZtukUl9E"
            )
        },
        {
            "question": "About the Super League ?",
            "answer": (
                "**What is the Super League ?**"
                "The Super League is a large clan tournament where different clans compete against each other!\n"
                "**Can I participate ?**"
                "Of course! You can participate in the Super League if you are part of a clan or have created your own. "
                "*If you don't have a clan but still want to play, you can become a free agent (free agents are players hired by participating clans).*"
            )
        },
        {
            "question": "All about clans!",
            "answer": (
                "**Where can I join a clan ?**"
                "You can join a clan in https://discord.com/channels/603655329120518223/1373288831058710740 (Not all clans may have posted their invitation!) or in eSports server\n"
                "**How do I become a clan leader ?**"
                "The requirements to become a clan leader are to have at least 10 members in the in-game clan.\n"
                "**How to host your own events/tournaments?**"
                f"To host your own tournaments, they must be approved by staff. Send a DM to an <@&{IDs.serverRoles.ESPORTS_ORGANIZER}> with your plan, rules, and projected size."
            )
        },
    ]