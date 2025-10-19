#!/usr/bin/env python3
# app.py
from jetforce import JetforceApplication, Response, Status
import os
import sys

# Ajoute le chemin pour importer vos modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from storage import Storage
from game.engine import GameEngine

app = JetforceApplication()

def get_friendly_username(environ):
    """
    Récupère le username convivial depuis le mapping stocké
    """
    try:
        fingerprint = environ.get('TLS_CLIENT_HASH')
        if fingerprint:
            storage = Storage()
            username = storage.get_username_from_fingerprint(fingerprint)
            return username
        return None
    except Exception:
        return None

def is_certificate_connected(environ):
    """Vérifie si un certificat client est détecté"""
    return environ.get('TLS_CLIENT_HASH') is not None

@app.route("test")
def test_route(request):
    """Route de test pour vérifier que l'application fonctionne"""
    return Response(Status.SUCCESS, "text/gemini", "# ✅ Test Réussi !\n\nL'application fonctionne correctement !\n\n=> / Retour à l'accueil")
    
@app.route("")
def index(request):
    user_id = get_friendly_username(request.environ)
    has_cert = is_certificate_connected(request.environ)
    
    if user_id:
        content = [
            f"# 👋 Bonjour {user_id} !",
            "",
            f"Content de vous revoir {user_id} ! Votre certificat est actif.",
            "",
            "=> /profile Votre profil",
            "=> /chapter1 Continuer l'aventure"
        ]
    elif has_cert:
        content = [
            "# 🔐 Certificat détecté",
            "",
            "Un certificat client a été détecté mais aucun profil n'y est associé.",
            "",
            "=> /create-profile Associer un nom à votre certificat",
            "=> /chapter1 Jouer en mode anonyme"
        ]
    else:
        content = [
            "# 🌟 CryptoQuest - Bienvenue !",
            "",
            "Bienvenue dans votre aventure Gemini !",
            "",
            "**Mode anonyme :**",
            "=> /chapter1 Commencer l'aventure sans compte",
            "",
            "**Mode authentifié :**",
            "=> /create-profile Créer un profil avec certificat"
        ]
    
    return Response(Status.SUCCESS, "text/gemini", "\n".join(content))

@app.route("create-profile")
def create_profile(request):
    """Crée un profil et l'associe au certificat"""
    has_cert = is_certificate_connected(request.environ)
    
    if not has_cert:
        return Response(Status.SUCCESS, "text/gemini",
                       "# ❌ Aucun certificat détecté\n\n"
                       "Pour créer un profil, vous devez être connecté avec un certificat client.\n\n"
                       "=> / Retour à l'accueil")
    
    query = request.query
    if not query:
        return Response(Status.INPUT, "Choisissez un nom pour votre profil (ex: Alice, Bob)")
    
    username = query.strip()
    
    # Validation
    if not username.isalnum() or len(username) < 3:
        return Response(Status.SUCCESS, "text/gemini", 
                       "# ❌ Erreur\n\nLe nom doit contenir 3 caractères alphanumériques minimum.\n\n=> /create-profile Recommencer")
    
    storage = Storage()
    if storage.load_user(username):
        return Response(Status.SUCCESS, "text/gemini",
                      f"# ❌ Erreur\n\nLe nom '{username}' est déjà utilisé.\n\n=> /create-profile Choisir un autre nom")
    
    # Sauvegarde le mapping fingerprint -> username
    fingerprint = request.environ.get('TLS_CLIENT_HASH')
    storage.save_cert_mapping(fingerprint, username)
    storage.ensure_user(username)
    
    return Response(Status.SUCCESS, "text/gemini",
                   f"# ✅ Profil créé !\n\n"
                   f"Bienvenue **{username}** !\n\n"
                   f"Votre certificat est maintenant associé à votre profil.\n\n"
                   f"=> /profile Accéder à votre profil\n"
                   "=> /chapter1 Commencer l'aventure")

