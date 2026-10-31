#!/bin/bash
# HKBU SCIE1007 coursework science video. Runs one render at a time per slot so parallel branches never hold more than two on the GPU.
# Usage: bash gpu_slot.sh <command> [args...]. mkdir is atomic, a slot older than 15 minutes counts as abandoned.
D="$(cd "$(dirname "$0")" && pwd)/.slots"
mkdir -p "$D"
while :; do
  for s in 1 2; do
    if mkdir "$D/$s" 2>/dev/null; then
      trap 'rmdir "$D/$s" 2>/dev/null' EXIT
      "$@"
      exit $?
    fi
    [ -n "$(find "$D/$s" -maxdepth 0 -mmin +15 2>/dev/null)" ] && rmdir "$D/$s" 2>/dev/null
  done
  sleep 3
done
