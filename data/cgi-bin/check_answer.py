#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_answer.py — vérifie les réponses des énigmes CryptoQuest.
"""

import cgi
import hashlib
import sys

def gemini_success(lines):
    """Réponse 20 text/gemini (OK)."""
    sys.stdout.write("20 text/gemini\r\n")
    sys.stdout.write("\n".join(lines) + "\n")

def gemini_error(lines):
    """Réponse d’erreur simple (20 text/gemini, mais message d’échec)."""
    sys.stdout.write("20 text/gemini\r\n")
    sys.stdout.write("\n".join(lines) + "\n")

# --- Lecture des paramètres ---
form = cgi.FieldStorage()
puzzle = form.getfirst("puzzle", "").strip()
answer = form.getfirst("answer", "").strip()

# --- Vérifications des réponses ---
def check_puzzle_c1(ans):
    expected_hash = hashlib.sha256(b"dragon").hexdigest()
    return ans == expected_hash

def check_puzzle_enigme2(ans):
    return ans == "SecretChapter"

# --- Traitement principal ---
if not puzzle or not answer:
    gemini_success([
        "# 🧭 Soumettre une réponse",
        "",
        "Utilise un lien comme :",
        "=> /cgi-bin/check_answer.py?puzzle=c1&answer=<ta_reponse>",
        "",
        "Exemples :",
        "=> /cgi-bin/check_answer.py?puzzle=c1&answer=6b1a43e9... (Énigme 1)",
        "=> /cgi-bin/check_answer.py?puzzle=enigme2&answer=SecretChapter (Énigme 2)"
    ])
else:
    ok = False
    if puzzle == "c1":
        ok = check_puzzle_c1(answer)
    elif puzzle == "enigme2":
        ok = check_puzzle_enigme2(answer)

    if ok:
        if puzzle == "c1":
            gemini_success([
                "# ✅ Bonne réponse — Énigme 1",
                "",
                "Bravo, tu as trouvé le hash du dragon ! 🐉",
                "",
                "=> /enigme2.gmi Passer à l’énigme suivante 🔐"
            ])
        elif puzzle == "enigme2":
            gemini_success([
                "# 🏁 Victoire finale ! 🎉",
                "",
                "Tu as déchiffré le message secret !",
                "",
                "=> /final.gmi Fin de l’aventure 🏆"
            ])
    else:
        gemini_error([
            "# ❌ Mauvaise réponse",
            "",
            "Ta réponse n’est pas correcte.",
            "",
            "=> /enigme1.gmi Réessayer l’énigme 🧩"
        ])
