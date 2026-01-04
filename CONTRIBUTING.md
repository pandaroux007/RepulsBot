# Contribute to RepulsBot
Thank you for your interest in contributing to the official [repuls.io](https://repuls.io) bot!
This guide will help you participate effectively in development.

## Report a problem/suggest an idea
Open an issue specifying:
1. Expected vs. Observed Bot Behavior
2. Steps to reproduce the bug
3. Screenshot if relevant
4. Bot version (commit executed)

# Development
## License
All contributions are subject to the [MIT License](LICENSE.txt).
**By participating, you agree to license your work under this license.**

## Prerequisites
- Python 3.12+ (dependencies in [pyproject.toml](pyproject.toml))
- [UV](https://docs.astral.sh/uv/getting-started/installation/) (modern and fast replacement for `pip`),
- Discord account with [developer portal](https://discord.com/developers/applications) enabled,
- [Mockoon](https://mockoon.com) to simulate API endpoints

## Fork and code
1. Fork the repository and clone it locally with:
```sh
git clone https://github.com/pandaroux007/RepulsBot.git
cd RepulsBot
```
2. Install dependencies with `uv`:
The required modules will be installed automatically with `uv run main.py`.
```sh
uv venv
```
3. Configure your environment:
    - Create a `.env` file in `src/data` with:
    ```env
    DISCORD_TOKEN=your_bot_token
    API_ENDPOINT_URL=http://localhost:3001/setvideo # set on the route created in Mockoon
    API_TOKEN=useless_for_dev
    ENV=dev # on prod by default (official server IDs), dev allows to use (your) development IDs

    YOUTUBE_KEY1=your_api_key_1
    YOUTUBE_KEY2=your_api_key_2
    YOUTUBE_KEY3=your_api_key_3
    ```
    - Change all the IDs in `src/data/constants.py`
4. Develop new features, fix bugs!
5. Test the bot by launching it with:
```sh
cd src
uv run main.py
```

## Best practices
- **Naming**: `snake_case` for variables/files
- **Cogs**: Structure the code into modules (`/src/cogs/`)
- **Test** Locally with [Mockoon](https://mockoon.com) for endpoints
- **Security**: Store the secret data (token, endpoint) in the .env file
- Use **RUFF linter**
- Open a **Pull Request** with:
  - Purpose of changes/bug fixed
  - Added commands and features/bug fixes
  - Remain the [Pull Request template](.github/PULL_REQUEST_TEMPLATE.md)

### How to update `discord.py`
```
uv lock --upgrade-package discord.py
uv sync
```