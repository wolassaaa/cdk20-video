#!/bin/sh
set -eu
PATH="/usr/bin:/bin:$PATH"
export PATH
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:?Usage: ROLLBACK.sh TARGET_COPY.pdf}
case "$target" in
  */ORIGINAL.pdf|ORIGINAL.pdf) echo 'Select a working copy as target' >&2; exit 2 ;;
esac
cp -- "$base/ORIGINAL.pdf" "$target"
echo 'ROLLBACK: restored original bytes'
