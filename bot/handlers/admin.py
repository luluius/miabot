import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputPaidMediaPhoto, InputPaidMediaVideo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.config import Config
from bot.database import Database
from bot.states import SellPhotoStates
from bot.keyboards import (
    get_cancel_inline_keyboard,
    get_destination_keyboard,
    get_confirm_keyboard,
    get_main_menu,
)

admin_router = Router(name="admin_router")

# ==============================================================================
# 1. Démarrage de la mise en vente (/vendre ou bouton de menu)
# ==============================================================================
@admin_router.message(Command("vendre"))
@admin_router.message(F.text == "📸 Vendre une photo")
async def start_sell_photo(message: Message, state: FSMContext, config: Config):
    if not config.is_admin(message.from_user.id):
        await message.answer("⛔ Cette commande est réservée à l'administrateur du bot.")
        return

    await state.clear()
    await state.set_state(SellPhotoStates.waiting_for_media)
    await message.answer(
        "📸 **Mise en vente d'un média de voyage**\n\n"
        "Veuillez envoyer la **photo** (ou **vidéo**) que vous souhaitez mettre en vente contre des Étoiles Telegram.",
        reply_markup=get_cancel_inline_keyboard(),
        parse_mode="Markdown"
    )

# ==============================================================================
# Annulation de l'opération en cours
# ==============================================================================
@admin_router.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: CallbackQuery, state: FSMContext, config: Config):
    await state.clear()
    await callback.message.edit_text("❌ L'opération a été annulée.")
    await callback.answer("Annulé")

# ==============================================================================
# 2. Réception de la photo ou de la vidéo
# ==============================================================================
@admin_router.message(SellPhotoStates.waiting_for_media, F.photo)
async def process_photo_received(message: Message, state: FSMContext):
    # La plus haute résolution est le dernier élément de photo
    file_id = message.photo[-1].file_id
    await state.update_data(file_id=file_id, media_type="photo")
    await state.set_state(SellPhotoStates.waiting_for_title)
    await message.answer(
        "✅ **Photo reçue avec succès !**\n\n"
        "Entrez maintenant un **titre** ou une **description** pour cette photo de voyage.\n"
        "*(Exemple : Coucher de soleil sur les falaises de Santorin 🌅)*",
        reply_markup=get_cancel_inline_keyboard(),
        parse_mode="Markdown"
    )

@admin_router.message(SellPhotoStates.waiting_for_media, F.video)
async def process_video_received(message: Message, state: FSMContext):
    file_id = message.video.file_id
    await state.update_data(file_id=file_id, media_type="video")
    await state.set_state(SellPhotoStates.waiting_for_title)
    await message.answer(
        "✅ **Vidéo reçue avec succès !**\n\n"
        "Entrez maintenant un **titre** ou une **description** pour cette vidéo de voyage.\n"
        "*(Exemple : Plongée avec les tortues à Bali 🐢)*",
        reply_markup=get_cancel_inline_keyboard(),
        parse_mode="Markdown"
    )

@admin_router.message(SellPhotoStates.waiting_for_media)
async def invalid_media(message: Message):
    await message.answer(
        "⚠️ Format non reconnu. Veuillez envoyer une **photo** ou une **vidéo**.",
        reply_markup=get_cancel_inline_keyboard(),
        parse_mode="Markdown"
    )

# ==============================================================================
# 3. Réception du titre / descriptif
# ==============================================================================
@admin_router.message(SellPhotoStates.waiting_for_title, F.text)
async def process_title_received(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) > 500:
        await message.answer("⚠️ Le titre est trop long (maximum 500 caractères). Réessayez :")
        return

    await state.update_data(title=title)
    await state.set_state(SellPhotoStates.waiting_for_price)
    await message.answer(
        f"📝 Titre enregistré : *{title}*\n\n"
        "⭐ **Combien d'Étoiles Telegram (⭐️) demandez-vous pour débloquer ce média ?**\n"
        "*(Entrez un nombre entier, par exemple : 10, 25, 50, 100)*",
        reply_markup=get_cancel_inline_keyboard(),
        parse_mode="Markdown"
    )

