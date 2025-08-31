<div align="center">

# RepulsBot
[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://stand-with-ukraine.pp.ua)
[![Built with Python3](https://img.shields.io/badge/built%20with-Python3-yellow.svg)](https://www.python.org/)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![Join the repuls.io discord!](https://img.shields.io/discord/603655329120518223?logo=discord&logoColor=white&color=black)](https://discord.com/invite/2YKgx2HSfR)

💬 ***The official bot for [the repuls.io discord server](https://discord.com/invite/2YKgx2HSfR)***
</div>

# ✨ About
## What's repuls.io ?
[Repuls.io](https://repuls.io/home) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!

Tired of the same run, aim, shoot gameplay that every shooter does ?! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech! **That's** the repuls experience son!
## And what about RepulsBot
- Authors : [pandaroux007](https://github.com/pandaroux007)
- License : the bot and everything that composes it (icon, code, etc.) are under [the MIT license](https://opensource.org/license/mit) (see [LICENSE.txt](LICENSE.txt) file).

<details>
<summary><strong>RepulsBot contributors</strong></summary>

## RepulsBot credits
### Main contributors
- [*itsdocski*](https://github.com/tahirG)
- *sergiolan55*
### Question/answer creators for the FAQ
- *snipertoad*
- *BratzelBrezel*
- *Abyss*
- *eagoose*
### Other contributors
- *aman_and_cats*
- *martin_9202* (**NaN**)
- *the_yerminator* (**NaN**)
- *lexedia* (**NaN**)
- *Mellow* (**d.py**)

</details>

**To learn more about RepulsBot, visit [the wiki](https://github.com/pandaroux007/RepulsBot/wiki) !**
___
# ⚙️ Development
> [!NOTE]
> **Your contributions are welcome, be sure to read [CONTRIBUTING.md](CONTRIBUTING.md) first!** Even if you don't want to contribute, you can find all the details for configuring and launching the bot in [CONTRIBUTING.md](CONTRIBUTING.md)

You can find details about the front-end operation of the bot in [the wiki](https://github.com/pandaroux007/RepulsBot/wiki), this section is intended for developers only.

## Development goals
### Objectives to be achieved
- Show game leaderboard with pagination via discord
- Replace all bots on the server, without being admin
#### Must be defined
- Manage competitions and display eSports results
- For authorized players, asset store of the game from discord
#### Requires an API
- Discord 1v1s ([details here](https://discord.com/channels/603655329120518223/686216026412941429/1370057672304492554))
- View repuls.io player information from discord (level, stats, RC count)
- Manage your clan and friends via bot commands
___
## Log System
### Moderation Logs
Moderation logs are dedicated to events that may be useful to admins, such as message deletions and modifications, automod actions, purges, kicked or banned users, or when a timeout is applied. Changes to roles are also logged.

> [!IMPORTANT]  
> **Since the bot is not an admin**, it will only log events from channels to which it has access; staff-only channels are not logged unless the bot is explicitly added.
### Bot Logs
This channel is less critical than the moderation logs; it contains messages from the bot: when it goes live, when an error occurs on an order, or when a ticket is opened or closed.

## Help command details
The help command differentiates between commands that are usable by all members and those that are only usable by admins. It does this by relying on the `extras` parameter of the `discord.py` decorators.
- Contextual commands ([discord.ext.commands.command](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.command))
- Slash commands ([discord.app_commands.command](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.command))

The problem with this method is that it does not allow you to mention slash commands since you do not get their ID.