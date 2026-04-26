import asyncio
import warnings
import disnake
from disnake.ext import commands
import os
import logging
from dotenv import load_dotenv
from utils.database import initialize_database, get_database_pool, fetch_products, run_auto_rotation
from utils.logging_config import setup_logging
from handlers.verification_handler import VerificationButton
import config

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

# Disnake creates this coroutine internally during shutdown but never awaits it — harmless.
warnings.filterwarnings("ignore", message="coroutine 'AsyncWebhookAdapter.request' was never awaited")

intents = disnake.Intents.default()
intents.guilds = True
command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.InteractionBot(
    intents=intents,
    command_sync_flags=command_sync_flags,
)

# Signals that the database is ready so on_ready doesn't race ahead of on_connect
_db_ready = asyncio.Event()

COG_DIR = "cogs"
for filename in os.listdir(COG_DIR):
    if filename.endswith(".py") and not filename.startswith("__"):
        bot.load_extension(f"{COG_DIR}.{filename[:-3]}")


@bot.event
async def on_connect():
    logger.info("Connected to Discord. Initializing database...")
    await initialize_database()
    await run_auto_rotation()
    _db_ready.set()


@bot.event
async def on_ready():
    await _db_ready.wait()
    logger.info(f"Bot is online as {bot.user}!")
    version = config.version
    activity = disnake.Game(name=f"/help | {version}")
    await bot.change_presence(activity=activity)

    async with (await get_database_pool()).acquire() as conn:
        rows = await conn.fetch("SELECT guild_id, message_id, channel_id FROM verification_message")
        for row in rows:
            guild_id, message_id, channel_id = row["guild_id"], row["message_id"], row["channel_id"]

            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel = guild.get_channel(int(channel_id))
            if not channel:
                await conn.execute("DELETE FROM verification_message WHERE guild_id = $1", guild_id)
                continue

            products = await fetch_products(guild_id)
            if not products:
                continue

            view = VerificationButton(guild_id)
            bot.add_view(view, message_id=int(message_id))
            logger.info(f"Verification message loaded for guild {guild_id}.")


@bot.event
async def on_close():
    logger.info("Bot is shutting down...")
    try:
        pool = await get_database_pool()
        await pool.close()
        logger.info("Database connection closed.")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


def run():
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run()
