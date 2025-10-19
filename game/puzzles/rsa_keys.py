# game/puzzles/rsa_keys.py
# Génération d'une paire RSA pédagogique + chiffrement avec la clé publique.
# Ici on génère une clé RSA 2048 bits (suffisante pour un vrai test).
# Le serveur garde seulement la clé publique (encoded PEM) pour chiffrer.

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_rsa_keypair_for_user():
    """
    Génère une paire RSA et renvoie (private_pem_bytes, public_pem_bytes).
    On donne la private_pem au joueur (dans cette démo pédagogique).
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_pem, public_pem

def encrypt_with_pubkey(public_pem: bytes, plaintext: bytes) -> bytes:
    """
    Chiffre des données (plaintext) avec la clé publique RSA (RSA-OAEP).
    Renvoie le ciphertext bytes.
    """
    from cryptography.hazmat.primitives import serialization
    public_key = serialization.load_pem_public_key(public_pem)
    cipher = public_key.encrypt(
        plaintext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return cipher

def serialize_private_key_pem(private_pem: bytes) -> str:
    """
    Retourne la représentation str de la clé privée PEM (affichable).
    """
    return private_pem.decode()
