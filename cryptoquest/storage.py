import os
import json
from encrypt_utils import encrypt_blob, decrypt_blob

class Storage:
    def __init__(self, filename="data/users.json.enc"):
        self.filename = filename
        # Clé de chiffrement fixe pour la démo
        self.password = "demo_key"
    
    def load_data(self):
        """Charge les données chiffrées"""
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, "rb") as f:
                encrypted = f.read()
            decrypted = decrypt_blob(encrypted, self.password)
            return json.loads(decrypted)
        except Exception:
            return {}
    
    def save_data(self, data):
        """Sauvegarde les données chiffrées"""
        json_str = json.dumps(data, indent=2)
        encrypted = encrypt_blob(json_str.encode(), self.password)
        with open(self.filename, "wb") as f:
            f.write(encrypted)
    
    def load_user(self, username):
        """Charge les données d'un utilisateur"""
        data = self.load_data()
        return data.get('users', {}).get(username)
    
    def ensure_user(self, username):
        """Crée un utilisateur s'il n'existe pas"""
        data = self.load_data()
        if 'users' not in data:
            data['users'] = {}
        if username not in data['users']:
            data['users'][username] = {
                'username': username,
                'current_stage': 'intro',
                'progress': 0,
                'score': 0
            }
            self.save_data(data)
        return data['users'][username]
    
    def update_user_progress(self, username, stage, progress):
        """Met à jour la progression d'un utilisateur"""
        data = self.load_data()
        if 'users' in data and username in data['users']:
            data['users'][username]['current_stage'] = stage
            data['users'][username]['progress'] = progress
            self.save_data(data)
    
    def save_cert_mapping(self, fingerprint, username):
        """Sauvegarde l'association fingerprint -> username"""
        data = self.load_data()
        if 'cert_mappings' not in data:
            data['cert_mappings'] = {}
        data['cert_mappings'][fingerprint] = username
        self.save_data(data)
    
    def get_username_from_fingerprint(self, fingerprint):
        """Récupère le username depuis le fingerprint"""
        data = self.load_data()
        return data.get('cert_mappings', {}).get(fingerprint)