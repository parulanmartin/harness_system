import re
import urllib.request
import urllib.error
from typing import Optional

def fetch_google_doc_text(url_or_path: str) -> str:
    """
    Fetches raw transcript text from Google Docs (authenticated via Drive API or public web fallback)
    or from a local file path.
    """
    # If it is a local file path, read directly
    if not url_or_path.startswith("http://") and not url_or_path.startswith("https://"):
        with open(url_or_path, "r", encoding="utf-8") as f:
            return f.read()

    # Extract Document ID
    doc_id_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url_or_path)
    if not doc_id_match:
        raise ValueError(f"Invalid Google Docs URL format: {url_or_path}")

    doc_id = doc_id_match.group(1)

    # 1. Try Authenticated Google Drive Export API first
    try:
        from harness.google_auth import get_google_access_token
        token = get_google_access_token()
        if token:
            export_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType=text/plain"
            req = urllib.request.Request(export_url, headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8")
                if len(text.strip()) > 10:
                    return text.strip()
    except Exception:
        pass  # Fallback to public web parsing

    # 2. Fallback to public web scraping if document is shared publicly
    view_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    req = urllib.request.Request(view_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as err:
        raise RuntimeError(f"Failed to load Google Doc at {url_or_path}: {err}") from err

    # Extract text from Google Docs model chunks
    chunks = re.findall(r'"s":"([^"]+)"', html)
    if chunks:
        raw_text = "".join(chunks)
        clean_text = (
            raw_text.replace("\\u000b", "\n")
            .replace("\\n", "\n")
            .replace("\\u0027", "'")
            .replace('\\"', '"')
        )
        return clean_text.strip()

    # Fallback to paragraph tags
    paragraphs = re.findall(r">([^<]{10,})<", html)
    if paragraphs:
        return "\n".join(paragraphs).strip()

    raise ValueError("Could not extract text from the provided Google Doc. Ensure the link sharing is set to 'Anyone with the link can view' or you are signed in via Google OAuth.")
