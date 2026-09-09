import aiosqlite
import json
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = "travel_bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Initialise les tables de la base de données."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    star_count INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    payload TEXT UNIQUE NOT NULL,
                    channel_id TEXT,
                    channel_msg_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    buyer_id INTEGER NOT NULL,
                    buyer_username TEXT,
                    star_count INTEGER NOT NULL,
                    payload TEXT,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id)
                )
            """)
            await db.commit()

    async def register_user(self, user_id: int, username: Optional[str], first_name: Optional[str]):
        """Enregistre ou met à jour un abonné qui interagit avec le bot."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO subscribers (user_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
            """, (user_id, username, first_name))
            await db.commit()

    async def get_all_subscribers(self) -> List[int]:
        """Récupère la liste de tous les identifiants d'abonnés."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM subscribers") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def create_post(
        self,
        title: str,
        description: str,
        star_count: int,
        media_type: str,
        file_id: str,
        payload: str,
        channel_id: Optional[str] = None,
        channel_msg_id: Optional[int] = None
    ) -> int:
        """Enregistre une nouvelle photo/vidéo mise en vente."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO posts (title, description, star_count, media_type, file_id, payload, channel_id, channel_msg_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, star_count, media_type, file_id, payload, channel_id, channel_msg_id))
            await db.commit()
            return cursor.lastrowid

    async def update_post_channel_info(self, post_id: int, channel_id: str, channel_msg_id: int):
        """Met à jour l'identifiant du message publié dans un canal."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE posts
                SET channel_id = ?, channel_msg_id = ?
                WHERE id = ?
            """, (channel_id, channel_msg_id, post_id))
            await db.commit()

    async def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un post par son identifiant numérique."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_post_by_payload(self, payload: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un post par son payload unique."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM posts WHERE payload = ?", (payload,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_recent_posts(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère la liste des photos publiées les plus récentes."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT p.*, COUNT(s.id) as sales_count, COALESCE(SUM(s.star_count), 0) as total_earned
                FROM posts p
                LEFT JOIN sales s ON p.id = s.post_id
                GROUP BY p.id
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def count_posts(self) -> int:
        """Nombre total de photos mises en vente."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM posts") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def delete_post(self, post_id: int) -> bool:
        """Supprime un média et son historique associé."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM sales WHERE post_id = ?", (post_id,))
            cursor = await db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def record_sale(
        self,
        post_id: Optional[int],
        buyer_id: int,
        buyer_username: Optional[str],
        star_count: int,
        payload: Optional[str]
    ) -> int:
        """Enregistre un achat réussi d'une photo contre des étoiles."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO sales (post_id, buyer_id, buyer_username, star_count, payload)
                VALUES (?, ?, ?, ?, ?)
            """, (post_id, buyer_id, buyer_username, star_count, payload))
            await db.commit()
            return cursor.lastrowid

    async def has_user_purchased(self, user_id: int, post_id: int) -> bool:
        """Vérifie si un utilisateur a déjà acheté cette photo."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM sales WHERE buyer_id = ? AND post_id = ? LIMIT 1
            """, (user_id, post_id)) as cursor:
                row = await cursor.fetchone()
                return row is not None

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales (étoiles, ventes, abonnés, etc.)."""
        async with aiosqlite.connect(self.db_path) as db:
            # Total étoiles et ventes
            async with db.execute("""
                SELECT COUNT(*), COALESCE(SUM(star_count), 0) FROM sales
            """) as cursor:
                sales_count, total_stars = await cursor.fetchone()

            # Total posts
            async with db.execute("SELECT COUNT(*) FROM posts") as cursor:
                posts_count = (await cursor.fetchone())[0]

            # Total abonnés
            async with db.execute("SELECT COUNT(*) FROM subscribers") as cursor:
                subscribers_count = (await cursor.fetchone())[0]

            # Top 5 photos les plus vendues
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT p.title, COUNT(s.id) as sales_count, COALESCE(SUM(s.star_count), 0) as stars
                FROM posts p
                JOIN sales s ON p.id = s.post_id
                GROUP BY p.id
                ORDER BY sales_count DESC, stars DESC
                LIMIT 5
            """) as cursor:
                top_posts = [dict(row) for row in await cursor.fetchall()]

            return {
                "sales_count": sales_count,
                "total_stars": total_stars,
                "posts_count": posts_count,
                "subscribers_count": subscribers_count,
                "top_posts": top_posts,
            }
