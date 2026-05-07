# Security

This repository is safe to keep public only if real credentials never enter git.

## Secrets Policy

- Commit `.env.example` with placeholder values only.
- Keep real credentials in local `.env`, deployment secrets, or GitHub repository secrets.
- Never commit generated `.env.*` files except `.env.example`.
- If a real key is committed, treat it as compromised and rotate it immediately.

Required local variables:

```env
RUNWAY_API_KEY=replace_me
ANTHROPIC_API_KEY=replace_me
OPENAI_API_KEY=replace_me
TELEGRAM_BOT_TOKEN=replace_me
DEMO_PASSWORD=replace_me
```

## Local Setup

```bash
cp .env.example .env
make install-hooks
```

`make install-hooks` points git at the tracked `.githooks/` directory. The pre-commit hook runs the same public repository safety scan as CI.

## Before Publishing

Run:

```bash
make public-check
git status --short
```

Also enable GitHub secret scanning in repository settings when the repository is public.
