# CryptoQuest - prototype hackathon

## But
Jeu textuel Gemini montrant AES (liens chiffrés), SHA-256 (vérification), RSA (énigme finale) et stockage chiffré.

## Installation

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
openssl req -x509 -newkey rsa:2048 -keyout keys/server_key.pem -out keys/server_cert.pem -days 365 -nodes -subj "/C=FR/ST=Ile-de-France/L=Paris/O=CryptoQuest/CN=localhost"

###### important 
## start the server: 
jetforce --host localhost --port 1965 \ \
  --tls-certfile keys/server_cert.pem \
  --tls-keyfile keys/server_key.pem \
  --dir ./data


## client:
 flatpak run fi.skyjake.Lagrange




## Accès (exemples)
- Accueil : gemini://localhost:1965/?user=alice
- Chapitre1 : gemini://localhost:1965/chapter1?user=alice
- Soumettre : gemini://localhost:1965/submit?puzzle=c1&answer=dragon&user=alice
- Lien secret : gemini://localhost:1965/secret_link?user=alice
- RSA start : gemini://localhost:1965/rsa_start?user=alice