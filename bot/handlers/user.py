from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputPaidMediaPhoto, InputPaidMediaVideo
from aiogram.filters import CommandStart, Command, CommandObject

from bot.config import Config
from bot.database import Database
from bot.keyboards import get_main_menu, get_catalog_item_keyboard

user_router = Router(name="user_router")

# ==============================================================================
# Commande /start avec gestion des deep-links (ex: /start photo_1)
# ==============================================================================
@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, db: Database, config: Config, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Enregistrement de l'utilisateur comme abonné
    await db.register_user(user_id=user_id, username=username, first_name=first_name)

    is_admin = config.is_admin(user_id)
    auto_promoted = False
    if not config.admin_ids:
        # Aucun administrateur configuré : le premier utilisateur devient automatiquement l'admin
        config.add_admin(user_id)
        is_admin = True
        auto_promoted = True

    # 1. Vérification si un lien direct vers une photo a été utilisé (ex: /start photo_12)
    if command.args and command.args.startswith("photo_"):
        raw_id = command.args.replace("photo_", "")
        if raw_id.isdigit():
            post_id = int(raw_id)
            post = await db.get_post_by_id(post_id)
            if post:
                # Vérifie si l'utilisateur possède déjà la photo
                already_purchased = await db.has_user_purchased(user_id, post_id)
                if already_purchased:
                    if post["media_type"] == "video":
                        await bot.send_video(
                            chat_id=user_id,
                            video=post["file_id"],
                            caption=f"✅ **{post['title']}**\n*(Vous possédez déjà ce média !)*",
                            parse_mode="Markdown"
                        )
                    else:
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=post["file_id"],
                            caption=f"✅ **{post['title']}**\n*(Vous possédez déjà cette photo !)*",
                            parse_mode="Markdown"
                        )
                    return

                # Envoi direct du média payant flouté avec l'API officielle send_paid_media !
                if post["media_type"] == "video":
                    media_item = InputPaidMediaVideo(media=post["file_id"])
                else:
                    media_item = InputPaidMediaPhoto(media=post["file_id"])

                await bot.send_paid_media(
                    chat_id=user_id,
                    star_count=post["star_count"],
                    media=[media_item],
                    caption=f"📸 **{post['title']}**\n\nClic sur la photo pour la débloquer 👆",
                    payload=post["payload"],
                    parse_mode="Markdown"
                )
                return

    # 2. Vérification si le lien ouvre la galerie globale (ex: /start galerie)
    if command.args in ("galerie", "catalogue", "photos"):
        bot_info = await bot.get_me()
        await show_catalog_page(message, db, page=0, is_new_message=True, bot_username=bot_info.username, is_admin=is_admin)
        return

    if is_admin:
        admin_badge = "👑 **Vous avez été configuré comme Administrateur du bot !**\n\n" if auto_promoted else ""
        welcome_text = (
            f"👋 **Bonjour {first_name} ! (Espace Créateur / Admin)**\n\n"
            f"{admin_badge}"
            "Ce bot vous permet de monétiser vos photos et vidéos grâce aux **Étoiles Telegram (Stars)**.\n\n"
            "🛠️ **Vos commandes :**\n"
            "• `/vendre` ou bouton **📸 Vendre une photo** : Mettre en vente un nouveau cliché flouté.\n"
            "• `/stats` ou bouton **📊 Mes Ventes** : Consulter vos gains en étoiles et vos meilleures ventes.\n"
            "• `/catalogue` : Parcourir l'ensemble des clichés disponibles.\n"
            "• `/mesliens` : Voir la liste de tous vos liens directs par photo.\n\n"
            "💡 *Chaque photo mise en vente est masquée/floutée par Telegram jusqu'à ce que l'acheteur verse les étoiles requises.*"
        )
        await message.answer(welcome_text, reply_markup=get_main_menu(is_admin=True), parse_mode="Markdown")
    else:
        # Pour un visiteur ou client qui clique sur https://t.me/Miwaysrbot sans argument :
        # On lui affiche directement le catalogue avec vos photos pour qu'il puisse débloquer celle qu'il veut !
        bot_info = await bot.get_me()
        await show_catalog_page(message, db, page=0, is_new_message=True, bot_username=bot_info.username, is_admin=False)

