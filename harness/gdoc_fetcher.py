import re
import urllib.request
import urllib.error

def fetch_google_doc_text(url_or_path: str) -> str:
    """
    Fetches raw transcript text from a public Google Docs URL or local text file path.
    """
    # If it is a local file path, read directly
    if not url_or_path.startswith("http://") and not url_or_path.startswith("https://"):
        with open(url_or_path, "r", encoding="utf-8") as f:
            return f.read()

    # Normalize Google Docs URL
    doc_id_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url_or_path)
    if not doc_id_match:
        raise ValueError(f"Invalid Google Docs URL format: {url_or_path}")

    doc_id = doc_id_match.group(1)
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
        # Unescape Unicode characters and newlines
        clean_text = (
            raw_text.replace("\\u000b", "\n")
            .replace("\\n", "\n")
            .replace("\\u0027", "'")
            .replace('\\"', '"')
        )
        return clean_text.strip()

    # Fallback: Extract from paragraph tags if available
    paragraphs = re.findall(r">([^<]{10,})<", html)
    if paragraphs:
        return "\n".join(paragraphs).strip()

    raise ValueError("Could not extract text from the provided Google Doc. Ensure the link sharing is set to 'Anyone with the link can view'.")
