<div align="center"\> \<h1\> KeyVerify\</h1\> \<p\>\<strong\>A Secure Discord Bot for License Verification via Payhip\</strong\>\</p\>

<p\>

<a href="https://www.python.org/downloads/"\>\<img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version"\>\</a\>

<a href="\[suspicious link removed\]"\>\<img src="https://img.shields.io/badge/Discord-Bot%20Ready-7289DA?logo=discord" alt="Discord Bot Ready"\>\</a\>

</p\>

</div\>

[Invite bot to your Server](https://discord.com/oauth2/authorize?client_id=1314098590951673927&permissions=268511232&integration_type=0&scope=bot+applications.commands)

## **What is KeyVerify?**

**KeyVerify** is a lightweight and secure Discord bot for automating license verification of Payhip digital products. It helps creators manage customer access to Discord roles in a streamlined and encrypted way.

Recently updated to be **fully asynchronous**, it handles multiple requests efficiently without slowing down.

## **Features**

* **License Verification** – Secure and user-friendly verification via in-server modal.  
* **Auto Role Reassignment** – Automatically reapply roles if a verified user rejoins.  
* **Product Management** – Add, list, or remove products with optional auto-generated roles.  
* **License Reset** – Reset usage count of a license for reactivations.  
* **Key Rotation** – **New\!** Safely rotate encryption keys without losing data access.  
* **Async Core** – **New\!** Built on aiohttp to prevent bot lag during API calls.  
* **Audit Logging** – Track all verification attempts and role assignments.  
* **Spam Protection** – Rate-limiting built-in to avoid abuse.  
* **Encrypted Storage** – License keys and product secrets are safely encrypted using AES (Fernet).

## **Slash Command Overview**

| Command | Description |
| :---- | :---- |
| /start\_verification | Deploys the verification interface to a channel. |
| /add\_product | Add a new product with a secret and optional role. |
| /remove\_product | Remove a product from the server list. |
| /list\_products | View all products and their associated roles. |
| /reset\_key | Reset usage for a license key on Payhip. |
| /set\_lchannel | Define the channel for verification logs. |
| /remove\_user | Revoke a user's access, delete DB entries, and disable licenses. |
| /help | Shows help message and support info. |

## **Security Practices**

* License keys and secrets are **AES-encrypted** (Fernet) before storage.  
* All commands are **permission-locked** to server owners or admins.  
* **Cooldown** logic prevents excessive or abusive interactions.  
* Optional logging ensures traceability in any server.

## **Installation & Setup**

1. **Clone the repo:**  
   git clone \[https://github.com/Fayelicious/KeyVerify\_Discord\_Bot.git\](https://github.com/Fayelicious/KeyVerify\_Discord\_Bot.git)

2. **Install dependencies:**  
   pip install \-r requirements.txt

### **Generating the Encryption Key**

KeyVerify uses secure encryption (Fernet) to store license keys. You must generate a secure key before running the bot.

**Step-by-step (Beginner Friendly)**

1. Generate a secure key. Run this command in your terminal:  
   python \-c "from cryptography.fernet import Fernet; print(Fernet.generate\_key().decode())"

   This will output a secure key like:  
   WdIf6ZfNNuHrXkVvZBMyPZr7nqSItmGqM9dWBtZsKfs=  
2. Set it in your .env file (see below).

### **Configuration (.env)**

Create a .env file in the bot root:

DISCORD\_TOKEN=your\_discord\_bot\_token  
PAYHIP\_API\_KEY=your\_payhip\_api\_key  
DATABASE\_URL=your\_postgres\_connection\_url  
LOG\_LEVEL=INFO

\# Paste the key you generated above here:  
ENCRYPTION\_KEYS=YOUR\_GENERATED\_KEY\_HERE

3. **Run the bot:**  
   python bot.py

*Make sure your bot has required permissions: Manage Roles, Send Messages, and Read Message History.*

## **🔄 Key Rotation (Security)**

If you ever need to change your encryption key (e.g., for security reasons), you can do so without breaking your database.

1. Generate a **NEW** key using the python command above.  
2. Add it to the **front** of your .env list, separated by a comma:  
   ENCRYPTION\_KEYS=NEW\_KEY,OLD\_KEY

3. **Restart the bot.**  
   * The bot will automatically detect the new key.  
   * It will scan the database on startup and **re-encrypt** all old data using the new key.  
4. Once the console says ✅ SECURITY ROTATION: Re-encrypted X records, you can safely remove the OLD\_KEY from your .env file.

## **Project Status**

KeyVerify is actively in development and used in live communities like Poodle's Discord. Feedback, contributions, and issue reports are always welcome\!

## **Support & Contact**

For help or to suggest a feature:

**Discord:** Fayelicious\_

**Built With:**

* disnake  
* aiohttp  
* asyncpg  
* cryptography  
* Python 3.11+

## **Legal for Hosted Bot**

* [Privacy Policy](https://payhip.com/Fayelicious/privacy-policy-discord-bot)  
* [Terms of Service](https://www.google.com/search?q=https://payhip.com/Fayelicious/discordbot-tos?)

**Link to hosted Bot**

* [KeyVerify](https://payhip.com/Fayelicious/payhip-license-verify-bot)