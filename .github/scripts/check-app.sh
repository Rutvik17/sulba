#!/usr/bin/env bash
# Checks the app on a deployed site: an address under /app/, opened as a browser opens a page,
# answers with the app's page, and the script that page loads answers as JavaScript (decision
# record 54). It asks for a minute while a deploy reaches every location.
set -euo pipefail

site=$1
script=''
type=''
for _ in 1 2 3 4 5 6; do
  page=$(curl -fsS --max-time 20 -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Dest: document' \
    "$site/app/specs/42") || page=''
  script=$(grep -o '/app/assets/[^"]*\.js' <<<"$page" | head -n 1) || script=''
  if [ -n "$script" ]; then
    type=$(curl -fsS --max-time 20 -o /dev/null -w '%{content_type}' \
      -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Dest: script' "$site$script") || type=''
    case $type in
      text/javascript* | application/javascript*)
        echo "$site/app/specs/42 loads $script, which answers as $type."
        exit 0
        ;;
    esac
  fi
  sleep 10
done
echo "::error::$site/app/specs/42 loads ${script:-no script}, which answers as ${type:-nothing}, not JavaScript."
exit 1
