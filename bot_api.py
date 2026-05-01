import os
import logging
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

    app = web.Application()
    app.router.add_get("/internal/cogs", list_cogs)
    app.router.add_post("/internal/cogs/reload", reload_cog)
    app.router.add_post("/internal/cogs/load", load_cog)
    app.router.add_post("/internal/cogs/unload", unload_cog)
    return app


async def start_bot_api(bot):
    app = create_bot_api(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8887)
    await site.start()
    logger.info("Bot internal API running on :8887")
