#!/usr/bin/env python3
# run_app.py
from app import app

if __name__ == "__main__":
    from jetforce import run
    run(app=app, host="localhost", port=1965, certfile="keys/server_cert.pem", keyfile="keys/server_key.pem")