from data.constants import (
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
                "If this is a RepulsBot bug, then you can create a ticket, contact the developer "
                f"<@{IDs.repulsTeam.BOT_DEVELOPER}> directly, or create a [GitHub issue]({bot.REPORT}) "
                "(just make sure it's actually a bug first).\n\n"
                "Otherwise, if the bug is coming from the game, then you can create a topic [in this channel]"
                "(https://discord.com/channels/603655329120518223/1076163933213311067) (or in [this one](https://discord.com/channels/603655329120518223/1349635397155684446) "
                "for bugs related to the beta). Videos and screenshots are welcome."
            )
        },
        {
            "question": "How does the YouTube video system work?",
            "answer": f"You'll find [all the details here]({links.EXPLANATION_VIDEO_SYSTEM}). Start posting your repuls videos now!"
        },
        {
            "question": "I would like to report someone.",
            "answer": (
                "To report a player's behavior in the game, use https://discord.com/channels/603655329120518223/849701341136027669\n\n"
                "Most of the time, it's recommended to keep reports private, whether it's about a player in chat, a hacker in the game, "
                "or a member of this server, and therefore use the ticket system: https://discord.com/channels/603655329120518223/1466079810320208148.\n\n"
                "Make sure your report **includes evidence, such as a screenshot or video!**"
            )
        },
        {
            "question": "How can I suggest new ideas for the game ?",
            "answer": (
                "You can suggest new ideas for Repuls on the forum https://discord.com/channels/603655329120518223/1079019183637016576 by creating a post introducing your idea. "
                "**Use the pinned forum guidelines to structure your idea. Make sure to include as much detail as possible for easy understanding.**\n\n"
            )
        },
        {
            "question": "How can I create a new element?",
            "answer": (
                "Rules for creating game elements, please read carefully: https://discord.com/channels/603655329120518223/1448042069930147840\n"
                "### Skin Creation\n"
                "To create a skin, [here's a post](https://discord.com/channels/603655329120518223/1240815231286906900) that provides models for some weapons, "
                "a skin example, and below you'll find a tutorial on how to edit and render a skin model.\n"
                "### 3D Modeling\n"
                "If you know how to model in 3D and are willing to contribute for free (or at least without receiving any payment), "
                "and you model an element (map, weapon, anything), you can submit it on https://discord.com/channels/603655329120518223/1240802379943641129 "
                f"(do not send anything directly to <@{IDs.repulsTeam.MAIN_DEVELOPER}>)."
            )
        },
    ]

class GameFAQ(FAQBase):
    faq_id = "game_faq_select"
    faq_data = [
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
                "Password changes are only performed in very rare cases, and they require very strong and clear evidence. "
                f"Furthermore, the only person authorized to perform them is <@{IDs.repulsTeam.MAIN_DEVELOPER}> himself "
                "(a very busy person who cannot handle all such requests), which significantly increases waiting times.\n\n"
                "It is best to **wait for a future update that will add password recovery**."
            )
        },
        {
            "question": "How to improve in repuls.io ?",
            "answer": (
                "Most active community members will be happy to answer your gameplay questions. "
                "Here are some helpful guides to help you improve your skills:\n"
                "- **Pro Guide**: https://www.youtube.com/watch?v=RssaVjnsDEk\n"
                "- **B-hopping**: https://www.youtube.com/watch?v=AjgZtukUl9E"
            )
        },
        {
            "question": "All about clans!",
            "answer": (
                "### Where can I join a clan ?\n"
                "You can join a clan in https://discord.com/channels/603655329120518223/1373288831058710740 (not all clans may have posted their invitation!) or in eSports server\n"
                "### How do I become a clan leader ?\n"
                "The requirements to become a clan leader are to have at least 10 members in the in-game clan.\n"
                "### How do I recruit people to my clan?\n"
                "To recruit members, you currently only have one option: word of mouth. Invite other people "
                "(the eSports server is a good place to find players looking for a clan) to join you via DMs "
                "(no spam, obviously), inform everyone about the existence of your clan in the game chat, "
                "create a post in https://discord.com/channels/603655329120518223/1373288831058710740, etc.\n"
                "### How to host your own events/tournaments?\n"
                f"To host your own tournaments, they must be approved by staff. Send a DM to an <@&{IDs.serverRoles.ESPORTS_ORGANIZER}> with your plan, rules, and projected size."
            )
        },
        {
            "question": "About the Super League ?",
            "answer": (
                "### What is the Super League ?\n"
                "The Super League is a large clan tournament where different clans compete against each other!\n"
                "### Can I participate ?\n"
                "Of course! You can participate in the Super League if you are part of a clan or have created your own. "
                "**If you don't have a clan but still want to play**, you can become a free agent (free agents are players hired by participating clans)."
            )
        },
        {
            "question": "Where can I get 3D assets of the game?",
            "answer": f"To prevent 3D assets in REPULS from being stolen, please join [the RWNC server]({links.RWNC_SERVER}) for access to certain models."
        },
    ]