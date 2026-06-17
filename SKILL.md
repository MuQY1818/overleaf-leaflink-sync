---
name: overleaf-leaflink-sync
description: Sync a LaTeX project to an Overleaf project with LeafLink when the user wants to avoid Overleaf Git, browser login, or manual zip upload. Use when setting up or running a LeafLink-based Overleaf sync workflow, including conda environment setup, browser login, clone/pull/push, dry-run checks, or packaging a clean Overleaf source tree from an existing manuscript repo.
---

# Overleaf LeafLink Sync

Use this skill to keep a local LaTeX source tree in sync with Overleaf through LeafLink.

## Workflow

1. Check the local repository for the clean Overleaf package target.
2. Use a dedicated conda environment, never `base`.
3. Install `leaflink[browser,watch]` and Chromium if needed.
4. Login to Overleaf through LeafLink.
5. Clone or update the dedicated sync directory.
6. Copy only the packaged Overleaf sources into that directory.
7. Run `status` and `push --dry-run` before any real push.
8. Push only after the dry run looks correct.

## Rules

- Keep the repository root as the source of truth.
- Sync only a clean Overleaf package directory, not the full repo.
- Exclude build products, research artifacts, and git metadata.
- Prefer `make overleaf-package` from the manuscript repo before syncing.
- If browser login or Chromium setup is blocked, stop and report the blocker instead of guessing.

## Practical checks

- Confirm `conda` environment is not `base`.
- Confirm `output/overleaf_src/` exists or can be generated.
- Confirm the target Overleaf URL or project id.
- Confirm the sync directory contains only files meant for Overleaf.
- If Playwright browsers were installed outside the default home cache, set or preserve `PLAYWRIGHT_BROWSERS_PATH`; common local path: `/mnt/data/.cache/ms-playwright`.

## Reference command shape

Use the repo’s existing package target first:

```bash
make overleaf-package
```

Then run LeafLink in the dedicated sync workspace:

```bash
leaflink login --base-url https://www.overleaf.com
leaflink clone https://www.overleaf.com/project/<project-id> <sync-dir>
leaflink status
leaflink push --dry-run
leaflink push
```

## Failure handling

- If the user has not logged in yet, ask them to complete the browser login.
- If LeafLink cannot resolve the project or remote tree, fall back to a clean package plus manual upload path.
- If the sync scope is unclear, default to the smallest Overleaf-safe source set.
