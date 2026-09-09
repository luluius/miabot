from bot.handlers.admin import admin_router
from bot.handlers.user import user_router
from bot.handlers.payments import payments_router
from bot.handlers.inline import inline_router

__all__ = ["admin_router", "user_router", "payments_router", "inline_router"]
