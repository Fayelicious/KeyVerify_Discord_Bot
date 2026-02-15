import disnake
import config
import logging

# Set up the logger for this file
logger = logging.getLogger(__name__)

async def safe_followup(inter, content=None, **kwargs):
    """
    Attempts to send a followup message. If it fails, it tries to notify the user.
    Errors are logged instead of silenced.
    """
    try:
        await inter.followup.send(content, **kwargs)
    
    except disnake.Forbidden:
        # 1. Main action failed because bot lacks permissions
        logger.warning(f"[Permission Error] Could not send followup in channel {inter.channel_id} (Guild: {inter.guild_id}). Missing permissions.")
        try:
            # Try to tell the user we lack permissions
            await inter.send("❌ I can’t speak here. Please check my permissions!", ephemeral=True, delete_after=config.message_timeout)
        except Exception as e:
            # 2. Fallback failed (Critical: We can't even tell the user we are broken)
            logger.error(f"[Fallback Failed] Could not send 'Permission Error' message to user: {e}")

    except disnake.NotFound:
        # Interaction expired (took longer than 15 minutes or 3 seconds without defer)
        logger.warning(f"[Interaction Not Found] Token expired or invalid for user {inter.author.id}.")
        try:
            await inter.send("❌ This interaction seems broken... try again.", ephemeral=True, delete_after=config.message_timeout)
        except Exception as e:
            logger.error(f"[Fallback Failed] Could not send 'Interaction Expired' message: {e}")

    except disnake.HTTPException as e:
        # Generic API error (Bad Request, discord server issues, etc.)
        logger.error(f"[HTTP Error] Failed to send followup: {e}")
        try:
            await inter.send(f"❌ Something went wrong: {e}", ephemeral=True, delete_after=config.message_timeout)
        except Exception as sub_e:
            logger.error(f"[Fallback Failed] Could not send error details to user: {sub_e}")