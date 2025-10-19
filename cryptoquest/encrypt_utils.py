# encrypt_utils.py
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Parameters
KDF_ITER = 200_000
KEY_LEN = 32
SALT_LEN = 16
NONCE_LEN = 12

def derive_key(password: str, salt: bytes) -> bytes:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=KDF_ITER,
    )
    return kdf.derive(password_bytes)

def encrypt_blob(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_LEN)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return salt + nonce + ct

def decrypt_blob(blob: bytes, password: str) -> bytes:
    if len(blob) < (SALT_LEN + NONCE_LEN + 16):
        raise ValueError("blob trop court")
    salt = blob[:SALT_LEN]
    nonce = blob[SALT_LEN:SALT_LEN+NONCE_LEN]
    ct = blob[SALT_LEN+NONCE_LEN:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, associated_data=None)
    return pt