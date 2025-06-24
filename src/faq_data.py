from constants import (
    BOT_LINK,
    YOUTUBER_ROLE_ID,
    VALIDATION_UNICODE
)

FAQ_ENTRIES = [
    {
        "question": "How to report a bug ?",
        "answer": f"If this is a RepulsBot bug, then you can create an issue [on github]({BOT_LINK}/issues) (just make sure it's actually a bug first). Otherwise, if the bug is coming from the game, then you can create a topic [in this channel](https://discord.com/channels/603655329120518223/1076163933213311067) or in [this one](https://discord.com/channels/603655329120518223/1349635397155684446) as part of the v2 of the netcode."
    },
    {
        "question": "How to post a youtube video ?",
        "answer": f"To post a YouTube video, you must have the <@&{YOUTUBER_ROLE_ID}> role. Then, either post your link directly or use the `!addvideo` command. A moderator will have to add the {VALIDATION_UNICODE} reaction if your video is valid."
    },
]