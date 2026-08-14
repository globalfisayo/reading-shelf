# Instructions for Claude Code

The person who handed you this folder wants their reading shelf live on GitHub Pages, and does not want to read
documentation or run steps by hand. Do the whole thing for them.

## What to do

Run `./setup.sh` and shepherd it to completion. It creates the repo, pushes, stores their Readwise token as a
secret, enables Pages, and triggers the first build.

Two moments need the person themselves — do not try to do these for them:

1. **GitHub login** (`gh auth login`) if they aren't already authenticated. Interactive by design.
2. **The Readwise token.** The script calls `gh secret set`, which prompts for it and hides the input. Point them
   at <https://readwise.io/access_token>. Never ask them to paste the token into the chat, never put it in a file,
   and never echo it — it goes straight from their keyboard into the secret.

If `setup.sh` fails, read the error, fix the cause, and re-run it. It is safe to run more than once: it skips repo
creation if the repo already exists and skips the commit if there is nothing to commit.

When it finishes, tell them the two URLs it prints (the live shelf and the repo) and that it refreshes hourly, plus
the "Run workflow" button in the Actions tab for refreshing on demand. Nothing else.

## Things that will bite you

- **GitHub Pages 404s for a minute or two** after the first successful run. That is normal propagation, not a
  failure. Check `gh run list` shows the run green before assuming anything is broken.
- **The workflow needs Actions write permission** to commit the rebuilt `index.html`. `setup.sh` sets this via the
  API, but if the push step fails with a 403, that is the cause — check
  `Settings → Actions → General → Workflow permissions`.
- **`data/cache.json` must never be committed.** It holds their entire Readwise library including everything they
  saved and never read; the repo is public. It is in `.gitignore` — leave it there. Only `index.html` is published.
- **Readwise allows 20 requests/minute.** `readwise_client.py` already paces itself and handles 429s. If a run
  looks slow, it is being polite, not stuck. The first full sync takes a few minutes.

## If they ask for changes afterwards

| What | Where |
|---|---|
| The floor for what gets built in (5%) | `MIN_PROGRESS` in `build.py` |
| Where the "Read at least" slider starts | `DEFAULT_PROGRESS` in `build.py` |
| Colours, copy, layout | `template.html` (plain HTML/CSS/JS, no build step) |
| Which Reader locations sync | `LOCATIONS` in `readwise_client.py` — the RSS `feed` is skipped on purpose |
| Refresh schedule | the `cron` in `.github/workflows/refresh.yml` |

After editing anything, run `python build.py` to regenerate `index.html`, then commit and push — the workflow
rebuilds and redeploys on every push to `main`.

Full background on how the shelf decides what counts is in `README.md`.
