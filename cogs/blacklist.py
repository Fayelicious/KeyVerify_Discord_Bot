import disnake
from disnake.ext import commands
import aiohttp
from utils.database import get_database_pool
from utils.encryption import decrypt_data
import os
import config
import logging

logger = logging.getLogger(__name__)


class RemoveUser(commands.Cog):
    """Handles removing a user and deactivating their licenses."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.payhip_api_key = os.getenv("PAYHIP_API_KEY")
        if not self.payhip_api_key:
            raise ValueError("PAYHIP_API_KEY is not defined in environment variables.")

    @commands.slash_command(
        description="Remove a user from the database and deactivate their licenses (server owner only).",
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
                SELECT verified_licenses.product_name, verified_licenses.license_key,
                       products.product_secret, products.role_id
                FROM verified_licenses
                JOIN products ON verified_licenses.product_name = products.product_name
                    AND verified_licenses.guild_id = products.guild_id
                WHERE verified_licenses.user_id = $1 AND verified_licenses.guild_id = $2
                """,
                str(user.id), str(inter.guild.id)
            )

            if not rows:
                await inter.followup.send(
                    f"⚠️ No licenses found for user `{user}` in this server.",
                    ephemeral=True,
                )
                return

            deactivated_licenses = []
            failed_licenses = []

            async with aiohttp.ClientSession() as session:
                for row in rows:
                    product_name = row["product_name"]
                    license_key = decrypt_data(row["license_key"])
                    product_secret = decrypt_data(row["product_secret"])

                    try:
                        PAYHIP_DISABLE_LICENSE_URL = "https://payhip.com/api/v2/license/disable"
                        headers = {
                            "product-secret-key": product_secret,
                            "payhip-api-key": self.payhip_api_key,
                            "Accept-Encoding": "gzip, deflate"
                        }
                        async with session.put(
                            PAYHIP_DISABLE_LICENSE_URL,
                            headers=headers,
                            data={"license_key": license_key},
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                deactivated_licenses.append(product_name)
                            else:
                                failed_licenses.append(product_name)
                    except aiohttp.ClientError:
                        failed_licenses.append(product_name)

            await conn.execute(
                "DELETE FROM verified_licenses WHERE user_id = $1 AND guild_id = $2",
                str(user.id), str(inter.guild.id)
            )

        # Remove Discord roles associated with their verified products
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

        message = ""
        if deactivated_licenses:
            message += f"✅ User `{user}` removed. Licenses deactivated: {', '.join(deactivated_licenses)}.\n"
        if failed_licenses:
            message += f"⚠️ Failed to deactivate: {', '.join(failed_licenses)}. Please check manually.\n"
        if roles_removed:
            message += f"🔒 Roles removed: {', '.join(r.name for r in roles_removed)}"

        logger.info(f"[User Removed] {user} removed from '{inter.guild.name}' by {inter.author}.")
        await inter.followup.send(message, ephemeral=True)


def setup(bot: commands.InteractionBot):
    bot.add_cog(RemoveUser(bot))
