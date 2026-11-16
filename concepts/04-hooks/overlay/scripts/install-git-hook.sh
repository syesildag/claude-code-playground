#!/usr/bin/env bash
# Install the same secret scanner as a real git pre-commit hook (the second layer of defence).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
exec python3 .claude/hooks/scan_secrets.py --git-hook
EOF
chmod +x .git/hooks/pre-commit
echo "Installed .git/hooks/pre-commit. Bypass with --no-verify, which block_dangerous_bash.py denies to Claude."