# ==============================================================================
# Commande /aide ou bouton d'information
# ==============================================================================
@user_router.message(Command("aide"))
@user_router.message(F.text == "ℹ️ Comment ça marche ?")
@user_router.message(F.text == "ℹ️ Aide")
async def cmd_help(message: Message, config: Config):
    is_admin = config.is_admin(message.from_user.id)

    help_text = (
        "🌟 **Guide d'utilisation des Étoiles Telegram (Telegram Stars)**\n\n"
        "**Qu'est-ce que les Étoiles Telegram ?**\n"
        "Les Étoiles (⭐️) sont la monnaie numérique officielle de Telegram. "
        "Elles permettent d'acheter des contenus numériques directement dans l'application, "
        "de manière 100% sécurisée via l'App Store, Google Play ou Fragment.\n\n"
        "**Comment débloquer une photo ?**\n"
        "1. Ouvrez le `/catalogue` ou observez les photos floutées sur notre canal.\n"
        "2. Cliquez sur le bouton indiquant le montant d'étoiles (ex: *Débloquer pour 20 ⭐️*).\n"
        "3. Telegram validera l'opération et la photo s'affichera immédiatement en grand format.\n\n"
    )

    if is_admin:
        help_text += (
            "👑 **Espace Administrateur :**\n"
            "- Pour vendre une photo : tapez `/vendre` et suivez les instructions pas-à-pas.\n"
            "- Pour voir vos recettes : tapez `/stats`.\n"
            "- Le bot utilise la méthode native `sendPaidMedia` de Telegram."
        )

    await message.answer(help_text, parse_mode="Markdown")

# ==============================================================================
# Commande /catalogue ou bouton d'exploration
# ==============================================================================
@user_router.message(Command("catalogue"))
@user_router.message(F.text == "🖼️ Explorer les photos")
@user_router.message(F.text == "🖼️ Catalogue Photos")
async def cmd_catalogue(message: Message, db: Database, config: Config, bot: Bot):
    is_admin = config.is_admin(message.from_user.id)
    bot_info = await bot.get_me()
    await show_catalog_page(message, db, page=0, is_new_message=True, bot_username=bot_info.username, is_admin=is_admin)

async def show_catalog_page(
    event: Message | CallbackQuery,
    db: Database,
    page: int = 0,
    is_new_message: bool = False,
    bot_username: str = "",
    is_admin: bool = False
):
    total_posts = await db.count_posts()
    if total_posts == 0:
        msg_text = "🏜️ Aucune photo de voyage n'est encore disponible dans le catalogue. Revenez très vite !"
        if is_new_message:
            await event.answer(msg_text)
        else:
            await event.message.edit_text(msg_text)
            await event.answer()
        return

    # Normalisation de la page
    page = max(0, min(page, total_posts - 1))

    posts = await db.get_recent_posts(limit=1, offset=page)
    if not posts:
        return

    post = posts[0]
    has_prev = page > 0
    has_next = (page + 1) < total_posts

    keyboard = get_catalog_item_keyboard(
        post_id=post["id"],
        star_count=post["star_count"],
        has_prev=has_prev,
        has_next=has_next,
        page=page,
        bot_username=bot_username,
        is_admin=is_admin
    )

    text = post['title']


    if is_new_message:
        await event.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await event.answer()

@user_router.callback_query(F.data.startswith("catalog_page:"))
async def handle_catalog_pagination(callback: CallbackQuery, db: Database, config: Config, bot: Bot):
    page = int(callback.data.split(":")[1])
    is_admin = config.is_admin(callback.from_user.id)
    bot_info = await bot.get_me()
    await show_catalog_page(
        callback,
        db,
        page=page,
        is_new_message=False,
        bot_username=bot_info.username,
        is_admin=is_admin
    )

# ==============================================================================
# Achat / Déblocage d'une photo depuis le catalogue
# ==============================================================================
@user_router.callback_query(F.data.startswith("buy_post:"))
async def handle_buy_post_from_catalog(callback: CallbackQuery, bot: Bot, db: Database):
    post_id = int(callback.data.split(":")[1])
    post = await db.get_post_by_id(post_id)

    if not post:
        await callback.answer("Photo introuvable ou supprimée.", show_alert=True)
        return

    # Vérification si l'utilisateur a déjà acheté
    already_purchased = await db.has_user_purchased(callback.from_user.id, post_id)
    if already_purchased:
        # Envoie directement la photo sans redemander d'étoiles
        if post["media_type"] == "video":
            await bot.send_video(
                chat_id=callback.from_user.id,
                video=post["file_id"],
                caption=f"✅ **{post['title']}**\n*(Vous possédez déjà cette vidéo !)*",
                parse_mode="Markdown"
            )
        else:
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=post["file_id"],
                caption=f"✅ **{post['title']}**\n*(Vous possédez déjà cette photo !)*",
                parse_mode="Markdown"
            )
        await callback.answer("Vous possédez déjà ce cliché !")
        return

    # Envoi du média payant flouté avec la méthode native send_paid_media
    if post["media_type"] == "video":
        media_item = InputPaidMediaVideo(media=post["file_id"])
    else:
        media_item = InputPaidMediaPhoto(media=post["file_id"])

    try:
        await bot.send_paid_media(
            chat_id=callback.from_user.id,
            star_count=post["star_count"],
            media=[media_item],
            caption=f"📸 **{post['title']}**\n\nClic sur la photo pour la débloquer 👆",
            payload=post["payload"],
            parse_mode="Markdown"
        )
        await callback.answer("Photo envoyée sous forme payante ci-dessous !")
    except Exception as e:
        await callback.answer(f"Erreur lors de l'envoi : {e}", show_alert=True)
