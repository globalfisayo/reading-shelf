#!/usr/bin/env bash
# One-shot setup: create the GitHub repo, publish the shelf, wire up the refresh.
set -euo pipefail

say() { printf "\n\033[1m%s\033[0m\n" "$*"; }
die() { printf "\n\033[31m%s\033[0m\n" "$*" >&2; exit 1; }

say "1/7  Checking tools"
for c in git gh python3; do
  command -v "$c" >/dev/null || die "Missing '$c'. Install it first (gh: https://cli.github.com)."
done
echo "ok: git, gh, python3"

say "2/7  Checking GitHub login"
if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in. Opening GitHub login..."
  gh auth login
fi
OWNER=$(gh api user --jq .login)
echo "ok: signed in as $OWNER"

say "3/7  Repository name"
read -r -p "Repo name [reading-shelf]: " REPO
REPO=${REPO:-reading-shelf}

say "4/7  Creating and pushing the repo"
[ -d .git ] || git init -q
git add -A
git diff --staged --quiet || git commit -qm "The shelf"
git branch -M main
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "Repo already exists, pushing to it."
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$OWNER/$REPO.git"
  git push -u origin main
else
  gh repo create "$REPO" --public --source=. --remote=origin --push \
    --description "A reading shelf built from Readwise, where saving something doesn't count as reading it."
fi
echo "ok: https://github.com/$OWNER/$REPO"

say "5/7  Readwise token"
echo "Get one at https://readwise.io/access_token (it will be hidden as you paste)."
gh secret set READWISE_TOKEN --repo "$OWNER/$REPO"
gh api -X PUT "repos/$OWNER/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=false >/dev/null
echo "ok: secret stored, Actions given write access"

say "6/7  Turning on GitHub Pages"
gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
  || gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
  || echo "note: couldn't set Pages automatically -- do it at Settings > Pages > Source: GitHub Actions"
echo "ok"

say "7/7  Running the first sync (this one is a full download, give it a few minutes)"
gh workflow run refresh.yml --repo "$OWNER/$REPO" || die "Couldn't start the workflow. Run it from the Actions tab."
sleep 12
gh run watch --repo "$OWNER/$REPO" --exit-status "$(gh run list --repo "$OWNER/$REPO" --workflow refresh.yml --limit 1 --json databaseId --jq '.[0].databaseId')" || {
  echo "The run failed. Open it with: gh run view --repo $OWNER/$REPO --log-failed"
  exit 1
}

cat <<MSG

  Done.

  Your shelf:   https://$OWNER.github.io/$REPO/
  The repo:     https://github.com/$OWNER/$REPO

  It refreshes hourly on its own. To refresh right now, either:
    gh workflow run refresh.yml --repo $OWNER/$REPO
  or hit "Run workflow" under the Actions tab.

  (Pages can take a minute or two to serve the first build.)
MSG
