# storage.py
# Module simple pour stocker l'état utilisateur chiffré avec AES-GCM.
# - utilise une clé maître (master_key.bin) pour chiffrer users.json.enc
# - fournit load_user, save_user, ensure_user

import os, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class Storage:
    def __init__(self, data_file="data/users.json.enc", master_key_file="keys/master_key.bin"):
        self.data_file = data_file
        self.master_key_file = master_key_file
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        os.makedirs(os.path.dirname(master_key_file), exist_ok=True)
        # crée une master key si elle n'existe pas (32 octets = AES-256)
        if not os.path.exists(master_key_file):
            with open(master_key_file, "wb") as f:
                f.write(os.urandom(32))
        with open(master_key_file, "rb") as f:
            self.master_key = f.read()
        # initialise le fichier chiffré s'il n'existe pas
        if not os.path.exists(self.data_file):
            self._save_encrypted({})

    def _load_encrypted(self):
        # retourne un dict python
        if not os.path.exists(self.data_file):
            return {}
        data = open(self.data_file, "rb").read()
        if not data:
            return {}
        aesgcm = AESGCM(self.master_key)
        nonce = data[:12]
        ct = data[12:]
        pt = aesgcm.decrypt(nonce, ct, None)
        return json.loads(pt.decode())

    def _save_encrypted(self, obj):
        aesgcm = AESGCM(self.master_key)
        nonce = os.urandom(12)
        pt = json.dumps(obj).encode()
        ct = aesgcm.encrypt(nonce, pt, None)
        open(self.data_file, "wb").write(nonce + ct)

    # charge l'objet user (dictionnaire) ou None
    def load_user(self, user_id):
        allu = self._load_encrypted()
        return allu.get(user_id)

    # sauvegarde un objet user (remplace ou ajoute)
    def save_user(self, user_id, user_obj):
        allu = self._load_encrypted()
        allu[user_id] = user_obj
        self._save_encrypted(allu)

    # crée un nouvel utilisateur si absent et retourne l'objet user
    def ensure_user(self, user_id):
        if user_id is None:
            return None
        u = self.load_user(user_id)
        if u is None:
            u = {"user_id": user_id, "stage": "intro", "inventory": [], "rsa_pub": None, "rsa_given": False}
            self.save_user(user_id, u)
        return u
