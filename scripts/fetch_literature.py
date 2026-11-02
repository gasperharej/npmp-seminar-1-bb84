#!/usr/bin/env python3
"""Download the manifest's open-access papers; standard library only."""

from __future__ import annotations

import json
import os
import tempfile
import time
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "literature" / "sources.json"
DEST = ROOT / "literature" / "pdfs"
MAX_SIZE = 30 * 1024 * 1024


def valid_pdf(path: Path) -> bool:
    """Check size, PDF header and EOF marker (not a full PDF parser)."""
    if not path.is_file() or not 1000 <= path.stat().st_size <= MAX_SIZE:
        return False
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            return False
        stream.seek(max(0, path.stat().st_size - 1024))
        return stream.read().rstrip().endswith(b"%%EOF")


def download(url: str, destination: Path) -> None:
    """Validate the complete response before atomically replacing the target."""
    request = Request(
        url,
        headers={
            "User-Agent": "BB84SeminarLiteratureDownloader/1.0 (academic personal study)",
            "Accept": "application/pdf",
        },
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".download-", suffix=".tmp", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output, urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f"nepričakovan HTTP status {response.status}")
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" in content_type:
                raise ValueError("strežnik je vrnil HTML namesto PDF")
            length = response.headers.get("Content-Length")
            if length is not None and not 1000 <= int(length) <= MAX_SIZE:
                raise ValueError("neveljavna ali prevelika dolžina odgovora")
            first = response.read(8192)
            if not first.startswith(b"%PDF-"):
                raise ValueError(f"odgovor ni PDF (Content-Type: {content_type!r})")
            output.write(first)
            total = len(first)
            while chunk := response.read(256 * 1024):
                total += len(chunk)
                if total > MAX_SIZE:
                    raise ValueError("PDF presega omejitev 30 MiB")
                output.write(chunk)
            if length is not None and total != int(length):
                raise ValueError(f"nepopoln odgovor: {total}/{length} bajtov")
        if not valid_pdf(temporary):
            raise ValueError("PDF ni prestal preverjanja glave, velikosti in oznake %%EOF")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def fetch_with_retry(url: str, destination: Path) -> None:
    """Retry transient network/server failures once, with a short polite delay."""
    for attempt in range(2):
        try:
            download(url, destination)
            return
        except HTTPError as exc:
            if attempt or exc.code not in (408, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, HTTPException):
            if attempt:
                raise
        print("       Začasna omrežna napaka; ponovni poskus čez 2 s.", flush=True)
        time.sleep(2)


def main() -> int:
    try:
        papers = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Napaka pri branju manifesta: {exc}")
        return 1
    DEST.mkdir(parents=True, exist_ok=True)
    available = 0
    for paper in papers:
        filename = paper["filename"]
        if Path(filename).name != filename or Path(filename).suffix.lower() != ".pdf":
            print(f"Neveljavno ime v manifestu: {filename!r}")
            continue
        target = DEST / filename
        if valid_pdf(target):
            available += 1
            print(f"SKIP   {filename} — obstoječi PDF je veljaven", flush=True)
            continue
        url = paper["pdf_url"]
        print(f"FETCH  {filename}", flush=True)
        try:
            fetch_with_retry(url, target)
        except (HTTPError, URLError, TimeoutError, HTTPException, OSError, ValueError) as exc:
            print(f"FAILED {filename}: {exc}")
            print(f"       Ročni prenos: {url}")
            if paper.get("arxiv"):
                print(f"       Stran članka: https://arxiv.org/abs/{paper['arxiv']}")
            if paper.get("doi"):
                print(f"       Stran založnika: https://doi.org/{paper['doi']}")
            if paper.get("fallback_url"):
                print(f"       Institucionalni repozitorij: {paper['fallback_url']}")
        else:
            available += 1
            print(f"OK     {filename} ({target.stat().st_size:,} bajtov)")
        time.sleep(1)
    print(f"\nNa voljo: {available}/{len(papers)} preverjenih PDF-jev.")
    return 0 if available == len(papers) else 1


if __name__ == "__main__":
    raise SystemExit(main())
