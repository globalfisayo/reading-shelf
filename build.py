#!/usr/bin/env python3
"""Turn data/cache.json into index.html -- the shelf.

The bar for making the shelf, per year:
  (a) you highlighted it that year, OR
  (b) you opened it that year AND got at least MIN_PROGRESS of the way through.
Saving something is not reading it, so saving alone never counts.
"""
import json, re, pathlib, datetime, collections

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "data" / "cache.json"
OUT = ROOT / "index.html"
TEMPLATE = ROOT / "template.html"

MIN_PROGRESS = 0.25
SKIP_CATEGORIES = {"rss"}

CANON = {"articles": "article", "tweets": "tweet", "books": "epub", "podcasts": "podcast"}
LABEL = {"epub": "Book", "pdf": "Report", "article": "Article", "video": "Talk",
         "podcast": "Podcast", "tweet": "Thread", "email": "Newsletter", "note": "Note"}
HUE = {"epub": 32, "pdf": 212, "article": 158, "video": 280,
       "podcast": 8, "tweet": 196, "email": 48, "note": 100}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def year_of(ts):
    return ts[:4] if ts else None


def clean_author(a):
    a = (a or "").strip()
    a = re.sub(r"\s*\[.*?\]\s*$", "", a)
    return "" if a.lower() in ("n/a", "unknown", "none", "") else a


def build():
    cache = json.loads(CACHE.read_text())
    docs, hl_books = cache["documents"], cache["highlights"]

    # highlight counts per source per year, indexed by normalised title
    by_title = {}
    for b in hl_books.values():
        years = collections.Counter()
        for h in b.get("highlights", []):
            y = year_of(h.get("highlighted_at") or h.get("created_at"))
            if y:
                years[y] += 1
        if not years:
            continue
        by_title[norm(b.get("title"))] = {
            "years": years, "title": b.get("title"), "author": b.get("author"),
            "category": b.get("category"), "url": b.get("source_url") or b.get("highlights_url"),
            "matched": False,
        }

    records = []

    def emit(year, title, author, cat, prog, hl, opened, first, wc, url, summary, ev):
        cat = CANON.get(cat, cat) or "article"
        records.append({
            "y": year, "title": (title or "").strip(), "author": clean_author(author),
            "cat": cat, "catLabel": LABEL.get(cat, cat.title()), "hue": HUE.get(cat, 220),
            "wc": wc or 0, "prog": None if prog is None else round(prog * 100),
            "hl": hl, "date": opened or "", "month": (opened or "")[:7],
            "first": (first or "")[:10], "url": url or "",
            "summary": (summary or "").strip(), "ev": ev,
        })

    for d in docs.values():
        cat = d.get("category")
        if cat in SKIP_CATEGORIES or not (d.get("title") or "").strip():
            continue
        key = norm(d.get("title"))
        hl_years = collections.Counter()
        if key in by_title:
            by_title[key]["matched"] = True
            hl_years = by_title[key]["years"]

        opened = d.get("last_opened_at") or ""
        prog = d.get("reading_progress")
        oy = year_of(opened)
        read_ok = oy and (prog or 0) >= MIN_PROGRESS

        for y in set(list(hl_years) + ([oy] if read_ok else [])):
            has_hl, has_read = hl_years.get(y, 0) > 0, (y == oy and read_ok)
            last = max([x for x in [opened if y == oy else "",
                                    f"{y}-12-31" if has_hl and y != oy else ""] if x] or [f"{y}-01-01"])
            emit(y, d.get("title"), d.get("author"), cat, prog, hl_years.get(y, 0),
                 last if y == oy and opened else (opened if year_of(opened) == y else f"{y}-06-15"),
                 d.get("first_opened_at") or d.get("saved_at") or d.get("created_at"),
                 d.get("word_count"), d.get("url") or d.get("source_url"), d.get("summary"),
                 "both" if has_hl and has_read else ("highlighted" if has_hl else "progress"))

    # highlighted sources with no Reader document of their own
    for b in by_title.values():
        if b["matched"]:
            continue
        for y, n in b["years"].items():
            emit(y, b["title"], b["author"], b["category"], None, n,
                 f"{y}-06-15", None, None, b["url"], None, "highlighted")

    # merge duplicates of the same piece within a year
    merged = {}
    for r in records:
        k = (r["y"], norm(r["title"]))
        if k in merged:
            m = merged[k]
            m["hl"] += r["hl"]
            if (r["prog"] or 0) > (m["prog"] or 0):
                m["prog"] = r["prog"]
            if r["date"] > m["date"]:
                m["date"], m["month"] = r["date"], r["month"]
            for f in ("summary", "author", "url"):
                m[f] = m[f] or r[f]
            if m["ev"] != r["ev"]:
                m["ev"] = "both"
        else:
            merged[k] = r
    records = sorted(merged.values(), key=lambda r: r["date"], reverse=True)

    years = sorted({r["y"] for r in records}, reverse=True)
    html = TEMPLATE.read_text()
    html = (html.replace("__DATA__", json.dumps(records, ensure_ascii=False))
                .replace("__YEARS__", json.dumps(years))
                .replace("__SYNCED__", (cache.get("last_synced") or "")[:16].replace("T", " ") + " UTC")
                .replace("__TOTALDOCS__", str(len(docs))))
    OUT.write_text(html)

    print(f"Built {OUT} -- {len(records)} shelf entries across {len(years)} years "
          f"({', '.join(years)}) from {len(docs)} documents.")
    for y in years:
        n = sum(1 for r in records if r["y"] == y)
        print(f"  {y}: {n}")


if __name__ == "__main__":
    build()
