<div align="center">
<h1>KeyVerify</h1>
<p><strong>A Secure Discord Bot for License Verification via Payhip</strong></p>

<p>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version"></a>
<a href="[suspicious link removed]"><img src="https://img.shields.io/badge/Discord-Bot%20Ready-7289DA?logo=discord" alt="Discord Bot Ready"></a>
</p>

<a href="[suspicious link removed]/oauth2/authorize?client_id=1314098590951673927&permissions=268511232&integration_type=0&scope=bot+applications.commands">
<img src="https://img.shields.io/badge/Invite_Bot-Click_Here-success?style=for-the-badge" alt="Invite Bot">
</a>
</div>

📖 What is KeyVerify?

KeyVerify is a lightweight and secure Discord bot for automating license verification of Payhip digital products. It helps creators manage customer access to Discord roles in a streamlined and encrypted way.

Recently updated to be fully asynchronous, it handles multiple requests efficiently without slowing down.

✨ Features

License Verification – Secure and user-friendly verification via in-server modal.

Auto Role Reassignment – Automatically reapply roles if a verified user rejoins.

Product Management – Add, list, or remove products with optional auto-generated roles.

License Reset – Reset usage count of a license for reactivations.

Key Rotation – New! Safely rotate encryption keys without losing data access.

Async Core – New! Built on aiohttp to prevent bot lag during API calls.

Audit Logging – Track all verification attempts and role assignments via a log channel.

Encrypted Storage – License keys and product secrets are safely encrypted using AES (Fernet).

🛠️ Slash Command Overview

Command

Description

/start_verification

Deploys the verification interface to a channel.

/add_product

Add a new product with a secret and optional role.

/remove_product

Remove a product from the server list.

/list_products

View all products and their associated roles.

/reset_key

Reset usage for a license key on Payhip.

/remove_user

Revoke a user's access, delete DB entries, and disable licenses.

/set_lchannel

Define the channel for verification logs.

/help

Shows help message and support info.

🔒 Security Practices

License keys and secrets are AES-encrypted (Fernet) before storage.

All management commands are permission-locked to server owners.

Cooldown logic prevents excessive or abusive interactions.

No Privileged Intents: The bot operates without reading message content or caching member lists.

⚙️ Installation & Setup

1. Clone the repo

git clone [https://github.com/Fayelicious/KeyVerify_Discord_Bot.git](https://github.com/Fayelicious/KeyVerify_Discord_Bot.git)

2. Install dependencies

pip install -r requirements.txt


3. Generating the Encryption Key

KeyVerify uses secure encryption to store license keys. You must generate a secure key before running the bot.

Run this simple command in your terminal:

python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"


Copy the output string (it will look like b'...' or end with =).

4. Configuration (.env)

Create a .env file in the bot folder and add your configuration:

DISCORD_TOKEN=your_discord_bot_token
PAYHIP_API_KEY=your_payhip_api_key
DATABASE_URL=postgresql://user:password@localhost/dbname
LOG_LEVEL=INFO

# Paste the key you generated above here:
ENCRYPTION_KEYS=YOUR_GENERATED_KEY_HERE


5. Run the Bot

python bot.py


Note: Make sure your bot has the required permissions in Discord: Manage Roles, Send Messages, and Read Message History.

🔄 Key Rotation (Security)

If you ever need to change your encryption key (e.g., for security reasons), you can do so without breaking your database.

Generate a NEW key using the python command in Step 3.

Add it to the front of your .env list, separated by a comma:

ENCRYPTION_KEYS=NEW_KEY,OLD_KEY


Restart the bot.

The bot will automatically detect the new key.

It will scan the database on startup and re-encrypt all old data using the new key.

Once the console says ✅ SECURITY ROTATION: Re-encrypted X records, you can safely remove the OLD_KEY from your .env file.

📜 Legal (Hosted Bot)

If you are using the public hosted version of KeyVerify:

Privacy Policy

Terms of Service

Get the Hosted Bot

🤝 Support & Contact

Project Status: KeyVerify is actively in development and used in live communities. Feedback, contributions, and issue reports are always welcome!

Discord: Fayelicious_

Built With

    disnake

    Payhip API

    PostgreSQL + asyncpg

    Python 3.11+