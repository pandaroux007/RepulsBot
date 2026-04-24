from data.constants import (
    BotInfo,
    IDs,
    GameUrl
)

SERVER_FAQ_DATA = [
    {
        "question": "How to report a bug ?",
        "answer": (
            "If it's a game bug, there's no point in reporting it on the usual channels; your message "
            "will get lost in the flood of messages and the developer will never see it. To report a bug, "
            "the appropriate place is here: https://discord.com/channels/603655329120518223/1076163933213311067 "
            "(be sure to read the rules before posting, provide screenshots/recordings, and give your post a clear title). "
            "If you're testing **the beta**, the appropriate forum is this one: "
            "https://discord.com/channels/603655329120518223/1349635397155684446 (same recommendations as for the other forum).\n\n"
            f"-# If it's a bot bug, contact the developer <@{IDs.repulsTeam.BOT_DEVELOPER}> or create an [GitHub issue]({BotInfo.REPORT})."
        )
    },
    {
        "question": "How does the YouTube video system work?",
        "answer": "You'll find [all the details here](https://officialrepuls.fandom.com/wiki/Discord_videos_voting_system). Start posting your repuls videos now!"
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

GAME_FAQ_DATA = [
    {
        "question": "Why is the game not working/loading ?",
        "answer": (
            "Your browser may have cached the game code. Clear your cache and cookies [as instructed "
            f"here](https://github.com/pandaroux007/RepulsBot/wiki/Troubleshoot-game-loading-issues), and try launching [repuls.io]({GameUrl.GAME}) again."
        )
    },
    {
        "question": "Is it possible to reset my password ?",
        "answer": (
            "We do not offer password changes. This is a FREE online game where anyone can have MULTIPLE accounts "
            f"and we do not have the resources to process every request (the only developer, <@{IDs.repulsTeam.MAIN_DEVELOPER}>, "
            "is the only person capable of doing this and he is very busy working on the game). **Better to wait for a "
            "future update that will add account recovery**"
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
        "answer": (
            f"To protect the work of <@{IDs.repulsTeam.MAIN_DEVELOPER}> and those who modeled or created assets, obtaining specific 3D elements is quite difficult. "
            f"Note that <@{IDs.repulsTeam.MAIN_DEVELOPER}> has provided some in the cosmetics channel [here](https://discord.com/channels/603655329120518223/1240815231286906900) "
            f"(do not use them for anything other than what <@{IDs.repulsTeam.MAIN_DEVELOPER}> has authorized in this post).\n\n"
            "You may be able to access the old RWNC server (the continued operation of this server and its assets are not guaranteed) "
            f"via [this invitation]({GameUrl.RWNC_SERVER}); some assets are available there (mostly without the game's UV wrap).\n\n"
            "If the asset you're looking for isn't publicly listed, the only solution is to ask in the general chat channel and hope"
            "a high-ranking server member sends it to you (few people have these assets, so don't insist if no one does, and "
            f"clearly state why you need it). Please do not ask <@{IDs.repulsTeam.MAIN_DEVELOPER}> unless you have a very good reason; it's an unnecessary hassle."
        )
    },
]