# Agent instructions — acquisition

Use this folder when downloading, refreshing, or inspecting Bible text data. The web application lives in `../webapp/` and should read from these outputs — do not duplicate scraped data there.

## Quick reference

| Translation | Script | Source | Output dir |
|---|---|---|---|
| Afrikaans AFR83 | `scrape_afr83_bible.py` | [BibleSA](https://www.biblesa.co.za/af/bybel/AFR83) | `afr83_output/` |
| NIV | `scrape_niv_bible.py` | [bolls.life](https://bolls.life) | `niv_output/` |
| NKJV | `scrape_nkjv_bible.py` | [bolls.life](https://bolls.life) | `nkjv_output/` |
| Shona SNA | `scrape_shona_bible.py` | [ebible.org](https://ebible.org/details.php?id=sna) | `shona_output/` |

## Running scrapers

Always prefer paths relative to this directory. Scripts default output to `acquisition/*_output/` regardless of current working directory.

```bash
# From repo root
python3 acquisition/scrape_afr83_bible.py --resume
python3 acquisition/scrape_niv_bible.py
python3 acquisition/scrape_nkjv_bible.py
python3 acquisition/scrape_shona_bible.py

# Single book test
python3 acquisition/scrape_afr83_bible.py --book REV -o acquisition/afr83_output
python3 acquisition/scrape_bolls_bible.py NIV --book GEN
```

Afrikaans full scrape: ~1,189 chapters, ~1 s delay → ~20 minutes. Use `--resume` to continue interrupted runs.

NIV/NKJV: one HTTP download per translation (~7–10 MB), then local processing. Re-runs use cached `.*_source.json` in the output directory.

Shona SNA: one USFM zip download (~1.4 MB) from ebible.org, then local parsing. Re-runs use cached `.sna_source.zip` in the output directory.

## Output schema

Per-chapter JSON (`json/{BOOK}/{chapter}.json`):

```json
{
  "id": "GEN.1",
  "number": 1,
  "headings": ["The Beginning"],
  "verses": [
    { "number": 1, "text": "..." }
  ]
}
```

Full Bible JSON (`{prefix}_bible.json`):

```json
{
  "translation": "...",
  "source": "...",
  "copyright": "...",
  "books": [ { "id": "GEN", "name": "Genesis", "chapters": [...] } ]
}
```

Book IDs use BibleSA-style codes: `GEN`, `EXO`, `1SA`, `MAT`, `REV`, etc. See `bible_books.py`.

## What to change here vs `webapp/`

| Task | Where |
|---|---|
| New translation scraper | `acquisition/` |
| Re-scrape / refresh data | `acquisition/` |
| API, UI, search, TTS | `../webapp/` |
| Git push helper | `acquisition/push_to_github.sh` (repo root is parent) |

## Pushing to GitHub

Requires `GH_TOKEN` as a runtime secret on a **new** cloud agent run:

```bash
acquisition/push_to_github.sh bibles
```

## Do not

- Commit scrape logs (`*_scrape.log`) or `__pycache__/`
- Copy full `*_output/` trees into `webapp/` — reference them or load at build time
- Re-scrape unless data is missing or sources changed; use `--resume` for partial Afrikaans runs
