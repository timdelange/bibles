#!/usr/bin/env python3
"""Download and convert the Shona Bible from ebible.org USFM into structured output.

Source: Biblica Open Shona Contemporary Bible (SNA), CC BY-SA 4.0
https://ebible.org/details.php?id=sna
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from bible_books import BOOK_BY_ID, BOOKS
from scrape_bolls_bible import Book, Chapter, Verse, write_outputs

ACQUISITION_DIR = Path(__file__).resolve().parent

SOURCE_URL = "https://ebible.org/Scriptures/sna_usfm.zip"
SOURCE_PAGE = "https://ebible.org/details.php?id=sna"
TRANSLATION_NAME = "Biblica Open Shona Contemporary Bible (SNA)"
COPYRIGHT_NOTICE = (
    "Copyright © 2005, 2018 Biblica, Inc. "
    "Available under Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA)."
)
OUTPUT_PREFIX = "shona"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

USFM_FILENAME_PATTERN = re.compile(r"^\d+-([0-9A-Z]+)sna\.usfm$", re.IGNORECASE)
FOOTNOTE_PATTERN = re.compile(r"\\f[^\\]*\\f\*")
CROSSREF_PATTERN = re.compile(r"\\x[^\\]*\\x\*")
CHAR_MARKER_PATTERN = re.compile(r"\\\+?[a-z0-9]+\*?", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^\\s\d?\s+(.+)$")
CHAPTER_PATTERN = re.compile(r"^\\c\s+(\d+)\s*$")
VERSE_PATTERN = re.compile(r"^\\v\s+(\d+)\s+(.*)$")
META_PATTERN = re.compile(r"^\\(id|h|toc1|toc2|toc3|mt1)\s+(.+)$")
CONTINUATION_PREFIXES = (
    "\\q",
    "\\p",
    "\\m",
    "\\nb",
    "\\b",
    "\\li",
    "\\pi",
    "\\pc",
    "\\ph",
    "\\pm",
)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def load_usfm_zip(cache_file: Path) -> dict[str, str]:
    if cache_file.exists():
        print(f"Loading cached USFM zip from {cache_file}...", flush=True)
        payload = cache_file.read_bytes()
    else:
        print(f"Downloading {TRANSLATION_NAME} from {SOURCE_URL}...", flush=True)
        payload = fetch_bytes(SOURCE_URL)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(payload)
        print(f"Cached source zip to {cache_file}", flush=True)

    files: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".usfm"):
                continue
            files[Path(name).name] = archive.read(name).decode("utf-8")
    return files


def strip_usfm_markup(text: str) -> str:
    cleaned = FOOTNOTE_PATTERN.sub("", text)
    cleaned = CROSSREF_PATTERN.sub("", cleaned)
    cleaned = CHAR_MARKER_PATTERN.sub("", cleaned)
    return " ".join(cleaned.split())


def parse_book_metadata(lines: list[str]) -> tuple[str, str, str]:
    book_id = ""
    book_name = ""
    abbreviation = ""
    for line in lines[:20]:
        match = META_PATTERN.match(line.strip())
        if not match:
            continue
        marker, value = match.groups()
        value = strip_usfm_markup(value)
        if marker == "id":
            book_id = value.split()[0].upper()
        elif marker == "toc1" and not book_name:
            book_name = value
        elif marker == "toc3" and not abbreviation:
            abbreviation = value
    if not book_id:
        raise ValueError("USFM file is missing \\id marker")
    if not book_name:
        book_name = BOOK_BY_ID[book_id].name
    if not abbreviation:
        abbreviation = BOOK_BY_ID[book_id].abbreviation
    return book_id, book_name, abbreviation


def is_continuation_line(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(prefix) for prefix in CONTINUATION_PREFIXES)


def parse_usfm_book(text: str) -> Book:
    lines = text.splitlines()
    book_id, book_name, abbreviation = parse_book_metadata(lines)

    book = Book(id=book_id, name=book_name, abbreviation=abbreviation)
    current_chapter: Chapter | None = None
    current_verse_number: int | None = None
    current_verse_parts: list[str] = []

    def finalize_verse() -> None:
        nonlocal current_verse_number, current_verse_parts
        if current_chapter is None or current_verse_number is None:
            current_verse_number = None
            current_verse_parts = []
            return
        verse_text = strip_usfm_markup(" ".join(current_verse_parts))
        if verse_text:
            current_chapter.verses.append(Verse(number=current_verse_number, text=verse_text))
        current_verse_number = None
        current_verse_parts = []

    def start_chapter(number: int) -> None:
        nonlocal current_chapter
        finalize_verse()
        current_chapter = Chapter(id=f"{book_id}.{number}", number=number)
        book.chapters.append(current_chapter)

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        chapter_match = CHAPTER_PATTERN.match(line)
        if chapter_match:
            start_chapter(int(chapter_match.group(1)))
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match and current_chapter is not None:
            finalize_verse()
            heading = strip_usfm_markup(heading_match.group(1))
            if heading and heading not in current_chapter.headings:
                current_chapter.headings.append(heading)
            continue

        verse_match = VERSE_PATTERN.match(line)
        if verse_match:
            finalize_verse()
            current_verse_number = int(verse_match.group(1))
            current_verse_parts = [verse_match.group(2)]
            continue

        if current_verse_number is not None and is_continuation_line(line):
            current_verse_parts.append(strip_usfm_markup(line))

    finalize_verse()
    return book


def build_books(usfm_files: dict[str, str], selected_ids: set[str] | None) -> list[Book]:
    parsed_by_id: dict[str, Book] = {}
    for filename, content in sorted(usfm_files.items()):
        filename_match = USFM_FILENAME_PATTERN.match(filename)
        if not filename_match:
            continue
        book = parse_usfm_book(content)
        if filename_match.group(1).upper() != book.id:
            raise ValueError(
                f"Book ID mismatch in {filename}: filename has "
                f"{filename_match.group(1).upper()}, file has {book.id}"
            )
        parsed_by_id[book.id] = book

    books: list[Book] = []
    for book_info in BOOKS:
        if selected_ids and book_info.id not in selected_ids:
            continue
        book = parsed_by_id.get(book_info.id)
        if book is None:
            raise ValueError(f"Missing USFM file for book {book_info.id}")
        books.append(book)
    return books


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the Shona Bible (SNA) from ebible.org and write structured output."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(ACQUISITION_DIR / f"{OUTPUT_PREFIX}_output"),
        help="Directory for scraped output (default: acquisition/shona_output)",
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
        help="Optional path to cache the downloaded USFM zip",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_dir = Path(args.output_dir)
    cache_file = Path(args.cache_file or output_dir / ".sna_source.zip")
    selected_ids = {book_id.upper() for book_id in args.book} if args.book else None

    usfm_files = load_usfm_zip(cache_file)
    print(f"Loaded {len(usfm_files)} USFM files from archive", flush=True)

    books = build_books(usfm_files, selected_ids)
    chapters = sum(len(book.chapters) for book in books)
    verses = sum(len(chapter.verses) for book in books for chapter in book.chapters)
    print(f"Built {len(books)} books, {chapters} chapters, {verses:,} verses", flush=True)

    write_outputs(
        books=books,
        output_dir=output_dir,
        translation_name=TRANSLATION_NAME,
        source_url=SOURCE_PAGE,
        copyright_notice=COPYRIGHT_NOTICE,
        output_prefix=OUTPUT_PREFIX,
        output_format=args.format,
    )
    print(f"\nDone. Output written to {output_dir.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
