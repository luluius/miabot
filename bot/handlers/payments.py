import logging
from aiogram import Router, Bot
from aiogram.types import PaidMediaPurchased, PreCheckoutQuery

from bot.config import Config
from bot.database import Database

logger = logging.getLogger(__name__)

payments_router = Router(name="payments_router")

@payments_router.purchased_paid_media()
async def handle_purchased_paid_media(
    event: PaidMediaPurchased,
    bot: Bot,
    config: Config,
    db: Database
):
    """
    Déclenché lorsque quelqu'un paie des Étoiles Telegram pour débloquer un média payant.
    Telegram débloque automatiquement le média pour l'acheteur dans le chat ou le canal.
    """
    buyer = event.from_user
    payload = event.paid_media_payload

    logger.info(f"Paiement reçu : utilisateur {buyer.id} (@{buyer.username}) pour le payload {payload}")

    # Recherche du post associé
    post = await db.get_post_by_payload(payload)
    star_count = post["star_count"] if post else 0
    post_id = post["id"] if post else None
    title = post["title"] if post else "Photo de voyage"

    # Enregistrement de la transaction en base
    await db.record_sale(
        post_id=post_id,
        buyer_id=buyer.id,
        buyer_username=buyer.username or buyer.first_name,
        star_count=star_count,
        payload=payload
    )

    # 1. Message de remerciement à l'acheteur s'il est en discussion privée avec le bot
    try:
        await bot.send_message(
            chat_id=buyer.id,
            text=(
                f"🎉 **Merci pour votre achat !**\n\n"
                f"Votre paiement de **{star_count} ⭐️** a bien été validé.\n"
                f"La photo *\"{title}\"* est désormais débloquée en haute résolution !"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.debug(f"Impossible d'envoyer le message de confirmation à l'acheteur : {e}")

    # 2. Notification instantanée à tous les administrateurs
    buyer_label = f"@{buyer.username}" if buyer.username else f"{buyer.first_name} (ID: `{buyer.id}`)"
    admin_alert = (
        "💰 **NOUVELLE VENTE RÉALISÉE !**\n\n"
        f"👤 **Acheteur :** {buyer_label}\n"
        f"📸 **Photo débloquée :** *{title}*\n"
        f"⭐ **Gain :** `+{star_count}` Étoiles Telegram ⭐️\n\n"
        "Tapez `/stats` pour consulter vos statistiques globales."
    )

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_alert,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte à l'admin {admin_id}: {e}")

@payments_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Validation automatique de pré-paiement requise par Telegram si des factures sont utilisées."""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
