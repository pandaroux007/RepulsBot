# Contribute to RepulsBot 🤖
Thank you for your interest in contributing to the official [repuls.io](https://repuls.io) bot!
This guide will help you participate effectively in development.

## 🛠️ Prerequisites
- Python 3.10+
- [UV](https://github.com/astral-sh/uv) (modern and fast replacement for `pip`),
- Discord account with [developer portal](https://discord.com/developers/applications) enabled,
- [Mockoon](https://mockoon.com) to simulate API endpoints

## 🚀 Develop
1. Fork the repository and clone it locally with:
```sh
git clone https://github.com/your-user/RepulsBot.git
cd RepulsBot
```
2. Install dependencies with `uv`:
```sh
uv pip install -r pyproject.toml
```
3. Configure your environment:
    - Create a `.env` file in `src/` with:
    ```env
    DISCORD_TOKEN=your_bot_token
    API_ENDPOINT_URL=your_endpoint_addr
    API_TOKEN=none_for_dev
    ```
    - Change the IDs in `src/constants.py` for your test server, or join the official [test server](https://discord.gg/mkeUKZA2Am).
4. Develop new features, fix bugs!
5. Test the bot by launching it with:
```sh
cd src
uv main.py
```

## 🪲 Report a problem/suggest an idea
Open an issue specifying:
1. Expected vs. Observed Bot Behavior
2. Steps to reproduce the bug
3. Screenshot if relevant
4. Bot version (commit executed)

## ✅ Best practices
- **Naming**: `snake_case` for variables/files
- **Cogs**: Structure the code into modules (`/src/cogs/`)
- **Test** locally with [Mockoon](https://mockoon.com) for endpoints
- **Security**: Never commit tokens/secrets
- Open a **Pull Request** with:
  - Purpose of changes/bug fixed
  - Added commands and features/bug fixes
  - Remain the [Pull Request template](.github/PULL_REQUEST_TEMPLATE.md)

## 📜 License
All contributions are subject to the [MIT License](LICENSE.txt).
By participating, you agree to license your work under this license.

## 🔗 Useful resources
- [`discordpy` documentation](https://discordpy.readthedocs.io/)
- [UV Guide](https://github.com/astral-sh/uv)
- [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)
