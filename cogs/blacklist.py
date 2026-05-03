import disnake
from disnake.ext import commands
from utils.database import get_database_pool
import config
import logging

logger = logging.getLogger(__name__)


class RemoveUser(commands.Cog):

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        description="Remove a user's verification records and roles (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def remove_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member
    ):
        if inter.author.id != inter.guild.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can use this command.",
                ephemeral=True,
                delete_after=config.message_timeout
            )
            return

        await inter.response.defer(ephemeral=True)

        async with (await get_database_pool()).acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT verified_licenses.product_name, products.role_id
                FROM verified_licenses
                JOIN products ON verified_licenses.product_name = products.product_name
                    AND verified_licenses.guild_id = products.guild_id
                WHERE verified_licenses.user_id = $1 AND verified_licenses.guild_id = $2
                """,
                str(user.id), str(inter.guild.id)
            )

            if not rows:
                await inter.followup.send(
                    f"⚠️ No records found for `{user}` in this server.",
                    ephemeral=True,
                )
                return

            await conn.execute(
                "DELETE FROM verified_licenses WHERE user_id = $1 AND guild_id = $2",
                str(user.id), str(inter.guild.id)
            )

        roles_removed = []
        for row in rows:
            if row["role_id"]:
                role = inter.guild.get_role(int(row["role_id"]))
                if role and role in user.roles:
                    roles_removed.append(role)

        if roles_removed:
            try:
                await user.remove_roles(*roles_removed, reason="KeyVerify: user removed by server owner")
            except disnake.Forbidden:
                logger.warning(f"[Permission Error] Could not remove roles from {user} in '{inter.guild.name}'")

        products_removed = [row["product_name"] for row in rows]
        message = f"✅ `{user}` removed. Records cleared for: {', '.join(products_removed)}."
        if roles_removed:
            message += f"\n🔒 Roles removed: {', '.join(r.name for r in roles_removed)}"
        message += "\n\nTo disable their license on Payhip, do so from your Payhip dashboard."

        logger.info(f"[User Removed] {user} removed from '{inter.guild.name}' by {inter.author}.")
        await inter.followup.send(message, ephemeral=True)


def setup(bot: commands.InteractionBot):
    bot.add_cog(RemoveUser(bot))
