import disnake
from disnake.ext import commands
from utils.database import get_database_pool, fetch_products
import config
import logging

logger = logging.getLogger(__name__)

class RemoveProduct(commands.Cog):
    @commands.slash_command(
        description="Remove a product from the server's list (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def remove_product(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id != inter.guild.owner_id:
            logger.warning(f"[Blocked] {inter.author} tried to access /remove_product in '{inter.guild.name}'")
            await inter.response.send_message("❌ Only the server owner can use this command.", ephemeral=True, delete_after=config.message_timeout)
            return

        products = await fetch_products(str(inter.guild.id))
        if not products:
            logger.info(f"[No Products] {inter.author} opened /remove_product but no products exist in '{inter.guild.name}'")
            await inter.response.send_message("❌ No products to remove.", ephemeral=True, delete_after=config.message_timeout)
            return

        options = [
            disnake.SelectOption(label=product, description=f"Remove '{product}'")
            for product in products.keys()
        ]

        dropdown = disnake.ui.StringSelect(
            placeholder="Select a product to remove",
            options=options
        )

        async def product_selected(select_inter: disnake.MessageInteraction):
            selected = select_inter.data["values"][0]

            # Define confirmation buttons
            class ConfirmView(disnake.ui.View):
                def __init__(self):
                    super().__init__(timeout=30)

                @disnake.ui.button(label="✅ Confirm", style=disnake.ButtonStyle.danger)
                async def confirm(self, button: disnake.ui.Button, button_inter: disnake.MessageInteraction):
                    async with (await get_database_pool()).acquire() as conn:
                        result = await conn.execute(
                            "DELETE FROM products WHERE guild_id = $1 AND product_name = $2",
                            str(inter.guild.id), selected
                        )
                    if result == "DELETE 0":
                        logger.warning(f"[Failed Delete] Product '{selected}' not found during deletion in '{inter.guild.name}' by {button_inter.author}")
                        await button_inter.response.send_message(
                            f"❌ Product '{selected}' not found.",
                            ephemeral=True,
                            delete_after=config.message_timeout
                        )
                    else:
                        logger.info(f"[Delete] Product '{selected}' removed from '{inter.guild.name}' by {button_inter.author}")
                        await button_inter.response.send_message(
                            f"✅ Product '{selected}' has been removed.",
                            ephemeral=True,
                            delete_after=config.message_timeout
                        )
                    self.stop()

                @disnake.ui.button(label="❌ Cancel", style=disnake.ButtonStyle.secondary)
                async def cancel(self, button: disnake.ui.Button, button_inter: disnake.MessageInteraction):
                    await button_inter.response.send_message(
                        "Deletion cancelled 💨",
                        ephemeral=True,
                        delete_after=config.message_timeout
                    )
                    logger.info(f"[Cancel] Product deletion cancelled by {button_inter.author} in '{inter.guild.name}'")
                    self.stop()

            view = ConfirmView()
            await select_inter.response.send_message(
                f"⚠️ Are you sure you want to delete **`{selected}`**?",
                view=view,
                ephemeral=True,
                delete_after=config.message_timeout
            )

        dropdown.callback = product_selected
        view = disnake.ui.View()
        view.add_item(dropdown)

        logger.info(f"[Dropdown Init] {inter.author} opened product removal dropdown in '{inter.guild.name}'")

        await inter.response.send_message(
            "🗑️ Select a product to remove:",
            view=view,
            ephemeral=True,
            delete_after=config.message_timeout
        )

def setup(bot):
    bot.add_cog(RemoveProduct(bot))