@app.route("profile")
def profile(request):
    """Affiche ou crée un profil"""
    user_id = get_friendly_username(request.environ)
    has_cert = is_certificate_connected(request.environ)
    query = request.query
    
    # Si certificat détecté mais pas de profil associé
    if has_cert and not user_id:
        return Response(Status.SUCCESS, "text/gemini",
                       "# 🔐 Certificat non associé\n\n"
                       "Votre certificat est détecté mais aucun profil n'y est associé.\n\n"
                       "=> /create-profile Créer un profil\n"
                       "=> /chapter1 Jouer en mode anonyme")
    
    # Si pas de certificat mais query string pour mode anonyme
    if not has_cert and query:
        user_id = query
    
    # Si toujours pas d'ID, demande le nom
    if not user_id:
        return Response(Status.INPUT, "Quel est votre nom ? (mode anonyme)")
    
    storage = Storage()
    user_data = storage.load_user(user_id)
    
    if user_data:
        current_stage = user_data.get('current_stage', 'intro')
        progress = user_data.get('progress', 0)
        
        profile_type = "✅ Certificat" if has_cert and user_id == get_friendly_username(request.environ) else "👤 Anonyme"
        
        content = [
            f"# 👋 Bonjour {user_id} !",
            "",
            f"**Type de session :** {profile_type}",
            f"**Progression :** {progress}%",
            f"**Étape actuelle :** {current_stage}",
            ""
        ]
        
        if has_cert and user_id == get_friendly_username(request.environ):
            content.append("Votre progression est sauvegardée avec votre certificat.")
            content.append("")
            content.append("=> /chapter1 Continuer l'aventure")
        else:
            content.append("Mode anonyme - la progression n'est pas sauvegardée.")
            content.append("")
            content.append("=> /create-profile Créer un profil permanent")
            content.append("=> /chapter1 Continuer l'aventure")
        
        content.append("=> / Retour à l'accueil")
        
    else:
        content = [
            f"# 👋 Bonjour {user_id} !",
            "",
            f"Bienvenue {user_id} !",
            ""
        ]
        
        if has_cert:
            content.append("=> /create-profile Associer ce nom à votre certificat")
        else:
            content.append("Mode anonyme - pour sauvegarder, créez un profil avec certificat.")
            content.append("")
            content.append("=> /create-profile Créer un profil permanent")
        
        content.append("=> /chapter1 Commencer l'aventure")
    
    return Response(Status.SUCCESS, "text/gemini", "\n".join(content))

@app.route("chapter1")
def chapter1(request):
    user_id = get_friendly_username(request.environ)
    has_cert = is_certificate_connected(request.environ)
    
    # Si pas d'ID mais query string pour mode anonyme
    if not user_id:
        user_id = request.query
    
    # Sauvegarde la progression si profil certifié
    if user_id and has_cert and user_id == get_friendly_username(request.environ):
        storage = Storage()
        storage.ensure_user(user_id)
        storage.update_user_progress(user_id, 'chapter1', 25)
        session_type = "✅ Profil certifié"
    elif user_id:
        session_type = "👤 Session anonyme"
    else:
        session_type = "👤 Invité"
        user_id = "Aventurier"
    
    content = [
        f"# Chapitre 1 - Le Réveil",
        "",
        f"**Joueur :** {user_id}",
        f"**Session :** {session_type}",
        "",
        "Vous vous réveillez dans une auberge inconnue...",
        "",
        "**Que faites-vous ?**",
        "",
        "=> /chapter1/explorer Explorer la pièce",
        "=> /chapter1/sortir Sortir de l'auberge",
        "",
        "=> /profile Gérer le profil",
        "=> / Retour à l'accueil"
    ]
    
    return Response(Status.SUCCESS, "text/gemini", "\n".join(content))

@app.route("my-certificate")
def my_certificate(request):
    """Affiche les infos du certificat"""
    fingerprint = request.environ.get('TLS_CLIENT_HASH')
    user_id = get_friendly_username(request.environ)
    
    if fingerprint:
        content = [
            "# 🔐 Votre Certificat",
            "",
            f"**Fingerprint :** {fingerprint}",
            f"**Profil associé :** {user_id if user_id else 'Aucun'}",
            ""
        ]
        
        if user_id:
            content.append("✅ Votre certificat est associé à un profil.")
            content.append("")
            content.append("=> /profile Voir votre profil")
        else:
            content.append("❌ Aucun profil associé à ce certificat.")
            content.append("")
            content.append("=> /create-profile Créer un profil")
        
        content.append("=> / Retour à l'accueil")
    else:
        content = [
            "# 🔐 Aucun Certificat",
            "",
            "Aucun certificat client n'est détecté.",
            "",
            "Pour utiliser les certificats :",
            "1. Créez un certificat dans votre client Gemini",
            "2. Associez-le à un profil dans CryptoQuest",
            "",
            "=> /create-profile Créer un profil",
            "=> / Retour à l'accueil"
        ]
    
    return Response(Status.SUCCESS, "text/gemini", "\n".join(content))

if __name__ == "__main__":
    print("Utilisez: python3 -m jetforce --host localhost --port 1965 --tls-certfile keys/server_cert.pem --tls-keyfile keys/server_key.pem")