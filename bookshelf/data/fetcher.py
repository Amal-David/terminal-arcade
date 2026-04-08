"""Fetch book data from Open Library and quote APIs.

This module is used to build/refresh the curated book catalog.
It is NOT used at runtime — the app ships with pre-built data.

Usage:
    python3 -m bookshelf.data.fetcher --genre motivation --limit 50
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
RECITE_API = "https://recite-flax.vercel.app/api/v1"

# Rate limiting
OL_DELAY = 1.0  # 1 request/sec for Open Library
RECITE_DELAY = 0.25  # 250 req/min for Recite


@dataclass
class FetchedBook:
    title: str
    author: str
    year: int
    ol_key: str


def search_books(
    subject: str, limit: int = 50, offset: int = 0
) -> list[FetchedBook]:
    """Search Open Library for books by subject."""
    params = urllib.parse.urlencode(
        {
            "subject": subject,
            "limit": limit,
            "offset": offset,
            "fields": "key,title,author_name,first_publish_year",
        }
    )
    url = f"{OPEN_LIBRARY_SEARCH}?{params}"

    req = urllib.request.Request(
        url, headers={"User-Agent": "Bookshelf-TUI/0.1 (terminal game)"}
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    books = []
    for doc in data.get("docs", []):
        authors = doc.get("author_name", [])
        books.append(
            FetchedBook(
                title=doc.get("title", "Unknown"),
                author=authors[0] if authors else "Unknown",
                year=doc.get("first_publish_year", 0),
                ol_key=doc.get("key", ""),
            )
        )
    time.sleep(OL_DELAY)
    return books


def fetch_quotes(query: str = "") -> list[dict]:
    """Fetch book quotes from the Recite API."""
    if query:
        params = urllib.parse.urlencode({"query": query})
        url = f"{RECITE_API}/quotes/search?{params}"
    else:
        url = f"{RECITE_API}/random"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    time.sleep(RECITE_DELAY)

    quotes = data.get("quotes", [])
    if isinstance(data, dict) and "quote" in data:
        quotes = [data]
    return quotes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch books from Open Library")
    parser.add_argument("--subject", default="self-help", help="Subject to search")
    parser.add_argument("--limit", type=int, default=20, help="Number of results")
    args = parser.parse_args()

    print(f"Searching Open Library for '{args.subject}'...")
    results = search_books(args.subject, limit=args.limit)
    for i, book in enumerate(results, 1):
        print(f"  {i}. {book.title} by {book.author} ({book.year})")
    print(f"\nFound {len(results)} books.")
