# game/engine.py
# Logique centrale du jeu : pages, vérification, distribution de clefs, énigme RSA.
# Utilise les modules puzzles/* et storage pour persistance.

import base64, hashlib, os
from game.puzzles.aes_links import gen_aes_key, encrypt_link, decrypt_link
from game.puzzles.hash_check import check_answer
from game.puzzles.rsa_keys import generate_rsa_keypair_for_user, encrypt_with_pubkey, serialize_private_key_pem

class GameEngine:
    def __init__(self, storage):
        self.storage = storage

    def page_index(self, user_id):
        if not user_id:
            return "59 Not found\r\n# Utilisateur manquant\r\nVeuillez fournir ?user=ton_nom\r\n"
        user = self.storage.ensure_user(user_id)
        return ("20 text/gemini\r\n"
                "# CryptoQuest — Accueil\r\n"
                f"Bonjour {user_id} !\n\n"
                "=> /chapter1 Commencer l'aventure\n"
                "=> /secret_link Voir le lien secret (nécessite la clé AES)\n"
                "=> /rsa_start Enigme finale (RSA)\n")

    def chapter1(self, user_id):
        user = self.storage.ensure_user(user_id)
        # Le joueur doit trouver "dragon"
        expected_hash = hashlib.sha256(b"dragon").hexdigest()
        # Nous affichons l'énigme ; la vérif est côté serveur via le hash stocké.
        return ("20 text/gemini\r\n"
                "# Chapitre 1 — La grotte\n"
                "Indice : c'est une créature qui crache du feu.\n\n"
                "Soumets via : /submit?puzzle=c1&answer=TA_REPONSE&user={}\n"
                f"(Le serveur compare le hash attendu : {expected_hash})\n").format(user_id)

    def handle_submit(self, user_id, puzzle, answer):
        user = self.storage.ensure_user(user_id)
        if puzzle == "c1":
            expected_hash = hashlib.sha256(b"dragon").hexdigest()
            if check_answer(answer, expected_hash):
                # Génère une clef AES pour l'utilisateur et la range dans inventory (b64)
                aes_key = gen_aes_key()
                user['inventory'].append({"aes_key": base64.b64encode(aes_key).decode()})
                user['stage'] = "after_c1"
                self.storage.save_user(user_id, user)
                return ("20 text/gemini\r\n"
                        "# Correct !\n"
                        "Tu as reçu une clé AES. Utilise-la pour déchiffrer le lien secret via /secret_link?user={}\n").format(user_id)
            else:
                return ("59 Not permitted\r\n"
                        "# Mauvaise réponse\n"
                        "Réessaie.\n")
        return "59 Not permitted\r\n# Puzzle inconnu\n"

    def reveal_link(self, user_id):
        user = self.storage.ensure_user(user_id)
        # lien secret vers chapitre final (la suite)
        secret_url = f"gemini://localhost/chapitre_final?user={user_id}"
        # Si le joueur a une clé AES, le serveur chiffre le lien avec cette clé et le déchiffre pour le montrer (démo)
        # En vrai: on montre le ciphertext et le joueur déchiffre localement
        # Récupère première clé AES de l'inventaire si elle existe
        aes_key_b64 = None
        for it in user.get("inventory", []):
            if "aes_key" in it:
                aes_key_b64 = it["aes_key"]
                break
        if aes_key_b64:
            aes_key = base64.b64decode(aes_key_b64)
            ciphertext = encrypt_link(aes_key, secret_url)
            # retourne le ciphertext et propose au joueur de déchiffrer localement (ou on déchiffre serveur-side)
            # ici pour la démo on déchiffre et montre le lien clair
            try:
                clear = decrypt_link(aes_key, ciphertext)
                return ("20 text/gemini\r\n"
                        "# Lien secret (déchiffré)\n"
                        f"Le lien : {clear}\n")
            except Exception:
                return ("20 text/gemini\r\n"
                        "# Lien secret (chiffré)\n"
                        f"Ciphertext (base64): {ciphertext}\n"
                        "Tu as une clé mais le déchiffrement a échoué (format/demo).\n")
        else:
            # pas de clé : on affiche seulement le ciphertext chiffré avec une clé inconnue
            # pour la démonstration on génère un ciphertext que le joueur ne peut pas déchiffrer
            random_key = os.urandom(32)
            ciphertext = encrypt_link(random_key, secret_url)
            return ("20 text/gemini\r\n"
                    "# Lien secret (chiffré)\n"
                    f"Ciphertext (base64) : {ciphertext}\n"
                    "Tu n'as pas encore la clé AES. Résous /chapter1 pour l'obtenir.\n")

    # RSA final : on génère pour l'utilisateur une paire clé publique/privée
    # On donne la clé privée au joueur (pour qu'il déchiffre le message final localement).
    def rsa_start(self, user_id):
        user = self.storage.ensure_user(user_id)
        if user.get("rsa_given"):
            return ("20 text/gemini\r\n"
                    "# RSA déjà généré\n"
                    "Tu as déjà reçu ta paire de clés. Déchiffre le message final avec ta clé privée.\n")
        # génère paire RSA pour ce joueur ; retourne la clé privée PEM à sauvegarder (démonstration)
        private_pem, public_pem = generate_rsa_keypair_for_user()
        # sauvegarde la clé publique côté serveur pour chiffrer le message final
        user['rsa_pub'] = public_pem.decode()
        user['rsa_given'] = True
        self.storage.save_user(user_id, user)
        # on renvoie la clé privée PEM en clair pour que le joueur la récupère (dans un vrai contexte, le joueur générerait la clé localement)
        return ("20 text/gemini\r\n"
                "# Énigme finale RSA — génération de paire\n\n"
                "Garde précieusement ta clé privée PEM suivante (copie locale !) :\n\n"
                f"----- PRIVATE KEY BEGIN -----\n{private_pem.decode()}\n----- PRIVATE KEY END -----\n\n"
                "Le serveur a chiffré un message avec ta clé publique. Déchiffre-le localement et soumets la preuve si demandé.\n")

    def rsa_submit(self, user_id, sol_hex):
        # Par simplicité ce endpoint vérifie que l'utilisateur a déjà la paire et marque comme réussi si sol_hex non vide.
        user = self.storage.ensure_user(user_id)
        if not user.get("rsa_given"):
            return "59 Not permitted\r\n# Pas de clé RSA associée à l'utilisateur\n"
        if not sol_hex:
            return "59 Not permitted\r\n# Solution manquante\n"
        # dans ce prototype, on accepte toute solution non vide comme réussite (adapter selon scénario)
        user['stage'] = "finished"
        self.storage.save_user(user_id, user)
        return ("20 text/gemini\r\n"
                "# Bravo !\n"
                "Tu as terminé CryptoQuest. Message final : FLAG{cryptoquest_demo}\n")
