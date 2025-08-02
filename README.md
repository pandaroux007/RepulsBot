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

## RepulsBot credits
### Question/answer creators for the FAQ
- *snipertoad*
- *BratzelBrezel*
- *Abyss 🇺🇦*
- *eagoose*
### Other contributors
- *sergiolan55*
- *aman_and_cats*
___
# ⚙️ Development
To run the project, install the `uv` tool (a more secure and faster equivalent to `pip`), and run `uv run "src/main.py"`.

> [!NOTE]
> Check the `pyproject.toml` file for dependencies. To mock an endpoint for the bot, use **Mockoon** software.
**Your contributions are welcome, be sure to read [CONTRIBUTING.md](CONTRIBUTING.md) first!**

> [!WARNING]
> *The token is hidden in a file not included with the other files on GitHub (`.env`). Please recreate it in [`./src/`](src/) with your own token before running the program if you wish to use this project or contribute to its development. Also change the IDs in [`constants.py`](src/constants.py)*

## 🚀 Development goals
### ✅ Objectives achieved:
- [x] Clean command
- [x] Ping command
- [x] Status message and activity
- [x] Command errors handling
- [x] Aboutserver and aboutgame command
- [x] Aboutmember and avatar command
- [x] Use `discord.py` cogs in the code before create the other commands
- [x] Help command
- [x] Vote for best video with reactions all 48h
- [x] Fix double send bug of addvideo command
- [x] Retrieving private information from a `.env` file
- [x] Membercount command
- [x] Send the best video to the main site via a secure endpoint
- [x] FAQ command
- [x] "Repuls wiki" command
- [x] Updated FAQs with new questions
- [x] Used Ruff linter on the project
- [x] Message management in the rules room
- [x] Added ticket system
- [x] Report an admin in tickets (visible only to the server owner)
- [x] Leaderboard command of votes for videos
- [x] Permanent online posting of the bot
- [x] Manage video equality cases
- [x] Added a simple error logging system
- [x] Improve the help command
___
### 🔥 Objectives to be achieved:
- moderation commands
- Displaying eSports results
- Discord 1v1s ([details here](https://discord.com/channels/603655329120518223/686216026412941429/1370057672304492554))
- Replace all bots on the server, including mute functions with timer, etc.
- For authorized players, 3D asset manager of the game from discord
- Show game leaderboard with pagination via discord
- View repuls.io player information from discord (level, stats, RC count)
- Manage your clan and friends via bot commands

**Lots of other amazing features!**
___
<details>
<summary>⛔️ Abandoned objectives (for now)</summary>

> - clear command (clean command but with messages' links)
> - Improved clean command ([discordpy.readthedocs.io](https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel.delete_messages), [discord.com/developers](https://discord.com/developers/docs/resources/message#bulk-delete-messages) ?)

</details>