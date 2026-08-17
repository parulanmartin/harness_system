import os
import json
import urllib.request
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_FILE = "google_token.json"
CLIENT_SECRET_FILE = "client_secret.json"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Successful!</h1><p>You can close this tab and return to the terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Failed.</h1></body></html>")

    def log_message(self, format, *args):
        pass  # Suppress server logs

def get_google_access_token() -> Optional[str]:
    """
    Retrieves a valid Google OAuth access token using client_secret.json.
    Automatically handles initial web consent and subsequent token refreshes.
    """
    # 1. Check if we have an existing saved token
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                token_data = json.load(f)
            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                new_token = refresh_access_token(refresh_token)
                if new_token:
                    return new_token
        except Exception:
            pass

    # 2. Need initial user authentication
    if not os.path.exists(CLIENT_SECRET_FILE):
        return None

    with open(CLIENT_SECRET_FILE, "r") as f:
        cs_data = json.load(f)

    cfg = cs_data.get("installed") or cs_data.get("web") or {}
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")

    if not client_id or not client_secret:
        return None

    redirect_port = 8080
    redirect_uri = f"http://localhost:{redirect_port}"

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    print("\n" + "=" * 65)
    print("  🔑 GOOGLE DRIVE & SHEETS AUTHENTICATION")
    print("=" * 65)
    print("Opening browser for one-time Google Workspace authorization...")
    print(f"If browser does not open automatically, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Listen on localhost:8080 for the callback
    server = HTTPServer(("localhost", redirect_port), OAuthCallbackHandler)
    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()
    server.server_close()

    code = OAuthCallbackHandler.auth_code
    if not code:
        raise RuntimeError("Failed to obtain OAuth authorization code.")

    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    print("✅ Google Drive & Sheets authentication successful!\n")
    return tokens.get("access_token")

def refresh_access_token(refresh_token: str) -> Optional[str]:
    if not os.path.exists(CLIENT_SECRET_FILE):
        return None
    with open(CLIENT_SECRET_FILE, "r") as f:
        cs_data = json.load(f)

    cfg = cs_data.get("installed") or cs_data.get("web") or {}
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")

    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
            tokens["refresh_token"] = refresh_token
            with open(TOKEN_FILE, "w") as f:
                json.dump(tokens, f, indent=2)
            return tokens.get("access_token")
    except Exception:
        return None
