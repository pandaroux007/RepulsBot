"""
Task to automatically retrieve videos about repuls.io from YouTube
➜ Special thanks to aman for his initial code

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import aiohttp
from discord.ext import (
    tasks,
    commands
)

from datetime import (
    datetime,
    timedelta,
    timezone
)
# bot files
from data.cogs import CogsNames
from data.constants import (
    PrivateData,
    IDs
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

CHECK_INTERVAL_HOURS = 1
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
# https://developers.google.com/youtube/v3/docs/search/list#q
SEARCH_QUERY = "repuls.io"

# must be equal to or greater than the publishedAfter parameter of the request!
MAX_POSTED_RETENTION_DAYS = 2

class YTAutoCog(commands.Cog, name=CogsNames.YT_AUTO):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    def cog_load(self):
        self.youtube_task.start()

    def cog_unload(self):
        self.youtube_task.cancel()

    # ---------------------------------- task
    @tasks.loop(hours=CHECK_INTERVAL_HOURS)
    async def youtube_task(self):
        try:
            await self.bot.youtube_storage.purge_old_posted_videos(MAX_POSTED_RETENTION_DAYS)
        except Exception:
            pass

        new_videos = await self.fetch_new_videos()
        if not new_videos:
            return

        target = self.bot.get_channel(IDs.serverChannel.SHARED_VIDEO)
        for vid in new_videos:
            await target.send(f"https://youtu.be/{vid}")

    async def fetch_new_videos(self):
        """
        Original creator: amanlovescat
        Modifications for production: pandaroux007
        """
        async with aiohttp.ClientSession() as session:
            for key in getattr(PrivateData, "YOUTUBE_KEYS", []):
                if not key:
                    continue

                one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                params = {
                    "key": key,
                    "part": "snippet",
                    "q": SEARCH_QUERY,
                    "type": "video",
                    "order": "date",
                    "publishedAfter": one_day_ago,
                    "maxResults": 10
                }

                try:
                    async with session.get(YOUTUBE_SEARCH_URL, params=params) as r:
                        data = await r.json()
                        if "error" in data:
                            continue
                        new_vids = []
                        for video in data.get("items", []):
                            id = video.get("id", {}).get("videoId")
                            if not id:
                                continue
                            try:
                                inserted = await self.bot.youtube_storage.add_posted_video(id)
                            except Exception:
                                inserted = False
                            if inserted:
                                new_vids.append(id)
                        return new_vids
                except Exception:
                    continue

        return []

    # ---------------------------------- initialization
    @youtube_task.before_loop
    async def before_youtube_task(self):
        await self.bot.wait_until_ready()
        try:
            await self.bot.youtube_storage.purge_old_posted_videos(MAX_POSTED_RETENTION_DAYS)
        except Exception:
            pass

async def setup(bot: "RepulsBot"):
    await bot.add_cog(YTAutoCog(bot))