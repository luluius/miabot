from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import Optional

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Clavier principal affiché au bas du chat."""
    if is_admin:
        keyboard = [
            [KeyboardButton(text="📸 Vendre une photo"), KeyboardButton(text="📤 Envoyer en privé")],
            [KeyboardButton(text="📊 Mes Ventes / Stats"), KeyboardButton(text="🖼️ Catalogue Photos")],
            [KeyboardButton(text="ℹ️ Aide")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="🖼️ Explorer les photos"), KeyboardButton(text="ℹ️ Comment ça marche ?")],
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """Bouton inline simple pour annuler l'action en cours."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Annuler l'opération", callback_data="cancel_action")]
        ]
    )

def get_destination_keyboard(has_default_channel: bool = False) -> InlineKeyboardMarkup:
    """Choix de l'endroit où publier le média payant."""
    buttons = [
        [
            InlineKeyboardButton(text="💬 Envoi Privé (Lien & Partage 1-clic)", callback_data="dest:private")
        ]
    ]
    if has_default_channel:
        buttons.append([
            InlineKeyboardButton(text="📢 Publier sur mon Canal Telegram", callback_data="dest:channel")
        ])
    buttons.append([
        InlineKeyboardButton(text="🤖 Ajouter au Catalogue du Bot", callback_data="dest:catalog")
    ])
    buttons.append([
        InlineKeyboardButton(text="👥 Diffuser à tous les abonnés du Bot", callback_data="dest:broadcast")
    ])
    if has_default_channel:
        buttons.append([
            InlineKeyboardButton(text="🚀 Partout (Canal + Catalogue + Abonnés)", callback_data="dest:all")
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Annuler", callback_data="cancel_action")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Boutons de validation finale avant publication."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirmer et publier", callback_data="confirm_publish:yes"),
                InlineKeyboardButton(text="❌ Annuler", callback_data="confirm_publish:no"),
            ]
        ]
    )

import urllib.parse

def get_share_keyboard(post_id: int, star_count: int, bot_username: str) -> InlineKeyboardMarkup:
    """Boutons pour partager rapidement un média payant à un contact en privé."""
    deep_link = f"https://t.me/{bot_username}?start=photo_{post_id}"
    encoded_url = urllib.parse.quote_plus(deep_link)
    share_url = f"https://t.me/share/url?url={encoded_url}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 Envoyer à un contact privé",
                    url=share_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Choisir un chat (Mode Inline)",
                    switch_inline_query=f"photo_{post_id}"
                )
            ]
        ]
    )

def get_confirm_delete_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Clavier de confirmation pour supprimer une photo."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Oui, supprimer définitivement", callback_data=f"confirm_delete:{post_id}"),
                InlineKeyboardButton(text="❌ Non, annuler", callback_data="cancel_delete"),
            ]
        ]
    )

def get_catalog_item_keyboard(post_id: int, star_count: int, has_prev: bool, has_next: bool, page: int, bot_username: Optional[str] = None, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Clavier pour naviguer dans le catalogue et acheter ou gérer une photo."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"⭐️ Débloquer pour {star_count} Étoiles",
                callback_data=f"buy_post:{post_id}"
            )
        ]
    ]

    if is_admin:
        admin_row = []
        if bot_username:
            deep_link = f"https://t.me/{bot_username}?start=photo_{post_id}"
            encoded_url = urllib.parse.quote_plus(deep_link)
            share_url = f"https://t.me/share/url?url={encoded_url}"
            admin_row.append(InlineKeyboardButton(text="📲 Partager", url=share_url))
        admin_row.append(InlineKeyboardButton(text="🗑️ Supprimer", callback_data=f"ask_delete:{post_id}"))
        buttons.append(admin_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