# ==============================================================================
# 4. Réception du prix en étoiles
# ==============================================================================
@admin_router.message(SellPhotoStates.waiting_for_price, F.text)
async def process_price_received(message: Message, state: FSMContext, config: Config):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(
            "⚠️ Le prix doit être un nombre entier d'étoiles (ex: 20). Veuillez réessayer :",
            reply_markup=get_cancel_inline_keyboard()
        )
        return

    price = int(text)
    if price < 1 or price > 2500:
        await message.answer(
            "⚠️ Le montant doit être compris entre **1 et 2500 Étoiles** (limite de l'API Telegram).",
            reply_markup=get_cancel_inline_keyboard(),
            parse_mode="Markdown"
        )
        return

    await state.update_data(star_count=price)

    has_channel = bool(config.default_channel_id)
    await state.set_state(SellPhotoStates.waiting_for_destination)
    await message.answer(
        f"💰 Prix fixé à **{price} ⭐️** !\n\n"
        "Où souhaitez-vous mettre à disposition ce média payant ?",
        reply_markup=get_destination_keyboard(has_default_channel=has_channel),
        parse_mode="Markdown"
    )

# ==============================================================================
# 5. Choix de la destination
# ==============================================================================
@admin_router.callback_query(SellPhotoStates.waiting_for_destination, F.data.startswith("dest:"))
async def process_destination_choice(callback: CallbackQuery, state: FSMContext):
    dest = callback.data.split(":", 1)[1]
    await state.update_data(destination=dest)

    data = await state.get_data()
    dest_labels = {
        "private": "💬 Envoi Privé uniquement (Lien et bouton de partage 1-clic)",
        "channel": "📢 Canal Telegram officiel",
        "catalog": "🤖 Catalogue du bot uniquement",
        "broadcast": "👥 Message direct à tous les abonnés du bot",
        "all": "🚀 Partout (Canal + Catalogue + Abonnés)"
    }

    summary = (
        "🔍 **Récapitulatif avant publication**\n\n"
        f"📸 **Type :** {data.get('media_type', 'photo').capitalize()}\n"
        f"📝 **Titre :** {data.get('title')}\n"
        f"⭐ **Prix :** {data.get('star_count')} Étoiles Telegram\n"
        f"📍 **Destination :** {dest_labels.get(dest, dest)}\n\n"
        "Telegram affichera automatiquement le média sous forme **floutée/verrouillée** "
        "avec un bouton permettant aux utilisateurs de le débloquer contre des étoiles.\n\n"
        "Voulez-vous confirmer la publication ?"
    )

    await state.set_state(SellPhotoStates.confirm_publish)
    await callback.message.edit_text(summary, reply_markup=get_confirm_keyboard(), parse_mode="Markdown")
    await callback.answer()

