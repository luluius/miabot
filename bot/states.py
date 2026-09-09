from aiogram.fsm.state import State, StatesGroup

class SellPhotoStates(StatesGroup):
    """Machine à états pour le processus de mise en vente et d'envoi direct d'un média."""
    waiting_for_media = State()       # Attente de la photo ou de la vidéo
    waiting_for_title = State()       # Attente du titre / descriptif du voyage
    waiting_for_price = State()       # Attente du prix en Étoiles Telegram
    waiting_for_destination = State() # Choix de la destination (Canal, Catalogue, Abonnés)
    confirm_publish = State()         # Confirmation finale avant publication
    waiting_for_fan_id = State()      # Attente de l'identifiant du fan pour envoi direct
