import disnake
from disnake.ext import commands
from utils.encryption import encrypt_data
from utils.database import get_database_pool
import config
import logging
import uuid
import asyncpg # For specific error handling
import traceback # For hardcore debugging

logger = logging.getLogger(__name__)
product_session_cache = {}  # session_id -> (product_name, product_secret)

class AddProduct(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description="Add a product to the server's list with an assigned role (server owner only).",
        default_member_permissions=disnake.Permissions(manage_guild=True),
    )
    async def add_product(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id != inter.guild.owner_id:
            logger.warning(f"[Unauthorized Attempt] {inter.author} tried to add a product in '{inter.guild.name}'")
            await inter.response.send_message(
                "❌ Only the server owner can use this command.",
                transient=True,
                delete_after=config.message_timeout
            )
            return

        await inter.response.send_modal(AddProductModal())

class AddProductModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Product Name",
                custom_id="product_name",
                placeholder="Enter the product name",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            disnake.ui.TextInput(
                label="Product Secret",
                custom_id="product_secret",
                placeholder="Enter the Payhip product secret",
                style=disnake.TextInputStyle.short,
                max_length=100,
            )
        ]
        super().__init__(
            title="Add a New Product",
            custom_id="add_product_modal",
            components=components
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        product_name = interaction.text_values["product_name"].strip()
        product_secret = interaction.text_values["product_secret"].strip()

        # Create a session ID to link this modal to the next view
        session_id = str(uuid.uuid4())[:12]
        product_session_cache[session_id] = (product_name, product_secret)

        # We pass the session_id to the new view
        view = RoleSelectView(session_id, product_session_cache, interaction.guild)
        
        # This is the fix for the initial TypeError
        await interaction.response.send_message(
            "Select an existing role (this list is searchable) or create one automatically:",
            view=view,ephemeral=True
        )
        
        # Store the message so the view can edit it on timeout
        view.message = await interaction.original_message()


class RoleSelectView(disnake.ui.View):
    """
    This view uses the modern RoleSelect component.
    It is searchable and does NOT have the 25-item limit.
    """

    def __init__(self, session_id: str, cache: dict, guild: disnake.Guild):
        super().__init__(timeout=180)
        self.session_id = session_id
        self.cache = cache
        self.guild = guild
        self.message: disnake.InteractionMessage = None

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        # Only the original user can interact
        if interaction.author.id != self.guild.owner_id:
            await interaction.response.send_message("❌ You are not the owner.", ephemeral=True, delete_after=5)
            return False
        
        # Stop double-clicks or race conditions
        if self.is_finished():
            await interaction.response.send_message(
                "⌛ Your request is already being processed or has timed out.", 
                ephemeral=True,
                delete_after=5
            )
            return False
            
        return True

    async def on_timeout(self):
        # Use the atomic pop to prevent race conditions
        session_data = self.cache.pop(self.session_id, None)

        if session_data is None: # Callback() already ran
            return 

        logger.debug(f"View timed out for session {self.session_id}")
        if self.message:
            try:
                await self.message.edit(content="❌ Session timed out. Please run the command again.", view=None)
            except (disnake.NotFound, disnake.Forbidden):
                pass # Message was deleted or permissions lost

    # This callback is for the searchable role dropdown
    @disnake.ui.role_select(
        placeholder="Choose an existing role (Type to search)",
        min_values=1,
        max_values=1,
        row=0
    )
    async def role_select_callback(self, select: disnake.ui.RoleSelect, interaction: disnake.MessageInteraction):
        # Defer immediately
        await interaction.response.defer()
        self.stop() # Stop the view

        # The role is provided as a full object
        role = select.values[0]
        
        await self.finish_product(interaction, role)

    # This callback is for the "Auto-Create" button
    @disnake.ui.button(
        label="Create New Role Automatically",
        style=disnake.ButtonStyle.success,
        row=1
    )
    async def auto_create_callback(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Defer immediately
        await interaction.response.defer()
        self.stop() # Stop the view
        
        # Pop the session data
        try:
            product_name, _ = self.cache[self.session_id]
        except KeyError:
            await interaction.edit_original_message(
                content="❌ Session expired or was already processed.",
                view=None
            )
            return
        
        role: disnake.Role = None
        role_name = f"Verified-{product_name}"
        
        try:
            role = await self.guild.create_role(name=role_name, reason="KeyVerify auto-role")
            await interaction.edit_original_message(
                content=f"Role '{role.name}' was created automatically.",
                view=None,
                ephemeral=True
            )
        except disnake.Forbidden:
            logger.error(f"Missing 'Manage Roles' permission in {self.guild.name}")
            await interaction.edit_original_message(
                content="❌ I don't have permission to create roles.", 
                view=None,ephemeral=True
            )
            return
        except Exception as e:
            logger.error(f"Failed to create role: {e}")
            await interaction.edit_original_message(
                content=f"❌ An error occurred while trying to create the role: {e}", 
                view=None,ephemeral=True
            )
            return
        
        await self.finish_product(interaction, role)

    async def finish_product(self, interaction: disnake.MessageInteraction, role: disnake.Role):
        """
        A helper function to handle the final database insertion.
        """
        
        # Wrap in a try/except to catch the REAL error
        try:
            # Pop the session data
            try:
                product_name, product_secret = self.cache.pop(self.session_id)
            except KeyError:
                # This should be rare, but handles a race with timeout
                await interaction.edit_original_message(
                    content="❌ Session expired or was already processed.",
                    view=None
                )
                return

            if not role:
                await interaction.edit_original_message(content="❌ An unknown error occurred: Role was not found.", view=None)
                return

            encrypted_secret = encrypt_data(product_secret)

            # --- THIS IS THE CORRECTED DATABASE CODE ---
            # 1. Await the function to get the pool
            pool = await get_database_pool()
            # 2. Use the pool to acquire a connection
            async with pool.acquire() as conn:
                try:
                    await conn.execute(
                        "INSERT INTO products (guild_id, product_name, product_secret, role_id) "
                        "VALUES ($1, $2, $3, $4)",
                        str(self.guild.id), product_name, encrypted_secret, str(role.id)
                    )
                    logger.info(f"[Product Added] '{product_name}' added to '{self.guild.name}' with role '{role.name}'")
                    
                    # We already edited the message, so we must use followup
                    # --- FIXED: 'transient=True' changed to 'ephemeral=True' ---
                    await interaction.followup.send(
                        f"✅ Product **`{product_name}`** added successfully with role {role.mention}.",
                        ephemeral=True,
                        delete_after=config.message_timeout
                    )
                except asyncpg.exceptions.UniqueViolationError: # Be specific
                    logger.warning(f"[Duplicate Product] Attempt to add duplicate product '{product_name}' in '{self.guild.name}'")
                    # --- FIXED: 'transient=True' changed to 'ephemeral=True' ---
                    await interaction.followup.send(
                        f"❌ Product **`{product_name}`** already exists.",
                        ephemeral=True,
                        delete_after=config.message_timeout
                    )
        
        except Exception as e:
            # This will catch and print the *real* error
            print(f"--- UNHANDLED ERROR IN FINISH_PRODUCT ---")
            traceback.print_exc()
            logger.error(f"--- UNHANDLED ERROR IN FINISH_PRODUCT ---")
            logger.exception(e)
            try:
                # --- FIXED: 'transient=True' changed to 'ephemeral=True' ---
                await interaction.followup.send(
                    f"❌ An unknown error occurred. The developers have been notified.\n`Error: {e}`", 
                    ephemeral=True
                )
            except Exception:
                pass

def setup(bot):
    bot.add_cog(AddProduct(bot))

