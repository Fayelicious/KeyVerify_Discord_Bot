import asyncpg
import logging
from utils.encryption import decrypt_data, reencrypt_if_needed
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
database_pool = None

logger = logging.getLogger(__name__)


async def initialize_database():
    global database_pool
    database_pool = await asyncpg.create_pool(DATABASE_URL)
    async with database_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            guild_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_secret TEXT NOT NULL,
            role_id TEXT,
            PRIMARY KEY (guild_id, product_name)
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS verification_message (
            guild_id TEXT NOT NULL PRIMARY KEY,
            message_id TEXT,
            channel_id TEXT
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS verified_licenses (
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            verified_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (user_id, guild_id, product_name)
        )
        """)
        await conn.execute("""
        ALTER TABLE verified_licenses ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ DEFAULT NOW()
        """)
        await conn.execute("""
        ALTER TABLE verified_licenses DROP COLUMN IF EXISTS license_key
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_guilds (
            guild_id TEXT PRIMARY KEY,
            reason   TEXT,
            added_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)

    logger.info("Database initialized.")


async def get_setting(key: str, default: str = "") -> str:
    async with (await get_database_pool()).acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM bot_settings WHERE key = $1", key)
    return row["value"] if row else default


async def set_setting(key: str, value: str):
    async with (await get_database_pool()).acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_settings (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = $2
        """, key, value)


async def get_database_pool():
    if database_pool is None:
        raise ValueError("Database not initialized. Call `initialize_database` first.")
    return database_pool


async def fetch_products(guild_id):
    async with (await get_database_pool()).acquire() as conn:
        rows = await conn.fetch(
            "SELECT product_name, product_secret FROM products WHERE guild_id = $1", guild_id
        )
        return {row["product_name"]: decrypt_data(row["product_secret"]) for row in rows}


async def save_verified_license(user_id, guild_id, product_name):
    async with (await get_database_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO verified_licenses (user_id, guild_id, product_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, guild_id, product_name)
            DO NOTHING
            """,
            str(user_id), str(guild_id), product_name
        )


async def get_verified_license(user_id, guild_id, product_name) -> bool:
    async with (await get_database_pool()).acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 1 FROM verified_licenses
            WHERE user_id = $1 AND guild_id = $2 AND product_name = $3
            """,
            str(user_id), str(guild_id), product_name
        )
        return row is not None


async def run_auto_rotation():
    logger.info("Checking for data validation and key rotation...")

    pool = await get_database_pool()
    rotated_count = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT guild_id, product_name, product_secret FROM products")
        for row in rows:
            original_secret = row["product_secret"]
            new_secret = reencrypt_if_needed(original_secret)
            if original_secret != new_secret:
                await conn.execute(
                    "UPDATE products SET product_secret = $1 WHERE guild_id = $2 AND product_name = $3",
                    new_secret, row["guild_id"], row["product_name"]
                )
                rotated_count += 1

    if rotated_count > 0:
        logger.info(f"SECURITY ROTATION: Re-encrypted {rotated_count} records with the new key.")
    else:
        logger.info("Database is already fully encrypted with the latest key.")
