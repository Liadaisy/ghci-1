# fairauth.py
import os
import requests
from urllib.parse import urlencode
import jwt
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

AUTH0_LOGOUT_URL = f"https://{AUTH0_DOMAIN}/v2/logout"
AUTH0_AUTHORIZE_URL = f"https://{AUTH0_DOMAIN}/authorize"
AUTH0_TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"

def build_auth_url(role: str = "user"):
    params = {
        "client_id": AUTH0_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
        "state": role,
        "prompt": "select_account"
    }
    return f"{AUTH0_AUTHORIZE_URL}?{urlencode(params)}"

def exchange_code_for_tokens(code: str):
    payload = {
        "grant_type": "authorization_code",
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    resp = requests.post(AUTH0_TOKEN_URL, data=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()

def decode_id_token(id_token: str):
    return jwt.decode(id_token, options={"verify_signature": False})