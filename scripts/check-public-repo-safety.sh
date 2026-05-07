#!/usr/bin/env bash
set -euo pipefail

failed=0

fail() {
  failed=1
  printf 'ERROR: %s\n' "$*" >&2
}

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  fail ".env is tracked. Remove it from git and rotate any keys that were committed."
fi

if git ls-files | grep -E '(^|/)\.env\.(local|development|production|staging|test)$' >/dev/null; then
  fail "A real .env.* file is tracked. Only .env.example may be committed."
fi

if ! git check-ignore -q .env; then
  fail ".env is not ignored by git."
fi

if ! git check-ignore -q .env.local; then
  fail ".env.local is not ignored by git."
fi

common_secret_matches="$(
  git grep -nIE \
    'BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY|sk-ant-api[0-9A-Za-z_-]+|sk-proj-[A-Za-z0-9_-]+|sk-[A-Za-z0-9]{20,}|[0-9]{8,10}:[A-Za-z0-9_-]{35,}|xox[baprs]-[A-Za-z0-9-]+' \
    -- . \
    ':!.git' \
    ':!scripts/check-public-repo-safety.sh' || true
)"

if [ -n "$common_secret_matches" ]; then
  fail "Potential secret-looking values found:"
  printf '%s\n' "$common_secret_matches" >&2
fi

sensitive_assignment_matches="$(
  git grep -nIE \
    '(^|[^A-Z0-9_])(RUNWAY_API_KEY|RUNWAYML_API_SECRET|ANTHROPIC_API_KEY|OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|DEMO_PASSWORD|WEBHOOK_SECRET|DATABASE_URL)[[:space:]]*[:=][[:space:]]*["'\'']?[^"'\''[:space:]#]+' \
    -- . \
    ':!.git' \
    ':!scripts/check-public-repo-safety.sh' || true
)"

if [ -n "$sensitive_assignment_matches" ]; then
  unsafe_assignments="$(
    printf '%s\n' "$sensitive_assignment_matches" |
      grep -vE '(replace_me|placeholder|example|your_|<[^>]+>|sqlite:///\./recall\.db|http://localhost:8000)' || true
  )"

  if [ -n "$unsafe_assignments" ]; then
    fail "Sensitive env-style assignments found with non-placeholder values:"
    printf '%s\n' "$unsafe_assignments" >&2
  fi
fi

if [ "$failed" -ne 0 ]; then
  exit 1
fi

printf '%s\n' "Public repo safety check passed: no tracked .env files or obvious secrets found."
