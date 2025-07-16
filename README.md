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

Tired of the same run, aim, shoot gameplay that every shooter does??! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech!! THATS the repuls experience son!
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
- [x] clean command
- [x] ping command
- [x] status message and activity
- [x] command errors handling
- [x] aboutserver and aboutgame command
- [x] aboutmember and avatar command
- [x] use `discord.py` cogs in the code before create the other commands
- [x] help command
- [x] vote for best video with reactions all 48h
- [x] fix double send bug of addvideo command
- [x] retrieving private information from a `.env` file
- [x] membercount command
- [x] send the best video to the main site via a secure endpoint
- [x] FAQ command
- [x] "Repuls wiki" command
- [x] Updated FAQs with new questions
- [x] used Ruff linter on the project
- [x] message management in the rules room
- [x] Added ticket system
- [x] report an admin in tickets (visible only to the server owner)
___
### 🕑️ Objectives in progress:
- [ ] leaderboard command of votes for videos
- [ ] commande msgcount

### ⛔️ Abandoned objectives (for now):
- [ ] clear command (clean command but with messages' links)
- [ ] Improved clean command ([discordpy.readthedocs.io](https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel.delete_messages), [discord.com/developers](https://discord.com/developers/docs/resources/message#bulk-delete-messages) ?)

## Discord.py cogs
- About cog (in [`src/cogs/about_cog.py`](src/cogs/about_cog.py)) : This cog contains information commands about members and the server;
  - aboutgame
  - aboutmember
  - aboutserver
  - avatar
  - membercount
  - wiki
- Server cog (in [`src/cogs/server_cog.py`](src/cogs/server_cog.py)) : Contains commands useful for server management;
  - help
  - clean
  - ping
  - serverfaq
  - gamefaq
- Event cog (in [`src/cogs/event_cog.py`](src/cogs/event_cog.py)) : Contains all events raised by the discord bot;
  - on_message
  - on_command_error
  - on_ready
- Vote cog (in [`src/cogs/vote_cog.py`](src/cogs/vote_cog.py)) : Contains all the elements relating to the management of votes for the best YouTube video every 48 hours;
  - addvideo (command)
  - discord ([tasks](https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html))
- Tickets cog (in [`src/cogs/tickets_cog.py`](src/cogs/tickets_cog.py)) : Contains the commands and management of messages, modals and selectors of the server moderation ticket system
  - open_ticket
  - close_ticket
  - setup_ticket