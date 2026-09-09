import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# Chargement du fichier .env
load_dotenv()

@dataclass
class Config:
    bot_token: str
    admin_ids: List[int] = field(default_factory=list)
    default_channel_id: Optional[str] = None
    database_path: str = "travel_bot.db"

    @classmethod
    def load(cls) -> "Config":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token == "ton_token_botfather_ici":
            raise ValueError(
                "BOT_TOKEN n'est pas configuré dans le fichier .env ! "
                "Obtenez un token auprès de @BotFather et renseignez-le."
            )

        admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
        admin_ids: List[int] = []
        if admin_ids_raw:
            for piece in admin_ids_raw.split(","):
                piece = piece.strip()
                if piece.isdigit() or (piece.startswith("-") and piece[1:].isdigit()):
                    admin_ids.append(int(piece))

        default_channel = os.getenv("DEFAULT_CHANNEL_ID", "").strip()
        channel_id = default_channel if default_channel else None

        db_path = os.getenv("DATABASE_PATH", "travel_bot.db").strip()

        return cls(
            bot_token=token,
            admin_ids=admin_ids,
            default_channel_id=channel_id,
            database_path=db_path,
        )

    def is_admin(self, user_id: int) -> bool:
        """Vérifie si un identifiant Telegram correspond à un administrateur."""
        if not self.admin_ids:
            return False
        return user_id in self.admin_ids

    def add_admin(self, user_id: int):
        """Ajoute dynamiquement un administrateur et met à jour le fichier .env."""
        if user_id not in self.admin_ids:
            self.admin_ids.append(user_id)
            env_file = ".env"
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    admin_str = ",".join(str(i) for i in self.admin_ids)
                    if "ADMIN_IDS=" in content:
                        import re
                        content = re.sub(r"ADMIN_IDS=.*", f"ADMIN_IDS={admin_str}", content)
                    else:
                        content += f"\nADMIN_IDS={admin_str}\n"
                    with open(env_file, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception:
                    pass


# Instance globale accessible dans l'application
try:
    config = Config.load()
except ValueError:
    # Permet l'import dans les environnements de test où .env n'est pas encore rempli
    config = Config(
        bot_token="DUMMY_TOKEN_FOR_INITIALIZATION",
        admin_ids=[],
        default_channel_id=None,
        database_path="travel_bot.db",
    )
