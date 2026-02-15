<div align="center">
  <h1>KeyVerify</h1>
  <p><strong>A Secure Discord Bot for License Verification via Payhip</strong></p>

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version"></a>
    <a href="https://discord.com"><img src="https://img.shields.io/badge/Discord-Bot%20Ready-7289DA?logo=discord" alt="Discord Bot Ready"></a>
  </p>

  <a href="https://discord.com/oauth2/authorize?client_id=1314098590951673927&permissions=268511232&integration_type=0&scope=bot+applications.commands">
    <img src="https://img.shields.io/badge/Invite_Bot-Click_Here-success?style=for-the-badge" alt="Invite Bot">
  </a>
</div>

---

## 📖 What is KeyVerify?

**KeyVerify** is a lightweight and secure Discord bot for automating license verification of Payhip digital products. It helps creators manage customer access to Discord roles in a streamlined and encrypted way.

Recently updated to be **fully asynchronous**, it handles multiple requests efficiently without slowing down.

---

## ✨ Features

- **License Verification** – Secure and user-friendly verification via in-server modal.
- **Auto Role Reassignment** – Automatically reapply roles if a verified user rejoins.
- **Product Management** – Add, list, or remove products with optional auto-generated roles.
- **License Reset** – Reset usage count of a license for reactivations.
- **Key Rotation** – **New!** Safely rotate encryption keys without losing data access.
- **Async Core** – **New!** Built on `aiohttp` to prevent bot lag during API calls.
- **Audit Logging** – Track all verification attempts and role assignments via a log channel.
- **Encrypted Storage** – License keys and product secrets are safely encrypted using AES (Fernet).

---

## 🛠️ Slash Command Overview

| Command | Description |
| :--- | :--- |
| `/start_verification` | Deploys the verification interface to a channel. |
| `/add_product` | Add a new product with a secret and optional role. |
| `/remove_product` | Remove a product from the server list. |
| `/list_products` | View all products and their associated roles. |
| `/reset_key` | Reset usage for a license key on Payhip. |
| `/remove_user` | Revoke a user's access, delete DB entries, and disable licenses. |
| `/set_lchannel` | Define the channel for verification logs. |
| `/help` | Shows help message and support info. |

---

## 🔒 Security Practices

- License keys and secrets are **AES-encrypted** (Fernet) before storage.
- All management commands are **permission-locked** to server owners.
- **Cooldown** logic prevents excessive or abusive interactions.
- **No Privileged Intents:** The bot operates without reading message content or caching member lists.

---

## ⚙️ Installation & Setup

### 1. Clone the repo
```bash
git clone [https://github.com/Fayelicious/KeyVerify_Discord_Bot.git](https://github.com/Fayelicious/KeyVerify_Discord_Bot.git)

Install dependencies:

    pip install -r requirements.txt

## Generating the Encryption Key
## KeyVerify uses AES encryption to securely store license keys and product secrets. To enable this, you need to generate a secure secret key and add it to your environment variables.

## Step-by-step (Beginner Friendly)
  Generate a 32-byte (256-bit) encryption key
  Run this Python command:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    Copy the output string (it will look like b'...' or end with =).

    'WdIf6ZfNNuHrXkVvZBMyPZr7nqSItmGqM9dWBtZsKfs='
Configuration (.env)
Create a .env file in the bot folder and add your configuration:
  DISCORD_TOKEN=your_discord_bot_token
  PAYHIP_API_KEY=your_payhip_api_key
  DATABASE_URL=postgresql://user:password@localhost/dbname
  LOG_LEVEL=INFO

  # Paste the key you generated above here:
  ENCRYPTION_KEYS=YOUR_GENERATED_KEY_HERE

Run the bot:

    python bot.py

Make sure your bot has required permissions: Manage Roles, Send Messages, and Read Message History.

🔄 Key Rotation (Security)
If you ever need to change your encryption key (e.g., for security reasons), you can do so without breaking your database.
Generate a NEW key using the python command in Step 3.

  Add it to the front of your .env list, separated by a comma:

  Code-Snippet
  ENCRYPTION_KEYS=NEW_KEY,OLD_KEY
  Restart the bot.

  The bot will automatically detect the new key.

  It will scan the database on startup and re-encrypt all old data using the new key.

  Once the console says ✅ SECURITY ROTATION: Re-encrypted X records, you can safely remove the OLD_KEY from your .env file.

Project Status
KeyVerify is actively in development and used in live communities like Poodle's Discord. Feedback, contributions, and issue reports are always welcome!

Support & Contact
For help or to suggest a feature:

Discord: Fayelicious_    


Built With
    disnake

    Payhip API

    PostgreSQL + asyncpg

    Python 3.11+

Legal for Hosted Bot

  [Privacy Policy](https://payhip.com/Fayelicious/privacy-policy-discord-bot)
  [Terms of Service](https://payhip.com/Fayelicious/discordbot-tos?)

  Link to hosted Bot
    [KeyVerify](https://payhip.com/Fayelicious/payhip-license-verify-bot)
   
