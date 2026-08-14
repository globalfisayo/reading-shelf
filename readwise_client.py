"""Minimal Readwise + Reader API client. Standard library only."""
import json, os, time, urllib.request, urllib.parse, urllib.error

BASE_READER = "https://readwise.io/api/v3/list/"
BASE_EXPORT = "https://readwise.io/api/v2/export/"
# Reader locations worth syncing. "feed" is RSS firehose noise -- deliberately skipped.
LOCATIONS = ["new", "later", "shortlist", "archive"]


def _token():
    t = os.environ.get("READWISE_TOKEN", "").strip()
    if not t:
        raise SystemExit(
            "READWISE_TOKEN is not set.\n"
            "  Local:  copy .env.example to .env and paste your token, or `export READWISE_TOKEN=...`\n"
            "  GitHub: Settings -> Secrets and variables -> Actions -> New repository secret\n"
            "  Get one at https://readwise.io/access_token"
        )
    return t


def _get(url, params, tries=6):
    """GET with Readwise's 20 req/min rate limit handled politely."""
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    req = urllib.request.Request(f"{url}?{q}", headers={"Authorization": f"Token {_token()}"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After") or 60) + 1
                print(f"  rate limited, sleeping {wait}s")
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < tries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise SystemExit("Readwise API kept failing after retries.")


def fetch_documents(updated_after=None):
    """Every Reader document (minus the RSS feed), keyed by id."""
    out = {}
    for loc in LOCATIONS:
        cursor, page = None, 0
        while True:
            page += 1
            data = _get(BASE_READER, {"location": loc, "pageCursor": cursor,
                                      "updatedAfter": updated_after})
            for d in data.get("results", []):
                if d.get("id"):
                    out[d["id"]] = d
            cursor = data.get("nextPageCursor")
            print(f"  {loc}: page {page}, {len(out)} docs so far")
            if not cursor:
                break
            time.sleep(3.2)          # stay under 20/min
        time.sleep(3.2)
    return out


def fetch_highlights(updated_after=None):
    """Readwise highlight export, keyed by book id."""
    out, cursor, page = {}, None, 0
    while True:
        page += 1
        data = _get(BASE_EXPORT, {"pageCursor": cursor, "updatedAfter": updated_after})
        for b in data.get("results", []):
            out[str(b.get("user_book_id"))] = b
        cursor = data.get("nextPageCursor")
        print(f"  highlights: page {page}, {len(out)} sources so far")
        if not cursor:
            break
        time.sleep(3.2)
    return out
