import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import Config
from bot.database import Database
from bot.handlers import admin_router, user_router, payments_router, inline_router

import os
from aiohttp import web

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TravelStarsBot")

async def start_dummy_webserver():
    """Démarre un mini-serveur HTTP requis par Render / Koyeb pour les plans gratuits."""
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()

    async def health(request):
        return web.Response(text="Bot Telegram actif et en ligne 🚀")

    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Serveur web de santé démarré sur http://0.0.0.0:{port}")

async def setup_bot_commands(bot: Bot):
    """Enregistre la liste des commandes suggérées dans le menu Telegram."""
    commands = [
        BotCommand(command="catalogue", description="🖼️ Explorer les photos de voyage"),
        BotCommand(command="vendre", description="📸 Mettre en vente une photo (Admin)"),
        BotCommand(command="envoyer", description="📤 Envoyer une photo en privé (Admin)"),
        BotCommand(command="stats", description="📊 Statistiques des ventes (Admin)"),
        BotCommand(command="aide", description="ℹ️ Comment fonctionnent les Étoiles"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    logger.info("Démarrage du Bot Telegram Stars - Photos de Voyage...")

    # Chargement de la configuration
    try:
        config = Config.load()
    except ValueError as e:
        logger.error(f"Erreur de configuration : {e}")
        logger.info("Veuillez éditer le fichier .env avec votre vrai BOT_TOKEN et redémarrer.")
        sys.exit(1)

    # Démarrage du serveur web de santé (requis pour hébergeur gratuit Render/Koyeb)
    try:
        await start_dummy_webserver()
    except Exception as e:
        logger.warning(f"Impossible de démarrer le serveur web local : {e}")

    # Initialisation de la base de données
    db = Database(db_path=config.database_path)
    await db.init_db()
    logger.info(f"Base de données SQLite initialisée : {config.database_path}")

    # Initialisation du Bot et du Dispatcher
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Injection des dépendances (accessibles directement dans les arguments des handlers)
    dp["db"] = db
    dp["config"] = config

    # Enregistrement des routeurs
    dp.include_router(payments_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(inline_router)

    # Configuration des commandes dans l'interface Telegram
    try:
        await setup_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Impossible de mettre à jour la liste des commandes : {e}")

    # Récupération des types d'updates utilisés (inclut 'purchased_paid_media' et 'inline_query')
    allowed_updates = dp.resolve_used_update_types()
    for extra in ("purchased_paid_media", "inline_query"):
        if extra not in allowed_updates:
            allowed_updates.append(extra)

    logger.info(f"Types d'updates écoutés : {allowed_updates}")
    logger.info(f"Admins configurés : {config.admin_ids}")
    if config.default_channel_id:
        logger.info(f"Canal de diffusion par défaut : {config.default_channel_id}")

    # Suppression des anciens webhooks éventuels et lancement du polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Le bot est en ligne et à l'écoute des messages et paiements !")

    try:
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt du bot.")
