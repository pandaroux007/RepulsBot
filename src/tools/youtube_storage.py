import datetime
# bot files
from tools.utils import BaseStorage
from data.constants import DEFAULT_DB_DIR

VIDEO_DB_PATH = DEFAULT_DB_DIR / "youtube.db"

class YouTubeStorage(BaseStorage):
    def __init__(self):
        super().__init__(VIDEO_DB_PATH)

    async def init(self) -> None:
        await super().init()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_videos (
                    video_id TEXT PRIMARY KEY NOT NULL,
                    posted_at TEXT NOT NULL DEFAULT (DATETIME(CURRENT_TIMESTAMP))
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS forced_video (
                    id INTEGER PRIMARY KEY NOT NULL CHECK (id = 1),
                    message_id INTEGER,
                    forced_until TEXT
                )
                """
            )
            await conn.execute(
                "INSERT OR IGNORE INTO forced_video(id, message_id, forced_until) VALUES(1, NULL, NULL)"
            )
            await conn.commit()

    # ---------------------------------- posted videos
    # https://stackoverflow.com/questions/12876177/how-to-create-a-singleton-tuple-with-only-one-element
    async def add_posted_video(self, video_id: str) -> bool:
        """
        Returns True if inserted (was new), False if it already existed.
        """
        await self._check_init()
        async with self._pool.acquire() as conn:
            exists_cur = await conn.execute("SELECT 1 FROM posted_videos WHERE video_id = ?", (video_id,))
            if await exists_cur.fetchone():
                return False
            try:
                await conn.execute("INSERT INTO posted_videos(video_id) VALUES(?)", (video_id,))
                await conn.commit()
                return True
            except Exception:
                return False

    async def purge_old_posted_videos(self, days: int) -> bool:
        """
        Delete posted_videos older than `days`.
        Returns number of deleted rows
        """
        await self._check_init()
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM posted_videos WHERE DATETIME(posted_at) < DATETIME('now', '-' || ? || ' days')", (days,))
                await conn.commit()
                return True
        except Exception:
            return False

    # ---------------------------------- featured forced video
    async def set_forced_video(self, message_id: int, forced_until: str) -> bool:
        await self._check_init()
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE forced_video SET message_id = ?, forced_until = ? WHERE id = 1",
                    (message_id, forced_until)
                )
                await conn.commit()
                return True
        except Exception:
            return False

    async def get_forced_video(self) -> int | None:
        """
        Returns the message ID containing the link to the forced video, and a datetime object
        containing the deadline beyond which the video is no longer forced to feature (the normal system takes over).
        """
        await self._check_init()
        async with self._pool.acquire() as conn:
            cur = await conn.execute("SELECT message_id, forced_until FROM forced_video WHERE id = 1")
            row = await cur.fetchone()
            if not row:
                return None
        
            message_id, forced_until_str = row
            forced_until_dt = datetime.datetime.fromisoformat(forced_until_str) if forced_until_str else None

            if message_id and forced_until_dt:
                now = datetime.datetime.now(datetime.timezone.utc)
                if now >= forced_until_dt:
                    await self.clear_forced_video()
                    return None

            return message_id

    async def clear_forced_video(self) -> bool:
        await self._check_init()
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE forced_video SET message_id = NULL, forced_until = NULL WHERE id = 1")
                await conn.commit()
                return True
        except Exception:
            return False