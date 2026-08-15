"""Local fallback replacement for the unavailable `pyPrivnote` PyPI package.

The original project imports `pyPrivnote as pn` only for `pn.read_note(url)`.
The package is no longer available on PyPI, so Railway cannot install it.
This small compatibility module prevents the self-bot from crashing at startup.
"""

import re
import requests
from bs4 import BeautifulSoup


def _clean_text(text):
    text = re.sub(r"\r\n?", "\n", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_note(url):
    """Best-effort Privnote reader compatible with pyPrivnote.read_note(url).

    Privnote-style sites change their frontend often. If the note cannot be
    decoded client-side, return a clear message instead of raising an import
    error and killing the whole self-bot.
    """
    url = (url or "").strip()
    if not url:
        return "Empty Privnote URL"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Common containers used by Privnote clones / older pyPrivnote targets.
        selectors = [
            "#note_contents",
            "#note-content",
            ".note_contents",
            ".note-content",
            "textarea",
            "pre",
            "article",
            "main",
        ]
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = _clean_text(node.get_text("\n"))
                if text:
                    return text

        # Fallback to page body, but avoid returning huge scripts/styles.
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        body_text = _clean_text(soup.get_text("\n"))
        if body_text:
            return body_text[:4000]
        return "Privnote page was fetched but no readable note text was found."
    except Exception as exc:
        return f"Privnote read failed: {type(exc).__name__}: {exc}"
