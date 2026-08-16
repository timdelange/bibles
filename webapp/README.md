# Webapp

Front-end application for browsing and using the Bible translations stored in `../acquisition/`.

## Status

Not started yet. This folder is reserved for the web application.

## Planned layout

```
webapp/
├── package.json
├── src/
└── public/
```

## Data source

Read scraped translations from `../acquisition/`:

| Translation | Data path |
|---|---|
| Afrikaans AFR83 | `../acquisition/afr83_output/` |
| NIV | `../acquisition/niv_output/` |
| NKJV | `../acquisition/nkjv_output/` |

Prefer loading per-chapter JSON (`json/{BOOK}/{chapter}.json`) for the UI rather than the full `{prefix}_bible.json` files (~6–7 MB each).

## Agent notes

- Keep application code in this folder only.
- Do not add scrapers or bulk Bible data here — use `../acquisition/`.
- See `../acquisition/AGENTS.md` for download and data-format details.
