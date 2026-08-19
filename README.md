# bibles

Bible translations in structured JSON and plain text, plus tools to acquire them and (eventually) a web app to browse them.

**Repository:** https://github.com/timdelange/bibles

## Layout

```
bibles/
├── acquisition/     # Scrapers and scraped Bible data
│   ├── afr83_output/
│   ├── niv_output/
│   ├── nkjv_output/
│   ├── shona_output/
│   └── AGENTS.md      # Instructions for coding agents
└── webapp/            # Web application (in progress)
```

## Translations

| Code | Translation | Source | Chapters |
|---|---|---|---|
| AFR83 | Afrikaans 1983/1992 | BibleSA | 1,189 |
| NIV | New International Version | bolls.life | 1,189 |
| NKJV | New King James Version | bolls.life | 1,189 |
| SNA | Biblica Open Shona Contemporary Bible | ebible.org | 1,189 |

## Quick start

```bash
# Refresh Afrikaans (chapter-by-chapter scrape)
python3 acquisition/scrape_afr83_bible.py --resume

# Refresh NIV / NKJV (bulk download)
python3 acquisition/scrape_niv_bible.py
python3 acquisition/scrape_nkjv_bible.py
python3 acquisition/scrape_shona_bible.py
```

See [acquisition/README.md](acquisition/README.md) for full scraper documentation and [acquisition/AGENTS.md](acquisition/AGENTS.md) for agent-oriented instructions.

## Copyright

Biblical text is copyrighted by the respective publishers. See [acquisition/README.md](acquisition/README.md) for per-translation notices.
