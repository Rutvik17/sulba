#!/usr/bin/env bash
# Prints the Preview name for a branch: lowercase letters, digits and dashes, starting with a
# letter, and short enough that "<name>-web" fits a 63-character DNS label.
set -euo pipefail

name=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^[^a-z]+//' | cut -c 1-59 | sed -E 's/-+$//')
printf '%s\n' "${name:-preview}"
