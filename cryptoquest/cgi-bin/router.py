#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import cgi
import datetime

# --- Configuration et Imports ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from storage import Storage
from game.engine import GameEngine 
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

# --- Debug ---
def debug_log(message):
    """Log de debug dans stderr"""
    print(f"DEBUG: {message}", file=sys.stderr)

# --- Fonctions de Certificat ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CA_KEY_PATH = os.path.join(BASE_DIR, "keys/server_key.pem")
CA_CERT_PATH = os.path.join(BASE_DIR, "keys/server_cert.pem")

def load_ca_data():
    with open(CA_KEY_PATH, "rb") as f:
        ca_private_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(CA_CERT_PATH, "rb") as f:
        ca_certificate = x509.load_pem_x509_certificate(f.read())
    return ca_private_key, ca_certificate

def generate_and_sign_certificate(username, ca_private_key, ca_certificate):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, username)])
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(private_key, hashes.SHA256())
    cert = x509.CertificateBuilder().subject_name(csr.subject).issuer_name(ca_certificate.subject).public_key(
        csr.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).sign(ca_private_key, hashes.SHA256())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    return private_pem

def get_friendly_username():
    """Récupère le username depuis le mapping stocké"""
    try:
        fingerprint = os.environ.get('TLS_CLIENT_HASH')
        debug_log(f"get_friendly_username - Fingerprint: {fingerprint}")
        
        if fingerprint:
            storage = Storage()
            username = storage.get_username_from_fingerprint(fingerprint)
            debug_log(f"get_friendly_username - Username trouvé: {username}")
            return username
        return None
    except Exception as e:
        debug_log(f"get_friendly_username - Erreur: {e}")
        return None

def is_certificate_connected():
    """Vérifie si un certificat client est détecté"""
    has_cert = os.environ.get('TLS_CLIENT_HASH') is not None
    debug_log(f"is_certificate_connected: {has_cert}")
    return has_cert

def handle_create_profile(form):
    """Crée un profil et l'associe au certificat"""
    query = os.environ.get("QUERY_STRING", "").strip()
    debug_log(f"handle_create_profile - Query: {query}")
    
    if not query:
        return "10 Choisissez un nom pour votre profil (ex: Alice, Bob)\r\n"
    
    username = query
    
    # Validation
    if not username.isalnum() or len(username) < 3:
        return ("20 text/gemini\r\n"
                "# ❌ Erreur\n"
                "Le nom doit contenir 3 caractères alphanumériques minimum.\n\n"
                "=> /cgi-bin/router.py/create-profile Recommencer\n")
    
    storage = Storage()
    if storage.load_user(username):
        return ("20 text/gemini\r\n"
                f"# ❌ Erreur\n"
                f"Le nom '{username}' est déjà utilisé.\n\n"
                "=> /cgi-bin/router.py/create-profile Choisir un autre nom\n")
    
    # Sauvegarde le mapping fingerprint -> username
    fingerprint = os.environ.get("TLS_CLIENT_HASH")
    debug_log(f"handle_create_profile - Fingerprint: {fingerprint}")
    
    if fingerprint:
        storage.save_cert_mapping(fingerprint, username)
        storage.ensure_user(username)
        debug_log(f"handle_create_profile - Mapping sauvegardé: {fingerprint} -> {username}")
        
        return ("20 text/gemini\r\n"
                f"# ✅ Profil créé !\n\n"
                f"Bienvenue **{username}** !\n\n"
                f"Votre certificat est maintenant associé à votre profil.\n\n"
                f"=> /cgi-bin/router.py/ Accéder à votre espace\n"
                "=> /cgi-bin/router.py/chapter1 Commencer l'aventure\n")
    else:
        debug_log("handle_create_profile - Aucun fingerprint trouvé!")
        return ("20 text/gemini\r\n"
                "# ❌ Erreur\n"
                "Aucun certificat détecté. Impossible de créer un profil.\n\n"
                "=> /cgi-bin/router.py/ Retour à l'accueil\n")

