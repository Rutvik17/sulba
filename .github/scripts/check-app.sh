#!/usr/bin/env bash
# Checks the app on a deployed site, where Cloudflare decides which addresses reach the Worker
# (decision records 54 and 55). An address under /app/, opened as a browser opens a page, answers
# with the app's page; the script that page loads answers as JavaScript; and the MCP server's
# metadata, which only the Worker writes, answers as JSON. It asks for a minute while a deploy
# reaches every location.
set -euo pipefail

site=$1
script=''
type=''
metadata=''
for _ in 1 2 3 4 5 6; do
  page=$(curl -fsS --max-time 20 -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Dest: document' \
    "$site/app/specs/42") || page=''
  script=$(grep -o '/app/assets/[^"]*\.js' <<<"$page" | head -n 1) || script=''
  type=''
  if [ -n "$script" ]; then
    type=$(curl -fsS --max-time 20 -o /dev/null -w '%{content_type}' \
      -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Dest: script' "$site$script") || type=''
  fi
  metadata=$(curl -fsS --max-time 20 -o /dev/null -w '%{content_type}' \
    "$site/.well-known/oauth-protected-resource/mcp") || metadata=''
  if [[ ($type == text/javascript* || $type == application/javascript*) && $metadata == application/json* ]]; then
    echo "$site/app/specs/42 loads $script, which answers as $type, and the MCP server's metadata answers as $metadata."
    exit 0
  fi
  sleep 10
done
echo "::error::$site/app/specs/42 loads ${script:-no script}, which answers as ${type:-nothing}, and the MCP server's metadata answers as ${metadata:-an error}. The script must be JavaScript and the metadata JSON."
exit 1
