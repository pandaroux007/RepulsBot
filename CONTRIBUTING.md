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
    ENV=dev # on prod by default (official server IDs), dev allows to use (your) development IDs
    DISCORD_TOKEN=your_bot_token
    VIDEO_ENDPOINT_URL=http://localhost:3001/setvideo # set on the route created in Mockoon
    VIDEO_ENDPOINT_TOKEN=useless_for_dev

    PLAYFAB_USERNAME=repuls_account_username
    PLAYFAB_PASSWORD=repuls_account_password

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

## Best Practices
- **Development**:
  - Use `snake_case` notation for variables and files.
  - Structure your code into modules (`/src/cogs/`) and adhere to the established directory structure.
  - Use the static analysis tool RUFF.

- **Test before submitting**
  - Use [Mockoon](https://mockoon.com) for endpoints (video system, game interaction, or anything else).
  - Verify the integrity of the database after adding your features/fixes. *This database powers several critical bot systems and must not contain erroneous data or record leaks.*

- **Submitting pull requests**
  - Use the [Pull Request template](.github/PULL_REQUEST_TEMPLATE.md) and provide the requested information.
  - Store secret data (tokens, endpoints, etc.) in the `.env` file.
> [!IMPORTANT]
> During review, **any contribution containing unmasked sensitive information will be systematically rejected** (*this demonstrates a lack of rigor on the part of the developer*).

### How to update `discord.py`
```
uv lock --upgrade-package discord.py
uv sync
```