def handle_index(user_id, form):
    """Nouvelle page d'accueil intelligente"""
    has_cert = is_certificate_connected()
    friendly_name = get_friendly_username()
    
    debug_log(f"handle_index - has_cert: {has_cert}, friendly_name: {friendly_name}")
    
    # Cas 1: Certificat avec profil connu
    if has_cert and friendly_name:
        storage = Storage()
        user_data = storage.load_user(friendly_name)
        
        if user_data:
            current_stage = user_data.get('current_stage', 'intro')
            progress = user_data.get('progress', 0)
            
            return (f"20 text/gemini\r\n"
                    f"# 👋 Bonjour {friendly_name} !\n\n"
                    f"**Progression :** {progress}%\n"
                    f"**Étape actuelle :** {current_stage}\n\n"
                    "**Actions :**\n"
                    f"=> /cgi-bin/router.py/{current_stage} Continuer l'aventure\n"
                    "=> /cgi-bin/router.py/profile Voir mon profil complet\n"
                    "=> /cgi-bin/router.py/chapter1 Recommencer\n\n"
                    f"***\n"
                    f"*Session certifiée : {friendly_name}*")
    
    # Cas 2: Certificat sans profil
    elif has_cert:
        fingerprint = os.environ.get('TLS_CLIENT_HASH', '')[:16] + "..."
        
        return (f"20 text/gemini\r\n"
                f"# 🔐 Certificat détecté\n\n"
                f"Fingerprint : {fingerprint}\n\n"
                "**Créez votre profil pour :**\n"
                "• Personnaliser votre expérience\n" 
                "• Sauvegarder votre progression\n"
                "• Avoir un nom convivial\n\n"
                "=> /cgi-bin/router.py/create-profile Créer mon profil\n"
                "=> /cgi-bin/router.py/chapter1 Jouer en anonyme\n\n"
                f"***\n"
                f"*Certificat non associé*")
    
    # Cas 3: Mode anonyme
    else:
        query_string = os.environ.get("QUERY_STRING", "").strip()
        username = query_string if query_string else "Aventurier"
        
        return (f"20 text/gemini\r\n"
                f"# 🌟 Bienvenue {username} !\n\n"
                "**Mode anonyme** - Votre progression ne sera pas sauvegardée.\n\n"
                "**Options :**\n"
                "=> /cgi-bin/router.py/chapter1 Commencer l'aventure\n"
                "=> /cgi-bin/router.py/create-profile?{username} Créer un profil\n"
                "=> /cgi-bin/router.py/register Créer un certificat\n\n"
                f"***\n"
                f"*Session anonyme*")

# --- Traitement principal (Routage) ---
def main():
    try:
        debug_log("=== DÉBUT REQUÊTE ===")
        
        # Affiche toutes les variables TLS pour debug
        for key, value in sorted(os.environ.items()):
            if key.startswith('TLS_'):
                debug_log(f"ENV {key}: {value}")
        
        # Récupération de l'identité utilisateur
        user_id = get_friendly_username()
        if not user_id:
            user_id = os.environ.get("TLS_CLIENT_HASH")
            
        form = cgi.FieldStorage()
        if not user_id:
            user_id = form.getfirst("user", "").strip()
            
        user_id = user_id if user_id else None
        
        debug_log(f"main - user_id final: {user_id}")

        # Routage
        path_info = os.environ.get("PATH_INFO", "/").strip('/')
        if path_info in ['', 'router.py']:
            path_info = 'index'

        output = ""
        engine = GameEngine(Storage())
        
        if path_info == 'index':
            output = handle_index(user_id, form)
            
        elif path_info == 'create-profile':
            output = handle_create_profile(form)
            
        elif path_info == 'register':
            output = "20 text/gemini\r\n# ⚠️ Ancien système\n\nUtilisez plutôt:\n=> /cgi-bin/router.py/create-profile Créer un profil simple\n"
            
        elif path_info == 'chapter1':
            output = engine.chapter1(user_id)
            
        elif path_info == 'profile':
            output = "20 text/gemini\r\n# 🔧 En construction\n\nCette page sera bientôt disponible.\n\n=> /cgi-bin/router.py/ Retour à l'accueil\n"
            
        else:
            output = "50 Not found\r\n# Page non trouvée\n"
            
        sys.stdout.write(output)
        debug_log("=== FIN REQUÊTE ===")

    except Exception as e:
        debug_log(f"ERREUR: {e}")
        import traceback
        debug_log(traceback.format_exc())
        sys.stdout.write(f"59 Server Error\r\n# Erreur Critique Serveur\nÉchec du routeur. Détail: {e}\n")

if __name__ == "__main__":
    main()