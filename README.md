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
- Authors : [pandaroux007](https://github.com/pandaroux007), [itsdocski](https://github.com/tahirG)
- License : the bot and everything that composes it (icon, code, etc.) are under the MIT license (see [LICENSE.txt](LICENSE.txt) file) - for more information go [there](https://opensource.org/license/mit).

RepulsBot is a versatile bot, primarily for managing the vote for the best video and its submission for display on repuls.io. Second, it has a tickets system for improved signal confidentiality. It also allows you to answer frequently asked questions via FAQ commands. Of course, RepulsBot allows other secondary commands, as well as a help command.

## RepulsBot credits
### Question/answer creators for the FAQ
- *snipertoad*
- *BratzelBrezel*
- *Abyss*
- *eagoose*
### Other contributors
- *sergiolan55*
- *aman_and_cats*
___
# ⚙️ Development
> [!NOTE]
> **Your contributions are welcome, be sure to read [CONTRIBUTING.md](CONTRIBUTING.md) first!** Even if you don't want to contribute, you can find all the details for configuring and launching the bot in [CONTRIBUTING.md](CONTRIBUTING.md)

## 🚀 Development goals
### Objectives to be achieved
#### Must be defined
- moderation commands
- Manage competitions and display eSports results
- Replace all bots on the server, including mute functions with timer, etc.
- For authorized players, 3D asset manager of the game from discord
#### Requires an API
- Discord 1v1s ([details here](https://discord.com/channels/603655329120518223/686216026412941429/1370057672304492554))
- Show game leaderboard with pagination via discord
- View repuls.io player information from discord (level, stats, RC count)
- Manage your clan and friends via bot commands

**Lots of other amazing features!**
___
<details>
<summary>Abandoned objectives</summary>

> - clear command (clean command but with messages' links)
> - Improved clean command ([discordpy.readthedocs.io](https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel.delete_messages), [discord.com/developers](https://discord.com/developers/docs/resources/message#bulk-delete-messages) ?)

</details>

## Difference between bot logs and moderation logs
### Moderation logs
- Deleted channel
- Created channel
- Deleted message
- Modified message
- Purge results
- Ban, ban, and kick log
- Role modification (including muted role management)
### Bot logs
- Message deletion by automod
- Ticket log
- Error log