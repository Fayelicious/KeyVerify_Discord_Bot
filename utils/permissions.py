import disnake
import config
import logging
from utils.database import get_role_ids_with_permission

logger = logging.getLogger(__name__)

# Canonical list of delegatable capabilities: (permission_key, human-readable label).
# Single source of truth shared by the authorization check and the /permissions menu —
# adding a new admin command means adding one line here and one is_authorized() call.
PERMISSIONS = [
    ("add_product",        "Add products"),
    ("edit_product",       "Edit products"),
    ("remove_product",     "Remove products"),
    ("list_products",      "List products"),
    ("reset_key",          "Reset license keys"),
    ("start_verification", "Post verification button"),
    ("set_log_channel",    "Set log channel"),
    ("remove_user",        "Remove users"),
    ("send_feedback",      "Send feedback to the developer"),
]

# Fast key -> label lookup for building confirmation messages.
PERMISSION_LABELS = dict(PERMISSIONS)


async def _deny(inter, message):
    # Centralised denial so every command reports refusals identically.
    await inter.response.send_message(
        message, ephemeral=True, delete_after=config.message_timeout
    )


async def is_authorized(inter: disnake.ApplicationCommandInteraction, permission_key: str) -> bool:
    """
    Gate an admin command behind the per-guild permission system.

    Returns True if the caller may run the command. On denial it sends an ephemeral
    message and returns False, so a command can simply do:

        if not await is_authorized(inter, "add_product"):
            return

    Authorization rules:
      - Commands are guild-only; in DMs `inter.guild` is None  -> denied (this is what
        previously crashed with 'NoneType has no attribute owner_id').
      - The server owner always passes.
      - Everyone else must hold a role the owner granted this specific permission.
    """
    if inter.guild is None:
        await _deny(inter, "❌ This command can only be used inside a server.")
        return False

    if inter.author.id == inter.guild.owner_id:
        return True

    granted_role_ids = await get_role_ids_with_permission(str(inter.guild.id), permission_key)
    if granted_role_ids and any(str(role.id) in granted_role_ids for role in inter.author.roles):
        return True

    await _deny(inter, "❌ You don't have permission to use this command.")
    return False
