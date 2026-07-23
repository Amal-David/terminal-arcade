#!/bin/zsh
set -eu

# Render the redacted asciinema capture from a real Claude Code session.
# The cast was recorded in the disposable rewrite-prod-in-rust-by-lunch crate;
# only idle time is compressed. No tool call, code edit, test result, response,
# joke, or Bookshelf Stop-hook output is synthesized by this renderer.

repo_root="${0:A:h:h:h}"
cast="$repo_root/videos/cli-recordings/bookshelf-claude-actual.cast"
output_dir="$repo_root/sites/bookshelf/assets"
source_gif="${TMPDIR:-/tmp}/bookshelf-claude-actual-source.gif"
source_mp4="${TMPDIR:-/tmp}/bookshelf-claude-actual-source.mp4"
source_poster="${TMPDIR:-/tmp}/bookshelf-claude-actual-source.png"
readme_gif="${TMPDIR:-/tmp}/bookshelf-claude-hero.gif"

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
  "$source_gif"

ffmpeg -y -i "$source_gif" \
  -an \
  -vf fps=30 \
  -c:v libx264 \
  -preset medium \
  -crf 24 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$source_mp4"

ffmpeg -y -ss 17 -i "$source_mp4" -frames:v 1 "$source_poster"

# Compress the setup and tool work, then give the actual Stop-hook quote the
# visual climax: a four-second hold, a modest camera push, and a bounded marker
# box. The edit preserves chronological order and never creates extra quotes.
filter_complex='[0:v]split=3[a][b][c];
[a]trim=start=0:end=4,setpts=(PTS-STARTPTS)/2.5,fps=30,scale=1102:832,pad=1224:924:61:46:color=black[a1];
[b]trim=start=6:end=12,setpts=(PTS-STARTPTS)/3,fps=30,scale=1102:832,pad=1224:924:61:46:color=black[b1];
[c]trim=start=12:end=17.89,setpts=(PTS-STARTPTS)/2,fps=30,scale=1102:832,pad=1224:924:61:46:color=black[c1];
[a1][b1][c1]concat=n=3:v=1:a=0[work];
[1:v]scale=1102:832,pad=1224:924:61:46:color=black,zoompan=z=min(zoom+0.0012\,1.08):x=iw/2-(iw/zoom/2):y=ih-ih/zoom:d=120:s=1224x924:fps=30,drawbox=x=28:y=588:w=1168:h=82:color=0xf6c85f@0.14:t=fill,drawbox=x=28:y=588:w=1168:h=82:color=0xf6c85f@0.95:t=4[hero];
[work][hero]concat=n=2:v=1:a=0,format=yuv420p[out]'

ffmpeg -y \
  -i "$source_mp4" \
  -loop 1 -framerate 30 -i "$source_poster" \
  -filter_complex "$filter_complex" \
  -map '[out]' \
  -t 10.55 \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -movflags +faststart \
  "$output_dir/bookshelf-demo.mp4"

ffmpeg -y -ss 9.5 -i "$output_dir/bookshelf-demo.mp4" \
  -frames:v 1 \
  "$output_dir/bookshelf-poster.png"

ffmpeg -y -i "$output_dir/bookshelf-demo.mp4" \
  -filter_complex 'fps=8,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5' \
  "$readme_gif"

print -r -- "$readme_gif"
