# Acquisition

Scripts and scraped Bible data for this repository. All downloaders write structured JSON and plain-text output under `*_output/` directories in this folder.

## Layout

```
acquisition/
├── bible_books.py           # Shared Protestant canon metadata
├── scrape_afr83_bible.py    # Afrikaans 1983/1992 (BibleSA)
├── scrape_bolls_bible.py    # NIV / NKJV (bolls.life bulk JSON)
├── scrape_niv_bible.py      # NIV wrapper
├── scrape_nkjv_bible.py     # NKJV wrapper
├── push_to_github.sh        # Push repo to GitHub (requires GH_TOKEN)
├── afr83_output/            # Afrikaans AFR83 scrape
├── niv_output/              # NIV scrape
└── nkjv_output/             # NKJV scrape
```

Each `*_output/` directory contains:

- `{prefix}_bible.json` / `{prefix}_bible.txt` — complete translation
- `json/{BOOK}/{chapter}.json` — per-chapter JSON
- `text/{BOOK}/{chapter}.txt` — per-chapter plain text
- `json/{BOOK}.json` / `text/{BOOK}.txt` — per-book files

## Usage

Run commands from the repository root or from `acquisition/`:

```bash
# Afrikaans (BibleSA, chapter-by-chapter; ~20 min full Bible)
python3 acquisition/scrape_afr83_bible.py
python3 acquisition/scrape_afr83_bible.py --book REV --resume

# NIV / NKJV (bolls.life; downloads full JSON, seconds to process)
python3 acquisition/scrape_niv_bible.py
python3 acquisition/scrape_nkjv_bible.py
python3 acquisition/scrape_bolls_bible.py NIV --book GEN
```

## Copyright

- **AFR83:** © Bybelgenootskap van Suid-Afrika 1983, 1992
- **NIV:** © Biblica, Inc.
- **NKJV:** © Thomas Nelson, Inc.

Use biblical text with permission. Do not redistribute commercially without rights clearance.

See [AGENTS.md](AGENTS.md) for instructions aimed at coding agents working in this folder.
