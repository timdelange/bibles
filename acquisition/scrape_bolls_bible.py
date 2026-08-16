#!/usr/bin/env python3
"""Download NIV or NKJV from bolls.life and write structured JSON/text output.

BibleSA does not expose NKJV, and its NIV pages do not embed chapter JSON.
bolls.life publishes full-translation JSON files intended for bulk download.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bible_books import BOOK_BY_ID, BOOK_BY_NUMBER, BOOKS, BookInfo

ACQUISITION_DIR = Path(__file__).resolve().parent

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "NIV": {
        "slug": "NIV",
        "name": "New International Version",
        "copyright": "Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.",
        "output_prefix": "niv",
    },
    "NKJV": {
        "slug": "NKJV",
        "name": "New King James Version",
        "copyright": "Copyright © 1982 by Thomas Nelson, Inc.",
        "output_prefix": "nkjv",
    },
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


@dataclass
class Book:
    id: str
    name: str
    abbreviation: str
    chapters: list[Chapter] = field(default_factory=list)


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def split_heading_and_text(raw_text: str) -> tuple[str | None, str]:
    text = html.unescape(raw_text)
    if re.search(r"<br\s*/?>", text, flags=re.IGNORECASE):
        heading_part, body_part = re.split(r"<br\s*/?>", text, maxsplit=1, flags=re.IGNORECASE)
        heading = re.sub(r"<[^>]+>", "", heading_part).strip()
        body = re.sub(r"<[^>]+>", "", body_part).strip()
        if heading and body:
            return heading, body
    cleaned = re.sub(r"<[^>]+>", "", text)
    return None, " ".join(cleaned.split())


def clean_verse_text(text: str) -> str:
    _, body = split_heading_and_text(text)
    return body


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


def build_books_from_rows(rows: list[dict[str, Any]], selected_ids: set[str] | None) -> list[Book]:
    grouped: dict[tuple[int, int], list[tuple[int, str, str | None]]] = defaultdict(list)
    for row in rows:
        book_number = int(row["book"])
        chapter_number = int(row["chapter"])
        verse_number = int(row["verse"])
        heading, text = split_heading_and_text(str(row.get("text", "")))
        if heading and verse_number != 1:
            text = f"{heading} {text}".strip()
            heading = None
        if not text:
            continue
        grouped[(book_number, chapter_number)].append((verse_number, text, heading))

    books: list[Book] = []
    for book_info in BOOKS:
        if selected_ids and book_info.id not in selected_ids:
            continue

        book = Book(
            id=book_info.id,
            name=book_info.name,
            abbreviation=book_info.abbreviation,
        )
        chapter_numbers = sorted(
            chapter_number
            for (book_number, chapter_number) in grouped
            if book_number == book_info.number
        )
        for chapter_number in chapter_numbers:
            verses = grouped[(book_info.number, chapter_number)]
            chapter = Chapter(
                id=f"{book_info.id}.{chapter_number}",
                number=chapter_number,
            )
            for verse_number, text, heading in sorted(verses, key=lambda item: item[0]):
                if heading and heading not in chapter.headings:
                    chapter.headings.append(heading)
                chapter.verses.append(Verse(number=verse_number, text=text))
            book.chapters.append(chapter)
        books.append(book)
    return books


def write_outputs(
    books: list[Book],
    output_dir: Path,
    translation_name: str,
    source_url: str,
    copyright_notice: str,
    output_prefix: str,
    output_format: str,
) -> None:
    for book in books:
        for chapter in book.chapters:
            if output_format in ("json", "both"):
                write_json(
                    output_dir / "json" / book.id / f"{chapter.number:03d}.json",
                    chapter_to_dict(chapter),
                )
            if output_format in ("text", "both"):
                write_text(
                    output_dir / "text" / book.id / f"{chapter.number:03d}.txt",
                    format_chapter_plain(book, chapter),
                )

        if output_format in ("json", "both"):
            write_json(output_dir / "json" / f"{book.id}.json", book_to_dict(book))
        if output_format in ("text", "both"):
            book_text = "\n\n".join(
                format_chapter_plain(book, chapter).rstrip() for chapter in book.chapters
            )
            write_text(output_dir / "text" / f"{book.id}.txt", book_text + "\n")

    bible_payload = {
        "translation": translation_name,
        "source": source_url,
        "copyright": copyright_notice,
        "books": [book_to_dict(book) for book in books],
    }
    if output_format in ("json", "both"):
        write_json(output_dir / f"{output_prefix}_bible.json", bible_payload)
    if output_format in ("text", "both"):
        full_text = "\n\n".join(
            format_chapter_plain(book, chapter).rstrip()
            for book in books
            for chapter in book.chapters
        )
        header = f"{translation_name}\n{copyright_notice}\n\n"
        write_text(output_dir / f"{output_prefix}_bible.txt", header + full_text + "\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download NIV or NKJV from bolls.life.")
    parser.add_argument(
        "translation",
        choices=sorted(TRANSLATIONS),
        help="Translation to download (NIV or NKJV)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Output directory (default: acquisition/niv_output or acquisition/nkjv_output)",
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
        help="Only export specific book IDs (e.g. GEN, REV). Can be repeated.",
    )
    parser.add_argument(
        "--cache-file",
        help="Optional path to cache the downloaded source JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = TRANSLATIONS[args.translation]
    output_dir = Path(
        args.output_dir or ACQUISITION_DIR / f"{config['output_prefix']}_output"
    )
    source_url = f"https://bolls.life/static/translations/{config['slug']}.json"
    cache_file = Path(args.cache_file or output_dir / f".{config['slug'].lower()}_source.json")

    selected_ids = {book_id.upper() for book_id in args.book} if args.book else None

    if cache_file.exists():
        print(f"Loading cached source from {cache_file}...", flush=True)
        rows = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        print(f"Downloading {config['name']} from {source_url}...", flush=True)
        rows = fetch_json(source_url)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(rows), encoding="utf-8")
        print(f"Cached source to {cache_file}", flush=True)

    print(f"Parsing {len(rows):,} verses...", flush=True)
    books = build_books_from_rows(rows, selected_ids)
    chapters = sum(len(book.chapters) for book in books)
    verses = sum(len(chapter.verses) for book in books for chapter in book.chapters)
    print(f"Built {len(books)} books, {chapters} chapters, {verses:,} verses", flush=True)

    write_outputs(
        books=books,
        output_dir=output_dir,
        translation_name=config["name"],
        source_url=source_url,
        copyright_notice=config["copyright"],
        output_prefix=config["output_prefix"],
        output_format=args.format,
    )
    print(f"\nDone. Output written to {output_dir.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
