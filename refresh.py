#!/usr/bin/env python3
"""Pull the latest from Readwise into data/cache.json.

Incremental by default: only asks Readwise for what changed since the last run,
which keeps it well under the 20 requests/minute limit even on an hourly schedule.
Pass --full to rewrite the cache from scratch.
"""
import json, os, sys, datetime, pathlib
import readwise_client as rw

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "data" / "cache.json"


def load():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {"last_synced": None, "documents": {}, "highlights": {}}


def main():
    rw._token()                       # fail fast if the token is missing
    full = "--full" in sys.argv
    cache = {"last_synced": None, "documents": {}, "highlights": {}} if full else load()
    since = None if full else cache.get("last_synced")
    started = datetime.datetime.now(datetime.timezone.utc)

    print(f"Sync mode: {'FULL' if not since else 'incremental since ' + since}")

    print("Fetching Reader documents...")
    docs = rw.fetch_documents(since)
    cache["documents"].update(docs)

    print("Fetching Readwise highlights...")
    hls = rw.fetch_highlights(since)
    cache["highlights"].update(hls)

    # drop anything Readwise has since deleted
    cache["documents"] = {k: v for k, v in cache["documents"].items()
                          if not v.get("is_deleted")}

    cache["last_synced"] = started.isoformat().replace("+00:00", "Z")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(f"\n{len(docs)} documents and {len(hls)} highlight sources changed this run.")
    print(f"Cache now holds {len(cache['documents'])} documents, "
          f"{len(cache['highlights'])} highlight sources.")


if __name__ == "__main__":
    main()
