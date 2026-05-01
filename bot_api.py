import os
import re
import logging
import disnake
from aiohttp import web

logger = logging.getLogger(__name__)
_INTERNAL_KEY = os.getenv("ADMIN_API_KEY", "").strip()


def _auth(request):
    if not _INTERNAL_KEY or request.headers.get("X-Admin-Key", "") != _INTERNAL_KEY:
        raise web.HTTPUnauthorized(text="Unauthorized")


def create_bot_api(bot):
    async def list_cogs(request):
        _auth(request)
        cog_dir = os.path.join(os.path.dirname(__file__), "cogs")
        available = [
            f"cogs.{f[:-3]}"
            for f in os.listdir(cog_dir)
            if f.endswith(".py") and not f.startswith("__")
        ]
        loaded = set(bot.extensions.keys())
        return web.json_response({
            "cogs": [
                {"name": name, "loaded": name in loaded}
                for name in sorted(available)
            ]
        })

    async def reload_cog(request):
        _auth(request)
        data = await request.json()
        name = data.get("name", "").strip()
        if not name:
            return web.json_response({"error": "name is required"}, status=400)
        try:
            bot.reload_extension(name)
            logger.info(f"[BotAPI] Reloaded: {name}")
            return web.json_response({"message": f"Reloaded {name}."})
        except Exception as e:
            logger.error(f"[BotAPI] Reload failed for {name}: {e}")
            return web.json_response({"error": str(e)}, status=400)

    async def load_cog(request):
        _auth(request)
        data = await request.json()
        name = data.get("name", "").strip()
        if not name:
            return web.json_response({"error": "name is required"}, status=400)
        try:
            bot.load_extension(name)
            logger.info(f"[BotAPI] Loaded: {name}")
            return web.json_response({"message": f"Loaded {name}."})
        except Exception as e:
            logger.error(f"[BotAPI] Load failed for {name}: {e}")
            return web.json_response({"error": str(e)}, status=400)

    async def unload_cog(request):
        _auth(request)
        data = await request.json()
        name = data.get("name", "").strip()
        if not name:
            return web.json_response({"error": "name is required"}, status=400)
        try:
            bot.unload_extension(name)
            logger.info(f"[BotAPI] Unloaded: {name}")
            return web.json_response({"message": f"Unloaded {name}."})
        except Exception as e:
            logger.error(f"[BotAPI] Unload failed for {name}: {e}")
            return web.json_response({"error": str(e)}, status=400)

    _config_path = os.path.join(os.path.dirname(__file__), "config.py")

    async def get_bot_config(request):
        _auth(request)
        import config
        activity = bot.activity.name if bot.activity else ""
        return web.json_response({"version": config.version, "status": activity})

    async def set_bot_config(request):
        _auth(request)
        data = await request.json()
        version = data.get("version", "").strip()
        status = data.get("status", "").strip()

        if version:
            content = open(_config_path).read()
            content = re.sub(r'version\s*=\s*"[^"]*"', f'version = "{version}"', content)
            open(_config_path, "w").write(content)
            import importlib, config
            importlib.reload(config)
            logger.info(f"[BotAPI] Version updated to {version}")

        if status:
            await bot.change_presence(activity=disnake.Game(name=status))
            logger.info(f"[BotAPI] Status updated to: {status}")

        return web.json_response({"message": "Bot config updated."})

    app = web.Application()
    app.router.add_get("/internal/cogs", list_cogs)
    app.router.add_post("/internal/cogs/reload", reload_cog)
    app.router.add_post("/internal/cogs/load", load_cog)
    app.router.add_post("/internal/cogs/unload", unload_cog)
    app.router.add_get("/internal/config", get_bot_config)
    app.router.add_post("/internal/config", set_bot_config)
    return app


async def start_bot_api(bot):
    app = create_bot_api(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8887)
    await site.start()
    logger.info("Bot internal API running on :8887")
