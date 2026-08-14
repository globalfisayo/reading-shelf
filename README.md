# The Shelf

> **Just want it running?** Open Claude Code in this folder and say "set this up", or run `./setup.sh`.
> Everything below is background.

A reading shelf built from [Readwise](https://readwise.io), on one principle: **saving something is not reading it.**

Most "year in books" pages are really year-in-*intentions* pages — they count what you added to a list. This one
only counts evidence. For each year, an item makes the shelf if either:

- you **highlighted** it that year, or
- you **opened** it that year and got at least **5%** of the way through.

Everything else — the saved-and-never-opened, the closed-on-the-first-screen — stays off. The result is
usually a much shorter shelf than you expect, and a much more honest one.

That 5% is only where the page *starts*. The **Read at least** slider moves the bar live, from 5% up to 100%,
and the whole page rescores as you drag: the shelf, the counts, the words and the hours. Push it to 50% and you
are asking a harder question — what did I really get through? Items kept by their highlights stay at every
setting, since marking a passage is evidence of reading whatever the scroll position claims.

Three ways to look at it, switchable at the top: **Shelf** stands the books on a board, spine out;
**Covers** lays them face-out like Apple Books; **Cards** is the plain list. Every book is the same height —
spine thickness carries the length — the lighter band at the base is how far you actually got, and a gold dot
means you left highlights in it. Hovering any book pops a card with its title, author, length, progress and
highlight count; clicking opens the full drawer. Tabs switch between years, and the page follows your system's
light or dark setting unless you override it with the toggle.

---

## Setup (about five minutes)

**1. Create the repo and push this folder**

```bash
git init && git add . && git commit -m "The shelf"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/reading-shelf.git
git push -u origin main
```

**2. Add your Readwise token as a secret**

Grab it from <https://readwise.io/access_token>, then in your repo:
`Settings → Secrets and variables → Actions → New repository secret`

- Name: `READWISE_TOKEN`
- Value: your token

**3. Turn on Pages**

`Settings → Pages → Build and deployment → Source: **GitHub Actions**`

**4. Run it once**

`Actions → Refresh shelf → Run workflow`

The first run does a full sync (a couple of minutes — Readwise allows 20 requests/minute and the script paces
itself accordingly). After that your shelf is live at `https://YOUR-USERNAME.github.io/reading-shelf/`.

---

## Refreshing

Three ways, all doing the same thing:

- **The button.** `Actions → Refresh shelf → Run workflow`. This is the "when I want" path.
- **Hourly.** A cron in the workflow refreshes on its own at 17 past the hour, UTC.
- **Locally.**

  ```bash
  cp .env.example .env        # paste your token in
  export $(cat .env | xargs)
  python refresh.py           # pull from Readwise
  python build.py             # rebuild index.html
  open index.html
  ```

  `python refresh.py --full` throws away the cache and re-syncs everything from scratch.

Refreshes are incremental: each run asks Readwise only for what changed since the last one, so the hourly
schedule costs a handful of API calls rather than a full re-download.

---

## A privacy note worth reading

`data/cache.json` holds your **entire** Readwise library — every saved document, including the ones you never
opened. It is deliberately in `.gitignore` and **never committed**. On GitHub it lives in the Actions cache
instead, and only the built `index.html` (the shelf itself, the items that passed the bar) is committed and
published.

If you ever change that, remember the shelf is public: the titles of everything you read become public with it.

---

## Tuning it

| What | Where |
|---|---|
| The 25% bar | `MIN_PROGRESS` in `build.py` |
| Which Reader locations get synced | `LOCATIONS` in `readwise_client.py` (the RSS `feed` is skipped on purpose) |
| Categories to ignore | `SKIP_CATEGORIES` in `build.py` |
| Colours, copy, layout | `template.html` — plain HTML/CSS/JS, no build step |

## Files

```
refresh.py           pull Readwise -> data/cache.json  (incremental)
build.py             cache.json -> index.html
readwise_client.py   API calls, pagination, rate-limit handling
template.html        the page; __DATA__ / __YEARS__ get substituted in
index.html           the built shelf (committed, this is what Pages serves)
```

No dependencies — standard library Python only, so CI needs no `pip install`.

---

## Two things that will eventually confuse you

**Scheduled workflows get disabled after 60 days of no repo activity.** GitHub does this to every public repo.
If the shelf stops updating, push any commit or hit the Run workflow button and the schedule resumes.

**Progress on PDFs and videos is Readwise's scroll estimate.** 100% on a talk means the transcript reached the
end, not that you watched every minute. The highlight counts are the harder evidence.
