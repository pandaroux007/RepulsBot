<div align="center">

# RepulsBot

💬 ***The official bot for the repuls.io discord server***

[![Join the repuls.io discord!](https://img.shields.io/discord/603655329120518223?logo=discord&logoColor=white&color=black)](https://discord.com/invite/2YKgx2HSfR)
[![GitHub](https://img.shields.io/badge/GitHub-%23121011.svg?logo=github&logoColor=white)](https://github.com/pandaroux007/RepulsBot/releases)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

[![Built with Python3](https://img.shields.io/badge/built%20with-Python3-yellow.svg)](https://www.python.org/)
[![GitHub Release](https://img.shields.io/github/v/release/pandaroux007/RepulsBot?include_prereleases&style=flat&logo=auto&color=blue&link=https%3A%2F%2Fgithub.com%2Fpandaroux007%RepulsBot%2Freleases)](https://github.com/pandaroux007/RepulsBot/releases)
[![Commits](https://img.shields.io/github/commit-activity/t/pandaroux007/RepulsBot)](https://github.com/pandaroux007/RepulsBot/commits/main/)
[![Stars](https://img.shields.io/github/stars/pandaroux007/RepulsBot.svg?style=social&label=Stars)](https://github.com/pandaroux007/RepulsBot)

</div>

# ✨ About
## What's repuls.io ?

<img align="right" width="100" height="100" src="https://repuls.io/img/repuls_logo_icon.png">

[Repuls.io](https://repuls.io/home) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!

Tired of the same run, aim, shoot gameplay that every shooter does ?! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech! **That's** the repuls experience son!
## And what about RepulsBot
- Author : [pandaroux007](https://github.com/pandaroux007)
- License : the bot and everything that composes it (icon, code, etc.) are under [the MIT license](https://opensource.org/license/mit) (see [LICENSE.txt](LICENSE.txt) file). **By contributing (whether it be code, graphics, links, or anything else), you agree to publish it under the same license.**
- GitHub created at : ***May 10, 2025, 4:49:10 PM***
- Added to the main server at : ***19 Jul 2025***

<details>
<summary><strong>RepulsBot contributors</strong></summary>

## RepulsBot credits
### Main contributors
- [*itsdocski*](https://github.com/tahirG)
- *sergiolan55*
- [*AmanLovesCats*](https://github.com/AmanLovesCats)
### Question/answer creators for the FAQ
- *snipertoad*
- *BratzelBrezel*
- [*Abyss*](https://github.com/abysmal-abyss)
- *eagoose*
- *AlfaStephano48*
### Other contributors
#### NaN server
- *martin_9202*
- [*the_yerminator*](https://github.com/YoannDev90)
- [*lexedia*](https://github.com/Lexedia)
#### discord.py server
- *solstice/solsticeshard*
- [*Lillifr/fretgfr*](https://github.com/fretgfr)
- *Mellow/codinglyl*
- [*Sheeb/soheab_*](https://github.com/Soheab)
- [*Link/hyliantwink*](https://github.com/AbstractUmbra)
- [*死/iyad8888*](https://github.com/iyad-f)

</details>

___
# ⚙️ Development
> [!NOTE]
> You can find details on how the bot and the game work in [the official fandom wiki](https://officialrepuls.fandom.com), this section is only for developers and maintainers of the bot. **Your contributions are welcome, be sure to read [CONTRIBUTING.md](CONTRIBUTING.md) first!**

### Useful tools for contributing
- Create interfaces with Components v2: https://discord.builders/
- Learn SQL statements: https://sqlbolt.com/
- Create, modify, and correct regular expressions: https://regexr.com/
#### Useful resources
- [`discord.py` documentation](https://discordpy.readthedocs.io/)
- [`uv` guide](https://github.com/astral-sh/uv)

### Features on Standby
I would like to replace the RCA Bot translation functionality (which uses Google Translate) by making it more reliable, bandwidth-efficient, and privacy-friendly. Several tools exist for this purpose (notably [`LibreTranslate`](https://libretranslate.com/) - based on the [`Argos`](https://github.com/argosopentech/argos-translate/) engine, which can be used in combination with [`langdetect`](https://pypi.org/project/langdetect/) to download the necessary language models if needed). This is a local solution that meets my requirements (free, no limitations, no requests), but it is more complex to implement (may require a Docker container to contain memory leaks; I am investigating this) and therefore must wait for the VPS.
> There are several translation APIs ([Google Translate](https://docs.cloud.google.com/translate/docs), [Lingvanex](https://lingvanex.com), [DeepL](https://www.deepl.com/en/pro-api), etc.), but they have several drawbacks:
> - You can't guarantee 100% what happens to the messages you send (privacy)
> - Most are not free and/or require accounts/API keys, which greatly reduces maintainability (and the ability to work as a team on the bot)
> - Most have fairly low limits on length, number of requests, etc.
> - Sending and receiving requests (especially if the texts are long) is very polluting