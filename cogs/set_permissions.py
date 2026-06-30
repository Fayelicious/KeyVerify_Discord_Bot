import disnake
from disnake.ext import commands
import config
import logging
from utils.database import get_role_permissions, set_role_permissions
from utils.permissions import PERMISSIONS, PERMISSION_LABELS

logger = logging.getLogger(__name__)


class PermissionSelect(disnake.ui.StringSelect):
    # Multi-select checklist of every capability, pre-ticked with the role's current grants.
    def __init__(self, role: disnake.Role, current: set):
        self.role = role
        options = [
            disnake.SelectOption(label=label, value=key, default=key in current)
            for key, label in PERMISSIONS
        ]
        super().__init__(
            placeholder="Select what this role can do…",
            min_values=0,                 # allow clearing every permission
            max_values=len(options),
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        # The submitted selection is the role's complete, replacing permission set.
        selected = set(self.values)
        await set_role_permissions(str(inter.guild.id), str(self.role.id), selected)

        if selected:
            granted = ", ".join(PERMISSION_LABELS[key] for key in selected)
            summary = f"✅ {self.role.mention} can now: {granted}."
        else:
            summary = f"✅ {self.role.mention} now has no bot permissions."

        # Swap the menu for a confirmation so it can't be re-submitted by accident.
        await inter.response.edit_message(content=summary, view=None)
        logger.info(
            f"[Permissions] {inter.author} set {len(selected)} permission(s) "
            f"for role '{self.role.name}' in '{inter.guild.name}'."
        )


class PermissionView(disnake.ui.View):
    # Only the owner who opened the menu may interact with it.
    def __init__(self, owner_id: int, role: disnake.Role, current: set):
        super().__init__(timeout=config.message_timeout)
        self.owner_id = owner_id
        self.add_item(PermissionSelect(role, current))

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can change permissions.",
                ephemeral=True,
                delete_after=config.message_timeout,
            )
            return False
        return True


class SetPermissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description="Choose which KeyVerify commands a role can use (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def permissions(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
    ):
        # Permission management is never delegatable — hard owner-only, guild-only.
        if inter.guild is None or inter.author.id != inter.guild.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can manage permissions.",
                ephemeral=True,
                delete_after=config.message_timeout,
            )
            return

        # @everyone would grant the whole server access — never allowed.
        if role.is_default():
            await inter.response.send_message(
                "❌ You can't assign permissions to @everyone.",
                ephemeral=True,
                delete_after=config.message_timeout,
            )
            return

        current = await get_role_permissions(str(inter.guild.id), str(role.id))
        await inter.response.send_message(
            content=f"Select what {role.mention} is allowed to do — the menu saves automatically:",
            view=PermissionView(inter.author.id, role, current),
            ephemeral=True,
        )


def setup(bot):
    bot.add_cog(SetPermissions(bot))
