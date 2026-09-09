# 📸 Telegram Stars Travel Bot — Vente de Photos de Voyage

Ce bot Telegram permet aux créateurs de contenu, photographes et passionnés de voyage de **vendre leurs photos et vidéos de voyage contre des Étoiles Telegram (Telegram Stars ⭐️)**.

Le bot exploite la méthode officielle et native de l'API Telegram [`sendPaidMedia`](https://core.telegram.org/bots/api#sendpaidmedia) : les médias sont automatiquement présentés **floutés et verrouillés**. Dès qu'un utilisateur clique et valide le montant en Étoiles, Telegram débloque et affiche instantanément le cliché en haute définition.

---

## ✨ Fonctionnalités Clés

- 🔒 **Floutage et Déblocage Natif Telegram** : Aucun traitement d'image lourd requis sur votre machine. Telegram masque automatiquement l'image et affiche l'icône de l'Étoile et le prix que vous avez fixé.
- 📸 **Processus de Vente Assisté (`/vendre`)** :
  1. Envoi de la photo ou vidéo de voyage.
  2. Titre descriptif (ex: *Coucher de soleil à Santorin 🌅*).
  3. Définition du prix en Étoiles (ex: `25` ⭐️).
  4. Choix de la destination : **Canal Telegram**, **Catalogue public du bot**, ou **Diffusion aux abonnés**.
  5. Récapitulatif et confirmation.
- 🔔 **Notifications d'Achat en Temps Réel** : Dès qu'une personne débloque votre photo, le bot vous envoie une alerte privée avec le pseudo de l'acheteur et le nombre d'étoiles encaissées.
- 📊 **Tableau de Bord & Statistiques (`/stats`)** : Total des étoiles récoltées, nombre de ventes cumulées, top 5 des photos les plus populaires.
- 🖼️ **Catalogue Interactif pour les Visiteurs (`/catalogue`)** : N'importe quel utilisateur peut feuilleter vos clichés et les débloquer directement dans le chat.
- 💾 **Historique d'Achat Permanent** : Si un acheteur a déjà payé pour une photo, il peut la redemander à tout moment sans repayer d'étoiles.

---

## 📁 Structure du Projet

```
telegram-stars-travel-bot/
├── .env.example            # Modèle des variables de configuration
├── requirements.txt        # Dépendances (aiogram 3, aiosqlite, python-dotenv)
├── main.py                 # Point d'entrée du bot
├── bot/
│   ├── config.py           # Chargement et validation de l'environnement
│   ├── database.py         # Gestion de la base de données SQLite
│   ├── states.py           # États FSM pour le flux de vente
│   ├── keyboards.py        # Menus et boutons interactifs (inline et reply)
│   └── handlers/
│       ├── admin.py        # Vente de photo (/vendre), stats (/stats)
│       ├── user.py         # Accueil (/start), catalogue (/catalogue), aide (/aide)
│       └── payments.py     # Gestion des achats Telegram Stars (purchased_paid_media)
├── tests/
│   ├── test_database.py    # Tests unitaires de la base de données
│   └── test_config.py      # Tests unitaires de configuration
└── README.md
```

---

## 🚀 Guide d'Installation et de Démarrage

### 1. Créer le Bot sur Telegram

1. Ouvrez Telegram et cherchez le bot officiel [@BotFather](https://t.me/BotFather).
2. Tapez la commande `/newbot`.
3. Choisissez un nom pour votre bot (ex: *Mon Voyage Photos*) et un nom d'utilisateur se terminant par `bot` (ex: *MonVoyagePhotos_bot*).
4. Copiez le **Token d'accès API** fourni par BotFather.

### 2. (Optionnel mais recommandé) Activer les Étoiles sur BotFather

Les Étoiles Telegram (Telegram Stars) sont prises en charge nativement.
1. Toujours dans [@BotFather](https://t.me/BotFather), envoyez `/mybots`.
2. Sélectionnez votre bot.
3. Allez dans **Bot Settings** > **Payments** et assurez-vous que les Étoiles sont disponibles.

### 3. Trouver votre ID Telegram Administrateur

Pour sécuriser la commande `/vendre` et recevoir les alertes de vente :
1. Démarrez le bot [@userinfobot](https://t.me/userinfobot) sur Telegram.
2. Notez votre identifiant numérique (ex: `123456789`).

### 4. (Optionnel) Configurer un Canal Telegram

Si vous souhaitez diffuser vos photos floutées dans un canal public ou privé :
1. Créez un canal Telegram ou utilisez un canal existant.
2. Ajoutez votre bot comme **Administrateur** de ce canal (avec la permission *Publier des messages*).
3. Notez le `@nom_du_canal` (ou son identifiant commençant par `-100...`).

---

### 5. Installation Locale

Clonez ou rendez-vous dans le dossier du projet :
```bash
cd /Users/lulu/.gemini/antigravity/scratch/telegram-stars-travel-bot
```

Créez et activez un environnement virtuel Python :
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installez les dépendances :
```bash
pip install -r requirements.txt
```

### 6. Configurer le fichier `.env`

Créez une copie du fichier `.env.example` nommée `.env` :
```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos informations :
```env
# Token fourni par @BotFather
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Votre ID Telegram (obtenu via @userinfobot)
ADMIN_IDS=123456789

# (Optionnel) Votre canal où poster les photos
DEFAULT_CHANNEL_ID=@MonCanalVoyage

# Emplacement de la base SQLite
DATABASE_PATH=travel_bot.db
```

### 7. Lancer le Bot

Démarrez le bot avec la commande :
```bash
python3 main.py
```

Vous devriez voir s'afficher :
```text
Démarrage du Bot Telegram Stars - Photos de Voyage...
Base de données SQLite initialisée : travel_bot.db
Types d'updates écoutés : ['message', 'callback_query', 'purchased_paid_media', 'pre_checkout_query']
🚀 Le bot est en ligne et à l'écoute des messages et paiements !
```

---

## 🎮 Comment Utiliser le Bot ?

### Côté Vendeur / Administrateur
1. Ouvrez une discussion avec votre bot sur Telegram.
2. Tapez `/start` (le bot détectera que vous êtes administrateur).
3. Cliquez sur **📸 Vendre une photo** ou tapez `/vendre`.
4. Envoyez votre photo de voyage.
5. Donnez-lui un titre (ex: *"Coucher de soleil sur les pyramides de Gizeh 🇪🇬"*).
6. Entrez le prix en étoiles (ex: `20`).
7. Choisissez la destination (ex: *📢 Publier sur mon Canal Telegram* ou *🤖 Ajouter au Catalogue*).
8. Confirmez : Telegram publie le post **flouté avec le verrou officiel** !
9. À tout moment, tapez `/stats` pour voir vos gains totaux.

### Côté Acheteur / Public
1. L'utilisateur découvre le post flouté sur votre canal ou via la commande `/catalogue` dans le bot.
2. Il clique sur le bouton **⭐️ Débloquer pour X Étoiles**.
3. Telegram ouvre la fenêtre de confirmation et valide les étoiles.
4. L'image se défloute immédiatement et s'affiche en grand format.
5. Vous recevez immédiatement une notification avec son pseudo et vos étoiles gagnées !

---

## 🧪 Lancer les Tests

Pour vérifier le bon fonctionnement de la base de données et de la configuration :
```bash
.venv/bin/python -m unittest discover tests
```
