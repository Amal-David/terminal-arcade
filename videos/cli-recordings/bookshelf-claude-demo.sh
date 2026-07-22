#!/bin/zsh
set -eu

# Render the redacted asciinema capture from a real Claude Code session.
# The cast was recorded in the disposable rewrite-prod-in-rust-by-lunch crate;
# only idle time is compressed. No tool call, code edit, test result, response,
# joke, or Bookshelf Stop-hook output is synthesized by this renderer.

repo_root="${0:A:h:h:h}"
cast="$repo_root/videos/cli-recordings/bookshelf-claude-actual.cast"
output_dir="$repo_root/sites/bookshelf/assets"
gif="${TMPDIR:-/tmp}/bookshelf-claude-actual.gif"

agg \
  --quiet \
  --theme github-dark \
  --font-size 20 \
  --speed 1.25 \
  --idle-time-limit 0.7 \
  --fps-cap 20 \
  --last-frame-duration 2 \
  --select '..17.2s' \
  "$cast" \
  "$gif"

ffmpeg -y -i "$gif" \
  -an \
  -c:v libx264 \
  -preset medium \
  -crf 24 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$output_dir/bookshelf-demo.mp4"

ffmpeg -y -i "$gif" -ss 17 -frames:v 1 "$output_dir/bookshelf-poster.png"
