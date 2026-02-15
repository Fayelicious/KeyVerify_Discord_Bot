import disnake
import aiohttp
from utils.database import get_database_pool, save_verified_license
from utils.validation import validate_license_key
import config
import logging

logger = logging.getLogger(__name__)

# This modal is shown to users when they select a product to verify.
# It prompts them to enter a license key, validates it via Payhip, and assigns the appropriate role if valid.
class VerifyLicenseModal(disnake.ui.Modal):
    def __init__(self, product_name, product_secret_key):
        self.product_name = product_name
        self.product_secret_key = product_secret_key

        # --- FIX: Truncate Title for Discord Limit (45 chars) ---
        # "Verify " takes 7 characters, leaving 38 for the name.
        display_name = product_name
        if len(display_name) > 38:
            # Cut to 35 chars and add "..." to fit safely
            display_name = display_name[:35] + "..."

        components = [
            disnake.ui.TextInput(
                label="License Key",
                custom_id="license_key",
                placeholder="Enter your license key",
                style=disnake.TextInputStyle.short,
                max_length=50,
            )
        ]
        # Use 'display_name' for the UI title, but 'self.product_name' for logic
        super().__init__(title=f"Verify {display_name}", custom_id="verify_license_modal", components=components)
        
    # Handles what happens after the user submits the modal.
    # It checks the license with Payhip, assigns a role, and logs the action if everything is valid.
    async def callback(self, interaction: disnake.ModalInteraction):
        license_key = interaction.text_values["license_key"].strip()

        # Validate license key format
        try:
            validate_license_key(license_key)
        except ValueError as e:
            logger.warning(f"[Validation Failed] {interaction.user} provided invalid key in '{interaction.guild.name}': {str(e)}")
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True, delete_after=config.message_timeout)
            return

        PAYHIP_VERIFY_URL = f"https://payhip.com/api/v2/license/verify?license_key={license_key}"
        PAYHIP_INCREMENT_USAGE_URL = "https://payhip.com/api/v2/license/usage"

        headers = {
                    "product-secret-key": self.product_secret_key,
                    "Accept-Encoding": "gzip, deflate"
                }

        try:
            # Verify license key with Payhip
            # We use aiohttp ClientSession here to prevent blocking the bot
            async with aiohttp.ClientSession() as session:
                async with session.get(PAYHIP_VERIFY_URL, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        # Emulate raise_for_status() behavior
                        await interaction.response.send_message("❌ Failed to verify license with server.", ephemeral=True, delete_after=config.message_timeout)
                        return
                    
                    full_response = await response.json()
                    data = full_response.get("data")

                if not data or not data.get("enabled"):
                    logger.warning(f"[Invalid License] {interaction.user} tried to use a disabled or invalid license in '{interaction.guild.name}'.")
                    await interaction.response.send_message("❌ This license is not valid or has been disabled.", ephemeral=True, delete_after=config.message_timeout)
                    return

                if data.get("uses", 0) > 0:
                    logger.warning(f"[Already Used] {interaction.user} tried a used license ({data['uses']} uses) in '{interaction.guild.name}'.")
                    await interaction.response.send_message(
                        f"❌ This license has already been used {data['uses']} times.",
                        ephemeral=True, delete_after=config.message_timeout
                    )
                    return

                # Mark the license as used in Payhip
                async with session.put(PAYHIP_INCREMENT_USAGE_URL, headers=headers, data={"license_key": license_key}, timeout=10) as increment_response:
                    if increment_response.status != 200:
                        await interaction.response.send_message("❌ Failed to mark the license as used.", ephemeral=True, delete_after=config.message_timeout)
                        return

            # Assign role to the user
            user = interaction.author
            guild = interaction.guild

            async with (await get_database_pool()).acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT role_id FROM products WHERE guild_id = $1 AND product_name = $2",
                    str(guild.id), self.product_name
                )
                if not row:
                    await interaction.response.send_message(
                        f"❌ Role information for '{self.product_name}' is missing.",
                        ephemeral=True, delete_after=config.message_timeout
                    )
                    return

                role_id = row["role_id"]
                role = disnake.utils.get(guild.roles, id=int(role_id))

                if not role:
                    await interaction.response.send_message(
                        "❌ The role associated with this product is missing or deleted.",
                        ephemeral=True, delete_after=config.message_timeout
                    )
                    return

            await user.add_roles(role)
            logger.info(f"[Role Assigned] Gave role '{role.name}' to {user} in '{guild.name}' for product '{self.product_name}'.")
            await interaction.response.send_message(
                f"✅🎉 {user.mention}, your license for '{self.product_name}' is verified! Role '{role.name}' has been assigned.",
                ephemeral=True, delete_after=config.message_timeout
            )
            
            await save_verified_license(interaction.author.id, interaction.guild.id, self.product_name, license_key) # Save the license in the local database
            # Optionally log the event in the server's log channel
            try:
                async with (await get_database_pool()).acquire() as conn:
                    log_row = await conn.fetchrow(
                        "SELECT channel_id FROM server_log_channels WHERE guild_id = $1",
                        str(guild.id)
                    )

                if log_row:
                    log_channel = guild.get_channel(int(log_row["channel_id"]))
                    if log_channel:
                        embed = disnake.Embed(
                            title="License Activation",
                            description=f"{user.mention} has registered the **{self.product_name}** product and has been granted the following role:",
                            color=disnake.Color.green()
                        )
                        embed.add_field(name="• Role", value=role.mention, inline=False)
                        embed.set_footer(text="Powered by KeyVerify")
                        embed.timestamp = interaction.created_at
                        await log_channel.send(embed=embed)
            except Exception as e:              
                print(f"[Log Error] Failed to log license for {user}: {e}") # Fails silently so user still gets a role even if logging fails

        except aiohttp.ClientError as e:
            logger.error(f"Payhip API Error: {e}")
            await interaction.response.send_message(
                "❌ Unable to contact the verification server. Please try again later.",
                ephemeral=True, delete_after=config.message_timeout
            )