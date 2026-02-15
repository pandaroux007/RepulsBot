import datetime
import asqlite

class YouTubeStorage():
    def __init__(self, pool: asqlite.Pool):
        self._pool = pool

    async def init_tables(self) -> None:
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
                    days_forced INTEGER,
                    forced_until TEXT
                )
                """
            )
            await conn.execute(
                "INSERT OR IGNORE INTO forced_video(id, message_id, days_forced, forced_until) VALUES(1, NULL, NULL, NULL)"
            )
            await conn.commit()

    async def reset_table(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DROP TABLE posted_videos")
            await conn.execute("DROP TABLE forced_video")
            await conn.commit()
        await self.init_tables()

    # ---------------------------------- posted videos
    # https://stackoverflow.com/questions/12876177/how-to-create-a-singleton-tuple-with-only-one-element
    async def add_posted_video(self, video_id: str) -> bool:
        """
        Returns True if inserted (was new), False if it already existed.
        """
        try:
            async with self._pool.acquire() as conn:
                exists_cur = await conn.execute("SELECT 1 FROM posted_videos WHERE video_id = ?", (video_id,))
                if await exists_cur.fetchone():
                    return False
                await conn.execute("INSERT INTO posted_videos(video_id) VALUES(?)", (video_id,))
                await conn.commit()
                return True
        except Exception:
            return False

    async def purge_old_posted_videos(self, days: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM posted_videos WHERE DATETIME(posted_at) < DATETIME('now', '-' || ? || ' days')", (days,))
                await conn.commit()
                return True
        except Exception:
            return False

    # ---------------------------------- featured forced video
    async def set_forced_video(self, message_id: int, days: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE forced_video SET message_id = ?, days_forced = ?, forced_until = NULL WHERE id = 1",
                    (message_id, days)
                )
                await conn.commit()
                return True
        except Exception:
            return False
        
    async def activate_forced_video(self) -> bool:
        """
        Calculate forced_until based on days_forced when the video is actually sent.
        """
        try:
            async with self._pool.acquire() as conn:
                cur = await conn.execute("SELECT days_forced FROM forced_video WHERE id = 1")
                row = await cur.fetchone()
                if not row or not row[0]:
                    return False
                
                days = row[0]
                forced_until_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
                
                await conn.execute(
                    "UPDATE forced_video SET forced_until = ? WHERE id = 1",
                    (forced_until_dt.isoformat(),)
                )
                await conn.commit()
                return True
        except Exception:
            return False

    async def get_forced_video(self) -> tuple[int | None, datetime.datetime | None]:
        """
        Returns the message ID and forced_until datetime.
        """
        async with self._pool.acquire() as conn:
            cur = await conn.execute("SELECT message_id, forced_until FROM forced_video WHERE id = 1")
            row = await cur.fetchone()
            if not row:
                return None, None
        
            message_id, forced_until_str = row
            forced_until_dt = datetime.datetime.fromisoformat(forced_until_str) if forced_until_str else None
            
            if message_id and forced_until_dt:
                now = datetime.datetime.now(datetime.timezone.utc)
                if now >= forced_until_dt:
                    await self.clear_forced_video()
                    return None, None

            return message_id, forced_until_dt

    async def clear_forced_video(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE forced_video SET message_id = NULL, days_forced = NULL, forced_until = NULL WHERE id = 1")
                await conn.commit()
                return True
        except Exception:
            return False