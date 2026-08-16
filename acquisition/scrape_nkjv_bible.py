#!/usr/bin/env python3
"""Download the New King James Version (NKJV) from bolls.life."""

from scrape_bolls_bible import main

if __name__ == "__main__":
    import sys

    raise SystemExit(main(["NKJV", *sys.argv[1:]]))
