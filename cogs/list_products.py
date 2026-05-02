import disnake
from disnake.ext import commands
from utils.database import get_database_pool
import config
import logging

logger = logging.getLogger(__name__)

class ListProducts(commands.Cog):
    @commands.slash_command(
        description="List all products configured for this server (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True)
    )
    async def list_products(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id != inter.guild.owner_id:
            await inter.response.send_message(
                "❌ Only the server owner can use this command.",
                ephemeral=True,
                delete_after=config.message_timeout
            )
            return
        
        async with (await get_database_pool()).acquire() as conn:
            rows = await conn.fetch(
                "SELECT product_name, role_id FROM products WHERE guild_id = $1",
                str(inter.guild.id)
            )

        if not rows:
            await inter.response.send_message(
                "📦 No products have been added to this server yet.",
                ephemeral=True,
                delete_after=config.message_timeout
            )
            return

        # Prepare the full list of formatted lines
        product_entries = []
        for row in rows:
            role = inter.guild.get_role(int(row["role_id"]))
            role_display = role.mention if role else "*⚠️ Role deleted — use `/edit_product` to reassign*"
            product_entries.append(f"• **{row['product_name']}** → {role_display}")

        # The Paginated View for Listing
        class ListPaginatorView(disnake.ui.View):
            def __init__(self, entries):
                super().__init__(timeout=60)
                self.entries = entries
                self.page = 0
                self.per_page = 10 # Number of products shown per page
                self.max_page = (len(entries) - 1) // self.per_page
                self.update_buttons()

            def create_embed(self):
                start = self.page * self.per_page
                end = start + self.per_page
                current_lines = self.entries[start:end]
                
                embed = disnake.Embed(
                    title="🧾 Products in This Server",
                    description="\n".join(current_lines),
                    color=disnake.Color.blurple()
                )
                embed.set_footer(text=f"Page {self.page + 1}/{self.max_page + 1} • Only visible to server owner")
                return embed

            def update_buttons(self):
                self.clear_items()
                if self.max_page > 0:
                    prev_btn = disnake.ui.Button(label="⬅️", style=disnake.ButtonStyle.gray, disabled=(self.page == 0))
                    prev_btn.callback = self.prev_page
                    self.add_item(prev_btn)

                    next_btn = disnake.ui.Button(label="➡️", style=disnake.ButtonStyle.gray, disabled=(self.page == self.max_page))
                    next_btn.callback = self.next_page
                    self.add_item(next_btn)

            async def prev_page(self, interaction: disnake.MessageInteraction):
                self.page -= 1
                self.update_buttons()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

            async def next_page(self, interaction: disnake.MessageInteraction):
                self.page += 1
                self.update_buttons()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)

        view = ListPaginatorView(product_entries)
        await inter.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(ListProducts(bot))