# ==============================================================================
# 6. Confirmation finale et publication avec send_paid_media
# ==============================================================================
@admin_router.callback_query(SellPhotoStates.confirm_publish, F.data.startswith("confirm_publish:"))
async def process_confirm_publish(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    config: Config,
    db: Database
):
    action = callback.data.split(":", 1)[1]
    if action != "yes":
        await state.clear()
        await callback.message.edit_text("❌ Publication annulée.")
        await callback.answer("Annulé")
        return

    data = await state.get_data()
    file_id = data["file_id"]
    media_type = data["media_type"]
    title = data["title"]
    star_count = data["star_count"]
    destination = data["destination"]

    # Création d'un identifiant payload unique pour cette vente
    payload = f"travel_{uuid.uuid4().hex[:12]}"

    # Préparation de l'objet PaidMedia
    if media_type == "video":
        paid_media = [InputPaidMediaVideo(media=file_id)]
    else:
        paid_media = [InputPaidMediaPhoto(media=file_id)]

    channel_msg_id = None
    channel_id_used = None
    status_messages = []

    # 1. Enregistrement en base de données
    post_id = await db.create_post(
        title=title,
        description="",
        star_count=star_count,
        media_type=media_type,
        file_id=file_id,
        payload=payload,
        channel_id=None,
        channel_msg_id=None
    )

    bot_info = await bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start=photo_{post_id}"

    # 2. Publication sur le canal Telegram si demandé
    if destination in ("channel", "all") and config.default_channel_id:
        try:
            sent_msg = await bot.send_paid_media(
                chat_id=config.default_channel_id,
                star_count=star_count,
                media=paid_media,
                caption=f"📸 **{title}**\n\nClic sur la photo pour la débloquer 👆",
                payload=payload,
                parse_mode="Markdown"
            )
            channel_msg_id = sent_msg.message_id
            channel_id_used = str(config.default_channel_id)
            await db.update_post_channel_info(post_id, channel_id_used, channel_msg_id)
            status_messages.append(f"📢 Publié sur le canal `{config.default_channel_id}` !")
        except Exception as e:
            status_messages.append(f"⚠️ Erreur lors de la publication sur le canal : `{e}`")

    # 3. Diffusion aux abonnés si demandée
    if destination in ("broadcast", "all"):
        subscribers = await db.get_all_subscribers()
        sent_count = 0
        for sub_id in subscribers:
            if sub_id == callback.from_user.id:
                continue
            try:
                await bot.send_paid_media(
                    chat_id=sub_id,
                    star_count=star_count,
                    media=paid_media,
                    caption=f"📸 **{title}**\n\nClic sur la photo pour la débloquer 👆",
                    payload=payload,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception:
                pass
        status_messages.append(f"👥 Diffusé à {sent_count} abonné(s) du bot !")

    # 4. Ajout au catalogue
    if destination in ("catalog", "all"):
        status_messages.append("🤖 Disponible dans le `/catalogue` du bot.")

    # 5. Options pour envoi privé direct
    from bot.keyboards import get_share_keyboard
    share_kb = get_share_keyboard(post_id=post_id, star_count=star_count, bot_username=bot_info.username)

    await state.clear()
    status_summary = ("\n".join(status_messages) + "\n\n") if status_messages else ""
    final_text = (
        "🎉 **Votre média est prêt à être vendu en privé !**\n\n"
        f"{status_summary}"
        f"🔗 **Lien direct pour vos contacts :**\n`{deep_link}`\n\n"
        "👉 Cliquez sur le bouton ci-dessous pour l'envoyer en 1 clic dans une discussion privée avec n'importe qui sur Telegram !"
    )

    await callback.message.edit_text(final_text, reply_markup=share_kb, parse_mode="Markdown")
    await callback.answer("Prêt à l'envoi !")

# ==============================================================================
# Statistiques des ventes (/stats ou bouton)
# ==============================================================================
@admin_router.message(Command("stats"))
@admin_router.message(F.text == "📊 Mes Ventes / Stats")
async def show_stats(message: Message, db: Database, config: Config):
    if not config.is_admin(message.from_user.id):
        await message.answer("⛔ Cette commande est réservée à l'administrateur du bot.")
        return

    stats = await db.get_stats()
    top_posts_text = ""
    if stats["top_posts"]:
        top_posts_text = "\n\n🏆 **Top des photos les plus vendues :**\n"
        for i, p in enumerate(stats["top_posts"], 1):
            top_posts_text += f"{i}. *{p['title']}* — {p['sales_count']} vente(s) ({p['stars']} ⭐️)\n"

    report = (
        "📊 **Tableau de Bord des Ventes - Telegram Stars**\n\n"
        f"⭐ **Total Étoiles récoltées :** `{stats['total_stars']}` ⭐️\n"
        f"🛍️ **Nombre total de ventes :** `{stats['sales_count']}`\n"
        f"📸 **Photos au catalogue :** `{stats['posts_count']}`\n"
        f"👥 **Abonnés actifs au bot :** `{stats['subscribers_count']}`"
        f"{top_posts_text}"
    )

    await message.answer(report, parse_mode="Markdown")

# ==============================================================================
# Commande /envoyer ou bouton "📤 Envoyer en privé"
# ==============================================================================
@admin_router.message(Command("envoyer"))
@admin_router.message(F.text == "📤 Envoyer en privé")
async def cmd_send_private(message: Message, bot: Bot, db: Database, config: Config):
    if not config.is_admin(message.from_user.id):
        await message.answer("⛔ Cette commande est réservée à l'administrateur du bot.")
        return

    posts = await db.get_recent_posts(limit=10)
    if not posts:
        await message.answer(
            "⚠️ Vous n'avez pas encore mis de photo en vente !\n"
            "Utilisez la commande `/vendre` pour créer votre premier contenu payant."
        )
        return

    bot_info = await bot.get_me()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for p in posts:
        buttons.append([
            InlineKeyboardButton(
                text=f"📸 {p['title']} ({p['star_count']} ⭐️)",
                callback_data=f"send_pick:{p['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "📤 **Choisissez la photo de voyage que vous souhaitez envoyer en privé :**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data.startswith("send_pick:"))
async def handle_send_pick(callback: CallbackQuery, state: FSMContext, db: Database):
    post_id = int(callback.data.split(":")[1])
    post = await db.get_post_by_id(post_id)

    if not post:
        await callback.answer("Photo introuvable.")
        return

    # Sauvegarder le post_id choisi dans l'état FSM
    await state.update_data(send_post_id=post_id)

    from bot.states import SellPhotoStates
    await state.set_state(SellPhotoStates.waiting_for_fan_id)

    await callback.message.edit_text(
        f"📸 **{post['title']}** ({post['star_count']} ⭐️)\n\n"
        "✏️ **Entrez l'identifiant Telegram du fan** (son @username ou son numéro ID) :\n\n"
        "💡 *Pour trouver l'ID de quelqu'un, il vous suffit de lui transférer un message depuis le bot @userinfobot.*\n\n"
        "Ou tapez **`/annuler`** pour revenir en arrière.",
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.message(F.text == "/annuler")
async def handle_cancel_send(message: Message, state: FSMContext, config: Config):
    if not config.is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("❌ Envoi annulé.", reply_markup=get_main_menu(is_admin=True))

@admin_router.message(SellPhotoStates.waiting_for_fan_id)
async def handle_fan_id_input(message: Message, state: FSMContext, bot: Bot, db: Database, config: Config):
    if not config.is_admin(message.from_user.id):
        return

    fan_input = message.text.strip().lstrip("@")
    data = await state.get_data()
    post_id = data.get("send_post_id")

    if not post_id:
        await state.clear()
        return

    post = await db.get_post_by_id(post_id)
    if not post:
        await state.clear()
        await message.answer("⚠️ Photo introuvable.")
        return

    # Résolution de l'identifiant : numérique ou username
    fan_chat_id = None
    if fan_input.lstrip("-").isdigit():
        fan_chat_id = int(fan_input)
    else:
        try:
            chat = await bot.get_chat(f"@{fan_input}")
            fan_chat_id = chat.id
        except Exception:
            await message.answer(
                f"⚠️ Impossible de trouver `@{fan_input}` sur Telegram.\n\n"
                "Le fan doit avoir démarré le bot au moins une fois **OU** vous devez entrer son **ID numérique** (ex: `123456789`).\n\n"
                "💡 *Demandez-lui d'envoyer un message à @userinfobot pour obtenir son ID.*",
                parse_mode="Markdown"
            )
            return

    # Envoi de la photo floutée directement dans le chat du fan
    if post["media_type"] == "video":
        media_item = InputPaidMediaVideo(media=post["file_id"])
    else:
        media_item = InputPaidMediaPhoto(media=post["file_id"])

    try:
        await bot.send_paid_media(
            chat_id=fan_chat_id,
            star_count=post["star_count"],
            media=[media_item],
            caption=f"📸 **{post['title']}**\n\nClic sur la photo pour la débloquer 👆",
            payload=post["payload"],
            parse_mode="Markdown"
        )
        await state.clear()
        await message.answer(
            f"✅ **Photo envoyée directement au fan !**\n\n"
            f"📸 *{post['title']}* ({post['star_count']} ⭐️) est maintenant visible dans sa discussion avec le bot, floutée et prête à débloquer.",
            parse_mode="Markdown",
            reply_markup=get_main_menu(is_admin=True)
        )
    except Exception as e:
        err = str(e)
        if "bot can't initiate conversation" in err or "Forbidden" in err:
            await message.answer(
                f"⚠️ **Le fan n'a jamais démarré le bot.**\n\n"
                "Il doit d'abord envoyer **n'importe quel message** à [@Miwaysrbot](https://t.me/Miwaysrbot) pour que le bot puisse lui écrire.\n\n"
                "➡️ Dites-lui : *« Envoie juste un message à @Miwaysrbot d'abord ! »*",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"⚠️ Erreur inattendue : `{err}`", parse_mode="Markdown")


# ==============================================================================
# Commande /mesliens (Récapitulatif de tous les liens secrets pour le clavier)
# ==============================================================================
@admin_router.message(Command("mesliens"))
async def cmd_my_links(message: Message, bot: Bot, db: Database, config: Config):
    if not config.is_admin(message.from_user.id):
        await message.answer("⛔ Cette commande est réservée à l'administrateur du bot.")
        return

    posts = await db.get_recent_posts(limit=50)
    if not posts:
        await message.answer("⚠️ Vous n'avez encore mis aucun média en vente.")
        return

    bot_info = await bot.get_me()
    lines = [
        "🔗 **Vos Liens Secrets & Raccourcis Clavier**\n",
        f"🌟 **Lien de votre Galerie Complète :**\n`https://t.me/{bot_info.username}?start=galerie`\n*(Raccourci suggéré : `!galerie`)*\n",
        "📸 **Liens individuels par photo :**"
    ]

    for p in posts:
        link = f"https://t.me/{bot_info.username}?start=photo_{p['id']}"
        lines.append(
            f"• **{p['title']}** ({p['star_count']} ⭐️) :\n`{link}`\n*(Raccourci suggéré : `!p{p['id']}`)*\n"
        )

    lines.append("💡 *Touchez un lien pour le copier en un clic sur votre iPhone !*")
    await message.answer("\n".join(lines), parse_mode="Markdown")

# ==============================================================================
# Suppression d'un média (/supprimer et callbacks)
# ==============================================================================
@admin_router.message(Command("supprimer"))
async def cmd_delete_media(message: Message, db: Database, config: Config):
    if not config.is_admin(message.from_user.id):
        await message.answer("⛔ Cette commande est réservée à l'administrateur du bot.")
        return

    posts = await db.get_recent_posts(limit=50)
    if not posts:
        await message.answer("⚠️ Aucune photo n'est actuellement enregistrée.")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for p in posts:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑️ Supprimer : {p['title']} ({p['star_count']} ⭐️)",
                callback_data=f"ask_delete:{p['id']}"
            )
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🗑️ **Choisissez le média que vous souhaitez supprimer :**", reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("ask_delete:"))
async def handle_ask_delete(callback: CallbackQuery, db: Database, config: Config):
    if not config.is_admin(callback.from_user.id):
        await callback.answer("Action réservée à l'admin.", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])
    post = await db.get_post_by_id(post_id)
    if not post:
        await callback.answer("Média introuvable.")
        return

    from bot.keyboards import get_confirm_delete_keyboard
    await callback.message.edit_text(
        f"⚠️ **Confirmation de suppression**\n\n"
        f"Voulez-vous vraiment supprimer définitivement :\n"
        f"📸 **{post['title']}** ({post['star_count']} Étoiles) ?\n\n"
        "Le lien de vente sera immédiatement désactivé et le média sera retiré du catalogue.",
        reply_markup=get_confirm_delete_keyboard(post_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("confirm_delete:"))
async def handle_confirm_delete(callback: CallbackQuery, db: Database, config: Config):
    if not config.is_admin(callback.from_user.id):
        await callback.answer("Action réservée à l'admin.", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])
    success = await db.delete_post(post_id)
    if success:
        await callback.message.edit_text("✅ **Le média a été supprimé avec succès.**", parse_mode="Markdown")
        await callback.answer("Supprimé !")
    else:
        await callback.message.edit_text("⚠️ Ce média n'existe plus ou a déjà été supprimé.")
        await callback.answer()

@admin_router.callback_query(F.data == "cancel_delete")
async def handle_cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Suppression annulée.")
    await callback.answer("Annulé")
