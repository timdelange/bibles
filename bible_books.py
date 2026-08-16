"""Standard Protestant canon book metadata (1-based numbering)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookInfo:
    number: int
    id: str
    name: str
    abbreviation: str


BOOKS: list[BookInfo] = [
    BookInfo(1, "GEN", "Genesis", "Gen."),
    BookInfo(2, "EXO", "Exodus", "Exod."),
    BookInfo(3, "LEV", "Leviticus", "Lev."),
    BookInfo(4, "NUM", "Numbers", "Num."),
    BookInfo(5, "DEU", "Deuteronomy", "Deut."),
    BookInfo(6, "JOS", "Joshua", "Josh."),
    BookInfo(7, "JDG", "Judges", "Judg."),
    BookInfo(8, "RUT", "Ruth", "Ruth"),
    BookInfo(9, "1SA", "1 Samuel", "1 Sam."),
    BookInfo(10, "2SA", "2 Samuel", "2 Sam."),
    BookInfo(11, "1KI", "1 Kings", "1 Kings"),
    BookInfo(12, "2KI", "2 Kings", "2 Kings"),
    BookInfo(13, "1CH", "1 Chronicles", "1 Chron."),
    BookInfo(14, "2CH", "2 Chronicles", "2 Chron."),
    BookInfo(15, "EZR", "Ezra", "Ezra"),
    BookInfo(16, "NEH", "Nehemiah", "Neh."),
    BookInfo(17, "EST", "Esther", "Est."),
    BookInfo(18, "JOB", "Job", "Job"),
    BookInfo(19, "PSA", "Psalms", "Ps."),
    BookInfo(20, "PRO", "Proverbs", "Prov."),
    BookInfo(21, "ECC", "Ecclesiastes", "Eccl."),
    BookInfo(22, "SNG", "Song of Songs", "Song"),
    BookInfo(23, "ISA", "Isaiah", "Isa."),
    BookInfo(24, "JER", "Jeremiah", "Jer."),
    BookInfo(25, "LAM", "Lamentations", "Lam."),
    BookInfo(26, "EZK", "Ezekiel", "Ezek."),
    BookInfo(27, "DAN", "Daniel", "Dan."),
    BookInfo(28, "HOS", "Hosea", "Hosea"),
    BookInfo(29, "JOL", "Joel", "Joel"),
    BookInfo(30, "AMO", "Amos", "Amos"),
    BookInfo(31, "OBA", "Obadiah", "Obad."),
    BookInfo(32, "JON", "Jonah", "Jonah"),
    BookInfo(33, "MIC", "Micah", "Mic."),
    BookInfo(34, "NAM", "Nahum", "Nah."),
    BookInfo(35, "HAB", "Habakkuk", "Hab."),
    BookInfo(36, "ZEP", "Zephaniah", "Zeph."),
    BookInfo(37, "HAG", "Haggai", "Hag."),
    BookInfo(38, "ZEC", "Zechariah", "Zech."),
    BookInfo(39, "MAL", "Malachi", "Mal."),
    BookInfo(40, "MAT", "Matthew", "Matt."),
    BookInfo(41, "MRK", "Mark", "Mark"),
    BookInfo(42, "LUK", "Luke", "Luke"),
    BookInfo(43, "JHN", "John", "John"),
    BookInfo(44, "ACT", "Acts", "Acts"),
    BookInfo(45, "ROM", "Romans", "Rom."),
    BookInfo(46, "1CO", "1 Corinthians", "1 Cor."),
    BookInfo(47, "2CO", "2 Corinthians", "2 Cor."),
    BookInfo(48, "GAL", "Galatians", "Gal."),
    BookInfo(49, "EPH", "Ephesians", "Eph."),
    BookInfo(50, "PHP", "Philippians", "Phil."),
    BookInfo(51, "COL", "Colossians", "Col."),
    BookInfo(52, "1TH", "1 Thessalonians", "1 Thess."),
    BookInfo(53, "2TH", "2 Thessalonians", "2 Thess."),
    BookInfo(54, "1TI", "1 Timothy", "1 Tim."),
    BookInfo(55, "2TI", "2 Timothy", "2 Tim."),
    BookInfo(56, "TIT", "Titus", "Titus"),
    BookInfo(57, "PHM", "Philemon", "Phlm."),
    BookInfo(58, "HEB", "Hebrews", "Heb."),
    BookInfo(59, "JAS", "James", "James"),
    BookInfo(60, "1PE", "1 Peter", "1 Pet."),
    BookInfo(61, "2PE", "2 Peter", "2 Pet."),
    BookInfo(62, "1JN", "1 John", "1 John"),
    BookInfo(63, "2JN", "2 John", "2 John"),
    BookInfo(64, "3JN", "3 John", "3 John"),
    BookInfo(65, "JUD", "Jude", "Jude"),
    BookInfo(66, "REV", "Revelation", "Rev."),
]

BOOK_BY_NUMBER = {book.number: book for book in BOOKS}
BOOK_BY_ID = {book.id: book for book in BOOKS}
