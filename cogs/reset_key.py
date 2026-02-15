import disnake
from disnake.ext import commands
import aiohttp
import os  
from utils.encryption import decrypt_data
from utils.database import get_database_pool
import config

# This cog allows server owners to reset the usage count of a license key for a Payhip product.
class ResetKey(commands.Cog):

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.payhip_api_key = os.getenv("PAYHIP_API_KEY")  # Load Payhip API key from environment variables

    @commands.slash_command(
        description="Reset a product license key's usage count (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def reset_key(
        self,
        inter: disnake.ApplicationCommandInteraction,
        product_name: str,
        license_key: str,
    ):
        # This slash command resets the usage counter for a license key through Payhip.
        if inter.author.id != inter.guild.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can use this command.", ephemeral=True, delete_after=config.message_timeout
            )
            return
        
        # Get the encrypted product secret key from the database
        async with (await get_database_pool()).acquire() as conn:
            row = await conn.fetchrow(
                "SELECT product_secret FROM products WHERE guild_id = $1 AND product_name = $2",
                str(inter.guild.id), product_name
            )

            if not row:
                await inter.response.send_message(
                    f"❌ Product '{product_name}' not found.", ephemeral=True, delete_after=config.message_timeout
                )
                return

            product_secret_key = decrypt_data(row["product_secret"])
            
        # Prepare request to Payhip to reset license usage
        PAYHIP_RESET_USAGE_URL = "https://payhip.com/api/v2/license/decrease"
        headers = {
                    "product-secret-key": self.product_secret_key,
                    "Accept-Encoding": "gzip, deflate"
                }

        try:
            # Use aiohttp for async request instead of blocking requests
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    PAYHIP_RESET_USAGE_URL,
                    headers=headers,
                    data={"license_key": license_key.strip()},
                    timeout=10
                ) as response:
                    
                    if response.status == 200:
                        await inter.response.send_message(
                            f"✅ License key for '{product_name}' has been reset successfully.",
                            ephemeral=True, delete_after=config.message_timeout
                        )
                    else:
                        # Handle non-200 responses
                        await inter.response.send_message(
                            f"❌ Failed to reset the license key. Status code: {response.status}",
                            ephemeral=True, delete_after=config.message_timeout
                        )

        except aiohttp.ClientError:
            await inter.response.send_message(
                "❌ Unable to reset License.",
                ephemeral=True, delete_after=config.message_timeout
            )
            
# Registers the ResetKey cog with the bot.
def setup(bot: commands.InteractionBot):
    bot.add_cog(ResetKey(bot))