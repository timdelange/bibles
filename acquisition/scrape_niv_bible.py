#!/usr/bin/env python3
"""Download the New International Version (NIV) from bolls.life."""

from scrape_bolls_bible import main

if __name__ == "__main__":
    import sys

    raise SystemExit(main(["NIV", *sys.argv[1:]]))
