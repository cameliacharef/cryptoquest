# game/puzzles/aes_links.py
# Fonctions utilitaires pour générer une clé AES-256, chiffrer/déchiffrer une URL (AES-GCM)
# Utilise cryptography.hazmat.primitives.ciphers.aead.AESGCM

import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def gen_aes_key():
    """
    Génère une clé AES-256 (32 octets).
    """
    return os.urandom(32)

def encrypt_link(aes_key: bytes, link_str: str) -> str:
    """
    Chiffre la chaîne link_str avec AES-GCM et renvoie base64(nonce + ciphertext).
    """
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)  # AES-GCM nonce 96 bits
    ct = aesgcm.encrypt(nonce, link_str.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_link(aes_key: bytes, b64_ciphertext: str) -> str:
    """
    Déchiffre le base64(nonce + ciphertext) et renvoie la chaîne claire.
    """
    data = base64.b64decode(b64_ciphertext)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(nonce, ct, None).decode()
