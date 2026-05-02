import disnake
from disnake.ext.commands import CooldownMapping, BucketType
from handlers.verify_license_modal import VerifyLicenseModal
from utils.database import fetch_products, get_database_pool, get_verified_license

import config
import time
import logging

logger = logging.getLogger(__name__)


def create_verification_embed():
    embed = disnake.Embed(
        title="Verify your purchase",
        description="Click the button below to begin verifying your purchase.",
        color=disnake.Color.blurple()
    )
    embed.set_footer(text="Powered by KeyVerify")
    return embed


def create_verification_view():
    return VerificationButton()


# Cooldown rate limiter: allows 1 verification request every 20 seconds per user
verify_cooldown = CooldownMapping.from_cooldown(1, 20, BucketType.user)


class ProductPaginationView(disnake.ui.View):
    def __init__(self, products: dict):
        super().__init__(timeout=60)
        self.products = products
        self.product_names = list(products.keys())
        self.page = 0
        self.page_size = 24
        self.update_items()

    def update_items(self):
        self.clear_items()

        start = self.page * self.page_size
        end = start + self.page_size
        current_chunk = self.product_names[start:end]

        options = [
            disnake.SelectOption(label=name, description=f"Verify {name}")
            for name in current_chunk
        ]
        dropdown = disnake.ui.StringSelect(placeholder=f"Products (Page {self.page + 1})", options=options)
        dropdown.callback = self.select_callback
        self.add_item(dropdown)

        if len(self.product_names) > self.page_size:
            prev_btn = disnake.ui.Button(label="⬅️ Previous", disabled=(self.page == 0))
            prev_btn.callback = self.prev_page

            next_btn = disnake.ui.Button(label="Next ➡️", disabled=(end >= len(self.product_names)))
            next_btn.callback = self.next_page

            self.add_item(prev_btn)
            self.add_item(next_btn)

    async def select_callback(self, interaction: disnake.MessageInteraction):
        await handle_product_dropdown(interaction, self.products)

    async def prev_page(self, interaction: disnake.MessageInteraction):
        self.page -= 1
        self.update_items()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: disnake.MessageInteraction):
        self.page += 1
        self.update_items()
        await interaction.response.edit_message(view=self)


class VerificationButton(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        button = disnake.ui.Button(label="Verify", style=disnake.ButtonStyle.primary, custom_id="verify_button")
        button.callback = self.on_button_click
        self.add_item(button)

    async def on_button_click(self, interaction: disnake.MessageInteraction):
        guild_id = str(interaction.guild_id)

        # Cooldown check
        current = time.time()
        bucket = verify_cooldown.get_bucket(interaction)
        retry_after = bucket.update_rate_limit(current)

        if retry_after:
            await interaction.response.send_message(
                f"⏳ You're clicking too fast, try again in `{int(retry_after)}s`.",
                ephemeral=True, delete_after=config.message_timeout
            )
            return

        await interaction.response.defer(ephemeral=True)

        products = await fetch_products(guild_id)
        if not products:
            await interaction.followup.send("❌ No products have been set up for this server yet. Contact the server owner.", ephemeral=True)
            return

        async with (await get_database_pool()).acquire() as conn:
            role_rows = await conn.fetch(
                "SELECT product_name, role_id FROM products WHERE guild_id = $1",
                guild_id
            )
        role_map = {row["product_name"]: row["role_id"] for row in role_rows}

        reassigned_roles = []
        unowned_products = {}

        for name, secret in products.items():
            if await get_verified_license(interaction.author.id, guild_id, name):
                role_id = role_map.get(name)
                if role_id:
                    role = disnake.utils.get(interaction.guild.roles, id=int(role_id))
                    if role and role not in interaction.author.roles:
                        await interaction.author.add_roles(role)
                        reassigned_roles.append(role.name)
            else:
                unowned_products[name] = secret

        if reassigned_roles:
            await interaction.followup.send(f"✅ Roles reassigned: {', '.join(reassigned_roles)}", ephemeral=True)

        if unowned_products:
            view = ProductPaginationView(unowned_products)
            await interaction.followup.send("Select a product to verify:", view=view, ephemeral=True)
        elif not reassigned_roles:
            await interaction.followup.send("✅ You are already fully verified for all products!", ephemeral=True)


async def handle_product_dropdown(interaction, products):
    product_name = interaction.data["values"][0]
    logger.info(f"[Product Selected] {interaction.user} selected '{product_name}' in '{interaction.guild.name}'.")

    product_secret_key = products[product_name]
    modal = VerifyLicenseModal(product_name, product_secret_key)
    try:
        await interaction.response.send_modal(modal)
    except disnake.NotFound:
        logger.warning(f"[Expired Interaction] User {interaction.user} tried to verify after interaction expired.")
