# game/engine.py
import os

class GameEngine:
    def __init__(self, storage):
        self.storage = storage

    def page_index(self, user_id=None):
        if user_id:
            # user_id est maintenant le Common Name (Alice, Bob, etc.)
            content = [
                f"# CryptoQuest — Bienvenue de retour {user_id} !",
                "",
                f"Ravi de vous revoir {user_id} ! Votre aventure vous attend.",
                "",
                "=> /cgi-bin/router.py/chapter1 Continuer l'aventure",
                "=> /cgi-bin/router.py/profile Voir mon profil",
                "",
                f"***",
                f"*Vous êtes identifié via votre certificat client (CN: {user_id}).*"
            ]
        else:
            content = [
                "# CryptoQuest — Bienvenue",
                "",
                "Bienvenue dans votre aventure Gemini !",
                "",
                "=> /cgi-bin/router.py/register Créer votre identité",
                "=> /cgi-bin/router.py/profile Se présenter",
                "=> /cgi-bin/router.py/chapter1 Commencer l'aventure"
            ]
        
        return "20 text/gemini\r\n" + "\n".join(content)

    def chapter1(self, user_id):
        user = self.storage.load_user(user_id) if user_id else None
        
        status = f"Identifié : {user_id} (Étape: {user['stage']})" if user else "Anonyme"
        
        return ("20 text/gemini\r\n"
                "# Chapitre 1 — Étape 1\n"
                f"Statut actuel : {status}\n\n"
                "Indice : C'est le tout début. (Ce sera l'énigme du 'dragon' plus tard).\n\n"
                "Pour continuer, vous devez vous identifier si ce n'est pas déjà fait.\n\n"
                "=> /cgi-bin/router.py Retour à l'accueil\n")