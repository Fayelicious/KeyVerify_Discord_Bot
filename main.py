import disnake
from disnake.ext import commands
import requests
import sqlite3
from dotenv import load_dotenv
import os
from flask import Flask
import threading
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

# Flask app for health check
app = Flask(__name__)

# Health check route
@app.route('/')
def health_check():
    return "OK", 200

# Load environment variables from the .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Default to INFO if not specified

# Generate or load encryption key for secrets
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# Rate limit dictionary for tracking user cooldowns
rate_limits = {}

# Database setup
def get_database_connection(database_url):
    if database_url.startswith("sqlite"):
        conn = sqlite3.connect(database_url.split("sqlite:///")[1])
        conn.row_factory = sqlite3.Row  # Enable column access by name
    elif database_url.startswith("postgresql"):
        import psycopg2
        from psycopg2.extras import DictCursor
        conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
    else:
        raise ValueError(f"Unsupported database type: {database_url}")
    return conn

try:
    conn = get_database_connection(DATABASE_URL)
    cursor = conn.cursor()

    # Ensure the table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        guild_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        product_secret TEXT NOT NULL,
        PRIMARY KEY (guild_id, product_name)
    )
    """)
    conn.commit()
    print("Database connected and ready.")
except Exception as e:
    print(f"Error initializing the database: {e}")
    exit(1)

intents = disnake.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.InteractionBot(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")
    try:
        await bot.tree.sync()  # Sync commands with Discord
        print("Commands have been synchronized.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Helper function to fetch products for a guild
def fetch_products(guild_id):
    cursor.execute("SELECT product_name, product_secret FROM products WHERE guild_id = ?", (guild_id,))
    return {row["product_name"]: cipher_suite.decrypt(row["product_secret"].encode()).decode() for row in cursor.fetchall()}

class ProductSelectionView(disnake.ui.View):
    def __init__(self, products, license_key):
        super().__init__(timeout=60)
        self.products = products
        self.license_key = license_key

        self.dropdown = disnake.ui.StringSelect(
            placeholder="Select a product",
            options=[
                disnake.SelectOption(label=name, description=f"Verify license for {name}")
                for name in products.keys()
            ]
        )
        self.dropdown.callback = self.select_callback
        self.add_item(self.dropdown)

    async def select_callback(self, interaction: disnake.MessageInteraction):
        product_name = interaction.data["values"][0]
        product_secret_key = self.products[product_name]
        license_key = self.license_key.strip()

        PAYHIP_VERIFY_URL = f"https://payhip.com/api/v2/license/verify?license_key={license_key}"
        headers = {"product-secret-key": product_secret_key}
        response = requests.get(PAYHIP_VERIFY_URL, headers=headers)

        if response.status_code == 200 and (data := response.json().get("data")):
            if not data["enabled"]:
                await interaction.response.send_message("❌ This license is not enabled.", ephemeral=True)
                return

            if data["uses"] > 0:
                await interaction.response.send_message(f"❌ This license has already been used {data['uses']} times.", ephemeral=True)
                return

            user = interaction.author
            role_name = f"Verified-{product_name}"
            guild = interaction.guild
            role = disnake.utils.get(guild.roles, name=role_name)

            if not role:
                role = await guild.create_role(name=role_name)

            await user.add_roles(role)
            await interaction.response.send_message(f"🎉 {user.mention}, your license for '{product_name}' is verified!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Invalid license key or product secret.", ephemeral=True)

# Define the /verify command
@bot.slash_command(description="Verify your product license key.")
async def verify(
    inter: disnake.ApplicationCommandInteraction,
    license_key: str = commands.Param(description="Enter your license key")
):
    products = fetch_products(str(inter.guild.id))
    if not products:
        await inter.response.send_message("❌ No products are registered for this server.", ephemeral=True)
        return

    view = ProductSelectionView(products, license_key)
    await inter.response.send_message("Select a product to verify:", view=view, ephemeral=True)

# Apply rate limit middleware
@verify.before_invoke
async def rate_limit(inter):
    user_id = inter.author.id
    now = datetime.now()
    if user_id in rate_limits and now < rate_limits[user_id]:
        await inter.response.send_message("❌ Please wait before using this command again.", ephemeral=True)
        raise commands.CommandError("Rate limit exceeded.")
    rate_limits[user_id] = now + timedelta(seconds=10)

# Apply server owner check middleware
@verify.before_invoke
async def ensure_owner(inter):
    if inter.author.id != inter.guild.owner_id:
        await inter.response.send_message("❌ Only the server owner can use this command.", ephemeral=True)
        raise commands.CheckFailure("User is not the server owner.")

def run():
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8080, debug=False), daemon=True
    ).start()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    run()
