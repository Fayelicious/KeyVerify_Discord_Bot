import disnake
from disnake.ext import commands
import config

# Help command providing a full overview of KeyVerify's capabilities (server owner only).
class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="help",
        description="Displays information about what the KeyVerify bot can do (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        # Restrict usage to the server owner
        if inter.author.id != inter.guild.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can use this command.",
                ephemeral=True,
                delete_after=config.message_timeout
            )
            return

        embed = disnake.Embed(
            title="🔑 Welcome to KeyVerify",
            description=(
                "KeyVerify helps you manage Payhip license verification and role assignment.\n\n"
                "Here's what you can do:"
            ),
            color=disnake.Color.blurple()
        )

        embed.add_field(
            name="🛠️ Verification",
            value="/start_verification — Post or update the verification message",
            inline=False
        )

        embed.add_field(
            name="🎁 Product Management",
            value=(
                "/add_product — Add a product with role assignment\n"
                "/edit_product — Rename a product or change its assigned role\n"
                "/list_products — View all added products\n"
                "/remove_product — Delete a product from the server"
            ),
            inline=False
        )

        embed.add_field(
            name="🔁 License Actions",
            value=(
                "/reset_key — Reset usage for a license key\n"
                "/remove_user — Revoke a user's access and remove all their verification records"
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Utility",
            value="/set_lchannel — Set a channel for verification log messages",
            inline=False
        )

        embed.add_field(
            name="🛡️ Security & Features",
            value=(
                "• Secure encrypted storage for license data\n"
                "• Role reassignment for rejoining users\n"
                "• Cooldown protection to prevent abuse\n"
                "• Activity logs and optional logging channel"
            ),
            inline=False
        )
        embed.add_field(
            name="Need support?",
            value="[Click here to join the support server](https://discord.com/oauth2/authorize?client_id=1314098590951673927&integration_type=0&permissions=268446720&redirect_uri=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1314098590951673927&response_type=code&scope=guilds.join+bot)",
            inline=False
        )
        await inter.response.send_message(embed=embed, ephemeral=True, delete_after=config.message_timeout)

def setup(bot):
    bot.add_cog(HelpCommand(bot))
