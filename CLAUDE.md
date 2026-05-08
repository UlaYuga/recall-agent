# Recall — Claude Code Instructions

## Working directory

Always work in the **main project root**: `/Users/axel/Documents/Проекты/Recall`

If you are spawned inside a worktree (path contains `.claude/worktrees/`), apply all file changes to the main repo path instead. The worktree is a review sandbox — it is not where the work lands.

## Git

Commit after every completed task. Stage only task-scoped files (never XLSX, `.env`, generated media). Use the task ID in the commit message, e.g.:

```
feat(db): T-03 — description

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Do not push unless Alexander explicitly asks.

## Checks before every commit

```bash
cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev pytest -q
cd backend && PYTHONPATH=. uv run --python 3.11 --extra dev ruff check .
make public-check
git status --short
```

All must pass. No commit on red.

## Scope rules

- Read `docs/curator_prompts/QUEUE_STATUS.md` at the start of each task.
- Do not implement tasks that are listed as out-of-scope in the active prompt.
- Do not touch XLSX files.
- Do not overwrite accepted seed/content artifacts (`backend/seeds/`).
