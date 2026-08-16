# Afrikaans 1983/1992 Bible (AFR83)

Scraped text of the Afrikaans 1983/1992 Bible translation from [BibleSA](https://www.biblesa.co.za/af/bybel/AFR83), plus the scraper used to extract it.

## Contents

- `scrape_afr83_bible.py` — downloads the translation book by book and chapter by chapter
- `afr83_output/afr83_bible.json` — complete Bible in structured JSON
- `afr83_output/afr83_bible.txt` — complete Bible in plain text
- `afr83_output/json/` — per-book and per-chapter JSON files
- `afr83_output/text/` — per-book and per-chapter plain-text files

## Scraper usage

Afrikaans (BibleSA, chapter-by-chapter):

```bash
python3 scrape_afr83_bible.py
python3 scrape_afr83_bible.py --book REV
python3 scrape_afr83_bible.py --list-books
python3 scrape_afr83_bible.py --resume
```

NIV and NKJV (bolls.life bulk JSON):

```bash
python3 scrape_niv_bible.py
python3 scrape_nkjv_bible.py
python3 scrape_bolls_bible.py NIV --book GEN
python3 scrape_bolls_bible.py NKJV -o nkjv_output
```

## Copyright

The biblical text is © Bybelgenootskap van Suid-Afrika 1983, 1992. Use with permission. All rights reserved.
