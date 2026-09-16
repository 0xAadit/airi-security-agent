import os
import asyncpg

_pool: asyncpg.Pool | None = None
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://appuser:apppass@localhost:5432/appdb",
)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Schema
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         SERIAL PRIMARY KEY,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                email      TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                status      TEXT NOT NULL DEFAULT 'open',
                priority    TEXT NOT NULL DEFAULT 'medium',
                owner_id    INTEGER REFERENCES users(id),
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id         SERIAL PRIMARY KEY,
                item_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                author_id  INTEGER NOT NULL REFERENCES users(id),
                body       TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id   SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS item_tags (
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                tag_id  INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (item_id, tag_id)
            )
        """)

        # Seed Users
        await conn.execute("""
            INSERT INTO users (username, password, email)
            VALUES 
                ('admin', 'secret123', 'admin@example.com'),
                ('alice', 'pass-alice', 'alice@example.com'),
                ('bob', 'pass-bob', 'bob@example.com')
            ON CONFLICT DO NOTHING
        """)

        # Seed Items (only if empty to avoid duplicates on restart)
        row = await conn.fetchrow("SELECT COUNT(*) FROM items")
        if row[0] == 0:
            await conn.execute("""
                INSERT INTO items (name, description, status, priority, owner_id)
                VALUES
                    ('Fix login timeout', 'Users report timeouts during peak hours', 'in_progress', 'high', 1),
                    ('Update documentation', 'Add API v2 docs', 'open', 'medium', 2),
                    ('Refactor database', 'Move to asyncpg', 'closed', 'low', 1),
                    ('Design new dashboard', 'Mockups for Q3', 'open', 'medium', 3),
                    ('Fix search bug', 'Search fails on special characters', 'in_progress', 'high', 2),
                    ('Deploy to staging', 'Release v1.4.0 to staging', 'open', 'high', 3)
            """)

            # Seed Tags
            await conn.execute("""
                INSERT INTO tags (name)
                VALUES ('bug'), ('feature'), ('docs'), ('urgent')
                ON CONFLICT DO NOTHING
            """)

            # Seed Comments & Item Tags (assuming sequential IDs starting at 1)
            await conn.execute("""
                INSERT INTO comments (item_id, author_id, body)
                VALUES 
                    (1, 2, 'I am looking into the connection pool limits.'),
                    (1, 3, 'Can you check the AWS logs too?'),
                    (2, 1, 'We should use Swagger for this.'),
                    (5, 1, 'This is a critical security issue.')
            """)

            await conn.execute("""
                INSERT INTO item_tags (item_id, tag_id)
                VALUES 
                    (1, 1), (1, 4), -- Fix login: bug, urgent
                    (2, 3),         -- Docs: docs
                    (4, 2),         -- Dashboard: feature
                    (5, 1), (5, 4)  -- Search bug: bug, urgent
            """)
