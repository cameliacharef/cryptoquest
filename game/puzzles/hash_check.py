# game/puzzles/hash_check.py
# Vérification simple de réponse par SHA-256

import hashlib

def check_answer(candidate: str, expected_hash_hex: str) -> bool:
    """
    Retourne True si SHA256(candidate) == expected_hash_hex
    """
    h = hashlib.sha256(candidate.encode()).hexdigest()
    return h == expected_hash_hex
