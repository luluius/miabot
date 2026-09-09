from aiogram import Router, Bot
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.database import Database

inline_router = Router(name="inline_router")

@inline_router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, db: Database, bot: Bot):
    """
    Permet d'envoyer une photo payante directement dans N'IMPORTE QUELLE discussion privée
    en tapant simplement @NomDuBot dans le champ de saisie !
    """
    bot_info = await bot.get_me()
    query = inline_query.query.strip().lower()

    # Récupération des photos disponibles
    posts = await db.get_recent_posts(limit=25)
    results = []

    for post in posts:
        post_title = post["title"]
        post_id = post["id"]
        star_count = post["star_count"]

        # Filtre de recherche si l'utilisateur a tapé du texte
        if query:
            if query not in post_title.lower() and query != f"photo_{post_id}" and query != str(post_id):
                continue

        deep_link = f"https://t.me/{bot_info.username}?start=photo_{post_id}"

        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🔓 Débloquer ma photo ({star_count} ⭐️)",
                        url=deep_link
                    )
                ]
            ]
        )

        message_text = (
            f"📸 **{post_title}**\n\n"
            f"Pour voir ma photo exclusive sans le flou, débloque-la juste ici 🙈👇\n"
            f"*(Tarif : {star_count} Étoiles Telegram ⭐️)*"
        )

        results.append(
            InlineQueryResultArticle(
                id=f"post_{post_id}",
                title=f"📸 {post_title} ({star_count} ⭐️)",
                description=f"Envoyer ma photo ({star_count} étoiles)",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="Markdown"
                ),
                reply_markup=reply_markup
            )
        )

    await inline_query.answer(results, cache_time=2, is_personal=True)
