#!/usr/bin/env python3
"""Scrape the Afrikaans 1983/1992 Bible (AFR83) from BibleSA chapter by chapter.

The BibleSA site embeds structured chapter JSON in each page's server-rendered state.
This script fetches those pages, extracts only biblical content (verses and section
headings), and writes clean output without adverts, navigation, or study notes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_URL = "https://www.biblesa.co.za/af/bybel/AFR83"
BIBLE_ID = "dfc6da1000025af7-01"
STATE_PATTERN = re.compile(
    r'<script id="IBEP-main-state" type="application/json">(.*?)</script>',
    re.DOTALL,
)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "af-ZA,af;q=0.9,en;q=0.8",
}


@dataclass
class Verse:
    number: int
    text: str


@dataclass
class Chapter:
    id: str
    number: int
    headings: list[str] = field(default_factory=list)
    verses: list[Verse] = field(default_factory=list)
    copyright: str | None = None


@dataclass
class Book:
    id: str
    name: str
    abbreviation: str
    chapters: list[Chapter] = field(default_factory=list)


def fetch_page(url: str, retries: int = 4, backoff: float = 2.0) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def load_embedded_state(html: str) -> dict[str, Any]:
    match = STATE_PATTERN.search(html)
    if not match:
        raise ValueError("Could not find embedded BibleSA state JSON in page HTML")
    return json.loads(match.group(1))


def find_state_entry(state: dict[str, Any], needle: str) -> dict[str, Any] | None:
    for key, value in state.items():
        if needle in key and isinstance(value, dict) and "data" in value:
            return value["data"]
    return None


def load_metadata(seed_html: str | None = None) -> tuple[list[Book], str | None]:
    html = seed_html or fetch_page(f"{BASE_URL}/GEN.1")
    state = load_embedded_state(html)
    metadata = find_state_entry(state, f"/bibles/{BIBLE_ID}/metadata")
    if not metadata:
        raise ValueError("Bible metadata not found in embedded page state")

    books: list[Book] = []
    for testament in metadata.get("testaments", []):
        for book_data in testament.get("books", []):
            chapters = [
                Chapter(id=chapter["id"], number=int(chapter["number"]))
                for chapter in book_data.get("chapters", [])
            ]
            books.append(
                Book(
                    id=book_data["id"],
                    name=book_data.get("name", book_data["id"]),
                    abbreviation=book_data.get("abbreviation", book_data["id"]),
                    chapters=chapters,
                )
            )

    copyright_notice = metadata.get("copyright")
    return books, copyright_notice


def parse_chapter_payload(chapter_data: dict[str, Any]) -> Chapter:
    chapter = Chapter(
        id=chapter_data["id"],
        number=int(chapter_data["number"]),
        copyright=chapter_data.get("copyright"),
    )

    verse_parts: dict[int, list[str]] = {}
    current_verse: int | None = None

    for block in chapter_data.get("content", []):
        style = block.get("style")
        if style == "s1":
            heading = _extract_text_nodes(block.get("content", []))
            if heading:
                chapter.headings.append(heading)
            continue

        if style == "b" or not block.get("content"):
            continue

        for item in block.get("content", []):
            item_type = item.get("type")
            if item_type == "verse-number":
                try:
                    current_verse = int(item.get("content", "").strip())
                except ValueError:
                    current_verse = None
            elif item_type == "verse-text":
                verse_id = item.get("verseId", "")
                verse_number = _verse_number_from_id(verse_id) or current_verse
                text = item.get("content", "").strip()
                if verse_number is None or not text:
                    continue
                verse_parts.setdefault(verse_number, []).append(text)

    for number in sorted(verse_parts):
        joined = " ".join(part.strip() for part in verse_parts[number] if part.strip())
        chapter.verses.append(Verse(number=number, text=joined))

    return chapter


def _extract_text_nodes(nodes: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for node in nodes:
        if node.get("type") == "text":
            text = node.get("content", "").strip()
            if text:
                parts.append(text)
    return " ".join(parts)


def _verse_number_from_id(verse_id: str) -> int | None:
    if not verse_id:
        return None
    try:
        return int(verse_id.rsplit(".", 1)[-1])
    except ValueError:
        return None


def fetch_chapter(chapter_id: str) -> Chapter:
    html = fetch_page(f"{BASE_URL}/{chapter_id}")
    state = load_embedded_state(html)
    chapter_data = find_state_entry(state, f"/chapters/{chapter_id}/with-study-content")
    if not chapter_data or "chapter" not in chapter_data:
        raise ValueError(f"Chapter payload not found for {chapter_id}")
    return parse_chapter_payload(chapter_data["chapter"])


def chapter_to_dict(chapter: Chapter) -> dict[str, Any]:
    return {
        "id": chapter.id,
        "number": chapter.number,
        "headings": chapter.headings,
        "verses": [{"number": verse.number, "text": verse.text} for verse in chapter.verses],
    }


def book_to_dict(book: Book) -> dict[str, Any]:
    return {
        "id": book.id,
        "name": book.name,
        "abbreviation": book.abbreviation,
        "chapters": [chapter_to_dict(chapter) for chapter in book.chapters],
    }


def format_chapter_plain(book: Book, chapter: Chapter) -> str:
    lines = [f"{book.name} {chapter.number}"]
    lines.extend(chapter.headings)
    if chapter.headings:
        lines.append("")
    for verse in chapter.verses:
        lines.append(f"{verse.number} {verse.text}")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Afrikaans 1983/1992 Bible (AFR83) from BibleSA."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="afr83_output",
        help="Directory for scraped output (default: afr83_output)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text", "both"),
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--book",
        action="append",
        metavar="BOOK_ID",
        help="Only scrape specific book IDs (e.g. GEN, REV). Can be repeated.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between chapter requests (default: 1.0)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip chapters whose output files already exist",
    )
    parser.add_argument(
        "--list-books",
        action="store_true",
        help="Print available book IDs and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_dir = Path(args.output_dir)

    print("Loading Bible metadata from BibleSA...", flush=True)
    books, copyright_notice = load_metadata()

    if args.list_books:
        for book in books:
            print(f"{book.id:>4}  {book.name} ({len(book.chapters)} chapters)")
        return 0

    selected_books = books
    if args.book:
        wanted = {book_id.upper() for book_id in args.book}
        selected_books = [book for book in books if book.id in wanted]
        missing = wanted - {book.id for book in selected_books}
        if missing:
            print(f"Warning: unknown book IDs ignored: {', '.join(sorted(missing))}", file=sys.stderr)

    scraped_books: list[Book] = []
    total_chapters = sum(len(book.chapters) for book in selected_books)
    completed = 0

    for book in selected_books:
        print(f"\n{book.name} ({book.id})", flush=True)
        scraped_book = Book(
            id=book.id,
            name=book.name,
            abbreviation=book.abbreviation,
        )

        for chapter_stub in book.chapters:
            completed += 1
            json_path = output_dir / "json" / book.id / f"{chapter_stub.number:03d}.json"
            text_path = output_dir / "text" / book.id / f"{chapter_stub.number:03d}.txt"

            if args.resume and (
                (args.format in ("json", "both") and json_path.exists())
                or (args.format in ("text", "both") and text_path.exists())
            ):
                print(f"  [{completed}/{total_chapters}] {chapter_stub.id} (skipped)", flush=True)
                if args.format in ("json", "both") and json_path.exists():
                    chapter_data = json.loads(json_path.read_text(encoding="utf-8"))
                    scraped_book.chapters.append(
                        Chapter(
                            id=chapter_data["id"],
                            number=chapter_data["number"],
                            headings=chapter_data.get("headings", []),
                            verses=[
                                Verse(number=verse["number"], text=verse["text"])
                                for verse in chapter_data.get("verses", [])
                            ],
                        )
                    )
                continue

            print(f"  [{completed}/{total_chapters}] {chapter_stub.id}", flush=True)
            chapter = fetch_chapter(chapter_stub.id)
            scraped_book.chapters.append(chapter)

            if args.format in ("json", "both"):
                write_json(json_path, chapter_to_dict(chapter))
            if args.format in ("text", "both"):
                write_text(text_path, format_chapter_plain(book, chapter))

            if args.delay > 0 and completed < total_chapters:
                time.sleep(args.delay)

        if args.format in ("json", "both"):
            write_json(output_dir / "json" / f"{book.id}.json", book_to_dict(scraped_book))
        if args.format in ("text", "both"):
            book_text = "\n\n".join(
                format_chapter_plain(book, chapter).rstrip()
                for chapter in scraped_book.chapters
            )
            write_text(output_dir / "text" / f"{book.id}.txt", book_text + "\n")

        scraped_books.append(scraped_book)

    bible_payload = {
        "translation": "Afrikaans 1983/1992 (AFR83)",
        "source": BASE_URL,
        "copyright": copyright_notice,
        "books": [book_to_dict(book) for book in scraped_books],
    }

    if args.format in ("json", "both"):
        write_json(output_dir / "afr83_bible.json", bible_payload)
    if args.format in ("text", "both"):
        full_text = "\n\n".join(
            format_chapter_plain(book, chapter).rstrip()
            for book in scraped_books
            for chapter in book.chapters
        )
        header = "Afrikaans 1983/1992 Bybel (AFR83)\n"
        if copyright_notice:
            header += f"{copyright_notice}\n"
        header += "\n"
        write_text(output_dir / "afr83_bible.txt", header + full_text + "\n")

    print(f"\nDone. Output written to {output_dir.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
